import requests
import json
import hmac
import hashlib
import os
from django.conf import settings
from django.urls import reverse
from .models import GitHubRepository, WebhookEvent

class GitHubWebhookService:
    """Service for managing GitHub webhooks"""
    
    def setup_webhook(self, repo_url, token, doc_folder):
        """Set up webhook for a GitHub repository"""
        try:
            # Validate token first
            if not token or not token.strip():
                return False, "GitHub token is required"
            
            # Extract owner and repo name from URL
            parts = repo_url.strip('/').split('/')
            if len(parts) < 5 or 'github.com' not in parts:
                return False, "Invalid GitHub URL format"
            
            owner = parts[-2]
            repo = parts[-1]
            
            # First, verify token is valid by testing it
            test_headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'repo2doc-webhook-setup'
            }
            
            # Test token with a simple API call
            test_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=test_headers
            )
            
            if test_response.status_code == 401:
                return False, "Invalid GitHub token. Please check your token has proper permissions."
            elif test_response.status_code == 404:
                return False, "Repository not found. Check if the token has access to this repository."
            elif test_response.status_code != 200:
                return False, f"GitHub API error: {test_response.status_code} - {test_response.text}"
            
            # Get the existing GitHub repository record
            try:
                github_repo = doc_folder.github_repo
            except GitHubRepository.DoesNotExist:
                # Create new if doesn't exist
                github_repo = GitHubRepository.objects.create(
                    doc_folder=doc_folder,
                    github_url=repo_url,
                    owner=owner,
                    repo_name=repo,
                    webhook_secret=self._generate_webhook_secret(),
                    auto_sync_enabled=False
                )
            
            # Update the repository with webhook info
            if not github_repo.webhook_secret:
                github_repo.webhook_secret = self._generate_webhook_secret()
            
            # Create webhook on GitHub
            webhook_url = f"{settings.HOST_URL}/webhook/github/{github_repo.id}/"
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'repo2doc-webhook-setup',
                'Content-Type': 'application/json'
            }
            
            webhook_data = {
                'name': 'web',
                'active': True,
                'events': ['push'],
                'config': {
                    'url': webhook_url,
                    'content_type': 'json',
                    'secret': github_repo.webhook_secret,
                    'insecure_ssl': '0'
                }
            }
            
            response = requests.post(
                f'https://api.github.com/repos/{owner}/{repo}/hooks',
                headers=headers,
                json=webhook_data
            )
            
            if response.status_code == 201:
                # Webhook created successfully
                hook_data = response.json()
                github_repo.webhook_id = str(hook_data.get('id'))
                github_repo.auto_sync_enabled = True
                github_repo.save()
                return True, "Webhook configured successfully"
            elif response.status_code == 422:
                # Webhook might already exist
                error_data = response.json()
                if 'errors' in error_data:
                    for error in error_data['errors']:
                        if 'already exists' in error.get('message', ''):
                            # Get existing webhooks to find ours
                            hooks_response = requests.get(
                                f'https://api.github.com/repos/{owner}/{repo}/hooks',
                                headers=headers
                            )
                            
                            if hooks_response.status_code == 200:
                                hooks = hooks_response.json()
                                for hook in hooks:
                                    hook_url = hook.get('config', {}).get('url', '')
                                    if f"/webhook/github/{github_repo.id}/" in hook_url:
                                        github_repo.webhook_id = str(hook.get('id'))
                                        github_repo.auto_sync_enabled = True
                                        github_repo.save()
                                        return True, "Using existing webhook"
                
                return False, f"Error creating webhook: {response.json().get('message', 'Unknown error')}"
            elif response.status_code == 401:
                return False, "GitHub token has insufficient permissions. Please ensure it has 'admin:repo_hook' or 'repo' scope."
            elif response.status_code == 403:
                return False, "Access forbidden. Check if your token has admin access to this repository for webhook creation."
            else:
                # Other error
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get('message', error_text)
                except:
                    pass
                return False, f"Error creating webhook: {response.status_code} - {error_text}"
                
        except Exception as e:
            return False, f"Error setting up webhook: {str(e)}"
    
    def disable_webhook(self, github_repo, token=None):
        """Disable webhook for a GitHub repository"""
        try:
            if not github_repo.webhook_id:
                github_repo.auto_sync_enabled = False
                github_repo.save()
                return True, "Auto-sync disabled"
            
            if token:
                # Try to delete the webhook from GitHub
                headers = {
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                response = requests.delete(
                    f'https://api.github.com/repos/{github_repo.owner}/{github_repo.repo_name}/hooks/{github_repo.webhook_id}',
                    headers=headers
                )
                
                if response.status_code in [204, 404]:
                    # Successfully deleted or webhook not found
                    github_repo.webhook_id = None
                    github_repo.auto_sync_enabled = False
                    github_repo.save()
                    return True, "Webhook removed and auto-sync disabled"
                else:
                    # Error deleting webhook
                    return False, f"Error removing webhook: {response.status_code} - {response.text}"
            else:
                # Just disable auto-sync without removing webhook
                github_repo.auto_sync_enabled = False
                github_repo.save()
                return True, "Auto-sync disabled"
                
        except Exception as e:
            return False, f"Error disabling webhook: {str(e)}"
    
    def verify_webhook_signature(self, payload, signature, secret):
        """Verify webhook signature from GitHub"""
        if not signature:
            return False
        
        try:
            # Get signature algorithm and hash
            algorithm, hash_value = signature.split('=', 1)
            if algorithm != 'sha1':
                return False
            
            # Calculate expected hash
            mac = hmac.new(
                secret.encode('utf-8'),
                msg=payload,
                digestmod=hashlib.sha1
            )
            expected = mac.hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected, hash_value)
            
        except Exception:
            return False
    
    def process_webhook_event(self, github_repo, event_type, payload_json, raw_payload):
        """Process webhook event from GitHub"""
        try:
            # Create event record
            event = WebhookEvent.objects.create(
                github_repo=github_repo,
                event_type=event_type,
                payload=payload_json,
                github_delivery_id=f"manual-{github_repo.id}-{payload_json.get('after', 'unknown')}",
                commit_sha=payload_json.get('after', '')
            )
            
            # Handle different event types
            if event_type == 'ping':
                # Just a test ping
                event.status = 'success'
                event.save()
                return True, "Ping received successfully"
                
            elif event_type == 'push':
                # Process push event
                return self._process_push_event(github_repo, event, payload_json)
                
            else:
                # Unsupported event type
                event.status = 'ignored'
                event.error_message = f"Unsupported event type: {event_type}"
                event.save()
                return False, f"Unsupported event type: {event_type}"
                
        except Exception as e:
            # Log error
            try:
                if 'event' in locals():
                    event.status = 'failed'
                    event.error_message = str(e)
                    event.save()
            except:
                pass
                
            return False, f"Error processing webhook: {str(e)}"
    
    def _process_push_event(self, github_repo, event, payload):
        """Process push event to update documentation"""
        try:
            # Extract commit information
            commits = payload.get('commits', [])
            if not commits:
                event.status = 'ignored'
                event.error_message = "No commits found in push event"
                event.save()
                return False, "No commits to process"
            
            # Track changed files
            added_files = []
            modified_files = []
            removed_files = []
            
            for commit in commits:
                added_files.extend(commit.get('added', []))
                modified_files.extend(commit.get('modified', []))
                removed_files.extend(commit.get('removed', []))
            
            # Filter for code files only
            def is_code_file(filename):
                code_extensions = [
                    '.py', '.js', '.ts', '.html', '.css', '.java', '.rb', '.go',
                    '.c', '.cpp', '.cs', '.php', '.swift', '.kt', '.rs', '.sh'
                ]
                return any(filename.endswith(ext) for ext in code_extensions)
            
            added_code_files = list(filter(is_code_file, added_files))
            modified_code_files = list(filter(is_code_file, modified_files))
            removed_code_files = list(filter(is_code_file, removed_files))
            
            # Update event with file counts
            event.files_processed = len(added_code_files) + len(modified_code_files) + len(removed_code_files)
            event.status = 'success'
            event.save()
            
            # TODO: Implement actual file synchronization logic
            # This would call your AI service to update documentation
            # for changed files
            
            # For now, just update the last sync time
            github_repo.last_sync_at = event.created_at
            github_repo.last_sync_error = None
            github_repo.save()
            
            total_files = len(added_code_files) + len(modified_code_files) + len(removed_code_files)
            return True, f"Processed {total_files} code files"
            
        except Exception as e:
            # Log error
            github_repo.last_sync_error = str(e)
            github_repo.save()
            
            event.status = 'failed'
            event.error_message = str(e)
            event.save()
            
            return False, f"Error processing push event: {str(e)}"
    
    def test_webhook_connection(self, github_repo, token):
        """Test webhook connection by checking if it exists on GitHub"""
        try:
            if not token:
                return False, "GitHub token not found"
            
            if not github_repo.webhook_id:
                return False, "Webhook not configured"
            
            # Check if webhook exists on GitHub
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'repo2doc-webhook-test'
            }
            
            response = requests.get(
                f'https://api.github.com/repos/{github_repo.owner}/{github_repo.repo_name}/hooks/{github_repo.webhook_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                hook_data = response.json()
                is_active = hook_data.get('active', False)
                
                if is_active:
                    return True, "Webhook is active and configured correctly"
                else:
                    return False, "Webhook exists but is not active"
            elif response.status_code == 404:
                return False, "Webhook not found on GitHub (may have been manually deleted)"
            elif response.status_code == 401:
                return False, "Invalid GitHub token or insufficient permissions"
            else:
                return False, f"GitHub API error: {response.status_code}"
                
        except Exception as e:
            return False, f"Error testing webhook: {str(e)}"
    
    def _generate_webhook_secret(self):
        """Generate a random secret for webhook validation"""
        return os.urandom(24).hex()