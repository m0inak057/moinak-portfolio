# API Endpoints

## Overview

All existing API endpoints stay unchanged. This document covers only the **new endpoints** added for the agent sync system.

---

## Existing Endpoints — Do Not Change

These already exist and work. Leave them alone:

```
GET    /api/projects/              List visible projects
GET    /api/projects/major/        List MAJOR projects
GET    /api/projects/other/        List OTHER projects
PATCH  /api/projects/{id}/         Update project
POST   /api/projects/{id}/generate-content/   Manual AI generation
GET    /api/certificates/          List visible certificates
POST   /api/contact/               Submit contact message
GET    /api/experience/            Work experience
GET    /api/education/             Education entries
GET    /api/about/                 About profile
```

---

## New Endpoint 1 — Trigger Sync

```
POST /api/sync/
```

Triggers the full LangGraph agent pipeline. Runs synchronously (the HTTP request blocks until the sync completes). At current scale (< 20 repos, < 15 cert files), this takes 15–45 seconds.

**Request body**: none required

**Response (200 OK — success or partial)**:
```json
{
    "status": "SUCCESS",
    "sync_log_id": 42,
    "summary": "GitHub: found 18 repos, created 2, updated 1. AI content: generated for 2 projects. Certificates: found 8 in Drive, added 1, skipped 7 already processed.",
    "details": {
        "github": {
            "repos_found": 18,
            "created": 2,
            "updated": 1,
            "needs_ai_generation": [34, 35]
        },
        "certificates": {
            "drive_files_found": 8,
            "created": 1,
            "skipped": 7
        },
        "content": {
            "processed": 2,
            "succeeded": 2,
            "failed": 0
        },
        "errors": []
    }
}
```

**Response (500 — total failure)**:
```json
{
    "status": "FAILED",
    "error": "Google Drive listing failed: invalid_grant"
}
```

**Implementation** in `projects/views.py`:

```python
from agents.orchestrator import run_sync

class SyncView(View):
    """
    POST /api/sync/
    Triggers the full agent pipeline.
    """
    
    def post(self, request):
        import json
        from django.http import JsonResponse
        
        try:
            final_state = run_sync(triggered_by="manual")
            
            return JsonResponse({
                "status": final_state.get("status", "UNKNOWN"),
                "sync_log_id": final_state.get("sync_log_id"),
                "summary": final_state.get("github_result", {}).get("summary", ""),
                "details": {
                    "github": final_state.get("github_result", {}),
                    "certificates": final_state.get("cert_result", {}),
                    "content": final_state.get("content_result", {}),
                    "errors": final_state.get("errors", [])
                }
            })
        
        except Exception as e:
            return JsonResponse(
                {"status": "FAILED", "error": str(e)},
                status=500
            )
```

---

## New Endpoint 2 — Get Last Sync Log

```
GET /api/sync/last/
```

Returns the most recent `SyncLog` entry. Used by the frontend to show the last sync result without triggering a new sync.

**Response (200)**:
```json
{
    "id": 42,
    "status": "SUCCESS",
    "triggered_at": "2025-05-09T14:32:00Z",
    "completed_at": "2025-05-09T14:32:38Z",
    "summary": "...",
    "projects_created": 2,
    "certificates_created": 1,
    "errors": []
}
```

**Implementation** in `projects/views.py`:

```python
class LastSyncView(View):
    def get(self, request):
        from django.http import JsonResponse
        from projects.models import SyncLog
        
        log = SyncLog.objects.first()  # ordered by -triggered_at
        if not log:
            return JsonResponse({"status": "never_run"})
        
        return JsonResponse({
            "id": log.pk,
            "status": log.status,
            "triggered_at": log.triggered_at.isoformat(),
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "summary": log.summary,
            "projects_created": log.projects_created,
            "projects_updated": log.projects_updated,
            "projects_ai_generated": log.projects_ai_generated,
            "certificates_created": log.certificates_created,
            "errors": log.errors
        })
```

---

## URL Registration

Add to `projects/urls.py`:

```python
from django.urls import path
from .views import SyncView, LastSyncView

# Add these to the existing urlpatterns list:
path('sync/', SyncView.as_view(), name='sync'),
path('sync/last/', LastSyncView.as_view(), name='sync-last'),
```

The existing `router` registration for the ViewSets stays unchanged.

---

## CSRF Note

The sync button on the frontend is on the same origin as the Django server, so CSRF is handled by reading the `csrftoken` cookie — the same pattern already used for the contact form in `script.js`:

```javascript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```
