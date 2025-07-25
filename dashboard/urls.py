from django.urls import path
from .views import index, view_doc, file_content_api

urlpatterns = [
    path('', index, name='home'),
    path('view/<int:doc_id>/', view_doc, name='view_doc'),
    path('api/file-content/', file_content_api, name='file_content_api'),
]
