from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    path('', include('social_django.urls', namespace='social')),
]