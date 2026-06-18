from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'certificates', views.CertificateViewSet, basename='certificate')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'contact', views.ContactMessageViewSet, basename='contact')
router.register(r'experience', views.WorkExperienceViewSet, basename='experience')
router.register(r'education', views.EducationViewSet, basename='education')
router.register(r'about', views.AboutProfileViewSet, basename='about')
router.register(r'skills', views.SkillViewSet, basename='skill')

urlpatterns = [
    path('', include(router.urls)),
    path('sync/', views.SyncView.as_view(), name='sync'),
    path('sync/last/', views.LastSyncView.as_view(), name='sync-last'),
]
