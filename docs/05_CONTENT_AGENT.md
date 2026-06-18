# Content Agent

## Responsibility

Receives a list of Project PKs from the Orchestrator (provided by the GitHub Agent). For each project, fetches its README from GitHub and uses Gemini to generate a polished `ai_title`, `ai_summary`, `key_features`, `tech_stack`, and auto-decides the project `category` (MAJOR vs OTHER).

This replaces the old `ai_service/gemini_handler.py` manual trigger. The logic is the same but it now runs automatically and also determines visibility/category instead of leaving that to Moinak.

---

## File Location

```
agents/
├── content_agent.py
└── tools/
    └── gemini_tools.py    # extract_certificate_data already here, add generate_project_content
```

---

## Gemini Tool — `generate_project_content`

Add to `agents/tools/gemini_tools.py`:

```python
def generate_project_content(readme_text: str, repo_name: str) -> dict | None:
    """
    Given README content and repo name, returns structured project content.
    
    Returns:
    {
        "title": str,
        "summary": str,
        "features": list[str],
        "tech_stack": list[str],
        "category": "MAJOR" | "OTHER",    # agent decides based on complexity
        "should_be_visible": bool          # agent decides if worth showing
    }
    
    Returns None on failure.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Truncate README if too long
    readme_truncated = readme_text[:8000] if len(readme_text) > 8000 else readme_text
    
    prompt = f"""You are a Senior Technical Recruiter reviewing a developer's GitHub portfolio.
Analyze this repository and return a JSON object with EXACTLY these fields:

{{
  "title": "A refined, professional project title (2-5 words). Better than the repo name.",
  "summary": "For complex projects: 2-3 paragraph summary covering The Problem, The Solution, The Impact. Use strong verbs: Architected, Optimised, Implemented. For simple/toy projects: 1 sentence only.",
  "features": ["Feature 1 with technical detail", "Feature 2", "Feature 3"],
  "tech_stack": ["Technology1", "Framework2", "Tool3"],
  "category": "MAJOR if this is a substantial, real-world project with meaningful complexity, clear purpose, and good documentation. OTHER if it is a tutorial, assignment, experiment, or small utility.",
  "should_be_visible": true if the project is worth showing to recruiters (not empty, not a fork-only, not a hello-world), false otherwise
}}

Repository name: {repo_name}

README content:
{readme_truncated if readme_truncated else "No README available."}

Return ONLY valid JSON. No markdown fences, no explanation."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        
        data = json.loads(text)
        
        # Validate and sanitise
        data.setdefault("category", "OTHER")
        data.setdefault("should_be_visible", False)
        data["category"] = "MAJOR" if data["category"] == "MAJOR" else "OTHER"
        data["features"] = data.get("features", [])[:6]   # cap at 6
        data["tech_stack"] = data.get("tech_stack", [])[:8]  # cap at 8
        
        return data
    
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Content generation failed for {repo_name}: {str(e)}")
        return None
```

---

## Content Agent (`agents/content_agent.py`)

```python
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
```

---

## Key Decisions

**Agent decides MAJOR vs OTHER**  
The Gemini prompt explicitly asks the model to classify the project. This saves Moinak from having to manually categorise every repo. The prompt criteria: MAJOR = substantial, real-world, well-documented. OTHER = tutorial, experiment, small utility.

**Agent decides `is_visible`**  
For new projects: if Gemini says `should_be_visible: true`, the project is auto-published. For existing projects that are already visible: the agent never hides them (that would remove something Moinak deliberately showed). For existing projects that are already hidden manually: the agent respects that choice and does not re-publish.

**Graceful failure per project**  
If one project fails (GitHub API error, Gemini error), the agent logs it and continues to the next. The error is recorded in the `SyncLog.errors` list.

**README length cap at 8000 chars**  
Gemini 1.5 Flash has a large context window, but very long READMEs are wasteful. 8000 characters captures the meaningful content.

---

## Note on the Old `ai_service/` Module

The existing `portfolio-cms/ai_service/gemini_handler.py` can be kept but is no longer the primary path. The `ContentAgent` replaces it. The Django admin action "Generate AI content" still works via the old path for manual overrides, which is fine.
