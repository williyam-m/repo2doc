# models.py
from django.db import models
import os
from django.contrib.auth.models import User

class GeneratedDocFolder(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('organization', 'Organization'),
    ]
    
    SOURCE_CHOICES = [
        ('upload', 'Uploaded ZIP'),
        ('github', 'GitHub Repository'),
    ]
    
    folder_path = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doc_folders')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    organization = models.ForeignKey('organization.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='doc_folders')
    
    # New fields for GitHub integration
    source_type = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='upload')
    auto_sync = models.BooleanField(default=False)
    github_token = models.CharField(max_length=255, null=True, blank=True)
    
    @property
    def folder_name(self):
        return os.path.basename(self.folder_path)
    
    @property
    def is_github_repo(self):
        """Check if this document was created from a GitHub repository"""
        return self.source_type == 'github' and hasattr(self, 'github_repo')
    
    @property
    def webhook_enabled(self):
        """Check if webhook is enabled for this repository"""
        if self.is_github_repo:
            return self.github_repo.is_webhook_active
        return False
