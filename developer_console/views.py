from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST
import os

from dashboard.models import GeneratedDocFolder
from webhook.models import GitHubRepository, WebhookEvent
from webhook.services import GitHubWebhookService


@login_required
def dashboard(request):
    """Developer console main dashboard"""
    # Get all GitHub repositories for the user
    github_repos = GeneratedDocFolder.objects.filter(
        user=request.user,
        source_type='github'
    ).select_related('github_repo').order_by('-uploaded_at')
    
    # Add pagination for GitHub repositories
    paginator = Paginator(github_repos, 15)  # Use pagination size from settings
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add sync status to each repository
    for repo in page_obj:
        try:
            github_repo = repo.github_repo
            repo.is_sync_enabled = github_repo.auto_sync_enabled
            repo.sync_status = 'enabled' if github_repo.auto_sync_enabled else 'disabled'
            repo.last_sync = github_repo.last_sync_at
            repo.sync_error = github_repo.last_sync_error
        except:
            repo.is_sync_enabled = False
            repo.sync_status = 'disabled'  # Changed from 'not_configured' to 'disabled'
            repo.last_sync = None
            repo.sync_error = None
    
    context = {
        'github_repos': page_obj,
        'page_obj': page_obj,
        'total_repos': github_repos.count(),
        'enabled_repos': sum(1 for repo in github_repos if hasattr(repo, 'github_repo') and repo.github_repo.auto_sync_enabled),
    }
    
    return render(request, 'developer_console/dashboard.html', context)


@login_required
def auto_sync_settings(request, doc_id):
    """Auto-sync settings for a specific repository"""
    doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id, user=request.user)
    
    if doc_folder.source_type != 'github':
        messages.error(request, 'Auto-sync is only available for GitHub repositories.')
        return redirect('developer_console:dashboard')
    
    try:
        github_repo = doc_folder.github_repo
    except:
        github_repo = None
    
    # Check if user has stored GitHub token
    user_profile = getattr(request.user, 'profile', None)
    has_stored_token = user_profile and user_profile.has_github_token() if user_profile else False
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enable':
            # Only enable if user has stored token
            if has_stored_token:
                github_token = user_profile.get_github_token()
                
                # Validate token is not None or empty
                if not github_token or not github_token.strip():
                    messages.error(request, 'Invalid GitHub token found. Please update your token in profile settings.')
                    return redirect('developer_console:auto_sync_settings', doc_id=doc_id)
                
                # Get GitHub URL from the related GitHubRepository model
                if not github_repo:
                    messages.error(request, 'GitHub repository information not found.')
                    return redirect('developer_console:auto_sync_settings', doc_id=doc_id)
                
                # Enable auto-sync
                try:
                    service = GitHubWebhookService()
                    success, message = service.setup_webhook(
                        github_repo.github_url,
                        github_token,
                        doc_folder
                    )
                    
                    if success:
                        messages.success(request, 'Auto-sync enabled successfully!')
                    else:
                        messages.error(request, f'Failed to enable auto-sync: {message}')
                        
                except Exception as e:
                    messages.error(request, f'Error enabling auto-sync: {str(e)}')
            else:
                messages.error(request, 'GitHub token is required to enable auto-sync. Please configure it in your profile first.')
                
        elif action == 'disable':
            # Disable auto-sync
            if github_repo:
                try:
                    github_repo.auto_sync_enabled = False
                    github_repo.save()
                    messages.success(request, 'Auto-sync disabled successfully!')
                except Exception as e:
                    messages.error(request, f'Error disabling auto-sync: {str(e)}')
        
        return redirect('developer_console:auto_sync_settings', doc_id=doc_id)
    
    context = {
        'doc_folder': doc_folder,
        'github_repo': github_repo,
        'sync_enabled': github_repo.auto_sync_enabled if github_repo else False,
        'last_sync': github_repo.last_sync_at if github_repo else None,
        'sync_error': github_repo.last_sync_error if github_repo else None,
        'has_stored_token': has_stored_token,
    }
    
    return render(request, 'developer_console/auto_sync_settings.html', context)


@login_required
def log_view(request, doc_id):
    """View webhook logs for a specific repository"""
    doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id, user=request.user)
    
    if doc_folder.source_type != 'github':
        messages.error(request, 'Logs are only available for GitHub repositories.')
        return redirect('developer_console:dashboard')
    
    try:
        github_repo = doc_folder.github_repo
        webhook_events = WebhookEvent.objects.filter(
            github_repo=github_repo
        ).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(webhook_events, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
    except:
        github_repo = None
        page_obj = None
    
    context = {
        'doc_folder': doc_folder,
        'github_repo': github_repo,
        'page_obj': page_obj,
        'webhook_events': page_obj.object_list if page_obj else [],
    }
    
    return render(request, 'developer_console/log_view.html', context)


@login_required
@require_POST
def test_webhook(request, doc_id):
    """Test webhook endpoint"""
    doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id, user=request.user)
    
    try:
        github_repo = doc_folder.github_repo
        if not github_repo.auto_sync_enabled:
            return JsonResponse({'success': False, 'message': 'Auto-sync is not enabled'})
        
        # Get user's GitHub token
        user_profile = getattr(request.user, 'profile', None)
        if not user_profile or not user_profile.has_github_token():
            return JsonResponse({'success': False, 'message': 'GitHub token not found'})
        
        github_token = user_profile.get_github_token()
        if not github_token:
            return JsonResponse({'success': False, 'message': 'Invalid GitHub token'})
        
        # Test webhook connection
        service = GitHubWebhookService()
        success, message = service.test_webhook_connection(github_repo, github_token)
        
        return JsonResponse({'success': success, 'message': message})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
