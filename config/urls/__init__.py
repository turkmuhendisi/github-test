"""
Merkezi URL Yapılandırması
==========================

Bu modül tüm URL pattern'larını birleştirir.
Her alt modül belirli bir alanı yönetir.

Import Sırası:
-------------
1. base      - Temel URL utilities
2. health    - Health check endpoints
3. i18n      - Dil değiştirme
4. admin     - Admin panel
5. auth      - Authentication
6. api       - REST API endpoints
7. webapp    - Frontend URL'leri
8. static    - Static/Media (dev only)
9. debug     - Debug toolbar (dev only)

Kullanım:
--------
ROOT_URLCONF = 'config.urls'
"""

from django.conf import settings

# Base URL patterns (her zaman aktif)
from .base import urlpatterns as base_patterns
from .health import urlpatterns as health_patterns
from .i18n import urlpatterns as i18n_patterns
from .admin import urlpatterns as admin_patterns

# Application URL patterns
from .auth import urlpatterns as auth_patterns
from .api import urlpatterns as api_patterns
from .webapp import urlpatterns as webapp_patterns

# Logs URL patterns
from django.urls import path, include
logs_patterns = [
    path('logs/', include('logs.urls', namespace='logs')),
]

# =============================================================================
# URL PATTERNS BIRLEŞTIRME
# =============================================================================

urlpatterns = []

# 1. Health checks (en önce - logging bypass için)
urlpatterns += health_patterns

# 2. i18n (dil değiştirme)
urlpatterns += i18n_patterns

# 3. Admin
urlpatterns += admin_patterns

# 4. Logs (Log Viewer & Analytics Dashboard)
urlpatterns += logs_patterns

# 5. Auth
urlpatterns += auth_patterns

# 6. API
urlpatterns += api_patterns

# 7. Webapp (frontend)
urlpatterns += webapp_patterns

# 8. Base patterns (catch-all, en sonda)
urlpatterns += base_patterns

# =============================================================================
# DEVELOPMENT-ONLY PATTERNS
# =============================================================================

if settings.DEBUG:
    from .static import urlpatterns as static_patterns
    from .debug import urlpatterns as debug_patterns
    
    # Debug toolbar en başa
    urlpatterns = debug_patterns + urlpatterns
    
    # Static/Media en sona
    urlpatterns += static_patterns

# =============================================================================
# STARTUP INFO
# =============================================================================
# Banner artık config/startup.py'da merkezi olarak yönetiliyor.
# URL bilgileri ana startup banner'da gösterilir.