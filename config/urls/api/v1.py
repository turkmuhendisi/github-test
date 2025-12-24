"""
API v1 Endpoints
================

REST API versiyon 1 endpoint'leri.
"""

from django.urls import path, include
from django.http import JsonResponse

app_name = 'api-v1'

# =============================================================================
# API ROOT VIEW
# =============================================================================

def api_root(request):
    """API v1 root endpoint."""
    return JsonResponse({
        'version': 'v1',
        'status': 'active',
        'endpoints': {
            'users': '/api/v1/users/',
            'health': '/api/v1/health/',
        }
    })


def api_health(request):
    """API health check."""
    return JsonResponse({'status': 'ok', 'version': 'v1'})

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    path('', api_root, name='root'),
    path('health/', api_health, name='health'),
    
    # Service URL'leri (services app'leri oluşturulduğunda)
    # path('users/', include('services.users.urls')),
    # path('products/', include('services.products.urls')),
]