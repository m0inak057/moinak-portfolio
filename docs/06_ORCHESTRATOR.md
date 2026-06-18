# Orchestrator — LangGraph Pipeline

## Responsibility

The Orchestrator is the brain. It defines a LangGraph `StateGraph` that runs the three agents in the correct order, passes state between them, handles errors gracefully, and writes the final `SyncLog` to the database.

---

## File Location

`agents/orchestrator.py`

---

## LangGraph State Schema

```python
from typing import TypedDict, Annotated
import operator

class SyncState(TypedDict):
    # Inputs
    triggered_by: str       # "manual" | "webhook"
    sync_log_id: int        # PK of the SyncLog record created at start

    # GitHub Agent outputs
    github_result: dict     # full result dict from GitHubAgent.run()

    # Certificate Agent outputs
    cert_result: dict       # full result dict from CertificateAgent.run()

    # Content Agent outputs
    content_result: dict    # full result dict from ContentAgent.run()

    # Accumulated errors across all agents
    errors: Annotated[list[str], operator.add]

    # Final status
    status: str             # "SUCCESS" | "PARTIAL" | "FAILED"
```

---

## LangGraph Graph Definition

```python
import logging
from django.utils import timezone
from langgraph.graph import StateGraph, END

from .github_agent import GitHubAgent
from .certificate_agent import CertificateAgent
from .content_agent import ContentAgent
from projects.models import SyncLog

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Node functions
# ─────────────────────────────────────────────

def run_github_agent(state: SyncState) -> SyncState:
    """Node 1: Sync GitHub repos."""
    logger.info("Orchestrator: running GitHub agent")
    result = GitHubAgent().run()
    state["github_result"] = result
    state["errors"] = result.get("errors", [])
    return state


def run_certificate_agent(state: SyncState) -> SyncState:
    """Node 2: Process new certificates from Google Drive."""
    logger.info("Orchestrator: running Certificate agent")
    result = CertificateAgent().run()
    state["cert_result"] = result
    state["errors"] = result.get("errors", [])
    return state


def run_content_agent(state: SyncState) -> SyncState:
    """Node 3: Generate AI content for new/updated projects."""
    logger.info("Orchestrator: running Content agent")
    
    project_pks = state.get("github_result", {}).get("needs_ai_generation", [])
    
    if not project_pks:
        logger.info("Orchestrator: no projects need content generation, skipping")
        state["content_result"] = {"processed": 0, "succeeded": 0, "failed": 0, "errors": []}
        return state
    
    result = ContentAgent().run(project_pks)
    state["content_result"] = result
    state["errors"] = result.get("errors", [])
    return state


def finalise(state: SyncState) -> SyncState:
    """Node 4: Write SyncLog, determine final status."""
    logger.info("Orchestrator: finalising sync run")
    
    all_errors = state.get("errors", [])
    github_result = state.get("github_result", {})
    cert_result = state.get("cert_result", {})
    content_result = state.get("content_result", {})
    
    # Determine status
    if not github_result and not cert_result:
        status = "FAILED"
    elif all_errors:
        status = "PARTIAL"
    else:
        status = "SUCCESS"
    
    state["status"] = status
    
    # Build human-readable summary
    lines = []
    if github_result:
        lines.append(
            f"GitHub: found {github_result.get('repos_found', 0)} repos, "
            f"created {github_result.get('created', 0)}, "
            f"updated {github_result.get('updated', 0)}."
        )
    if content_result and content_result.get("processed", 0) > 0:
        lines.append(
            f"AI content: generated for {content_result.get('succeeded', 0)} projects "
            f"({content_result.get('failed', 0)} failed)."
        )
    if cert_result:
        lines.append(
            f"Certificates: found {cert_result.get('drive_files_found', 0)} in Drive, "
            f"added {cert_result.get('created', 0)}, "
            f"skipped {cert_result.get('skipped', 0)} already processed."
        )
    if all_errors:
        lines.append(f"{len(all_errors)} error(s) encountered.")
    
    summary = " ".join(lines) if lines else "No changes detected."
    
    # Update SyncLog
    try:
        sync_log = SyncLog.objects.get(pk=state["sync_log_id"])
        sync_log.status = status
        sync_log.completed_at = timezone.now()
        sync_log.github_repos_found = github_result.get("repos_found", 0)
        sync_log.projects_created = github_result.get("created", 0)
        sync_log.projects_updated = github_result.get("updated", 0)
        sync_log.projects_ai_generated = content_result.get("succeeded", 0)
        sync_log.drive_files_found = cert_result.get("drive_files_found", 0)
        sync_log.certificates_created = cert_result.get("created", 0)
        sync_log.certificates_skipped = cert_result.get("skipped", 0)
        sync_log.errors = all_errors
        sync_log.summary = summary
        sync_log.save()
    except SyncLog.DoesNotExist:
        logger.error(f"SyncLog PK {state['sync_log_id']} not found during finalise")
    
    return state


# ─────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────

def build_sync_graph():
    """
    Builds and returns the compiled LangGraph sync pipeline.
    
    Graph topology:
    
    github_agent ──┐
                   ├──> content_agent ──> finalise ──> END
    cert_agent ────┘
    
    GitHub and Certificate agents run in parallel (LangGraph handles this).
    Content agent runs after GitHub agent (needs its output).
    """
    graph = StateGraph(SyncState)
    
    graph.add_node("github_agent", run_github_agent)
    graph.add_node("certificate_agent", run_certificate_agent)
    graph.add_node("content_agent", run_content_agent)
    graph.add_node("finalise", finalise)
    
    # Entry points — both start simultaneously
    graph.set_entry_point("github_agent")
    # Note: LangGraph doesn't have native parallel entry, so we sequence:
    # github → cert → content → finalise
    # This is fine for the current scale (< 5 seconds total)
    graph.add_edge("github_agent", "certificate_agent")
    graph.add_edge("certificate_agent", "content_agent")
    graph.add_edge("content_agent", "finalise")
    graph.add_edge("finalise", END)
    
    return graph.compile()


# Module-level compiled graph (created once, reused across requests)
sync_graph = build_sync_graph()
```

