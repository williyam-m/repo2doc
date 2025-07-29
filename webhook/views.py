import json
import hashlib
import hmac
import os
import tempfile
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import GitHubRepository, WebhookEvent, FileSync
from dashboard.models import GeneratedDocFolder
from message_resource.api_message_resource import API_KEY_NAME


class GitHubWebhookService:
    """Service class to handle GitHub webhook operations"""
    
    @staticmethod
    def create_webhook(github_repo, github_token):
        """Create webhook on GitHub repository"""
        try:
            webhook_data = {
                "name": "web",
                "active": True,
                "events": ["push"],
                "config": {
                    "url": github_repo.webhook_url,
                    "content_type": "json",
                    "secret": github_repo.webhook_secret,
                    "insecure_ssl": "0"
                }
            }
            
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.post(
                f"{github_repo.api_url}/hooks",
                json=webhook_data,
                headers=headers
            )
            
            if response.status_code == 201:
                webhook_info = response.json()
                github_repo.webhook_id = str(webhook_info['id'])
                github_repo.is_webhook_active = True
                github_repo.save()
                return True, "Webhook created successfully"
            else:
                return False, f"GitHub API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Error creating webhook: {str(e)}"
    
    @staticmethod
    def delete_webhook(github_repo, github_token):
        """Delete webhook from GitHub repository"""
        try:
            if not github_repo.webhook_id:
                return True, "No webhook to delete"
            
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.delete(
                f"{github_repo.api_url}/hooks/{github_repo.webhook_id}",
                headers=headers
            )
            
            if response.status_code in [204, 404]:  # 404 means already deleted
                github_repo.webhook_id = None
                github_repo.is_webhook_active = False
                github_repo.save()
                return True, "Webhook deleted successfully"
            else:
                return False, f"GitHub API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Error deleting webhook: {str(e)}"


