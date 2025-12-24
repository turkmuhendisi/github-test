# -*- coding: utf-8 -*-
"""
Monitor Middleware
==================

Request'leri izleyerek LiveMonitor'a gönderir.
DEBUG modunda aktiftir.

Kullanım:
--------
Merkezi middleware yönetimi için config/settings/middleware.py dosyasını düzenleyin.

build_middleware() fonksiyonunda aşağıdaki satırları yorum dışına alın:
    
    if IS_DEVELOPMENT and DEBUG:
        middleware.append('tools.monitor.middleware.MonitorMiddleware')
        middleware.append('tools.monitor.middleware.DatabaseQueryMonitorMiddleware')

Veya doğrudan MIDDLEWARE listesine ekleyin:
    'tools.monitor.middleware.MonitorMiddleware',
    'tools.monitor.middleware.DatabaseQueryMonitorMiddleware',
"""

import time
import uuid
from django.conf import settings


class MonitorMiddleware:
    """
    Request'leri izleyen middleware.
    
    LiveMonitor çalışıyorsa request akışını tracker'a gönderir.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._tracker = None
    
    @property
    def tracker(self):
        """Lazy load tracker."""
        if self._tracker is None:
            try:
                from tools.monitor.live_monitor import RequestTracker
                self._tracker = RequestTracker()
            except ImportError:
                pass
        return self._tracker
    
    def __call__(self, request):
        # Sadece DEBUG modunda çalış
        if not getattr(settings, 'DEBUG', False):
            return self.get_response(request)
        
        if not self.tracker:
            return self.get_response(request)
        
        # Request ID oluştur
        request_id = str(uuid.uuid4())[:8]
        request.monitor_id = request_id
        
        # User bilgisi
        user = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
        
        # Request başlangıcını izle
        start_time = time.time()
        self.tracker.track_request_start(
            request_id=request_id,
            method=request.method,
            path=request.path,
            user=user
        )
        
        # Middleware'den geçişi izle
        self.tracker.track_component('middleware')
        
        # Response al
        response = self.get_response(request)
        
        # Response'u izle
        duration_ms = (time.time() - start_time) * 1000
        self.tracker.track_request_end(
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """View çağrılmadan önce."""
        if self.tracker and getattr(settings, 'DEBUG', False):
            self.tracker.track_component('urls')
            self.tracker.track_component('views')
        return None
    
    def process_template_response(self, request, response):
        """Template render edilmeden önce."""
        if self.tracker and getattr(settings, 'DEBUG', False):
            self.tracker.track_component('templates')
        return response


class DatabaseQueryMonitorMiddleware:
    """
    Veritabanı sorgularını izleyen middleware.
    Django Debug Toolbar ile birlikte kullanılabilir.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._tracker = None
    
    @property
    def tracker(self):
        """Lazy load tracker."""
        if self._tracker is None:
            try:
                from tools.monitor.live_monitor import RequestTracker
                self._tracker = RequestTracker()
            except ImportError:
                pass
        return self._tracker
    
    def __call__(self, request):
        if not getattr(settings, 'DEBUG', False):
            return self.get_response(request)
        
        # Database sorgularını izle
        from django.db import connection
        
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Yeni sorguları say
        if self.tracker:
            new_queries = len(connection.queries) - initial_queries
            for _ in range(new_queries):
                self.tracker.track_db_query()
            
            if new_queries > 0:
                self.tracker.track_component('database')
                self.tracker.track_component('models')
        
        return response

