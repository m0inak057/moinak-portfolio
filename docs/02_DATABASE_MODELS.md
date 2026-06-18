# Database Models

## Philosophy

The existing models are well-structured. Make the **minimum additive changes** needed for the new agent system. Do not remove any existing fields. Do not restructure existing models.

---

## Existing Models — Keep As-Is

All of these models already exist in `projects/models.py`. Do not change their fields:

- `Certificate` — name, issuer, issued_date, pdf_file, is_visible, created_at, updated_at
- `Project` — github_id, repo_name, repo_url, repo_description, is_visible, category, ai_title, ai_summary, key_features, tech_stack, last_synced, ai_generated_at, created_at
- `Comment`
- `ContactMessage`
- `WorkExperience`
- `Education`
- `AboutProfile`
- `Skill`

---

## Changes to Existing Models

### Certificate — add two fields

```python
# Add to Certificate model in projects/models.py

drive_file_id = models.CharField(
    max_length=255,
    blank=True,
    null=True,
    unique=True,
    help_text="Google Drive file ID — used to detect duplicates and avoid re-processing"
)

auto_extracted = models.BooleanField(
    default=False,
    help_text="True if this certificate was extracted by the AI agent, False if manually created"
)
```

**Why `drive_file_id`**: The certificate agent checks this field before processing. If a Drive file ID already exists in the DB, the agent skips it. This is the deduplication mechanism — without it, every sync would re-create all certificates.

### Project — add one field

```python
# Add to Project model in projects/models.py

last_agent_run = models.DateTimeField(
    null=True,
    blank=True,
    help_text="Timestamp of the last time the agent processed this project"
)
```

---

## New Model — SyncLog

Add this new model to `projects/models.py`. It records every sync run so the frontend can display a diff report.

```python
class SyncLog(models.Model):
    """
    Records the result of each agent sync run.
    Used to display the diff report after a sync.
    """

    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('PARTIAL', 'Partial — some errors'),
        ('FAILED', 'Failed'),
    ]

    triggered_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='RUNNING')

    # GitHub agent results
    github_repos_found = models.IntegerField(default=0)
    projects_created = models.IntegerField(default=0)
    projects_updated = models.IntegerField(default=0)
    projects_ai_generated = models.IntegerField(default=0)

    # Certificate agent results
    drive_files_found = models.IntegerField(default=0)
    certificates_created = models.IntegerField(default=0)
    certificates_skipped = models.IntegerField(default=0)

    # Error tracking
    errors = models.JSONField(default=list, blank=True,
        help_text="List of error strings encountered during the run")

    # Human-readable summary for the UI diff report
    summary = models.TextField(blank=True,
        help_text="Plain English summary of what changed this run")

    class Meta:
        ordering = ['-triggered_at']
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"

    def __str__(self):
        return f"Sync {self.triggered_at.strftime('%Y-%m-%d %H:%M')} — {self.status}"
```

---

## Migration

After making the above changes, run:

```bash
python manage.py makemigrations projects
python manage.py migrate
```

---

## Admin Registration

Add `SyncLog` to Django admin in `projects/admin.py`:

```python
from .models import SyncLog

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['triggered_at', 'status', 'projects_created', 'certificates_created', 'completed_at']
    list_filter = ['status']
    readonly_fields = ['triggered_at', 'completed_at', 'errors', 'summary']
```
