"""
Logging Middleware
==================

Her request için user ve IP bilgisini thread-local storage'a kaydeder.
Logger bu bilgileri otomatik olarak log mesajlarına ekler.

Kullanım:
--------
MIDDLEWARE = [
    ...
    'tools.logs.middleware.RequestLoggingMiddleware',
    ...
]
"""

import time
import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.conf import settings

from .user_local import set_user_context, clear_user_context
from .utils import get_client_ip, generate_request_id

logger = logging.getLogger('django.request')


class RequestLoggingMiddleware:
    """
    Her request için logging context'i ayarlar.
    
    Özellikler:
    ----------
    - User bilgisini thread-local'e kaydeder
    - IP adresini tespit eder (proxy-aware)
    - Request ID üretir (distributed tracing için)
    - Request süresini loglar
    - Response status code'u loglar
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        # Loglanmayacak path'ler
        self.excluded_paths = getattr(settings, 'LOGGING_EXCLUDED_PATHS', [
            '/health/',
            '/ready/',
            '/favicon.ico',
        ])
        # Static file path'leri
        self.static_url = getattr(settings, 'STATIC_URL', '/static/')
        self.media_url = getattr(settings, 'MEDIA_URL', '/media/')
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Excluded path kontrolü
        if self._should_skip(request.path):
            return self.get_response(request)
        
        # Request başlangıç zamanı
        start_time = time.time()
        
        # Request ID üret
        request_id = request.META.get('HTTP_X_REQUEST_ID') or generate_request_id()
        
        # Context'i set et
        set_user_context(
            user=getattr(request, 'user', None),
            ip_address=get_client_ip(request),
            request_id=request_id,
            path=request.path,
            method=request.method,
        )
        
        # Request ID'yi response header'ına ekle
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        
        # Request süresini hesapla
        duration = (time.time() - start_time) * 1000  # ms
        
        # Access log
        self._log_request(request, response, duration, request_id)
        
        # Context'i temizle
        clear_user_context()
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """Log'lanmaması gereken path'leri kontrol eder."""
        # Excluded paths
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return True
        # Static/media files
        if path.startswith(self.static_url) or path.startswith(self.media_url):
            return True
        return False
    
    def _log_request(
        self,
        request: HttpRequest,
        response: HttpResponse,
        duration: float,
        request_id: str
    ) -> None:
        """Request bilgilerini loglar."""
        status_code = response.status_code
        
        # Log level'ı status code'a göre belirle
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Log mesajı
        logger.log(
            log_level,
            f"{request.method} {request.path} {status_code} {duration:.2f}ms",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'status_code': status_code,
                'duration': duration,
                'user_agent': request.META.get('HTTP_USER_AGENT', '-')[:100],
            }
        )