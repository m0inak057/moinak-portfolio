import logging
from django.conf import settings
from django.utils import timezone
from projects.models import Project
from .tools.github_tools import fetch_readme
from .tools.gemini_tools import generate_project_content

logger = logging.getLogger(__name__)


class ContentAgent:
    """
    Generates AI descriptions for projects that need it.
    Called by the Orchestrator with a list of Project PKs.
    """

    def run(self, project_pks: list[int]) -> dict:
        """
        Main entry point.
        
        Args:
            project_pks: List of Project PKs to process (from GitHubAgent result)
        
        Returns:
        {
            "processed": int,
            "succeeded": int,
            "failed": int,
            "errors": list[str]
        }
        """
        result = {
            "processed": len(project_pks),
            "succeeded": 0,
            "failed": 0,
            "errors": []
        }

        for pk in project_pks:
            try:
                self._process_project(pk, result)
            except Exception as e:
                result["failed"] += 1
                result["errors"].append(f"Project PK {pk}: {str(e)}")

        return result

    def _process_project(self, pk: int, result: dict):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            result["errors"].append(f"Project PK {pk} not found in DB")
            result["failed"] += 1
            return

        # Fetch README from GitHub
        readme = fetch_readme(project.repo_url, settings.GITHUB_TOKEN)

        # Generate content via Gemini
        content = generate_project_content(readme, project.repo_name)

        if not content:
            result["failed"] += 1
            result["errors"].append(
                f"Gemini failed to generate content for {project.repo_name}"
            )
            return

        # Update project fields
        project.ai_title = content["title"]
        project.ai_summary = content["summary"]
        project.key_features = content["features"]
        project.tech_stack = content["tech_stack"]
        project.category = content["category"]
        project.ai_generated_at = timezone.now()
        project.last_agent_run = timezone.now()

        # Only auto-make visible if Gemini thinks it's worth showing
        # AND it's a new project (never been visible before)
        # Moinak's manual visibility choices are respected — never override is_visible=True
        if content["should_be_visible"] and not project.is_visible:
            project.is_visible = True
            logger.info(f"Auto-published project: {project.repo_name}")

        project.save()
        result["succeeded"] += 1
        logger.info(f"Generated content for: {project.repo_name} (category: {content['category']})")
