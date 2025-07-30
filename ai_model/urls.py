from django.urls import path
from .views import ai_model_api

urlpatterns = [
    path('api/', ai_model_api, name='ai_model_api'),
]