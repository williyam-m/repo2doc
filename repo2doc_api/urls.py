from django.urls import path
from .views import GenerateDocView

urlpatterns = [
    path('', GenerateDocView.as_view(), name='generate_doc'),
]
