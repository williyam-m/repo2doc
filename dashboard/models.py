# models.py
from django.db import models
import os
from django.contrib.auth.models import User

class GeneratedDocFolder(models.Model):
    folder_path = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doc_folders')

    @property
    def folder_name(self):
        return os.path.basename(self.folder_path)
