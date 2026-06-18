console.log("Clean script loaded");

document.addEventListener("DOMContentLoaded", () => {

    const mobileToggle = document.querySelector(".mobile-menu-toggle");
    const sidebar = document.querySelector(".sidebar");
    const mobileOverlay = document.querySelector(".mobile-overlay");

    function toggleMobileMenu() {
        sidebar.classList.toggle("active");
        mobileOverlay.classList.toggle("active");
        mobileToggle.classList.toggle("active");
        document.body.style.overflow = sidebar.classList.contains("active") ? "hidden" : "auto";
    }

    function closeMobileMenu() {
        sidebar.classList.remove("active");
        mobileOverlay.classList.remove("active");
        mobileToggle.classList.remove("active");
        document.body.style.overflow = "auto";
    }

    if (mobileToggle) {
        mobileToggle.addEventListener("click", toggleMobileMenu);
    }

    if (mobileOverlay) {
        mobileOverlay.addEventListener("click", closeMobileMenu);
    }

    document.querySelectorAll("nav a").forEach(anchor => {
        anchor.addEventListener("click", (e) => {
            const targetId = anchor.getAttribute("href");
            const section = document.querySelector(targetId);
            if (section) {
                e.preventDefault();
                section.scrollIntoView({ behavior: "smooth" });
                if (window.innerWidth <= 480) closeMobileMenu();
            }
        });
    });

    const demoLinks = document.querySelectorAll(".project-links a");
    demoLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            window.open(link.href, "_blank");
        });
    });

    const seeAllProjectsBtn = document.querySelector(".see-all-projects-btn");
    const projectsModal = document.getElementById("projects-modal");

    if (seeAllProjectsBtn && projectsModal) {
        seeAllProjectsBtn.addEventListener("click", (e) => {
            e.preventDefault();
            projectsModal.style.display = "block";
            document.body.style.overflow = "hidden";
        });
    }

    const educationItems = document.querySelectorAll(".education-item");
    const educationModal = document.getElementById("education-modal");
    const educationTitle = document.getElementById("education-modal-title");

    if (educationItems) {
        educationItems.forEach(item => {
            item.style.cursor = "pointer";
            item.addEventListener("click", () => {
                const eduType = item.getAttribute("data-edu");
                document.querySelectorAll(".education-details").forEach(d => d.style.display = "none");
                const details = document.getElementById(`${eduType}-details`);
                if (details) details.style.display = "block";
                educationTitle.textContent = item.querySelector("h3").textContent;
                educationModal.style.display = "block";
                document.body.style.overflow = "hidden";
            });
        });
    }

    const closeButtons = document.querySelectorAll(".close-modal");
    closeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".modal").forEach(m => (m.style.display = "none"));
            document.body.style.overflow = "auto";
        });
    });

    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("modal")) {
            e.target.style.display = "none";
            document.body.style.overflow = "auto";
        }
    });

    const skillTags = document.querySelectorAll(".skill-tag");
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, { threshold: 0.2 });

    skillTags.forEach(tag => {
        tag.style.opacity = "0";
        tag.style.transform = "translateY(20px)";
        observer.observe(tag);
    });

    const submitBtn = document.querySelector(".submit-btn");
    if (submitBtn) {
        submitBtn.addEventListener("click", (e) => {
            const form = document.getElementById("contactForm");
            if (form) sendEmail(e);
        });
    }

    // Certificate Modal Functionality
    const certLinks = document.querySelectorAll('.cert-link');
    const certificateModal = document.getElementById('certificate-modal');
    const certificateCanvas = document.getElementById('certificate-canvas');
    const certificateViewer = document.getElementById('certificate-viewer');
    const certificateLoading = document.getElementById('certificate-loading');

    console.log('Cert setup - links:', certLinks.length, 'modal:', !!certificateModal);

    if (certLinks.length > 0 && certificateModal && certificateCanvas) {
        certLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                // Get PDF URL from data attribute
                let pdfUrl = link.getAttribute('data-pdf-url');
                
                // Fallback to href if data attribute not present
                if (!pdfUrl) {
                    pdfUrl = link.getAttribute('href');
                }
                
                // Convert relative URL to absolute if needed
                if (pdfUrl && !pdfUrl.startsWith('http')) {
                    pdfUrl = window.location.origin + pdfUrl;
                }
                
                console.log('Opening Certificate PDF:', pdfUrl);
                
                // Show loading state
                certificateViewer.style.display = 'none';
                certificateLoading.style.display = 'flex';
                
                // Use PDF.js to render the PDF
                if (typeof pdfjsLib !== 'undefined') {
                    pdfjsLib.getDocument(pdfUrl).promise.then(pdf => {
                        console.log('PDF loaded, rendering first page');
                        return pdf.getPage(1).then(page => {
                            const scale = 1.5;
                            const viewport = page.getViewport({ scale });
                            certificateCanvas.width = viewport.width;
                            certificateCanvas.height = viewport.height;
                            
                            const renderContext = {
                                canvasContext: certificateCanvas.getContext('2d'),
                                viewport: viewport
                            };
                            
                            return page.render(renderContext).promise.then(() => {
                                console.log('Certificate PDF rendered successfully');
                                certificateLoading.style.display = 'none';
                                certificateViewer.style.display = 'flex';
                            });
                        });
                    }).catch(error => {
                        console.error('Failed to load certificate PDF:', error);
                        certificateLoading.innerHTML = '<div style="text-align: center;"><p style="color: #ff6b6b; font-size: 16px; margin-bottom: 15px;">Failed to load certificate</p></div>';
                    });
                } else {
                    console.error('PDF.js not loaded');
                    certificateLoading.innerHTML = '<p style="color: #ff6b6b; font-size: 16px;">PDF viewer not available</p>';
                }
                
                certificateModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            });
        });

        certificateModal.addEventListener('click', (e) => {
            if (e.target === certificateModal) {
                certificateModal.style.display = 'none';
                certificateCanvas.width = 0;
                certificateCanvas.height = 0;
                document.body.style.overflow = 'auto';
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && certificateModal.style.display === 'block') {
                certificateModal.style.display = 'none';
                certificateCanvas.width = 0;
                certificateCanvas.height = 0;
                document.body.style.overflow = 'auto';
            }
        });
    }

}); // DOMContentLoaded END

function sendEmail(e) {
    e.preventDefault();
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const subject = document.getElementById("subject").value;
    const message = document.getElementById("message").value;

    emailjs.send("service_snhvtuv", "template_bd1c457", {
        to_name: "Moinak",
        to_email: "moinak.mondal057@gmail.com",
        from_name: name,
        reply_to: email,
        email: email,
        subject: subject,
        message: message,
    }).then(
        () => {
            alert("Message sent successfully!");
            document.getElementById("contactForm").reset();
        },
        (error) => {
            alert("Failed to send message. Please try again.");
            console.error("EmailJS Error:", error);
        }
    );
}
