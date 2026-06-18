# Portfolio Rebuild — Master Overview

## What This Project Is

A complete rebuild of Moinak Mondal's personal portfolio (github: `m0inak057`).

The **old system** was only half-automated: certificates had to be manually uploaded through the Django admin panel, and AI content generation had to be triggered per-project by hand. The new system requires **zero manual input after initial setup** — one button click triggers a multi-agent pipeline that auto-discovers everything and updates the live portfolio.

---

## Golden Rule: What Stays vs What Changes

### STAYS EXACTLY THE SAME (do not touch)
- All frontend HTML structure, layout, and section order
- All CSS colours, fonts, and design tokens (see `01_FRONTEND_SPEC.md`)
- All section content: Hero, About, Skills, Experience, Projects, Certifications, Contact
- The sidebar navigation layout
- Space Grotesk font
- Mobile responsiveness behaviour

### CHANGES COMPLETELY (rebuild from scratch)
- How certificates reach the portfolio (Google Drive → agent → auto-publish, no manual upload)
- How project descriptions are written (LangGraph agent pipeline, not manual admin trigger)
- How the sync is triggered (single "Sync Now" API endpoint, no admin panel needed)
- Django app structure — new `agents/` app added, old `ai_service/` module replaced

---

## System Architecture — Bird's Eye View

```
USER (Moinak)
    |
    | clicks "Sync Now" button (or GitHub push webhook)
    v
[Django API — POST /api/sync/]
    |
    v
[Orchestrator Agent — LangGraph]
    |
    |---- [GitHub Agent] -----> fetches all repos + READMEs
    |---- [Certificate Agent] -> watches Google Drive folder, OCRs new PDFs
    |---- [Content Agent] ------> Gemini writes titles, summaries, tech stacks
    |
    v
[Django ORM — writes to DB]
    |
    v
[Frontend — reads from REST API, displays live data]
    |
    v
PORTFOLIO VISITOR sees fully updated portfolio
```

---

## Repository & File Structure (New)

```
portfolio_final/
└── portfolio-cms/
    ├── manage.py
    ├── requirements.txt
    ├── .env                         # secrets (never commit)
    ├── portfolio_cms/               # Django project settings
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── projects/                    # existing app — KEEP, extend models only
    │   ├── models.py                # Certificate + Project models (add drive_file_id field)
    │   ├── views.py                 # existing views — keep, add SyncView
    │   ├── serializers.py           # keep as-is
    │   └── urls.py                  # add /api/sync/ route
    ├── agents/                      # NEW app — entire agent layer lives here
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── orchestrator.py          # LangGraph graph definition
    │   ├── github_agent.py          # GitHub tool-calling agent
    │   ├── certificate_agent.py     # Google Drive + Gemini Vision agent
    │   ├── content_agent.py         # Gemini content generation agent
    │   └── tools/
    │       ├── github_tools.py      # fetch repos, fetch README
    │       ├── drive_tools.py       # list Drive folder, download PDF
    │       └── gemini_tools.py      # generate description, OCR certificate
    ├── static/
    │   ├── css/styles.css           # DO NOT MODIFY
    │   ├── js/script.js             # DO NOT MODIFY (add sync.js separately)
    │   └── images/
    └── templates/
        └── portfolio/
            └── index.html           # DO NOT MODIFY layout/styles (add sync button only)
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Web framework | Django 4.2 + DRF | Keep existing |
| Agent orchestration | LangGraph 0.2+ | New |
| AI | Google Gemini 1.5 Flash | Upgrade existing |
| Certificate OCR | Gemini Vision (`gemini-1.5-flash`) | New — replaces manual upload |
| Drive integration | `google-api-python-client` + `google-auth` | New |
| GitHub sync | `requests` against GitHub REST API | Keep existing logic |
| Database | SQLite (dev) → PostgreSQL (prod) | Keep |
| Frontend | Django templates + vanilla JS | Keep, minor additions only |

---

## Environment Variables Required

```env
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# GitHub
GITHUB_TOKEN=
GITHUB_USERNAME=m0inak057

# Gemini
GEMINI_API_KEY=

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_JSON=   # path to service account JSON file
GOOGLE_DRIVE_FOLDER_ID=          # ID of the folder to watch for new certificates

# Email (keep existing)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

---

## Build Order

Read the docs in this order and build in this order:

1. `01_FRONTEND_SPEC.md` — understand exactly what must not change
2. `02_DATABASE_MODELS.md` — model changes (minimal, additive only)
3. `03_GITHUB_AGENT.md` — build the GitHub agent first (simplest)
4. `04_CERTIFICATE_AGENT.md` — build the certificate agent
5. `05_CONTENT_AGENT.md` — build the Gemini content agent
6. `06_ORCHESTRATOR.md` — wire all agents together with LangGraph
7. `07_API_ENDPOINTS.md` — expose the sync endpoint + diff report
8. `08_SYNC_BUTTON_UI.md` — add the one-click sync button to the frontend

---

## Definition of "Done"

The system is complete when:
1. Moinak drops a certificate PDF into a specific Google Drive folder
2. Pushes new code to GitHub (or does neither)
3. Clicks "Sync Now" once
4. The live portfolio shows the new certificate, updated project descriptions, and a diff report — with zero other manual steps from Moinak
