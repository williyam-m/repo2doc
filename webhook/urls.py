from django.urls import path
from . import views

urlpatterns = [
    # Webhook endpoint for GitHub
    path('github/<int:repo_id>/', views.GitHubWebhookView.as_view(), name='github_webhook'),
    
    # API endpoints for webhook management
    path('api/setup/', views.setup_webhook, name='setup_webhook'),
    path('api/remove/', views.remove_webhook, name='remove_webhook'),
    path('api/status/<int:doc_id>/', views.webhook_status, name='webhook_status'),
]
