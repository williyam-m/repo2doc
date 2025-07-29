from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from .models import Profile
from dashboard.models import GeneratedDocFolder
import logging

logger = logging.getLogger(__name__)

def login(request):
    """Login page view"""
    return render(request, 'users/login.html')

@login_required
def profile(request, username=None):
    """View user profile"""
    if username:
        user = get_object_or_404(User, username=username)
        # Only allow users to view their own profile
        if user != request.user:
            return redirect('user_profile', username=request.user.username)
    else:
        user = request.user
    
    # Get profile - it should already exist from the signal or pipeline
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist (fallback only)
        profile = Profile.objects.create(user=user)
        logger.warning(f"Created missing profile for {user.username}")
    
    # Handle token management
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_token':
            token = request.POST.get('github_token', '').strip()
            if token:
                profile.set_github_token(token)
                profile.save()
                messages.success(request, 'GitHub token added successfully!')
            else:
                messages.error(request, 'Please provide a valid GitHub token.')
        
        elif action == 'update_token':
            token = request.POST.get('github_token', '').strip()
            if token:
                profile.set_github_token(token)
                profile.save()
                messages.success(request, 'GitHub token updated successfully!')
            else:
                messages.error(request, 'Please provide a valid GitHub token.')
        
        elif action == 'delete_token':
            profile.set_github_token(None)
            profile.save()
            messages.success(request, 'GitHub token deleted successfully!')
        
        return redirect('user_profile', username=user.username)
    
    context = {
        'profile_user': user,
        'profile': profile,
    }
    
    return render(request, 'users/profile.html', context)

def logout_view(request):
    """Logout the user and redirect to home"""
    logout(request)
    return HttpResponseRedirect(reverse('index'))
