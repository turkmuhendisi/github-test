"""
Logs URL Configuration
======================

Tüm log app'lerinin URL'lerini birleştirir.

Kullanım:
--------
# Ana urls.py'de:
urlpatterns = [
    path('logs/', include('logs.urls')),
]

URL Yapısı:
----------
- /logs/viewer/     : Log dosyası görüntüleyici
- /logs/analytics/  : Analytics dashboard
"""

from django.urls import path, include

app_name = 'logs'

urlpatterns = [
    # Log Viewer
    path('viewer/', include('logs.viewer.urls', namespace='viewer')),
    
    # Analytics Dashboard
    path('analytics/', include('logs.analytics.urls', namespace='analytics')),
]

