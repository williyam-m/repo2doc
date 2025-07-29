from django.db import models
from django.contrib.auth.models import User

class DeveloperSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='developer_settings')
    github_token = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Developer Settings for {self.user.username}"
