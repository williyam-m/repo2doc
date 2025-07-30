import os, zipfile, tempfile
import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from message_resource.api_message_resource import *
from .models import GeneratedDocFolder
from django.contrib.auth.models import User  
from organization.models import Organization, OrganizationMember
from webhook.models import GitHubRepository

def index(request):
    context = {}
    
    public_doc_folders = GeneratedDocFolder.objects.filter(visibility='public').order_by('-uploaded_at')[:settings.PAGINATION_SIZE]
    context['doc_folders'] = public_doc_folders
    context['public_doc_count'] = GeneratedDocFolder.objects.filter(visibility='public').count()
    
    if request.user.is_authenticated:
        context['user_profile'] = request.user.profile
        
        my_doc_folders = GeneratedDocFolder.objects.filter(user=request.user).order_by('-uploaded_at')[:settings.PAGINATION_SIZE]
        private_doc_folders = GeneratedDocFolder.objects.filter(user=request.user, visibility='private').order_by('-uploaded_at')[:settings.PAGINATION_SIZE]
        
        context['my_doc_folders'] = my_doc_folders
        context['private_doc_folders'] = private_doc_folders
        context['my_doc_count'] = GeneratedDocFolder.objects.filter(user=request.user).count()
        context['private_doc_count'] = GeneratedDocFolder.objects.filter(user=request.user, visibility='private').count()
        
        user_orgs = Organization.objects.filter(
            members__user=request.user
        ).distinct()
        context['user_organizations'] = user_orgs
        
        org_doc_folders = GeneratedDocFolder.objects.filter(
            organization__in=user_orgs
        ).order_by('-uploaded_at')[:settings.PAGINATION_SIZE]
        context['org_doc_folders'] = org_doc_folders
        context['org_doc_count'] = GeneratedDocFolder.objects.filter(organization__in=user_orgs).count()

    if request.method == 'POST':
        uploaded_file = request.FILES.get('code_file')
        github_url = request.POST.get('github_url', '').strip()
        visibility = request.POST.get('visibility', 'public')
        organization_id = request.POST.get('organization_id') if visibility == 'organization' else None
        auto_sync = request.POST.get('auto_sync', 'disabled')
        github_token = None
        
        if auto_sync == 'enabled' and request.user.is_authenticated:
            try:
                profile = request.user.profile
                if profile.has_github_token():
                    github_token = profile.get_github_token()
                else:
                    github_token = request.POST.get('github_token', '').strip()
                    if github_token:
                        profile.set_github_token(github_token)
                        profile.save()
            except:
                github_token = request.POST.get('github_token', '').strip()
        
        organization = None
        if organization_id and request.user.is_authenticated:
            try:
                organization = Organization.objects.get(id=organization_id)
                if not OrganizationMember.objects.filter(organization=organization, user=request.user).exists():
                    organization = None
            except Organization.DoesNotExist:
                organization = None
        
        if github_url and github_url.startswith(('https://github.com/', 'http://github.com/')):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    parts = github_url.rstrip('/').split('/')
                    if len(parts) >= 5:
                        owner = parts[-2]
                        repo = parts[-1]
                        
                        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
                        
                        response = requests.get(zip_url, stream=True)
                        branch = 'main'
                        if response.status_code == 404:
                            zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
                            response = requests.get(zip_url, stream=True)
                            branch = 'master'
                        
                        if response.status_code == 404:
                            zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
                            response = requests.get(zip_url, stream=True)
                            branch = 'default'
                        
                        if response.status_code == 200:
                            zip_path = os.path.join(temp_dir, f"{repo}.zip")
                            with open(zip_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                                    
                            return process_zip_file(request, zip_path, visibility, organization, context, 
                                                  github_info={'url': github_url, 'owner': owner, 'repo': repo, 'branch': branch})
                        else:
                            context[API_KEY_NAME.ERROR] = f"Failed to download repository: HTTP {response.status_code}"
                    else:
                        context[API_KEY_NAME.ERROR] = "Invalid GitHub repository URL format. Please use format: https://github.com/owner/repo"
            except Exception as e:
                context[API_KEY_NAME.ERROR] = f"Error processing GitHub URL: {str(e)}"                
        
        elif uploaded_file and zipfile.is_zipfile(uploaded_file):
            with tempfile.TemporaryDirectory() as temp_zip_dir:
                zip_path = os.path.join(temp_zip_dir, uploaded_file.name)
                with open(zip_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                return process_zip_file(request, zip_path, visibility, organization, context, github_info=None)
        else:
            context[API_KEY_NAME.ERROR] = ErrorMessages.INVALID_FILE_TYPE

    return render(request, 'index.html', context)

def process_zip_file(request, zip_path, visibility, organization, context, github_info=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_filename = os.path.basename(zip_path)
        zip_name = os.path.splitext(zip_filename)[0]
        
        extract_dir = os.path.join(temp_dir, 'extracted')
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        docs_output_root = os.path.join(settings.PUBLIC_DOCS_PATH, zip_name)
        os.makedirs(docs_output_root, exist_ok=True)

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.startswith('.') or '__MACOSX' in root or file.endswith('.zip'):
                    continue

                abs_path = os.path.join(root, file)
                if not os.path.isfile(abs_path):
                    continue

                try:
                    with open(abs_path, 'r', encoding='utf-8', errors='ignore') as source_file:
                        code = source_file.read()
                except Exception:
                    continue

                if not code.strip():
                    continue

                api_url = settings.HOST_URL + "/api/repo2doc/"
                res = requests.post(api_url, json={API_KEY_NAME.CODE: code})

                if res.status_code == 200:
                    documentation = res.json().get(API_KEY_NAME.DOCUMENTATION)

                    rel_path = os.path.relpath(abs_path, extract_dir)
                    md_path = os.path.join(docs_output_root, os.path.splitext(rel_path)[0] + ".md")

                    os.makedirs(os.path.dirname(md_path), exist_ok=True)
                    with open(md_path, 'w', encoding='utf-8') as doc_file:
                        doc_file.write(documentation)

        source_type = 'github' if github_info else 'upload'

        if request.user.is_authenticated:
            doc_folder = GeneratedDocFolder.objects.create(
                folder_path=docs_output_root, 
                user=request.user,
                visibility=visibility,
                organization=organization,
                source_type=source_type
            )
        else:
            doc_folder = GeneratedDocFolder.objects.create(
                folder_path=docs_output_root,
                visibility='public',
                source_type=source_type
            )

        if github_info and request.user.is_authenticated:
            github_repo = GitHubRepository.objects.create(
                doc_folder=doc_folder,
                github_url=github_info['url'],
                owner=github_info['owner'],
                repo_name=github_info['repo'],
                branch=github_info['branch'],
                auto_sync_enabled=False
            )
            
            auto_sync_requested = request.POST.get('auto_sync', 'disabled') == 'enabled'
            github_token = request.POST.get('github_token', '').strip()
            
            if auto_sync_requested and github_token:
                try:
                    from webhook.services import GitHubWebhookService
                    service = GitHubWebhookService()
                    success, message = service.setup_webhook(
                        github_info['url'],
                        github_token,
                        doc_folder
                    )
                    if success:
                        context['auto_sync_message'] = 'Auto-sync enabled successfully!'
                        if request.user.is_authenticated:
                            try:
                                profile = request.user.profile
                                profile.set_github_token(github_token)
                                profile.save()
                            except:
                                pass
                    else:
                        context['auto_sync_error'] = f'Auto-sync setup failed: {message}'
                except Exception as e:
                    context['auto_sync_error'] = f'Auto-sync setup error: {str(e)}'
            elif auto_sync_requested and not github_token:
                context['auto_sync_error'] = 'GitHub token is required to enable auto-sync'

        context[API_KEY_NAME.MESSAGE] = SuccessMessages.DOCUMENTATION_GENERATED
        
        if request.user.is_authenticated:
            my_doc_folders = GeneratedDocFolder.objects.filter(user=request.user).order_by('-uploaded_at')
            context['my_doc_folders'] = my_doc_folders
        
        public_doc_folders = GeneratedDocFolder.objects.filter(visibility='public').order_by('-uploaded_at')
        context['doc_folders'] = public_doc_folders
        
        context['latest_doc_id'] = doc_folder.id
        
    return render(request, 'index.html', context)