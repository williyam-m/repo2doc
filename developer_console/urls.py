from django.urls import path
from . import views

app_name = 'developer_console'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('auto-sync/<int:doc_id>/', views.auto_sync_settings, name='auto_sync_settings'),
    path('logs/<int:doc_id>/', views.log_view, name='log_view'),
    path('test-webhook/<int:doc_id>/', views.test_webhook, name='test_webhook'),
]