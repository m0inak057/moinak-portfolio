# GitHub Agent

## Responsibility

The GitHub agent fetches all public repositories for the user `m0inak057`, creates or updates `Project` records in the database, and flags new/changed projects for the Content Agent to process.

---

## File Location

`agents/github_agent.py`

---

## Tools Used

Located in `agents/tools/github_tools.py`. These are plain Python functions that the agent calls.

### `fetch_all_repos(username: str, token: str) -> list[dict]`

Calls the GitHub REST API to list all public repos.

```python
import requests

def fetch_all_repos(username: str, token: str) -> list[dict]:
    """
    Returns list of repo dicts from GitHub API.
    Handles pagination — fetches ALL pages.
    Each dict contains: id, name, html_url, description, updated_at, pushed_at
    """
    headers = {"Authorization": f"token {token}"}
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos
```

### `fetch_readme(repo_url: str, token: str) -> str`

Fetches the raw README.md content from a repo.

```python
def fetch_readme(repo_url: str, token: str) -> str:
    """
    Given a GitHub repo HTML URL (e.g. https://github.com/user/repo),
    fetches the raw README.md content.
    Returns empty string if no README exists.
    """
    # Extract owner/repo from URL
    parts = repo_url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]
    
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 404:
        return ""
    
    resp.raise_for_status()
    import base64
    content = resp.json().get("content", "")
    return base64.b64decode(content).decode("utf-8", errors="replace")
```

---

## Agent Logic (`agents/github_agent.py`)

This is a plain Python class (not a LangGraph node itself — the Orchestrator wraps it). The Orchestrator calls `run()` and receives back a structured result dict.

```python
import logging
from django.conf import settings
from projects.models import Project
from .tools.github_tools import fetch_all_repos, fetch_readme

logger = logging.getLogger(__name__)

class GitHubAgent:
    """
    Syncs GitHub repos into the Project model.
    Returns a result dict consumed by the Orchestrator.
    """

    def run(self) -> dict:
        """
        Main entry point.
        Returns:
        {
            "repos_found": int,
            "created": int,
            "updated": int,
            "needs_ai_generation": list[int],  # Project PKs that need Content Agent
            "errors": list[str]
        }
        """
        result = {
            "repos_found": 0,
            "created": 0,
            "updated": 0,
            "needs_ai_generation": [],
            "errors": []
        }

        try:
            repos = fetch_all_repos(
                username=settings.GITHUB_USERNAME,
                token=settings.GITHUB_TOKEN
            )
        except Exception as e:
            result["errors"].append(f"GitHub API fetch failed: {str(e)}")
            return result

        result["repos_found"] = len(repos)

        for repo in repos:
            try:
                self._process_repo(repo, result)
            except Exception as e:
                result["errors"].append(f"Error processing repo {repo.get('name')}: {str(e)}")

        return result

    def _process_repo(self, repo: dict, result: dict):
        github_id = repo["id"]
        repo_name = repo["name"]
        repo_url = repo["html_url"]
        repo_description = repo.get("description") or ""

        project, created = Project.objects.get_or_create(
            github_id=github_id,
            defaults={
                "repo_name": repo_name,
                "repo_url": repo_url,
                "repo_description": repo_description,
                "is_visible": False,   # new projects default to hidden
                "category": "OTHER",   # Content Agent will upgrade to MAJOR if appropriate
            }
        )

        if created:
            result["created"] += 1
            result["needs_ai_generation"].append(project.pk)
            logger.info(f"Created new project: {repo_name}")
        else:
            # Update repo metadata in case description or URL changed
            changed = False
            if project.repo_description != repo_description:
                project.repo_description = repo_description
                changed = True
            if project.repo_url != repo_url:
                project.repo_url = repo_url
                changed = True

            # Re-generate AI content if repo was pushed more recently than last agent run
            repo_pushed = repo.get("pushed_at")
            if repo_pushed and project.last_agent_run:
                from django.utils.dateparse import parse_datetime
                pushed_dt = parse_datetime(repo_pushed)
                if pushed_dt and pushed_dt > project.last_agent_run:
                    result["needs_ai_generation"].append(project.pk)
                    changed = True
            elif not project.ai_title:
                # Never had AI content generated
                result["needs_ai_generation"].append(project.pk)

            if changed:
                project.save()
                result["updated"] += 1
```

---

## Key Decisions

**New projects default to `is_visible=False`**  
Moinak can choose to make a project visible through the admin panel or by updating the DB directly. The agent never auto-publishes a project without AI content being generated first.

**The agent tells the Orchestrator which projects need Content Agent**  
It returns `needs_ai_generation` — a list of Project PKs. The Orchestrator passes this list to the Content Agent. This keeps the agents decoupled.

**Re-run logic**  
If a project's `pushed_at` timestamp on GitHub is more recent than `last_agent_run` in the DB, the AI content is regenerated. This means updated READMEs automatically get fresh descriptions on the next sync.

---

## Settings Required

```python
# portfolio_cms/settings.py — already exists
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'm0inak057')
```
