# Sync Button UI

## The Only Permitted Frontend Change

The existing `index.html`, `styles.css`, and `script.js` must not be modified except for:

1. One HTML addition to `index.html` — the sync panel
2. One new file `static/js/sync.js` — all sync JS lives here, referenced at the bottom of `index.html`

---

## Where to Place the Sync Panel in `index.html`

Add the sync panel immediately **after** the closing `</nav>` sidebar tag and **before** `<div class="mobile-overlay">`.

```html
<!-- Sync Panel — place after </nav> and before mobile-overlay div -->
<div id="sync-panel">
    <button id="sync-btn" title="Sync portfolio with GitHub and Google Drive">
        <i class="fas fa-sync-alt" id="sync-icon"></i>
    </button>
    <div id="sync-status" class="sync-status-hidden">
        <span id="sync-status-text"></span>
    </div>
    <div id="sync-report" class="sync-report-hidden"></div>
</div>
```

Also add this line at the **bottom of `<body>`**, just before the existing `<script src="{% static 'js/script.js' %}">` tag:

```html
<script src="{% static 'js/sync.js' %}"></script>
```

---

## CSS to Add in `styles.css`

Add the following block at the very **bottom** of `static/css/styles.css`. Do not change anything above it.

```css
/* ─── Sync Panel ─────────────────────────────────────────── */

#sync-panel {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 999;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
}

#sync-btn {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background-color: var(--dark-gray);
    border: 2px solid var(--accent-color);
    color: var(--accent-color);
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s, box-shadow 0.2s;
}

#sync-btn:hover {
    background-color: var(--accent-color);
    color: var(--bg-color);
    box-shadow: 0 0 12px rgba(0, 255, 136, 0.4);
}

#sync-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

#sync-btn.spinning #sync-icon {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}

.sync-status-hidden {
    display: none;
}

.sync-status-visible {
    display: block;
    background: var(--dark-gray);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    color: var(--gray-text);
    max-width: 220px;
    text-align: right;
}

.sync-status-success {
    border-color: var(--accent-color);
    color: var(--accent-color);
}

.sync-status-error {
    border-color: #ff4444;
    color: #ff4444;
}

.sync-report-hidden {
    display: none;
}

.sync-report-visible {
    display: block;
    background: var(--dark-gray);
    border: 1px solid rgba(0, 255, 136, 0.15);
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 11px;
    color: var(--gray-text);
    max-width: 280px;
    text-align: right;
    line-height: 1.6;
}

.sync-report-visible .report-line {
    margin-bottom: 3px;
}

.sync-report-visible .report-line span {
    color: var(--accent-color);
    font-weight: 600;
}
```

---

## `static/js/sync.js` — Complete File

Create this as a new file. Do not modify `script.js`.

```javascript
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
```

---

## Visual Behaviour Summary

| State | Button | Status chip | Report |
|---|---|---|---|
| Page load (synced before) | Normal | Hidden | Shows last sync stats |
| Page load (never synced) | Normal | Hidden | Hidden |
| Sync running | Disabled + spinning icon | "Syncing..." grey | Hidden |
| Sync success | Normal | "Sync complete!" green | Shows counts |
| Sync partial | Normal | "Sync complete (with warnings)" green | Shows counts + warning count |
| Sync failed | Normal | "Sync failed" red | Shows error message |

---

## Important: This Button is for Moinak Only

The sync button is a floating button at the bottom-right. Portfolio visitors will see it too in the current implementation. If Moinak wants to hide it from visitors later, he can put it behind Django's `request.user.is_staff` check in the template:

```html
{% if request.user.is_staff %}
<div id="sync-panel">...</div>
{% endif %}
```

For now, it's visible to everyone — the button just won't do anything harmful if a visitor clicks it (it just runs the sync, which is idempotent and safe).
