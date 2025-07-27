from django.shortcuts import render, get_object_or_404
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
        
    profile = get_object_or_404(Profile, user=user)
    
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
