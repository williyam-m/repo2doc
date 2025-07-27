import os, zipfile, tempfile
import requests
from django.shortcuts import render
from django.conf import settings
from message_resource.api_message_resource import *
from .models import GeneratedDocFolder
from django.contrib.auth.models import User
from organization.models import Organization, OrganizationMember

def index(request):
    context = {}
    
    # Get public doc folders for listing
    public_doc_folders = GeneratedDocFolder.objects.filter(visibility='public').order_by('-uploaded_at')
    context['doc_folders'] = public_doc_folders
    
    # Add user profile data and their docs if authenticated
    if request.user.is_authenticated:
        context['user_profile'] = request.user.profile
        
        # Get user's docs for "My Repos" tab
        my_doc_folders = GeneratedDocFolder.objects.filter(user=request.user).order_by('-uploaded_at')
        context['my_doc_folders'] = my_doc_folders
        
        # Get organizations for dropdown
        user_orgs = Organization.objects.filter(
            members__user=request.user
        ).distinct()
        context['user_organizations'] = user_orgs

    if request.method == 'POST':
        uploaded_file = request.FILES.get('code_file')
        visibility = request.POST.get('visibility', 'public')
        organization_id = request.POST.get('organization_id') if visibility == 'organization' else None
        
        if organization_id:
            try:
                organization = Organization.objects.get(id=organization_id)
                # Verify user is a member of this organization
                if not OrganizationMember.objects.filter(organization=organization, user=request.user).exists():
                    organization = None
            except Organization.DoesNotExist:
                organization = None
        else:
            organization = None

        if uploaded_file and zipfile.is_zipfile(uploaded_file):
            with tempfile.TemporaryDirectory() as temp_zip_dir:
                zip_path = os.path.join(temp_zip_dir, uploaded_file.name)
                with open(zip_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)

                # Extract to a subdirectory to avoid processing the original zip
                extract_dir = os.path.join(temp_zip_dir, 'extracted')
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                docs_output_root = os.path.join(settings.PUBLIC_DOCS_PATH, os.path.splitext(uploaded_file.name)[0])
                os.makedirs(docs_output_root, exist_ok=True)

                # Walk only the extracted directory, not the temp_zip_dir containing the zip file
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        # Skip system/metadata files and zip files
                        if file.startswith('.') or '__MACOSX' in root or file.endswith('.zip'):
                            continue

                        abs_path = os.path.join(root, file)
                        if not os.path.isfile(abs_path):
                            continue

                        try:
                            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as source_file:
                                code = source_file.read()
                        except Exception:
                            continue  # skip binary/non-readable

                        if not code.strip():  # skip empty files
                            continue

                        # Send to model
                        api_url = settings.HOST_URL + "/api/repo2doc/"
                        res = requests.post(api_url, json={API_KEY_NAME.CODE: code})

                        if res.status_code == 200:
                            documentation = res.json().get(API_KEY_NAME.DOCUMENTATION)

                            rel_path = os.path.relpath(abs_path, extract_dir)
                            md_path = os.path.join(docs_output_root, os.path.splitext(rel_path)[0] + ".md")

                            os.makedirs(os.path.dirname(md_path), exist_ok=True)
                            with open(md_path, 'w', encoding='utf-8') as doc_file:
                                doc_file.write(documentation)

                # Save folder path to DB with user if authenticated
                if request.user.is_authenticated:
                    GeneratedDocFolder.objects.create(
                        folder_path=docs_output_root, 
                        user=request.user,
                        visibility=visibility,
                        organization=organization
                    )
                else:
                    # Anonymous users can only create public docs
                    GeneratedDocFolder.objects.create(
                        folder_path=docs_output_root,
                        visibility='public'
                    )

                context[API_KEY_NAME.MESSAGE] = SuccessMessages.DOCUMENTATION_GENERATED
                
                # Get updated list of folders
                if request.user.is_authenticated:
                    my_doc_folders = GeneratedDocFolder.objects.filter(user=request.user).order_by('-uploaded_at')
                    context['my_doc_folders'] = my_doc_folders
                
                public_doc_folders = GeneratedDocFolder.objects.filter(visibility='public').order_by('-uploaded_at')
                context['doc_folders'] = public_doc_folders
                
                # Store the ID of the newly created doc for the view link
                latest_doc = GeneratedDocFolder.objects.filter(folder_path=docs_output_root).latest('uploaded_at')
                context['latest_doc_id'] = latest_doc.id
        else:
            context[API_KEY_NAME.ERROR] = ErrorMessages.INVALID_FILE_TYPE

    return render(request, 'index.html', context)