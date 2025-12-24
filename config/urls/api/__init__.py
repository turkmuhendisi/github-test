"""
API URL Router
==============

Tüm API versiyonlarını birleştirir.
"""

from django.urls import path, include

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # API v1
    path('api/v1/', include('config.urls.api.v1')),
    
    # API v2 (gelecekte)
    # path('api/v2/', include('config.urls.api.v2')),
]