@method_decorator(csrf_exempt, name='dispatch')
class GitHubWebhookView(View):
    """Handle GitHub webhook events"""
    
    def verify_signature(self, request, secret):
        """Verify GitHub webhook signature"""
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            return False
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def post(self, request, repo_id):
        """Handle webhook POST requests"""
        try:
            # Get the GitHub repository
            github_repo = get_object_or_404(GitHubRepository, id=repo_id)
            
            # Verify signature
            if not self.verify_signature(request, github_repo.webhook_secret):
                return JsonResponse({'error': 'Invalid signature'}, status=403)
            
            # Parse payload
            try:
                payload = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
            
            # Get event type
            event_type = request.headers.get('X-GitHub-Event', 'other')
            delivery_id = request.headers.get('X-GitHub-Delivery', '')
            
            # Create webhook event record
            webhook_event = WebhookEvent.objects.create(
                github_repo=github_repo,
                event_type=event_type,
                github_delivery_id=delivery_id,
                payload=payload,
                status='pending'
            )
            
            # Handle ping event (GitHub webhook test)
            if event_type == 'ping':
                webhook_event.status = 'success'
                webhook_event.processed_at = timezone.now()
                webhook_event.save()
                return JsonResponse({'status': 'pong'})
            
            # Handle push event
            if event_type == 'push':
                return self.handle_push_event(webhook_event, payload)
            
            # Other events are ignored for now
            webhook_event.status = 'ignored'
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
            return JsonResponse({'status': 'ignored', 'event': event_type})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def handle_push_event(self, webhook_event, payload):
        """Process push event and update documentation"""
        try:
            webhook_event.status = 'processing'
            webhook_event.save()
            
            github_repo = webhook_event.github_repo
            
            # Get commit information
            commits = payload.get('commits', [])
            if not commits:
                webhook_event.status = 'ignored'
                webhook_event.processed_at = timezone.now()
                webhook_event.save()
                return JsonResponse({'status': 'no commits'})
            
            # Get the latest commit
            latest_commit = commits[-1]
            commit_sha = latest_commit['id']
            webhook_event.commit_sha = commit_sha
            
            # Check if we've already processed this commit
            if github_repo.last_commit_sha == commit_sha:
                webhook_event.status = 'ignored'
                webhook_event.processed_at = timezone.now()
                webhook_event.save()
                return JsonResponse({'status': 'already processed'})
            
            # Get modified files
            modified_files = []
            added_files = []
            removed_files = []
            
            for commit in commits:
                modified_files.extend(commit.get('modified', []))
                added_files.extend(commit.get('added', []))
                removed_files.extend(commit.get('removed', []))
            
            # Remove duplicates
            modified_files = list(set(modified_files))
            added_files = list(set(added_files))
            removed_files = list(set(removed_files))
            
            # Process files
            files_processed = 0
            
            # Handle removed files
            for file_path in removed_files:
                self.handle_file_removal(webhook_event, file_path)
                files_processed += 1
            
            # Handle added and modified files
            all_changed_files = list(set(added_files + modified_files))
            for file_path in all_changed_files:
                if self.should_process_file(file_path):
                    success = self.process_file_update(webhook_event, file_path, commit_sha)
                    if success:
                        files_processed += 1
            
            # Update webhook event
            webhook_event.files_processed = files_processed
            webhook_event.status = 'success'
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
            # Update GitHub repository
            github_repo.last_commit_sha = commit_sha
            github_repo.last_sync_at = timezone.now()
            github_repo.sync_failures = 0
            github_repo.last_error_message = None
            github_repo.save()
            
            return JsonResponse({
                'status': 'success',
                'files_processed': files_processed,
                'commit': commit_sha[:7]
            })
            
        except Exception as e:
            webhook_event.status = 'failed'
            webhook_event.error_message = str(e)
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
            # Update failure count
            github_repo = webhook_event.github_repo
            github_repo.sync_failures += 1
            github_repo.last_error_message = str(e)
            github_repo.save()
            
            return JsonResponse({'error': str(e)}, status=500)
    
    def should_process_file(self, file_path):
        """Check if file should be processed for documentation"""
        # Skip hidden files, config files, etc.
        skip_patterns = [
            '.git/', '__pycache__/', 'node_modules/', '.env', 
            '.gitignore', 'README.md', 'LICENSE', '.DS_Store'
        ]
        
        for pattern in skip_patterns:
            if pattern in file_path:
                return False
        
        # Only process code files (you can extend this list)
        code_extensions = [
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h',
            '.php', '.rb', '.go', '.rs', '.swift', '.kt',
            '.cs', '.sql', '.html', '.css', '.scss', '.less'
        ]
        
        return any(file_path.lower().endswith(ext) for ext in code_extensions)
    
    def process_file_update(self, webhook_event, file_path, commit_sha):
        """Download and process a single file update"""
        try:
            github_repo = webhook_event.github_repo
            
            # Create FileSync record
            file_sync = FileSync.objects.create(
                webhook_event=webhook_event,
                file_path=file_path,
                action='modified'
            )
            
            # Download file content from GitHub
            file_url = f"{github_repo.api_url}/contents/{file_path}?ref={commit_sha}"
            response = requests.get(file_url)
            
            if response.status_code != 200:
                file_sync.error_message = f"Failed to download file: {response.status_code}"
                file_sync.save()
                return False
            
            file_data = response.json()
            
            # Decode file content
            import base64
            file_content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
            
            if not file_content.strip():
                file_sync.error_message = "Empty file content"
                file_sync.save()
                return False
            
            # Generate documentation using the same API as initial upload
            api_url = settings.HOST_URL + "/api/repo2doc/"
            api_response = requests.post(api_url, json={API_KEY_NAME.CODE: file_content})
            
            if api_response.status_code != 200:
                file_sync.error_message = f"Documentation API failed: {api_response.status_code}"
                file_sync.save()
                return False
            
            documentation = api_response.json().get(API_KEY_NAME.DOCUMENTATION)
            if not documentation:
                file_sync.error_message = "No documentation generated"
                file_sync.save()
                return False
            
            # Save updated documentation
            doc_folder = github_repo.doc_folder
            md_file_path = os.path.join(
                doc_folder.folder_path,
                os.path.splitext(file_path)[0] + ".md"
            )
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(md_file_path), exist_ok=True)
            
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            file_sync.success = True
            file_sync.save()
            
            return True
            
        except Exception as e:
            if 'file_sync' in locals():
                file_sync.error_message = str(e)
                file_sync.save()
            raise e
    
    def handle_file_removal(self, webhook_event, file_path):
        """Handle file removal"""
        try:
            # Create FileSync record
            file_sync = FileSync.objects.create(
                webhook_event=webhook_event,
                file_path=file_path,
                action='removed'
            )
            
            # Remove corresponding markdown file
            github_repo = webhook_event.github_repo
            doc_folder = github_repo.doc_folder
            md_file_path = os.path.join(
                doc_folder.folder_path,
                os.path.splitext(file_path)[0] + ".md"
            )
            
            if os.path.exists(md_file_path):
                os.remove(md_file_path)
                
                # Remove empty directories
                dir_path = os.path.dirname(md_file_path)
                while dir_path != doc_folder.folder_path:
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            dir_path = os.path.dirname(dir_path)
                        else:
                            break
                    except OSError:
                        break
            
            file_sync.success = True
            file_sync.save()
            
        except Exception as e:
            if 'file_sync' in locals():
                file_sync.error_message = str(e)
                file_sync.save()