---

## Orchestrator Entry Point Function

This is what the Django view calls:

```python
def run_sync(triggered_by: str = "manual") -> dict:
    """
    Creates a SyncLog, runs the full LangGraph pipeline, returns the result.
    
    This is the function called by the Django SyncView.
    
    Returns the final SyncState dict.
    """
    # Create SyncLog record at start so the frontend can poll it
    sync_log = SyncLog.objects.create(status="RUNNING")
    
    initial_state: SyncState = {
        "triggered_by": triggered_by,
        "sync_log_id": sync_log.pk,
        "github_result": {},
        "cert_result": {},
        "content_result": {},
        "errors": [],
        "status": "RUNNING"
    }
    
    try:
        final_state = sync_graph.invoke(initial_state)
        return final_state
    except Exception as e:
        logger.error(f"Orchestrator pipeline failed: {str(e)}")
        sync_log.status = "FAILED"
        sync_log.errors = [str(e)]
        sync_log.completed_at = timezone.now()
        sync_log.save()
        raise
```

---

## New App Setup

Create `agents/apps.py`:

```python
from django.apps import AppConfig

class AgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents'
```

Create `agents/__init__.py` — empty file.

Add to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'projects',
    'agents',   # add this
]
```

---

## New Dependencies

Add to `requirements.txt`:

```
langgraph==0.2.28
langchain-core==0.3.15
```

---

## Error Handling Philosophy

- **Per-agent errors** are caught inside each agent's `run()` method and returned in its result dict's `errors` list
- **Catastrophic errors** (e.g. LangGraph itself crashes) are caught in `run_sync()` and written to the SyncLog directly
- The pipeline never raises an unhandled exception to the Django view — the view always gets a response
- A sync that partially fails (e.g. GitHub worked, certificate agent failed) logs status `PARTIAL` not `FAILED`
