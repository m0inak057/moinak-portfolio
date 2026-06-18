(function () {
    "use strict";

    const btn = document.getElementById("sync-btn");
    const icon = document.getElementById("sync-icon");
    const statusEl = document.getElementById("sync-status");
    const statusText = document.getElementById("sync-status-text");
    const reportEl = document.getElementById("sync-report");

    if (!btn) return; // guard — sync panel not in DOM

    // ── Load last sync result on page load ──────────────────
    fetch("/api/sync/last/")
        .then(r => r.json())
        .then(data => {
            if (data.status && data.status !== "never_run") {
                showReport(data);
            }
        })
        .catch(() => {}); // silently ignore if endpoint not available yet

    // ── Sync button click ───────────────────────────────────
    btn.addEventListener("click", function () {
        if (btn.disabled) return;
        triggerSync();
    });

    function triggerSync() {
        btn.disabled = true;
        btn.classList.add("spinning");
        setStatus("Syncing...", "");
        clearReport();

        fetch("/api/sync/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, data };
                });
            })
            .then(function ({ ok, data }) {
                btn.disabled = false;
                btn.classList.remove("spinning");

                if (!ok || data.status === "FAILED") {
                    setStatus(
                        "Sync failed — check errors",
                        "sync-status-error"
                    );
                    if (data.error) {
                        showSimpleReport([data.error]);
                    }
                    return;
                }

                const label =
                    data.status === "PARTIAL"
                        ? "Sync complete (with warnings)"
                        : "Sync complete!";
                setStatus(label, "sync-status-success");
                showReport(data);
            })
            .catch(function (err) {
                btn.disabled = false;
                btn.classList.remove("spinning");
                setStatus("Network error — try again", "sync-status-error");
                console.error("Sync error:", err);
            });
    }

    // ── Helpers ─────────────────────────────────────────────

    function setStatus(text, className) {
        statusText.textContent = text;
        statusEl.className = "sync-status-visible";
        if (className) statusEl.classList.add(className);
    }

    function clearReport() {
        reportEl.className = "sync-report-hidden";
        reportEl.innerHTML = "";
    }

    function showReport(data) {
        const lines = [];

        // Try structured details first
        const details = data.details || {};
        const gh = details.github || {};
        const cert = details.certificates || {};
        const content = details.content || {};

        if (gh.repos_found !== undefined) {
            lines.push(
                `<div class="report-line">Repos: <span>${gh.repos_found}</span> found · <span>${gh.created || 0}</span> new · <span>${gh.updated || 0}</span> updated</div>`
            );
        }
        if (content.processed > 0) {
            lines.push(
                `<div class="report-line">AI content: <span>${content.succeeded || 0}</span> generated</div>`
            );
        }
        if (cert.drive_files_found !== undefined) {
            lines.push(
                `<div class="report-line">Certificates: <span>${cert.created || 0}</span> added · <span>${cert.skipped || 0}</span> already exist</div>`
            );
        }

        // Fall back to summary string if no details
        if (lines.length === 0 && data.summary) {
            lines.push(`<div class="report-line">${data.summary}</div>`);
        }

        const errors = data.errors || (details.errors) || [];
        if (errors.length > 0) {
            lines.push(
                `<div class="report-line" style="color:#ff4444">${errors.length} warning(s) — check admin</div>`
            );
        }

        if (lines.length > 0) {
            reportEl.innerHTML = lines.join("");
            reportEl.className = "sync-report-visible";
        }
    }

    function showSimpleReport(errorList) {
        const html = errorList
            .map(e => `<div class="report-line" style="color:#ff4444">${e}</div>`)
            .join("");
        reportEl.innerHTML = html;
        reportEl.className = "sync-report-visible";
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    }
})();