@api_view(['POST'])
def setup_webhook(request):
    """API endpoint to setup webhook for a GitHub repository"""
    try:
        doc_id = request.data.get('doc_id')
        github_token = request.data.get('github_token')
        
        if not doc_id or not github_token:
            return Response({
                'error': 'doc_id and github_token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the document folder
        doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id)
        
        # Check if user owns this document
        if request.user != doc_folder.user:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
# Check if GitHub repository record exists
        try:
            github_repo = doc_folder.github_repo
        except GitHubRepository.DoesNotExist:
            return Response({
                'error': 'This document was not created from a GitHub repository'
            }, status=status.HTTP_400_BAD_REQUEST)        
        # Setup webhook
        success, message = GitHubWebhookService.create_webhook(github_repo, github_token)
        
        if success:
            return Response({
                'success': True,
                'message': message,
                'webhook_url': github_repo.webhook_url
            })
        else:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def remove_webhook(request):
    """API endpoint to remove webhook from GitHub repository"""
    try:
        doc_id = request.data.get('doc_id')
        github_token = request.data.get('github_token')
        
        if not doc_id or not github_token:
            return Response({
                'error': 'doc_id and github_token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the document folder
        doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id)
        
        # Check if user owns this document
        if request.user != doc_folder.user:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
# Check if GitHub repository record exists  
        try:
            github_repo = doc_folder.github_repo
        except GitHubRepository.DoesNotExist:
            return Response({
                'error': 'This document was not created from a GitHub repository'
            }, status=status.HTTP_400_BAD_REQUEST)        
        # Remove webhook
        success, message = GitHubWebhookService.delete_webhook(github_repo, github_token)
        
        if success:
            return Response({
                'success': True,
                'message': message
            })
        else:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def webhook_status(request, doc_id):
    """Get webhook status for a document"""
    try:
        # Get the document folder
        doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id)
        
        # Check if user owns this document
        if request.user != doc_folder.user:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            github_repo = doc_folder.github_repo
            return Response({
                'is_github_repo': True,
                'webhook_active': github_repo.is_webhook_active,
                'auto_sync_enabled': github_repo.auto_sync_enabled,
                'last_sync_at': github_repo.last_sync_at,
                'sync_failures': github_repo.sync_failures,
                'last_error': github_repo.last_sync_error,
                'repo_url': github_repo.github_url
            })
        except GitHubRepository.DoesNotExist:
            return Response({
                'is_github_repo': False,
                'message': 'This document was not created from a GitHub repository'
            })
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
