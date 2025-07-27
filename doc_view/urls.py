from django.urls import path
from . import views

urlpatterns = [
    path('view/<int:doc_id>/', views.view_doc, name='view_doc'),
    path('api/file-content/', views.file_content_api, name='file_content_api'),
]