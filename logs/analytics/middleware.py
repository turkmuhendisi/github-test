"""
Analytics Middleware
====================

Request metriklerini toplar.
"""

import time
import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.conf import settings

from tools.logs.utils import get_client_ip

logger = logging.getLogger(__name__)


class MetricsMiddleware:
    """
    Request metriklerini toplayan middleware.
    
    Kullanım:
    --------
    MIDDLEWARE = [
        ...
        'logs.analytics.middleware.MetricsMiddleware',
        ...
    ]
    
    Settings:
    --------
    METRICS_ENABLED = True
    METRICS_EXCLUDE_PATHS = ['/health/', '/static/', '/media/']
    METRICS_SAMPLE_RATE = 1.0  # 0.0 - 1.0 arası
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        
        # Settings
        self.enabled = getattr(settings, 'METRICS_ENABLED', True)
        self.exclude_paths = getattr(settings, 'METRICS_EXCLUDE_PATHS', [
            '/health/',
            '/ready/',
            '/live/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ])
        self.sample_rate = getattr(settings, 'METRICS_SAMPLE_RATE', 1.0)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.enabled:
            return self.get_response(request)
        
        # Excluded path kontrolü
        if self._should_skip(request.path):
            return self.get_response(request)
        
        # Sampling
        if self.sample_rate < 1.0:
            import random
            if random.random() > self.sample_rate:
                return self.get_response(request)
        
        # Başlangıç zamanı
        start_time = time.time()
        
        # Request'i işle
        response = self.get_response(request)
        
        # Response time
        response_time = (time.time() - start_time) * 1000  # ms
        
        # Metriği kaydet (async olarak)
        self._record_metric(request, response, response_time)
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """Path'in skip edilip edilmeyeceğini kontrol eder."""
        return any(path.startswith(ep) for ep in self.exclude_paths)
    
    def _record_metric(
        self,
        request: HttpRequest,
        response: HttpResponse,
        response_time: float
    ):
        """Metriği veritabanına kaydet."""
        try:
            from .models import RequestMetric
            
            user_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.id
            
            RequestMetric.objects.create(
                path=request.path[:500],
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                user_id=user_id,
            )
            
        except Exception as e:
            logger.error(f"Error recording metric: {e}")

