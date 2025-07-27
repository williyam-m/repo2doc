from django.shortcuts import render
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import GeneratedDocFolder
from organization.models import Organization

def paginate_queryset(queryset, request):
    """Helper function to paginate a queryset"""
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, settings.PAGINATION_SIZE)
    
    try:
        paginated_items = paginator.page(page)
    except PageNotAnInteger:
        paginated_items = paginator.page(1)
    except EmptyPage:
        paginated_items = paginator.page(paginator.num_pages)
        
    return paginated_items

def public_repos_list(request):
    """View for listing all public repositories with pagination"""
    public_doc_folders = GeneratedDocFolder.objects.filter(visibility='public').order_by('-uploaded_at')
    paginated_docs = paginate_queryset(public_doc_folders, request)
    
    context = {
        'doc_folders': paginated_docs,
        'list_type': 'public',
        'title': 'Public Repositories'
    }
    
    return render(request, 'list_view.html', context)

def private_repos_list(request):
    """View for listing all private repositories with pagination"""
    # Only show private repos if user is authenticated
    if not request.user.is_authenticated:
        return render(request, 'list_view.html', {'error': 'You must be logged in to view private repositories'})
    
    private_doc_folders = GeneratedDocFolder.objects.filter(
        user=request.user, 
        visibility='private'
    ).order_by('-uploaded_at')
    
    paginated_docs = paginate_queryset(private_doc_folders, request)
    
    context = {
        'doc_folders': paginated_docs,
        'list_type': 'private',
        'title': 'Private Repositories'
    }
    
    return render(request, 'list_view.html', context)

def my_repos_list(request):
    """View for listing all user's repositories with pagination"""
    # Only show user repos if authenticated
    if not request.user.is_authenticated:
        return render(request, 'list_view.html', {'error': 'You must be logged in to view your repositories'})
    
    user_doc_folders = GeneratedDocFolder.objects.filter(user=request.user).order_by('-uploaded_at')
    paginated_docs = paginate_queryset(user_doc_folders, request)
    
    context = {
        'doc_folders': paginated_docs,
        'list_type': 'my',
        'title': 'My Repositories'
    }
    
    return render(request, 'list_view.html', context)

def organization_repos_list(request):
    """View for listing all organization repositories with pagination"""
    # Only show organization repos if authenticated
    if not request.user.is_authenticated:
        return render(request, 'list_view.html', {'error': 'You must be logged in to view organization repositories'})
    
    # Get organizations the user is a member of
    user_orgs = Organization.objects.filter(
        members__user=request.user
    ).distinct()
    
    # Get docs from those organizations
    org_doc_folders = GeneratedDocFolder.objects.filter(
        organization__in=user_orgs
    ).order_by('-uploaded_at')
    
    paginated_docs = paginate_queryset(org_doc_folders, request)
    
    context = {
        'doc_folders': paginated_docs,
        'list_type': 'organization',
        'title': 'Organization Repositories',
        'organizations': user_orgs
    }
    
    return render(request, 'list_view.html', context)