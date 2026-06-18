from rest_framework import serializers
from .models import Project, Certificate, Comment, ContactMessage, WorkExperience, Education, AboutProfile, Skill


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for Certificate model"""
    
    class Meta:
        model = Certificate
        fields = [
            'id',
            'name',
            'issuer',
            'issued_date',
            'pdf_file',
            'is_visible',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
        ]


class ProjectSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    has_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id',
            'github_id',
            'repo_name',
            'repo_url',
            'repo_description',
            'is_visible',
            'category',
            'category_display',
            'ai_title',
            'ai_summary',
            'key_features',
            'tech_stack',
            'has_content',
            'last_synced',
            'ai_generated_at',
            'created_at',
        ]
        read_only_fields = [
            'github_id',
            'repo_url',
            'repo_description',
            'last_synced',
            'created_at',
            'ai_generated_at',
        ]
    
    def get_has_content(self, obj):
        return obj.has_ai_content()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'project',
            'author_name',
            'author_email',
            'content',
            'status',
            'status_display',
            'created_at',
            'approved_at',
        ]
        read_only_fields = [
            'status',
            'created_at',
            'approved_at',
        ]


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for ContactMessage model"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ContactMessage
        fields = [
            'id',
            'name',
            'email',
            'subject',
            'message',
            'status',
            'status_display',
            'created_at',
            'read_at',
        ]
        read_only_fields = [
            'status',
            'created_at',
            'read_at',
        ]


class WorkExperienceSerializer(serializers.ModelSerializer):
    """Serializer for WorkExperience model"""
    
    class Meta:
        model = WorkExperience
        fields = [
            'id',
            'job_title',
            'company',
            'start_date',
            'end_date',
            'description',
            'is_current',
            'order',
        ]


class EducationSerializer(serializers.ModelSerializer):
    """Serializer for Education model"""
    
    class Meta:
        model = Education
        fields = [
            'id',
            'degree',
            'institution',
            'start_date',
            'end_date',
            'gpa',
            'description',
            'order',
        ]


class AboutProfileSerializer(serializers.ModelSerializer):
    """Serializer for AboutProfile model"""
    
    class Meta:
        model = AboutProfile
        fields = [
            'id',
            'professional_summary',
            'resume_file',
            'github_url',
            'linkedin_url',
            'twitter_url',
            'other_url',
            'updated_at',
        ]
        read_only_fields = [
            'updated_at',
        ]


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Skill
        fields = [
            'id',
            'name',
            'category',
            'category_display',
            'proficiency',
            'order',
            'is_featured',
            'auto_generated',
        ]
        read_only_fields = [
            'auto_generated',
        ]
