"""
SEO views for robots.txt and sitemap.xml
"""
from django.http import HttpResponse
from django.views import View
from django.urls import reverse
from projects.models import Project, Certificate
from django.utils import timezone


class RobotsView(View):
    """Serve robots.txt for search engine crawlers"""
    
    def get(self, request):
        content = """User-agent: *
Allow: /
Allow: /api/
Disallow: /admin/
Disallow: /api-auth/

Sitemap: https://{domain}/sitemap.xml
""".format(domain=request.get_host())
        return HttpResponse(content, content_type="text/plain")


class SitemapView(View):
    """Serve sitemap.xml for search engines"""
    
    def get(self, request):
        host = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        
        pages = [
            {
                'url': f"{protocol}://{host}/",
                'lastmod': timezone.now().isoformat(),
                'changefreq': 'weekly',
                'priority': '1.0'
            },
        ]
        
        # Add all visible projects
        for project in Project.objects.filter(is_visible=True):
            pages.append({
                'url': f"{protocol}://{host}/api/projects/{project.id}/",
                'lastmod': project.last_synced.isoformat(),
                'changefreq': 'monthly',
                'priority': '0.8'
            })
        
        # Add all visible certificates
        for cert in Certificate.objects.filter(is_visible=True):
            pages.append({
                'url': f"{protocol}://{host}/api/certificates/{cert.id}/",
                'lastmod': cert.updated_at.isoformat(),
                'changefreq': 'yearly',
                'priority': '0.6'
            })
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for page in pages:
            xml += f"""
  <url>
    <loc>{page['url']}</loc>
    <lastmod>{page['lastmod']}</lastmod>
    <changefreq>{page['changefreq']}</changefreq>
    <priority>{page['priority']}</priority>
  </url>
"""
        
        xml += '\n</urlset>'
        return HttpResponse(xml, content_type="application/xml")
