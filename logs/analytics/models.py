"""
Log Analytics Models
====================

Log analizi için modeller ve agregasyon.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class RequestMetric(models.Model):
    """
    HTTP Request metrikleri.
    
    Her request için temel performans metrikleri.
    """
    
    # Zaman bilgisi
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Zaman',
    )
    
    # Request bilgileri
    path = models.CharField(
        max_length=500,
        db_index=True,
        verbose_name='Path',
    )
    method = models.CharField(
        max_length=10,
        verbose_name='Method',
    )
    
    # Response bilgileri
    status_code = models.PositiveSmallIntegerField(
        verbose_name='Status Code',
        db_index=True,
    )
    response_time = models.FloatField(
        verbose_name='Response Time (ms)',
    )
    
    # Client bilgileri
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
    
    # Kullanıcı
    user_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='User ID',
    )
    
    class Meta:
        verbose_name = 'Request Metriği'
        verbose_name_plural = 'Request Metrikleri'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'status_code']),
            models.Index(fields=['path', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} ({self.response_time}ms)"


class DailyMetricSummary(models.Model):
    """
    Günlük metrik özeti.
    
    Performans dashboard'u için agregasyon.
    """
    
    date = models.DateField(
        unique=True,
        db_index=True,
        verbose_name='Tarih',
    )
    
    # Request sayıları
    total_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='Toplam Request',
    )
    successful_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='Başarılı (2xx)',
    )
    client_errors = models.PositiveIntegerField(
        default=0,
        verbose_name='Client Error (4xx)',
    )
    server_errors = models.PositiveIntegerField(
        default=0,
        verbose_name='Server Error (5xx)',
    )
    
    # Response time
    avg_response_time = models.FloatField(
        default=0,
        verbose_name='Ortalama Response Time (ms)',
    )
    max_response_time = models.FloatField(
        default=0,
        verbose_name='Max Response Time (ms)',
    )
    min_response_time = models.FloatField(
        default=0,
        verbose_name='Min Response Time (ms)',
    )
    p95_response_time = models.FloatField(
        default=0,
        verbose_name='P95 Response Time (ms)',
    )
    
    # Unique değerler
    unique_users = models.PositiveIntegerField(
        default=0,
        verbose_name='Unique Users',
    )
    unique_ips = models.PositiveIntegerField(
        default=0,
        verbose_name='Unique IPs',
    )
    
    # Güncelleme zamanı
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Güncelleme',
    )
    
    class Meta:
        verbose_name = 'Günlük Metrik Özeti'
        verbose_name_plural = 'Günlük Metrik Özetleri'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date} - {self.total_requests} requests"
    
    @property
    def error_rate(self) -> float:
        """Hata oranı (%)."""
        if self.total_requests == 0:
            return 0
        return ((self.client_errors + self.server_errors) / self.total_requests) * 100
    
    @property
    def success_rate(self) -> float:
        """Başarı oranı (%)."""
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100


class EndpointMetric(models.Model):
    """
    Endpoint bazlı metrikler.
    
    En çok kullanılan/hata veren endpoint'ler.
    """
    
    date = models.DateField(
        db_index=True,
        verbose_name='Tarih',
    )
    path = models.CharField(
        max_length=500,
        db_index=True,
        verbose_name='Path',
    )
    method = models.CharField(
        max_length=10,
        verbose_name='Method',
    )
    
    # Sayılar
    request_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Request Sayısı',
    )
    error_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Hata Sayısı',
    )
    
    # Response time
    avg_response_time = models.FloatField(
        default=0,
        verbose_name='Ortalama Response Time (ms)',
    )
    max_response_time = models.FloatField(
        default=0,
        verbose_name='Max Response Time (ms)',
    )
    
    class Meta:
        verbose_name = 'Endpoint Metriği'
        verbose_name_plural = 'Endpoint Metrikleri'
        unique_together = ['date', 'path', 'method']
        ordering = ['-date', '-request_count']
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.request_count} requests"
    
    @property
    def error_rate(self) -> float:
        """Hata oranı (%)."""
        if self.request_count == 0:
            return 0
        return (self.error_count / self.request_count) * 100


class ErrorLog(models.Model):
    """
    Hata logları.
    
    Exception ve error tracking.
    """
    
    class ErrorLevel(models.TextChoices):
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        CRITICAL = 'CRITICAL', 'Critical'
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Zaman',
    )
    
    level = models.CharField(
        max_length=10,
        choices=ErrorLevel.choices,
        default=ErrorLevel.ERROR,
        db_index=True,
        verbose_name='Seviye',
    )
    
    logger_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Logger',
    )
    
    message = models.TextField(
        verbose_name='Mesaj',
    )
    
    exception_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Exception Tipi',
    )
    
    exception_message = models.TextField(
        blank=True,
        verbose_name='Exception Mesajı',
    )
    
    traceback = models.TextField(
        blank=True,
        verbose_name='Traceback',
    )
    
    # Request bilgileri
    path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Path',
    )
    method = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Method',
    )
    user_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='User ID',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Adresi',
    )
    
    # Hata sayısı (aynı hatanın tekrarı)
    occurrence_count = models.PositiveIntegerField(
        default=1,
        verbose_name='Tekrar Sayısı',
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name='Son Görülme',
    )
    
    # Çözüldü mü?
    is_resolved = models.BooleanField(
        default=False,
        verbose_name='Çözüldü',
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Çözülme Zamanı',
    )
    resolved_by = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Çözen',
    )
    
    class Meta:
        verbose_name = 'Hata Logu'
        verbose_name_plural = 'Hata Logları'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['exception_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.message[:100]}"
    
    def resolve(self, user: str = ''):
        """Hatayı çözüldü olarak işaretle."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save(update_fields=['is_resolved', 'resolved_at', 'resolved_by'])

