from django.contrib import admin
from .models import Organization, OrganizationMember

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'creator__username']
    readonly_fields = ['unique_id']

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'organization__name']