from django.contrib import admin
from .models import GitHubRepository, WebhookEvent, FileSync

@admin.register(GitHubRepository)
class GitHubRepositoryAdmin(admin.ModelAdmin):
    list_display = ['owner', 'repo_name', 'is_webhook_active', 'auto_sync_enabled', 'last_sync_at', 'sync_failures']
    list_filter = ['is_webhook_active', 'auto_sync_enabled', 'branch']
    search_fields = ['owner', 'repo_name', 'github_url']
    readonly_fields = ['webhook_secret', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Repository Information', {
            'fields': ('doc_folder', 'github_url', 'owner', 'repo_name', 'branch')
        }),
        ('Webhook Configuration', {
            'fields': ('webhook_id', 'webhook_secret', 'is_webhook_active')
        }),
        ('Sync Settings', {
            'fields': ('auto_sync_enabled', 'last_commit_sha', 'last_sync_at')
        }),
        ('Status', {
            'fields': ('sync_failures', 'last_error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['github_repo', 'event_type', 'status', 'files_processed', 'created_at', 'processed_at']
    list_filter = ['event_type', 'status', 'created_at']
    search_fields = ['github_repo__owner', 'github_repo__repo_name', 'github_delivery_id', 'commit_sha']
    readonly_fields = ['payload', 'created_at', 'processed_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('github_repo', 'event_type', 'github_delivery_id', 'commit_sha')
        }),
        ('Processing', {
            'fields': ('status', 'files_processed', 'error_message')
        }),
        ('Payload', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        }),
    )

@admin.register(FileSync)
class FileSyncAdmin(admin.ModelAdmin):
    list_display = ['webhook_event', 'file_path', 'action', 'success', 'created_at']
    list_filter = ['action', 'success', 'created_at']
    search_fields = ['file_path', 'webhook_event__github_repo__owner', 'webhook_event__github_repo__repo_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('webhook_event', 'file_path', 'action')
        }),
        ('Processing Result', {
            'fields': ('success', 'error_message')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
