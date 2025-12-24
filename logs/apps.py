"""
Logs Package App Configuration
==============================

logs/ altındaki tüm app'leri yönetir.
Bu dosya Django tarafından logs package'ının ana app config'i olarak kullanılır.

Alt App'ler:
-----------
- logs.viewer    : Log dosyası görüntüleyici
- logs.audit     : Audit log sistemi  
- logs.analytics : Log analizi ve dashboard
- logs.utils     : Logging utilities

NOT: Her alt app'in kendi apps.py dosyası vardır.
INSTALLED_APPS'e eklerken alt app'leri ayrı ayrı ekleyin.
"""

from django.apps import AppConfig


class LogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs'
    label = 'logs_package'
    verbose_name = 'Logs Package'

