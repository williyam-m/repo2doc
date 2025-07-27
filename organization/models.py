from django.db import models
from django.contrib.auth.models import User
import uuid

class Organization(models.Model):
    name = models.CharField(max_length=200)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_organizations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class OrganizationMember(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('organization', 'user')
    
    def __str__(self):
        return f"{self.user.username} in {self.organization.name}"