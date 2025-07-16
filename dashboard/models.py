# models.py
from django.db import models

class GeneratedDocFolder(models.Model):
    folder_path = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
