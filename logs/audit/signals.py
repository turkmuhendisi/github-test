"""
Audit Log Signals
=================

Django signal'ları ile otomatik audit log kaydı.
"""

import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import AuditLog, UserSession

logger = logging.getLogger(__name__)


# =============================================================================
# AUTHENTICATION SIGNALS
# =============================================================================

def get_client_info(request):
    """Request'ten client bilgilerini çıkarır."""
    if not request:
        return None, None
    
    # IP adresi
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # User agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return ip, user_agent


def parse_user_agent(user_agent: str) -> dict:
    """User agent string'ini parse eder."""
    result = {
        'device_type': 'desktop',
        'browser': '',
        'os': '',
    }
    
    if not user_agent:
        return result
    
    ua_lower = user_agent.lower()
    
    # Device type
    if 'mobile' in ua_lower or 'android' in ua_lower and 'mobile' in ua_lower:
        result['device_type'] = 'mobile'
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        result['device_type'] = 'tablet'
    
    # Browser
    if 'chrome' in ua_lower and 'edg' not in ua_lower:
        result['browser'] = 'Chrome'
    elif 'firefox' in ua_lower:
        result['browser'] = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        result['browser'] = 'Safari'
    elif 'edg' in ua_lower:
        result['browser'] = 'Edge'
    elif 'opera' in ua_lower or 'opr' in ua_lower:
        result['browser'] = 'Opera'
    
    # OS
    if 'windows' in ua_lower:
        result['os'] = 'Windows'
    elif 'mac os' in ua_lower or 'macos' in ua_lower:
        result['os'] = 'macOS'
    elif 'linux' in ua_lower:
        result['os'] = 'Linux'
    elif 'android' in ua_lower:
        result['os'] = 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower:
        result['os'] = 'iOS'
    
    return result


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Kullanıcı girişini logla."""
    try:
        ip, user_agent = get_client_info(request)
        ua_info = parse_user_agent(user_agent)
        
        # Audit log
        AuditLog.objects.log_action(
            user=user,
            action=AuditLog.ActionType.LOGIN,
            ip_address=ip,
            user_agent=user_agent,
            extra_data=ua_info,
        )
        
        # User session
        if request and hasattr(request, 'session') and request.session.session_key:
            UserSession.objects.update_or_create(
                session_key=request.session.session_key,
                defaults={
                    'user': user,
                    'ip_address': ip,
                    'user_agent': user_agent,
                    'device_type': ua_info.get('device_type', ''),
                    'browser': ua_info.get('browser', ''),
                    'os': ua_info.get('os', ''),
                    'is_active': True,
                }
            )
        
        logger.info(f"User login: {user.username} from {ip}")
        
    except Exception as e:
        logger.error(f"Error logging user login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Kullanıcı çıkışını logla."""
    try:
        ip, user_agent = get_client_info(request)
        
        # Audit log
        AuditLog.objects.log_action(
            user=user,
            action=AuditLog.ActionType.LOGOUT,
            ip_address=ip,
            user_agent=user_agent,
        )
        
        # Close session
        if request and hasattr(request, 'session') and request.session.session_key:
            try:
                session = UserSession.objects.get(
                    session_key=request.session.session_key
                )
                session.close()
            except UserSession.DoesNotExist:
                pass
        
        logger.info(f"User logout: {user.username if user else 'unknown'}")
        
    except Exception as e:
        logger.error(f"Error logging user logout: {e}")


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Başarısız giriş denemesini logla."""
    try:
        ip, user_agent = get_client_info(request)
        username = credentials.get('username', 'unknown')
        
        AuditLog.objects.log_action(
            user=None,
            action=AuditLog.ActionType.LOGIN_FAILED,
            ip_address=ip,
            user_agent=user_agent,
            extra_data={'username': username},
        )
        
        logger.warning(f"Failed login attempt: {username} from {ip}")
        
    except Exception as e:
        logger.error(f"Error logging failed login: {e}")


# =============================================================================
# MODEL CHANGE TRACKING
# =============================================================================

# Audit edilecek modeller (app_label.model_name formatında)
# Boş bırakılırsa hiçbir model otomatik audit edilmez
# settings.AUDIT_MODELS ile konfigüre edilebilir
AUDIT_MODELS = set()

# Audit edilmeyecek alanlar
EXCLUDED_FIELDS = {'password', 'last_login', 'date_joined', 'updated_at', 'created_at'}


def get_model_changes(instance, created: bool = False) -> dict:
    """
    Model değişikliklerini tespit eder.
    
    Returns:
        dict: {field_name: {'old': old_value, 'new': new_value}}
    """
    changes = {}
    
    if created:
        # Yeni kayıt - tüm alanları logla
        for field in instance._meta.fields:
            if field.name in EXCLUDED_FIELDS:
                continue
            value = getattr(instance, field.name, None)
            if value is not None:
                changes[field.name] = {'old': None, 'new': str(value)[:500]}
    else:
        # Güncelleme - sadece değişenleri logla
        if hasattr(instance, '_original_values'):
            for field_name, old_value in instance._original_values.items():
                if field_name in EXCLUDED_FIELDS:
                    continue
                new_value = getattr(instance, field_name, None)
                if old_value != new_value:
                    changes[field_name] = {
                        'old': str(old_value)[:500] if old_value else None,
                        'new': str(new_value)[:500] if new_value else None,
                    }
    
    return changes


def should_audit_model(instance) -> bool:
    """Model'in audit edilip edilmeyeceğini kontrol eder."""
    if not AUDIT_MODELS:
        return False
    
    model_label = f"{instance._meta.app_label}.{instance._meta.model_name}"
    return model_label in AUDIT_MODELS or '*' in AUDIT_MODELS


@receiver(pre_save)
def store_original_values(sender, instance, **kwargs):
    """Güncelleme öncesi orijinal değerleri sakla."""
    if not should_audit_model(instance):
        return
    
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_values = {
                field.name: getattr(original, field.name)
                for field in instance._meta.fields
                if field.name not in EXCLUDED_FIELDS
            }
        except sender.DoesNotExist:
            instance._original_values = {}


@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    """Model kayıt/güncelleme işlemini logla."""
    if not should_audit_model(instance):
        return
    
    try:
        from .models import ModelChangeLog
        
        content_type = ContentType.objects.get_for_model(instance)
        changes = get_model_changes(instance, created)
        
        if not changes and not created:
            return  # Değişiklik yoksa loglama
        
        # Mevcut kullanıcıyı al (thread-local'den)
        user = None
        try:
            from tools.logs.user_local import get_user
            user = get_user()
        except:
            pass
        
        ModelChangeLog.objects.create(
            content_type=content_type,
            object_id=str(instance.pk),
            object_repr=str(instance)[:200],
            change_type=ModelChangeLog.ChangeType.CREATE if created else ModelChangeLog.ChangeType.UPDATE,
            changes=changes,
            user=user,
        )
        
    except Exception as e:
        logger.error(f"Error logging model save: {e}")


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    """Model silme işlemini logla."""
    if not should_audit_model(instance):
        return
    
    try:
        from .models import ModelChangeLog
        
        content_type = ContentType.objects.get_for_model(instance)
        
        user = None
        try:
            from tools.logs.user_local import get_user
            user = get_user()
        except:
            pass
        
        ModelChangeLog.objects.create(
            content_type=content_type,
            object_id=str(instance.pk),
            object_repr=str(instance)[:200],
            change_type=ModelChangeLog.ChangeType.DELETE,
            changes={},
            user=user,
        )
        
    except Exception as e:
        logger.error(f"Error logging model delete: {e}")

