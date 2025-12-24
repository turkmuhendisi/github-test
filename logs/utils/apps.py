"""
Log Utils App Configuration
"""

from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs.utils'
    label = 'log_utils'
    verbose_name = 'Log Utilities'

