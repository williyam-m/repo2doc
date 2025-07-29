from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    github_id = models.CharField(max_length=100, blank=True, null=True)
    github_username = models.CharField(max_length=100, blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    encrypted_github_token = models.TextField(blank=True, null=True)
    
    def set_github_token(self, token):
        """Encrypt and store GitHub token"""
        if token and token.strip():
            try:
                # Get encryption key from settings
                key = getattr(settings, 'ENCRYPTION_KEY', 'your-default-key-here-must-be-32-chars!')
                if isinstance(key, str):
                    key = key.encode()
                
                # Ensure key is 32 bytes for Fernet
                if len(key) < 32:
                    key = key.ljust(32, b'0')
                elif len(key) > 32:
                    key = key[:32]
                
                # For valid Fernet key, we need base64-encoded 32 bytes
                from cryptography.fernet import Fernet
                fernet_key = base64.urlsafe_b64encode(key)
                fernet = Fernet(fernet_key)
                
                encrypted_token = fernet.encrypt(token.strip().encode())
                self.encrypted_github_token = base64.b64encode(encrypted_token).decode()
            except Exception as e:
                print(f"Error encrypting token: {e}")
                self.encrypted_github_token = None
        else:
            self.encrypted_github_token = None
    
    def get_github_token(self):
        """Decrypt and return GitHub token"""
        if self.encrypted_github_token:
            try:
                # Get encryption key from settings
                key = getattr(settings, 'ENCRYPTION_KEY', 'your-default-key-here-must-be-32-chars!')
                if isinstance(key, str):
                    key = key.encode()
                
                # Ensure key is 32 bytes for Fernet
                if len(key) < 32:
                    key = key.ljust(32, b'0')
                elif len(key) > 32:
                    key = key[:32]
                
                # For valid Fernet key, we need base64-encoded 32 bytes
                from cryptography.fernet import Fernet
                fernet_key = base64.urlsafe_b64encode(key)
                fernet = Fernet(fernet_key)
                
                encrypted_token = base64.b64decode(self.encrypted_github_token.encode())
                decrypted_token = fernet.decrypt(encrypted_token).decode()
                return decrypted_token.strip()
            except Exception as e:
                print(f"Error decrypting token: {e}")
                return None
        return None
    
    def has_github_token(self):
        """Check if user has a GitHub token stored"""
        return bool(self.encrypted_github_token)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
