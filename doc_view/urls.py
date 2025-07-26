from django.urls import path
from .views import view_doc, file_content_api

urlpatterns = [
    path('view/<int:doc_id>/', view_doc, name='view_doc'),
    path('api/file-content/', file_content_api, name='file_content_api'),
]