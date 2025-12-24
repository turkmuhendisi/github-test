"""
Log Viewer App Configuration
"""

from django.apps import AppConfig


class ViewerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs.viewer'
    label = 'log_viewer'
    verbose_name = 'Log Viewer'

