"""
URL configuration for portfolio_cms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from projects.views import PortfolioView
from portfolio_cms.seo_views import RobotsView, SitemapView

urlpatterns = [
    path('', PortfolioView.as_view(), name='portfolio'),  # Portfolio homepage
    path('admin/', admin.site.urls),
    path('api/', include('projects.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('robots.txt', RobotsView.as_view(), name='robots'),
    path('sitemap.xml', SitemapView.as_view(), name='sitemap'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve media files (user uploads like PDFs)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
