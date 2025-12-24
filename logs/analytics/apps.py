"""
Log Analytics App Configuration
"""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs.analytics'
    label = 'log_analytics'
    verbose_name = 'Log Analytics'

