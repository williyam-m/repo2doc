import logging

logger = logging.getLogger(__name__)

def save_profile(backend, user, response, *args, **kwargs):
    """
    Custom pipeline function to save GitHub profile information.
    This is called only once during the OAuth flow.
    """
    if backend.name == 'github':
        from users.models import Profile
        
        logger.info(f"Saving GitHub profile for {user.username}")
        
        try:
            # Get or create the profile in a single database operation
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Only update if the GitHub data is available and profile doesn't have it yet
            if not profile.github_username or not profile.avatar_url:
                # GitHub API returns 'id', 'login' and 'avatar_url'
                profile.github_id = str(response.get('id', ''))
                profile.github_username = response.get('login', '')
                profile.avatar_url = response.get('avatar_url', '')
                profile.save()
                
                logger.info(f"Profile data saved: username={profile.github_username}, " 
                           f"has_avatar={'Yes' if profile.avatar_url else 'No'}")
            else:
                logger.info(f"Profile data already exists for {user.username}, skipping update")
                
        except Exception as e:
            logger.error(f"Error saving profile for {user.username}: {e}")