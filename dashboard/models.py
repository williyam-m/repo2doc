# models.py
from django.db import models
import os

class GeneratedDocFolder(models.Model):
    folder_path = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def folder_name(self):
        return os.path.basename(self.folder_path)
