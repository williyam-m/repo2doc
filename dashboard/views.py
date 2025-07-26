import os, zipfile, tempfile, json
import requests
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from message_resource.api_message_resource import *
from .models import GeneratedDocFolder



def index(request):
    context = {}
    
    # Get all generated doc folders for listing
    doc_folders = GeneratedDocFolder.objects.all().order_by('-uploaded_at')
    context['doc_folders'] = doc_folders

    if request.method == 'POST':
        uploaded_file = request.FILES.get('code_file')

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

                docs_output_root = os.path.join(settings.MEDIA_DOCS_PATH, os.path.splitext(uploaded_file.name)[0])
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

                # Save folder path to DB
                GeneratedDocFolder.objects.create(folder_path=docs_output_root)

                context[API_KEY_NAME.MESSAGE] = SuccessMessages.DOCUMENTATION_GENERATED
                
                # Get updated list of folders
                doc_folders = GeneratedDocFolder.objects.all().order_by('-uploaded_at')
                context['doc_folders'] = doc_folders
        else:
            context[API_KEY_NAME.ERROR] = ErrorMessages.INVALID_FILE_TYPE

    return render(request, 'index.html', context)

def build_file_tree(folder_path, base_path=""):
    """Build a hierarchical file tree structure"""
    tree = []
    
    try:
        items = os.listdir(os.path.join(folder_path, base_path))
        items.sort()  # Sort alphabetically
        
        # Separate directories and files
        dirs = []
        files = []
        
        for item in items:
            full_path = os.path.join(folder_path, base_path, item)
            rel_path = os.path.join(base_path, item) if base_path else item
            
            if os.path.isdir(full_path):
                dirs.append({
                    'name': item,
                    'path': rel_path,
                    'is_dir': True,
                    'children': build_file_tree(folder_path, rel_path)
                })
            elif item.endswith('.md'):
                files.append({
                    'name': item,
                    'path': rel_path,
                    'is_dir': False
                })
        
        # Return directories first, then files
        tree.extend(dirs)
        tree.extend(files)
        
    except (OSError, IOError):
        pass
    
    return tree

def view_doc(request, doc_id):
    # Get the document folder by ID
    doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id)
    
    # Build hierarchical file tree
    file_tree = build_file_tree(doc_folder.folder_path)
    
    # Find first file for default display
    def find_first_file(tree):
        for item in tree:
            if not item['is_dir']:
                return item
            elif item.get('children'):
                first_child = find_first_file(item['children'])
                if first_child:
                    return first_child
        return None
    
    first_file = find_first_file(file_tree)
    current_file_content = ""
    current_file_name = ""
    
    if first_file:
        try:
            full_path = os.path.join(doc_folder.folder_path, first_file['path'])
            with open(full_path, 'r', encoding='utf-8') as f:
                current_file_content = f.read()
            current_file_name = first_file['name']
        except Exception:
            pass
    
    context = {
        'doc_folder': doc_folder,
        'file_tree_json': json.dumps(file_tree),
        'current_file_content': current_file_content,
        'current_file_name': current_file_name,
    }
    
    return render(request, 'doc_view.html', context)

def file_content_api(request):
    """API endpoint to get file content"""
    path = request.GET.get('path')
    doc_id = request.GET.get('doc_id')
    
    if not path or not doc_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id)
        full_path = os.path.join(doc_folder.folder_path, path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        return JsonResponse({
            'raw_content': raw_content,
            'path': path
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)