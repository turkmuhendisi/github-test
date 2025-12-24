"""
Health Check Endpoints
======================

Kubernetes, Docker ve load balancer health check'leri için.
"""

from django.urls import path
from django.http import JsonResponse
from django.db import connection

# =============================================================================
# HEALTH CHECK VIEWS
# =============================================================================

def health_check(request):
    """
    Basit health check.
    Uygulamanın çalışıp çalışmadığını kontrol eder.
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'globalmain'
    })


def readiness_check(request):
    """
    Readiness check.
    Veritabanı bağlantısını kontrol eder.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        db_status = 'ok'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    status = 'ok' if db_status == 'ok' else 'degraded'
    
    return JsonResponse({
        'status': status,
        'database': db_status,
    }, status=200 if status == 'ok' else 503)


def liveness_check(request):
    """
    Liveness check.
    Uygulamanın canlı olup olmadığını kontrol eder.
    """
    return JsonResponse({'status': 'alive'})

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    path('health/', health_check, name='health'),
    path('ready/', readiness_check, name='ready'),
    path('live/', liveness_check, name='live'),
]