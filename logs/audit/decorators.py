"""
Audit Decorators
================

View ve fonksiyon bazlı audit logging.
"""

import functools
import logging
from typing import Callable, Optional

from django.contrib.contenttypes.models import ContentType

from .models import AuditLog

logger = logging.getLogger(__name__)


def audit_action(
    action: str = AuditLog.ActionType.CUSTOM,
    object_getter: Optional[Callable] = None,
    description: str = '',
):
    """
    View'ı audit loglar.
    
    Args:
        action: İşlem tipi (AuditLog.ActionType)
        object_getter: İlgili objeyi döndüren fonksiyon (request, *args, **kwargs alır)
        description: İşlem açıklaması
    
    Kullanım:
    --------
    @audit_action(action='VIEW', description='Kullanıcı detay görüntüleme')
    def user_detail(request, pk):
        ...
    
    @audit_action(
        action='EXPORT',
        object_getter=lambda r, *a, **k: Report.objects.get(pk=k['pk'])
    )
    def export_report(request, pk):
        ...
    """
    def decorator(view_func: Callable):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # View'ı çalıştır
            response = view_func(request, *args, **kwargs)
            
            try:
                # Obje bilgisi
                obj = None
                content_type = None
                object_id = None
                object_repr = description
                
                if object_getter:
                    try:
                        obj = object_getter(request, *args, **kwargs)
                        if obj:
                            content_type = ContentType.objects.get_for_model(obj)
                            object_id = str(obj.pk)
                            object_repr = str(obj)[:200]
                    except:
                        pass
                
                # IP ve user agent
                ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                if not ip:
                    ip = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                # Audit log
                AuditLog.objects.log_action(
                    user=request.user if hasattr(request, 'user') else None,
                    action=action,
                    content_type=content_type,
                    object_id=object_id,
                    object_repr=object_repr,
                    ip_address=ip,
                    user_agent=user_agent,
                    extra_data={
                        'view': view_func.__name__,
                        'path': request.path,
                        'method': request.method,
                    },
                )
                
            except Exception as e:
                logger.error(f"Audit decorator error: {e}")
            
            return response
        
        return wrapper
    return decorator


def audit_model_action(
    action: str = AuditLog.ActionType.CUSTOM,
    description: str = '',
):
    """
    Model method'unu audit loglar.
    
    Kullanım:
    --------
    class Order(models.Model):
        @audit_model_action(action='UPDATE', description='Sipariş onaylandı')
        def approve(self, user):
            self.status = 'approved'
            self.save()
    """
    def decorator(method: Callable):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            result = method(self, *args, **kwargs)
            
            try:
                # User bilgisi (ilk argument user ise)
                user = None
                if args and hasattr(args[0], 'is_authenticated'):
                    user = args[0]
                
                content_type = ContentType.objects.get_for_model(self)
                
                AuditLog.objects.log_action(
                    user=user,
                    action=action,
                    content_type=content_type,
                    object_id=str(self.pk),
                    object_repr=str(self)[:200],
                    extra_data={
                        'method': method.__name__,
                        'description': description,
                    },
                )
                
            except Exception as e:
                logger.error(f"Audit model decorator error: {e}")
            
            return result
        
        return wrapper
    return decorator


class AuditContext:
    """
    Context manager ile audit logging.
    
    Kullanım:
    --------
    with AuditContext(user, 'EXPORT', 'Rapor dışa aktarıldı') as audit:
        # İşlemler...
        audit.add_data('file_name', 'report.xlsx')
    """
    
    def __init__(
        self,
        user,
        action: str = AuditLog.ActionType.CUSTOM,
        description: str = '',
        obj=None,
        request=None,
    ):
        self.user = user
        self.action = action
        self.description = description
        self.obj = obj
        self.request = request
        self.extra_data = {}
    
    def add_data(self, key: str, value):
        """Extra data ekle."""
        self.extra_data[key] = value
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            content_type = None
            object_id = None
            object_repr = self.description
            
            if self.obj:
                content_type = ContentType.objects.get_for_model(self.obj)
                object_id = str(self.obj.pk)
                object_repr = str(self.obj)[:200]
            
            ip = None
            user_agent = None
            
            if self.request:
                ip = self.request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                if not ip:
                    ip = self.request.META.get('REMOTE_ADDR')
                user_agent = self.request.META.get('HTTP_USER_AGENT', '')
            
            # Exception bilgisi
            if exc_type:
                self.extra_data['error'] = str(exc_val)
                self.extra_data['error_type'] = exc_type.__name__
            
            AuditLog.objects.log_action(
                user=self.user,
                action=self.action,
                content_type=content_type,
                object_id=object_id,
                object_repr=object_repr,
                ip_address=ip,
                user_agent=user_agent,
                extra_data=self.extra_data,
            )
            
        except Exception as e:
            logger.error(f"AuditContext error: {e}")
        
        return False  # Exception'ı yutma

