from django.db import models
from django.contrib.auth.models import User
from dashboard.models import GeneratedDocFolder
import uuid

class GitHubRepository(models.Model):
    """Track GitHub repositories for webhook integration"""
    
    doc_folder = models.OneToOneField(
        GeneratedDocFolder, 
        on_delete=models.CASCADE,
        related_name="github_repo"
    )
    
    # GitHub repository information
    github_url = models.URLField(max_length=500)
    owner = models.CharField(max_length=100)  # GitHub username/organization
    repo_name = models.CharField(max_length=100)  # Repository name
    branch = models.CharField(max_length=100, default="main")  # Branch to track
    
    # Webhook configuration
    webhook_id = models.CharField(max_length=100, null=True, blank=True)  # GitHub webhook ID
    webhook_secret = models.CharField(max_length=100, default=str(uuid.uuid4)[:32])  # Secret for validation
    is_webhook_active = models.BooleanField(default=False)
    
    # Sync settings
    auto_sync_enabled = models.BooleanField(default=True)
    last_commit_sha = models.CharField(max_length=40, null=True, blank=True)  # Last processed commit
    last_sync_at = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    sync_failures = models.IntegerField(default=0)
    last_sync_error = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = []  # Remove unique constraint to allow multiple docs from same repo
    
    def __str__(self):
        return f"{self.owner}/{self.repo_name}"
    
    @property
    def webhook_url(self):
        """Generate webhook URL for GitHub"""
        from django.conf import settings
        return f"{settings.HOST_URL}/webhook/github/{self.id}/"
    
    @property
    def api_url(self):
        """GitHub API URL for this repository"""
        return f"https://api.github.com/repos/{self.owner}/{self.repo_name}"


class WebhookEvent(models.Model):
    """Log webhook events for debugging and monitoring"""
    
    EVENT_TYPES = [
        ("push", "Push"),
        ("ping", "Ping"),
        ("pull_request", "Pull Request"),
        ("other", "Other"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("ignored", "Ignored"),
    ]
    
    github_repo = models.ForeignKey(
        GitHubRepository, 
        on_delete=models.CASCADE,
        related_name="webhook_events"
    )
    
    # Event details
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    github_delivery_id = models.CharField(max_length=100, unique=True)
    commit_sha = models.CharField(max_length=40, null=True, blank=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(null=True, blank=True)
    files_processed = models.IntegerField(default=0)
    
    # Raw payload for debugging
    payload = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.github_repo} - {self.event_type} - {self.status}"


class FileSync(models.Model):
    """Track individual file synchronization"""
    
    webhook_event = models.ForeignKey(
        WebhookEvent,
        on_delete=models.CASCADE,
        related_name="file_syncs"
    )
    
    file_path = models.CharField(max_length=500)  # Relative path in repository
    action = models.CharField(max_length=20)  # added, modified, removed
    
    # Processing details
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_path} - {self.action}"
