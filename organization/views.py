from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Organization, OrganizationMember
from dashboard.models import GeneratedDocFolder
import uuid

def organization_list(request):
    """List all organizations for authenticated users"""
    if not request.user.is_authenticated:
        return render(request, 'organization/organization_list.html')
    
    # Get organizations user is a member of
    user_memberships = OrganizationMember.objects.filter(user=request.user).select_related('organization')
    
    context = {
        'user_memberships': user_memberships,
    }
    return render(request, 'organization/organization_list.html', context)

@login_required
def create_organization(request):
    """Create a new organization"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            org = Organization.objects.create(
                name=name,
                description=description,
                creator=request.user
            )
            
            # Add creator as admin member
            OrganizationMember.objects.create(
                organization=org,
                user=request.user,
                role='admin'
            )
            
            messages.success(request, f'Organization "{name}" created successfully!')
            return redirect('organization_detail', org_id=org.unique_id)
        else:
            messages.error(request, 'Organization name is required.')
    
    return render(request, 'organization/create_organization.html')

@login_required
def join_organization(request):
    """Join an organization using unique ID"""
    if request.method == 'POST':
        unique_id_str = request.POST.get('unique_id', '')
        
        try:
            # Convert string to UUID
            unique_id = uuid.UUID(unique_id_str)
            organization = Organization.objects.get(unique_id=unique_id)
            
            # Check if user is already a member
            if OrganizationMember.objects.filter(organization=organization, user=request.user).exists():
                messages.warning(request, 'You are already a member of this organization.')
            else:
                # Add user as a member
                OrganizationMember.objects.create(
                    organization=organization,
                    user=request.user,
                    role='member'
                )
                messages.success(request, f'You have joined "{organization.name}" organization.')
            
            return redirect('organization_detail', org_id=organization.unique_id)
        
        except (ValueError, Organization.DoesNotExist):
            context = {
                'join_error': 'Invalid organization ID. Please check and try again.',
                'user_memberships': OrganizationMember.objects.filter(user=request.user).select_related('organization')
            }
            return render(request, 'organization/organization_list.html', context)
    
    return redirect('organization_list')

@login_required
def organization_detail(request, org_id):
    organization = get_object_or_404(Organization, unique_id=org_id)
    
    # Check if user is a member
    try:
        membership = OrganizationMember.objects.get(organization=organization, user=request.user)
        is_member = True
        is_admin = membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        is_member = False
        is_admin = False
    
    if not is_member:
        messages.error(request, 'You do not have access to this organization.')
        return redirect('organization_list')
    
    # Get all members
    members = OrganizationMember.objects.filter(organization=organization).select_related('user')
    
    # Get organization docs
    organization_docs = GeneratedDocFolder.objects.filter(
        organization=organization,
        visibility='organization'
    ).select_related('user')
    
    context = {
        'organization': organization,
        'members': members,
        'organization_docs': organization_docs,
        'is_admin': is_admin
    }
    
    return render(request, 'organization/organization_detail.html', context)

@login_required
def remove_member(request, org_id, user_id):
    organization = get_object_or_404(Organization, unique_id=org_id)
    user_to_remove = get_object_or_404(User, id=user_id)
    
    # Check if requesting user is an admin
    try:
        membership = OrganizationMember.objects.get(organization=organization, user=request.user)
        is_admin = membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        is_admin = False
    
    if not is_admin:
        messages.error(request, 'You do not have permission to remove members.')
        return redirect('organization_detail', org_id=org_id)
    
    # Cannot remove yourself
    if user_to_remove == request.user:
        messages.error(request, 'You cannot remove yourself from the organization.')
        return redirect('organization_detail', org_id=org_id)
    
    # Remove the member
    OrganizationMember.objects.filter(organization=organization, user=user_to_remove).delete()
    messages.success(request, f'{user_to_remove.username} has been removed from the organization.')
    
    return redirect('organization_detail', org_id=org_id)

@login_required
def delete_organization(request, org_id):
    organization = get_object_or_404(Organization, unique_id=org_id)
    
    # Check if requesting user is the creator/admin
    try:
        membership = OrganizationMember.objects.get(organization=organization, user=request.user)
        is_admin = membership.role == 'admin'
    except OrganizationMember.DoesNotExist:
        is_admin = False
    
    if not is_admin:
        messages.error(request, 'You do not have permission to delete this organization.')
        return redirect('organization_list')
    
    # Delete the organization
    organization_name = organization.name
    organization.delete()
    messages.success(request, f'Organization "{organization_name}" has been deleted.')
    
    return redirect('organization_list')