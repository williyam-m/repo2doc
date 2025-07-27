from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Profile
from dashboard.models import GeneratedDocFolder
import logging

logger = logging.getLogger(__name__)

def login(request):
    """Login page view"""
    logger.info(f"Login page accessed. Next URL: {request.GET.get('next')}")
    return render(request, 'users/login.html')

@login_required
def profile(request, username=None):
    """View user profile"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    logger.debug(f"Accessing profile for user: {user.username}")
    
    # Ensure profile exists for the user
    try:
        profile = Profile.objects.get(user=user)
        logger.debug(f"Found profile for {user.username}: github_username={profile.github_username}, avatar_url={profile.avatar_url}")
    except Profile.DoesNotExist:
        logger.warning(f"No profile found for {user.username}, creating one")
        profile = Profile.objects.create(user=user)
    
    # Refresh profile data if it's the current user and missing GitHub info
    if user == request.user and not profile.github_username and hasattr(request.user, 'social_auth'):
        try:
            social_user = request.user.social_auth.filter(provider='github').first()
            if social_user:
                logger.debug(f"Found social auth data for {user.username}")
                extra_data = social_user.extra_data
                logger.debug(f"Extra data: {extra_data}")
                
                if 'login' in extra_data:
                    profile.github_username = extra_data.get('login')
                    profile.avatar_url = extra_data.get('avatar_url')
                    profile.github_id = str(extra_data.get('id', ''))
                    profile.save()
                    logger.debug(f"Updated profile with GitHub data: {profile.github_username}")
        except Exception as e:
            logger.error(f"Error refreshing GitHub data: {e}")
    
    # Get user's generated docs
    user_doc_folders = GeneratedDocFolder.objects.filter(user=user).order_by('-uploaded_at')
    
    context = {
        'profile_user': user,
        'profile': profile,
        'user_doc_folders': user_doc_folders,
    }
    
    return render(request, 'users/profile.html', context)

def logout_view(request):
    """Logout the user and redirect to home"""
    logout(request)
    return HttpResponseRedirect(reverse('index'))
