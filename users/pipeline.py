import logging

logger = logging.getLogger(__name__)

def save_profile(backend, user, response, *args, **kwargs):
    """
    Custom pipeline function to save GitHub profile information
    """
    logger.debug(f"Processing save_profile for {user.username}")
    logger.debug(f"Response from GitHub: {response}")
    
    if backend.name == 'github':
        from users.models import Profile
        
        try:
            profile, created = Profile.objects.get_or_create(user=user)
            profile.github_id = response.get('id')
            profile.github_username = response.get('login')
            profile.avatar_url = response.get('avatar_url')
            profile.save()
            
            logger.debug(f"Profile {'created' if created else 'updated'} for user {user.username}")
        except Exception as e:
            logger.error(f"Error saving profile for {user.username}: {e}")