"""
Audit Middleware
================

Request bazlı audit logging.
"""

import time
import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.conf import settings

from tools.logs.utils import get_client_ip
from .models import AuditLog

logger = logging.getLogger(__name__)


class AuditMiddleware:
    """
    Belirli işlemleri otomatik olarak audit loglar.
    
    Özellikler:
    ----------
    - POST, PUT, PATCH, DELETE isteklerini loglar
    - Belirli URL pattern'lerini loglar
    - Response süresini kaydeder
    
    Kullanım:
    --------
    MIDDLEWARE = [
        ...
        'logs.audit.middleware.AuditMiddleware',
        ...
    ]
    
    Settings:
    --------
    AUDIT_MIDDLEWARE_ENABLED = True
    AUDIT_PATHS = ['/api/', '/admin/']
    AUDIT_EXCLUDE_PATHS = ['/api/health/']
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        
        # Settings
        self.enabled = getattr(settings, 'AUDIT_MIDDLEWARE_ENABLED', True)
        self.audit_paths = getattr(settings, 'AUDIT_PATHS', ['/admin/'])
        self.exclude_paths = getattr(settings, 'AUDIT_EXCLUDE_PATHS', [
            '/admin/jsi18n/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ])
        self.audit_methods = getattr(settings, 'AUDIT_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE'])
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.enabled:
            return self.get_response(request)
        
        # Audit edilmeli mi?
        should_audit = self._should_audit(request)
        
        if should_audit:
            start_time = time.time()
        
        response = self.get_response(request)
        
        if should_audit:
            duration = (time.time() - start_time) * 1000
            self._log_request(request, response, duration)
        
        return response
    
    def _should_audit(self, request: HttpRequest) -> bool:
        """Request'in audit edilip edilmeyeceğini kontrol eder."""
        path = request.path
        method = request.method
        
        # Excluded path kontrolü
        if any(path.startswith(ep) for ep in self.exclude_paths):
            return False
        
        # Method kontrolü
        if method not in self.audit_methods:
            return False
        
        # Path kontrolü
        if self.audit_paths:
            return any(path.startswith(ap) for ap in self.audit_paths)
        
        return True
    
    def _log_request(
        self,
        request: HttpRequest,
        response: HttpResponse,
        duration: float
    ):
        """Request'i audit logla."""
        try:
            user = request.user if hasattr(request, 'user') else None
            
            # Action type
            method = request.method
            if method == 'POST':
                action = AuditLog.ActionType.CREATE
            elif method in ('PUT', 'PATCH'):
                action = AuditLog.ActionType.UPDATE
            elif method == 'DELETE':
                action = AuditLog.ActionType.DELETE
            else:
                action = AuditLog.ActionType.CUSTOM
            
            # Admin sayfası ise API_CALL yerine uygun action kullan
            if '/admin/' in request.path:
                if 'add' in request.path:
                    action = AuditLog.ActionType.CREATE
                elif 'change' in request.path:
                    action = AuditLog.ActionType.UPDATE
                elif 'delete' in request.path:
                    action = AuditLog.ActionType.DELETE
            
            AuditLog.objects.log_action(
                user=user,
                action=action,
                object_repr=f"{request.method} {request.path}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                extra_data={
                    'method': method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration, 2),
                    'query_string': request.META.get('QUERY_STRING', '')[:200],
                },
            )
            
        except Exception as e:
            logger.error(f"Error in audit middleware: {e}")

