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
        
        # Log the entire response to diagnose what's available
        logger.debug(f"GitHub response keys: {response.keys()}")
        
        try:
            profile, created = Profile.objects.get_or_create(user=user)
            
            # GitHub API returns 'id', 'login' and 'avatar_url'
            profile.github_id = str(response.get('id', ''))
            profile.github_username = response.get('login', '')
            profile.avatar_url = response.get('avatar_url', '')
            
            # Debug log to see what values we're setting
            logger.debug(f"Setting profile data: github_id={profile.github_id}, "
                        f"github_username={profile.github_username}, "
                        f"avatar_url={profile.avatar_url}")
            
            profile.save()
            
            # Verify after save
            logger.debug(f"Profile {'created' if created else 'updated'} for user {user.username}")
            logger.debug(f"Saved profile values: github_id={profile.github_id}, "
                        f"github_username={profile.github_username}, "
                        f"avatar_url={profile.avatar_url}")
        except Exception as e:
            logger.error(f"Error saving profile for {user.username}: {e}")