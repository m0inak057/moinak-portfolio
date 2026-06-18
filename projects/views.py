import logging
from django.shortcuts import render
from django.views import View
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project, Certificate, Comment, ContactMessage, WorkExperience, Education, AboutProfile, Skill, SyncLog
from .serializers import (
    ProjectSerializer, CertificateSerializer, CommentSerializer, 
    ContactMessageSerializer, WorkExperienceSerializer, EducationSerializer,
    AboutProfileSerializer, SkillSerializer
)
from ai_service.gemini_handler import GeminiProjectAnalyzer
from agents.orchestrator import run_sync

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Project management.
    
    Public endpoints:
    - GET /api/projects/ - List visible projects
    - GET /api/projects/major/ - List visible MAJOR projects
    - GET /api/projects/other/ - List visible OTHER projects
    
    Admin endpoints:
    - PATCH /api/projects/{id}/ - Update project
    - POST /api/projects/{id}/generate-content/ - Generate AI content
    """
    
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_visible']
    search_fields = ['repo_name', 'ai_title']
    ordering_fields = ['last_synced', 'created_at', 'category']
    ordering = ['-last_synced']
    
    def get_queryset(self):
        """Override to filter only visible projects for non-admin users"""
        queryset = super().get_queryset()
        
        # Check if user is accessing admin-only data
        # For now, we're allowing all access (can be restricted later with authentication)
        # In production, add: if not self.request.user.is_staff: queryset = queryset.filter(is_visible=True)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List projects - only visible ones for public API"""
        # Filter to visible only unless admin
        if not request.user.is_staff:
            self.queryset = Project.objects.filter(is_visible=True)
        
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='major')
    def major_projects(self, request):
        """Get only MAJOR category projects"""
        queryset = self.queryset.filter(category='MAJOR', is_visible=True)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='other')
    def other_projects(self, request):
        """Get only OTHER category projects"""
        queryset = self.queryset.filter(category='OTHER', is_visible=True)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_content(self, request, pk=None):
        """
        Generate or refresh AI content for a specific project.
        POST /api/projects/{id}/generate-content/
        """
        project = self.get_object()
        
        try:
            analyzer = GeminiProjectAnalyzer()
            analyzer.analyze_and_update_project(project)
            
            serializer = self.get_serializer(project)
            return Response(
                {
                    'status': 'success',
                    'message': f'AI content generated successfully for {project.repo_name}',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error generating content for project {project.id}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': f'Failed to generate AI content: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_update(self, serializer):
        """Allow updating is_visible and category fields"""
        serializer.save()


class CertificateViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Certificate management.
    
    Public endpoints:
    - GET /api/certificates/ - List visible certificates
    
    Admin endpoints:
    - POST /api/certificates/ - Create certificate
    - PATCH /api/certificates/{id}/ - Update certificate
    - DELETE /api/certificates/{id}/ - Delete certificate
    """
    
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_visible']
    search_fields = ['name', 'issuer']
    ordering_fields = ['issued_date', 'created_at']
    ordering = ['-issued_date']
    
    def get_queryset(self):
        """Override to filter only visible certificates for non-admin users"""
        queryset = super().get_queryset()
        
        # Filter to visible only unless admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_visible=True)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List certificates - only visible ones for public API"""
        # Filter to visible only unless admin
        if not request.user.is_staff:
            self.queryset = Certificate.objects.filter(is_visible=True)
        
        return super().list(request, *args, **kwargs)


class PortfolioView(View):
    """
    Render the public portfolio page with dynamic project and certificate data.
    Fetches visible MAJOR and OTHER projects, plus all visible certificates,
    work experience, education, skills, and about profile.
    """
    
    def get(self, request):
        """Render portfolio with all dynamic data"""
        # Use list() to avoid SQLite compound statement ORDER BY issue
        major_projects = list(Project.objects.filter(
            is_visible=True, 
            category='MAJOR'
        ).order_by('-last_synced'))
        
        other_projects = list(Project.objects.filter(
            is_visible=True, 
            category='OTHER'
        ).order_by('-last_synced'))
        
        certificates = list(Certificate.objects.filter(
            is_visible=True
        ).order_by('-issued_date'))
        
        work_experiences = list(WorkExperience.objects.all().order_by('-start_date'))
        educations = list(Education.objects.all().order_by('-start_date'))
        
        # Get about profile (singleton)
        about_profile = AboutProfile.objects.first()
        
        # Extract all tech stacks from visible projects (avoid union() SQLite issue)
        tech_from_projects = []
        all_projects = major_projects + other_projects
        for project in all_projects:
            if project.tech_stack:
                tech_from_projects.extend(project.tech_stack)
        
        context = {
            'major_projects': major_projects,
            'other_projects': other_projects,
            'certificates': certificates,
            'work_experiences': work_experiences,
            'educations': educations,
            'about_profile': about_profile,
            'total_projects': len(major_projects) + len(other_projects),
            'total_certificates': len(certificates),
            'tech_stack_count': len(set(tech_from_projects)),
        }
        
        return render(request, 'portfolio/index.html', context)


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Comment management.
    
    Public endpoints:
    - GET /api/comments/ - List approved comments
    - POST /api/comments/ - Submit a new comment (pending moderation)
    
    Admin endpoints:
    - PATCH /api/comments/{id}/ - Approve/reject comments
    """
    
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter only approved comments for public API"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='APPROVED')
        
        return queryset
    
    def perform_create(self, serializer):
        """Set comment status to PENDING by default"""
        serializer.save(status='PENDING')


class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Contact messages.
    
    Public endpoints:
    - POST /api/contact/ - Submit a contact message
    
    Admin endpoints:
    - GET /api/contact/ - View all messages
    - PATCH /api/contact/{id}/ - Mark as read/replied
    """
    
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only admin can view contact messages"""
        if self.request.user.is_staff:
            return super().get_queryset()
        return ContactMessage.objects.none()


class WorkExperienceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for Work Experience.
    
    Public endpoints:
    - GET /api/experience/ - List all work experiences
    """
    
    queryset = WorkExperience.objects.all()
    serializer_class = WorkExperienceSerializer
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['start_date', 'order']
    ordering = ['-start_date']


class EducationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for Education.
    
    Public endpoints:
    - GET /api/education/ - List all education entries
    """
    
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['start_date', 'order']
    ordering = ['-start_date']


class AboutProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for About Profile (Singleton).
    
    Public endpoints:
    - GET /api/about/ - Get portfolio owner profile information
    """
    
    queryset = AboutProfile.objects.all()
    serializer_class = AboutProfileSerializer
    pagination_class = None


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for Skills.
    
    Public endpoints:
    - GET /api/skills/ - List all skills
    """
    
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured']
    ordering_fields = ['is_featured', 'order', 'proficiency']
    ordering = ['-is_featured', 'order']


class SyncView(View):
    """
    POST /api/sync/
    Triggers the full agent pipeline.
    """
    
    def post(self, request):
        import json
        from django.http import JsonResponse
        
        try:
            final_state = run_sync(triggered_by="manual")
            
            return JsonResponse({
                "status": final_state.get("status", "UNKNOWN"),
                "sync_log_id": final_state.get("sync_log_id"),
                "summary": final_state.get("github_result", {}).get("summary", ""),
                "details": {
                    "github": final_state.get("github_result", {}),
                    "certificates": final_state.get("cert_result", {}),
                    "content": final_state.get("content_result", {}),
                    "errors": final_state.get("errors", [])
                }
            })
        
        except Exception as e:
            return JsonResponse(
                {"status": "FAILED", "error": str(e)},
                status=500
            )


class LastSyncView(View):
    """
    GET /api/sync/last/
    Returns the most recent SyncLog entry.
    """
    def get(self, request):
        from django.http import JsonResponse
        from projects.models import SyncLog
        
        log = SyncLog.objects.first()  # ordered by -triggered_at
        if not log:
            return JsonResponse({"status": "never_run"})
        
        return JsonResponse({
            "id": log.pk,
            "status": log.status,
            "triggered_at": log.triggered_at.isoformat(),
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "summary": log.summary,
            "projects_created": log.projects_created,
            "projects_updated": log.projects_updated,
            "projects_ai_generated": log.projects_ai_generated,
            "certificates_created": log.certificates_created,
            "errors": log.errors
        })
