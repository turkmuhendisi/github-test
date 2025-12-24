"""
Webapp Core App Configuration
=============================

Core template tags ve context processors için Django app config.
"""

from django.apps import AppConfig


class WebappCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webapp.core'
    label = 'webapp_core'
    verbose_name = 'Webapp Core'

