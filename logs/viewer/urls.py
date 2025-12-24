"""
Log Viewer URL Configuration
"""

from django.urls import path
from . import views

app_name = 'log_viewer'

urlpatterns = [
    # Web UI
    path('', views.LogViewerView.as_view(), name='index'),
    
    # API endpoints
    path('api/files/', views.LogFileListView.as_view(), name='api_files'),
    path('api/files/<str:filename>/', views.LogFileReadView.as_view(), name='api_read'),
    path('api/files/<str:filename>/download/', views.LogFileDownloadView.as_view(), name='api_download'),
    path('api/files/<str:filename>/stream/', views.LogFileStreamView.as_view(), name='api_stream'),
    path('api/statistics/', views.LogStatisticsView.as_view(), name='api_statistics'),
]

