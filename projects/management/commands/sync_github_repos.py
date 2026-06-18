import logging
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from projects.models import Project

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync GitHub repositories for a user into the Project model'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=settings.GITHUB_USERNAME,
            help=f'GitHub username to sync (default: {settings.GITHUB_USERNAME})'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all repositories, even if already synced'
        )
    
    def handle(self, *args, **options):
        username = options['username']
        force = options.get('force', False)
        
        self.stdout.write(f"Starting GitHub sync for user: {username}")
        
        try:
            repos = self.fetch_all_repos(username)
            self.stdout.write(f"Found {len(repos)} repositories")
            
            created_count = 0
            updated_count = 0
            
            for repo in repos:
                # Skip forked repos by default (customize if needed)
                if repo.get('fork'):
                    self.stdout.write(f"  Skipping forked repo: {repo['name']}")
                    continue
                
                project, created = Project.objects.update_or_create(
                    github_id=repo['id'],
                    defaults={
                        'repo_name': repo['name'],
                        'repo_url': repo['html_url'],
                        'repo_description': repo.get('description', ''),
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {repo['name']}")
                    )
                elif force or project.repo_description != repo.get('description', ''):
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ⟳ Updated: {repo['name']}")
                    )
            
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Sync complete!\n"
                f"  Created: {created_count}\n"
                f"  Updated: {updated_count}\n"
                f"  Total projects in DB: {Project.objects.count()}"
            ))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during sync: {str(e)}"))
            logger.exception("GitHub sync failed")
    
    def fetch_all_repos(self, username: str, per_page: int = 100) -> list:
        """
        Fetch all repositories for a given GitHub user.
        Handles pagination automatically.
        
        Args:
            username: GitHub username
            per_page: Number of repos per API request (max 100)
            
        Returns:
            List of repository objects
        """
        repos = []
        page = 1
        
        headers = {}
        if settings.GITHUB_TOKEN:
            headers['Authorization'] = f'token {settings.GITHUB_TOKEN}'
            headers['Accept'] = 'application/vnd.github.v3+json'
        
        while True:
            url = f"https://api.github.com/users/{username}/repos"
            params = {
                'per_page': per_page,
                'page': page,
                'sort': 'updated',
                'direction': 'desc',
            }
            
            self.stdout.write(f"  Fetching page {page}...", ending=' ')
            
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                page_repos = response.json()
                if not page_repos:
                    self.stdout.write(self.style.SUCCESS("Done"))
                    break
                
                repos.extend(page_repos)
                self.stdout.write(self.style.SUCCESS(f"({len(page_repos)} repos)"))
                page += 1
                
                # Check rate limit headers
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = response.headers['X-RateLimit-Remaining']
                    if int(remaining) < 10:
                        self.stdout.write(
                            self.style.WARNING(f"Warning: Only {remaining} API calls remaining")
                        )
            
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"API Error: {str(e)}"))
                raise
        
        return repos
