from django.urls import path
from . import views

urlpatterns = [
    path('', views.organization_list, name='organization_list'),
    path('create/', views.create_organization, name='create_organization'),
    path('join/', views.join_organization, name='join_organization'),
    path('<uuid:org_id>/', views.organization_detail, name='organization_detail'),
    path('<uuid:org_id>/remove/<int:user_id>/', views.remove_member, name='remove_member'),
    path('<uuid:org_id>/delete/', views.delete_organization, name='delete_organization'),
]