"""
Audit Log App Configuration
"""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs.audit'
    label = 'audit'  # LogsRouter bu label'ı kullanır
    verbose_name = 'Audit Logs'
    
    def ready(self):
        """Signal'ları kaydet."""
        from . import signals  # noqa

