from django.urls import path
from .views import index
from .list_views import (
    public_repos_list,
    private_repos_list,
    my_repos_list,
    organization_repos_list
)

urlpatterns = [
    path('', index, name='index'),
    path('list/public/', public_repos_list, name='public_repos_list'),
    path('list/private/', private_repos_list, name='private_repos_list'),
    path('list/my/', my_repos_list, name='my_repos_list'),
    path('list/organization/', organization_repos_list, name='organization_repos_list'),
]
