import os
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from dashboard.models import GeneratedDocFolder
from message_resource.api_message_resource import API_KEY_NAME, ErrorMessages
from rest_framework import status

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
    
    return render(request, 'doc_view/doc_view.html', context)

def file_content_api(request):
    """API endpoint to get file content"""
    path = request.GET.get('path')
    doc_id = request.GET.get('doc_id')
    
    if not path or not doc_id:
        return JsonResponse({API_KEY_NAME.ERROR: 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        doc_folder = get_object_or_404(GeneratedDocFolder, id=doc_id)
        
        # First try direct path
        full_path = os.path.join(doc_folder.folder_path, path)
        if not os.path.exists(full_path):
            # If direct path doesn't exist, try adding the extracted folder name
            # This handles the case where the zip and extracted folder names match
            folder_name = os.path.basename(doc_folder.folder_path)
            nested_path = os.path.join(doc_folder.folder_path, folder_name, path)
            
            if os.path.exists(nested_path):
                full_path = nested_path
            else:
                return JsonResponse({
                    API_KEY_NAME.ERROR: ErrorMessages.FILE_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        return JsonResponse({
            API_KEY_NAME.RAW_CONTENT: raw_content,
            API_KEY_NAME.PATH: path
        })
    
    except Exception as e:
        return JsonResponse({
            API_KEY_NAME.ERROR: str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
