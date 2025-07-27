from django.urls import path
from . import views

urlpatterns = [
    path("", views.file_content_api, name="file_content_api"),
]
