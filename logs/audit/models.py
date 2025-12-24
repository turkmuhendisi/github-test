"""
Audit Log Models
================

Kullanıcı aktivitelerini kaydetmek için modeller.
"""

import json
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class AuditLogManager(models.Manager):
    """Audit log için özel manager."""
    
    def log_action(
        self,
        user,
        action: str,
        content_type=None,
        object_id=None,
        object_repr: str = '',
        changes: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        extra_data: dict = None,
    ):
        """
        Audit log kaydı oluşturur.
        
        Args:
            user: İşlemi yapan kullanıcı
            action: İşlem tipi (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, VIEW, EXPORT vb.)
            content_type: Model ContentType
            object_id: İlgili obje ID
            object_repr: Objenin string gösterimi
            changes: Değişiklikler (before/after)
            ip_address: Client IP
            user_agent: Browser/Client bilgisi
            extra_data: Ek veriler
        """
        return self.create(
            user=user if user and user.is_authenticated else None,
            username=user.username if user and hasattr(user, 'username') else 'anonymous',
            action=action,
            content_type=content_type,
            object_id=str(object_id) if object_id else None,
            object_repr=object_repr[:200] if object_repr else '',
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            extra_data=extra_data or {},
        )
    
    def for_user(self, user):
        """Belirli bir kullanıcının loglarını döndürür."""
        return self.filter(user=user)
    
    def for_object(self, obj):
        """Belirli bir objenin loglarını döndürür."""
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(
            content_type=content_type,
            object_id=str(obj.pk),
        )
    
    def recent(self, hours: int = 24):
        """Son N saat içindeki logları döndürür."""
        since = timezone.now() - timezone.timedelta(hours=hours)
        return self.filter(created_at__gte=since)


class AuditLog(models.Model):
    """
    Audit Log Modeli
    ================
    
    Tüm kullanıcı aktivitelerini kaydeder.
    """
    
    class ActionType(models.TextChoices):
        CREATE = 'CREATE', 'Oluşturma'
        UPDATE = 'UPDATE', 'Güncelleme'
        DELETE = 'DELETE', 'Silme'
        VIEW = 'VIEW', 'Görüntüleme'
        LOGIN = 'LOGIN', 'Giriş'
        LOGOUT = 'LOGOUT', 'Çıkış'
        LOGIN_FAILED = 'LOGIN_FAILED', 'Başarısız Giriş'
        EXPORT = 'EXPORT', 'Dışa Aktarma'
        IMPORT = 'IMPORT', 'İçe Aktarma'
        PERMISSION_CHANGE = 'PERMISSION_CHANGE', 'Yetki Değişikliği'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Şifre Değişikliği'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Şifre Sıfırlama'
        API_CALL = 'API_CALL', 'API Çağrısı'
        CUSTOM = 'CUSTOM', 'Özel'
    
    # Kullanıcı bilgileri
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Kullanıcı',
    )
    username = models.CharField(
        max_length=150,
        verbose_name='Kullanıcı Adı',
        help_text='Kullanıcı silinse bile kayıt kalır',
    )
    
    # İşlem bilgileri
    action = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        default=ActionType.CUSTOM,
        verbose_name='İşlem',
        db_index=True,
    )
    
    # İlgili obje
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='İçerik Tipi',
    )
    object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Obje ID',
        db_index=True,
    )
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Obje Gösterimi',
    )
    
    # Değişiklikler (JSON)
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Değişiklikler',
        help_text='{"field": {"old": "...", "new": "..."}}'
    )
    
    # Bağlantı bilgileri
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Adresi',
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='User Agent',
    )
    
    # Ek veriler
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Ek Veriler',
    )
    
    # Zaman damgası
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi',
        db_index=True,
    )
    
    objects = AuditLogManager()
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.username} - {self.action}"
    
    @property
    def changes_formatted(self) -> str:
        """Değişiklikleri okunabilir formatta döndürür."""
        if not self.changes:
            return ''
        return json.dumps(self.changes, indent=2, ensure_ascii=False)


class UserSession(models.Model):
    """
    Kullanıcı oturum bilgileri.
    
    Login/logout takibi ve aktif oturum yönetimi.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions_log',
        verbose_name='Kullanıcı',
    )
    
    session_key = models.CharField(
        max_length=40,
        unique=True,
        verbose_name='Session Key',
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Adresi',
    )
    
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='User Agent',
    )
    
    device_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Cihaz Tipi',
        help_text='mobile, tablet, desktop',
    )
    
    browser = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tarayıcı',
    )
    
    os = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='İşletim Sistemi',
    )
    
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Konum',
        help_text='GeoIP ile tespit edilen konum',
    )
    
    login_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Giriş Zamanı',
    )
    
    logout_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Çıkış Zamanı',
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='Son Aktivite',
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Aktif mi?',
    )
    
    class Meta:
        verbose_name = 'Kullanıcı Oturumu'
        verbose_name_plural = 'Kullanıcı Oturumları'
        ordering = ['-login_at']
    
    def __str__(self):
        return f"{self.user} - {self.login_at:%Y-%m-%d %H:%M}"
    
    def close(self):
        """Oturumu kapat."""
        self.is_active = False
        self.logout_at = timezone.now()
        self.save(update_fields=['is_active', 'logout_at'])


class ModelChangeLog(models.Model):
    """
    Model değişiklik geçmişi.
    
    Hangi modelin hangi alanları ne zaman değişti.
    """
    
    class ChangeType(models.TextChoices):
        CREATE = 'CREATE', 'Oluşturma'
        UPDATE = 'UPDATE', 'Güncelleme'
        DELETE = 'DELETE', 'Silme'
    
    # İlgili obje
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='Model',
    )
    object_id = models.CharField(
        max_length=255,
        verbose_name='Obje ID',
        db_index=True,
    )
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Obje Gösterimi',
    )
    
    # Değişiklik bilgileri
    change_type = models.CharField(
        max_length=10,
        choices=ChangeType.choices,
        verbose_name='Değişiklik Tipi',
    )
    
    # Değişen alanlar
    field_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Alan Adı',
    )
    old_value = models.TextField(
        blank=True,
        null=True,
        verbose_name='Eski Değer',
    )
    new_value = models.TextField(
        blank=True,
        null=True,
        verbose_name='Yeni Değer',
    )
    
    # Tüm değişiklikler (JSON)
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Tüm Değişiklikler',
    )
    
    # Kullanıcı bilgisi
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='model_changes',
        verbose_name='Kullanıcı',
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Değişiklik Zamanı',
        db_index=True,
    )
    
    class Meta:
        verbose_name = 'Model Değişiklik Logu'
        verbose_name_plural = 'Model Değişiklik Logları'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.content_type} #{self.object_id} - {self.change_type}"

