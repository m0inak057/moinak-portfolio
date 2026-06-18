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
