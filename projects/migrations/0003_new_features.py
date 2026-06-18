# Generated migration for new features

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_certificate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_name', models.CharField(help_text="Name of the person commenting", max_length=255)),
                ('author_email', models.EmailField(help_text="Email of the person commenting", max_length=254)),
                ('content', models.TextField(help_text="Comment content")),
                ('status', models.CharField(choices=[('PENDING', 'Pending Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', help_text="Approval status of the comment", max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="When the comment was created")),
                ('approved_at', models.DateTimeField(blank=True, help_text="When the comment was approved", null=True)),
                ('project', models.ForeignKey(help_text="The project this comment is for", on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='projects.project')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Visitor's name", max_length=255)),
                ('email', models.EmailField(help_text="Visitor's email address", max_length=254)),
                ('subject', models.CharField(help_text="Message subject", max_length=255)),
                ('message', models.TextField(help_text="Message content")),
                ('status', models.CharField(choices=[('NEW', 'New'), ('READ', 'Read'), ('REPLIED', 'Replied'), ('ARCHIVED', 'Archived')], default='NEW', help_text="Status of the contact message", max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="When the message was sent")),
                ('read_at', models.DateTimeField(blank=True, help_text="When the message was read", null=True)),
            ],
            options={
                'verbose_name': 'Contact Message',
                'verbose_name_plural': 'Contact Messages',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkExperience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_title', models.CharField(help_text="Job title/position", max_length=255)),
                ('company', models.CharField(help_text="Company name", max_length=255)),
                ('start_date', models.DateField(help_text="Start date of employment")),
                ('end_date', models.DateField(blank=True, help_text="End date of employment (leave blank if current)", null=True)),
                ('description', models.TextField(help_text="Description of responsibilities and achievements")),
                ('is_current', models.BooleanField(default=False, help_text="Mark as current position")),
                ('order', models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")),
            ],
            options={
                'verbose_name': 'Work Experience',
                'verbose_name_plural': 'Work Experiences',
                'ordering': ['-start_date', 'order'],
            },
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('degree', models.CharField(help_text="Degree or qualification (e.g., 'B.Tech Computer Science')", max_length=255)),
                ('institution', models.CharField(help_text="School/College/University name", max_length=255)),
                ('start_date', models.DateField(help_text="Start date of studies")),
                ('end_date', models.DateField(blank=True, help_text="End date of studies", null=True)),
                ('gpa', models.CharField(blank=True, help_text="GPA or CGPA (e.g., '8.25')", max_length=10)),
                ('description', models.TextField(blank=True, help_text="Additional details about education")),
                ('order', models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")),
            ],
            options={
                'verbose_name': 'Education',
                'verbose_name_plural': 'Educations',
                'ordering': ['-start_date', 'order'],
            },
        ),
        migrations.CreateModel(
            name='AboutProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('professional_summary', models.TextField(help_text="Your professional summary/bio (appears on About section)")),
                ('resume_file', models.FileField(help_text="Your resume/CV PDF to download", upload_to='resume/')),
                ('github_url', models.URLField(blank=True, help_text="GitHub profile URL")),
                ('linkedin_url', models.URLField(blank=True, help_text="LinkedIn profile URL")),
                ('twitter_url', models.URLField(blank=True, help_text="Twitter/X profile URL")),
                ('other_url', models.URLField(blank=True, help_text="Any other social/portfolio URL")),
                ('updated_at', models.DateTimeField(auto_now=True, help_text="Last updated timestamp")),
            ],
            options={
                'verbose_name': 'About Profile',
                'verbose_name_plural': 'About Profile',
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Skill name (e.g., 'Python', 'Django', 'React')", max_length=100, unique=True)),
                ('category', models.CharField(choices=[('LANGUAGE', 'Programming Language'), ('FRAMEWORK', 'Framework / Library'), ('TOOL', 'Tool / Platform'), ('DATABASE', 'Database / Storage'), ('OTHER', 'Other')], default='OTHER', help_text="Category of this skill", max_length=20)),
                ('proficiency', models.PositiveIntegerField(default=50, help_text="Proficiency level (0-100)")),
                ('order', models.PositiveIntegerField(default=0, help_text="Display order")),
                ('is_featured', models.BooleanField(default=False, help_text="Show in featured skills section")),
                ('auto_generated', models.BooleanField(default=False, help_text="Was this auto-generated from projects")),
            ],
            options={
                'verbose_name': 'Skill',
                'verbose_name_plural': 'Skills',
                'ordering': ['-is_featured', 'order', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['project', 'status'], name='projects_co_project_dd23c6_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['-created_at'], name='projects_co_created_ab12fg_idx'),
        ),
        migrations.AddIndex(
            model_name='contactmessage',
            index=models.Index(fields=['status', '-created_at'], name='projects_cm_status__12ab34_idx'),
        ),
    ]
