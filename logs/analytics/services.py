"""
Log Analytics Services
======================

Analiz ve raporlama servisleri.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from django.db import models
from django.db.models import Count, Avg, Max, Min, F, Q
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone

from .models import (
    RequestMetric,
    DailyMetricSummary,
    EndpointMetric,
    ErrorLog,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Log analizi servisi.
    
    Dashboard ve raporlar için veri sağlar.
    """
    
    @staticmethod
    def get_overview(days: int = 7) -> Dict[str, Any]:
        """
        Genel bakış istatistikleri.
        
        Args:
            days: Son N gün
            
        Returns:
            dict: Özet istatistikler
        """
        since = timezone.now() - timedelta(days=days)
        
        # Request metrikleri
        metrics = RequestMetric.objects.filter(timestamp__gte=since)
        
        total_requests = metrics.count()
        
        status_counts = metrics.values('status_code').annotate(
            count=Count('id')
        ).order_by('status_code')
        
        # Kategorize et
        success = sum(s['count'] for s in status_counts if 200 <= s['status_code'] < 300)
        client_errors = sum(s['count'] for s in status_counts if 400 <= s['status_code'] < 500)
        server_errors = sum(s['count'] for s in status_counts if s['status_code'] >= 500)
        
        # Response time
        response_stats = metrics.aggregate(
            avg=Avg('response_time'),
            max=Max('response_time'),
            min=Min('response_time'),
        )
        
        # Unique counts
        unique_users = metrics.exclude(user_id__isnull=True).values('user_id').distinct().count()
        unique_ips = metrics.exclude(ip_address__isnull=True).values('ip_address').distinct().count()
        
        # Error log count
        error_count = ErrorLog.objects.filter(
            timestamp__gte=since,
            is_resolved=False,
        ).count()
        
        return {
            'period_days': days,
            'total_requests': total_requests,
            'successful_requests': success,
            'client_errors': client_errors,
            'server_errors': server_errors,
            'error_rate': ((client_errors + server_errors) / total_requests * 100) if total_requests else 0,
            'avg_response_time': round(response_stats['avg'] or 0, 2),
            'max_response_time': round(response_stats['max'] or 0, 2),
            'min_response_time': round(response_stats['min'] or 0, 2),
            'unique_users': unique_users,
            'unique_ips': unique_ips,
            'unresolved_errors': error_count,
        }
    
    @staticmethod
    def get_daily_trend(days: int = 30) -> List[Dict[str, Any]]:
        """
        Günlük trend verileri.
        
        Args:
            days: Son N gün
            
        Returns:
            list: Günlük veriler
        """
        since = date.today() - timedelta(days=days)
        
        summaries = DailyMetricSummary.objects.filter(
            date__gte=since
        ).order_by('date')
        
        return [
            {
                'date': s.date.isoformat(),
                'total_requests': s.total_requests,
                'successful_requests': s.successful_requests,
                'client_errors': s.client_errors,
                'server_errors': s.server_errors,
                'error_rate': round(s.error_rate, 2),
                'avg_response_time': round(s.avg_response_time, 2),
                'unique_users': s.unique_users,
            }
            for s in summaries
        ]
    
    @staticmethod
    def get_hourly_trend(hours: int = 24) -> List[Dict[str, Any]]:
        """
        Saatlik trend verileri.
        
        Args:
            hours: Son N saat
            
        Returns:
            list: Saatlik veriler
        """
        since = timezone.now() - timedelta(hours=hours)
        
        hourly = RequestMetric.objects.filter(
            timestamp__gte=since
        ).annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            count=Count('id'),
            avg_response=Avg('response_time'),
            errors=Count('id', filter=Q(status_code__gte=400)),
        ).order_by('hour')
        
        return [
            {
                'hour': h['hour'].isoformat(),
                'request_count': h['count'],
                'avg_response_time': round(h['avg_response'] or 0, 2),
                'error_count': h['errors'],
            }
            for h in hourly
        ]
    
    @staticmethod
    def get_top_endpoints(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        En çok kullanılan endpoint'ler.
        
        Args:
            days: Son N gün
            limit: Kaç endpoint gösterilecek
            
        Returns:
            list: Endpoint listesi
        """
        since = timezone.now() - timedelta(days=days)
        
        endpoints = RequestMetric.objects.filter(
            timestamp__gte=since
        ).values('path', 'method').annotate(
            count=Count('id'),
            avg_response=Avg('response_time'),
            max_response=Max('response_time'),
            errors=Count('id', filter=Q(status_code__gte=400)),
        ).order_by('-count')[:limit]
        
        return [
            {
                'path': e['path'],
                'method': e['method'],
                'request_count': e['count'],
                'avg_response_time': round(e['avg_response'] or 0, 2),
                'max_response_time': round(e['max_response'] or 0, 2),
                'error_count': e['errors'],
                'error_rate': round((e['errors'] / e['count'] * 100) if e['count'] else 0, 2),
            }
            for e in endpoints
        ]
    
    @staticmethod
    def get_slowest_endpoints(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        En yavaş endpoint'ler.
        
        Args:
            days: Son N gün
            limit: Kaç endpoint gösterilecek
            
        Returns:
            list: Endpoint listesi
        """
        since = timezone.now() - timedelta(days=days)
        
        endpoints = RequestMetric.objects.filter(
            timestamp__gte=since
        ).values('path', 'method').annotate(
            count=Count('id'),
            avg_response=Avg('response_time'),
            max_response=Max('response_time'),
        ).filter(count__gte=10).order_by('-avg_response')[:limit]
        
        return [
            {
                'path': e['path'],
                'method': e['method'],
                'request_count': e['count'],
                'avg_response_time': round(e['avg_response'] or 0, 2),
                'max_response_time': round(e['max_response'] or 0, 2),
            }
            for e in endpoints
        ]
    
    @staticmethod
    def get_error_endpoints(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        En çok hata veren endpoint'ler.
        
        Args:
            days: Son N gün
            limit: Kaç endpoint gösterilecek
            
        Returns:
            list: Endpoint listesi
        """
        since = timezone.now() - timedelta(days=days)
        
        endpoints = RequestMetric.objects.filter(
            timestamp__gte=since,
            status_code__gte=400,
        ).values('path', 'method').annotate(
            error_count=Count('id'),
        ).order_by('-error_count')[:limit]
        
        return [
            {
                'path': e['path'],
                'method': e['method'],
                'error_count': e['error_count'],
            }
            for e in endpoints
        ]
    
    @staticmethod
    def get_recent_errors(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Son hatalar.
        
        Args:
            limit: Kaç hata gösterilecek
            
        Returns:
            list: Hata listesi
        """
        errors = ErrorLog.objects.filter(
            is_resolved=False
        ).order_by('-timestamp')[:limit]
        
        return [
            {
                'id': e.id,
                'timestamp': e.timestamp.isoformat(),
                'level': e.level,
                'message': e.message[:200],
                'exception_type': e.exception_type,
                'path': e.path,
                'occurrence_count': e.occurrence_count,
            }
            for e in errors
        ]
    
    @staticmethod
    def get_status_distribution(days: int = 7) -> Dict[str, int]:
        """
        Status code dağılımı.
        
        Args:
            days: Son N gün
            
        Returns:
            dict: Status code -> count
        """
        since = timezone.now() - timedelta(days=days)
        
        distribution = RequestMetric.objects.filter(
            timestamp__gte=since
        ).values('status_code').annotate(
            count=Count('id')
        ).order_by('status_code')
        
        return {str(d['status_code']): d['count'] for d in distribution}


class MetricAggregator:
    """
    Metrik agregasyon servisi.
    
    Günlük özetler oluşturur.
    """
    
    @staticmethod
    def aggregate_daily(target_date: date = None):
        """
        Belirli bir gün için metrikleri agrege eder.
        
        Args:
            target_date: Hedef tarih (default: dün)
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end = start + timedelta(days=1)
        
        metrics = RequestMetric.objects.filter(
            timestamp__gte=start,
            timestamp__lt=end,
        )
        
        if not metrics.exists():
            logger.info(f"No metrics for {target_date}")
            return
        
        # Agregasyon
        stats = metrics.aggregate(
            total=Count('id'),
            success=Count('id', filter=Q(status_code__gte=200, status_code__lt=300)),
            client_err=Count('id', filter=Q(status_code__gte=400, status_code__lt=500)),
            server_err=Count('id', filter=Q(status_code__gte=500)),
            avg_response=Avg('response_time'),
            max_response=Max('response_time'),
            min_response=Min('response_time'),
        )
        
        unique_users = metrics.exclude(user_id__isnull=True).values('user_id').distinct().count()
        unique_ips = metrics.exclude(ip_address__isnull=True).values('ip_address').distinct().count()
        
        # P95 hesapla (basit yaklaşım)
        response_times = list(metrics.values_list('response_time', flat=True).order_by('response_time'))
        p95_index = int(len(response_times) * 0.95)
        p95 = response_times[p95_index] if response_times else 0
        
        # Kaydet
        DailyMetricSummary.objects.update_or_create(
            date=target_date,
            defaults={
                'total_requests': stats['total'],
                'successful_requests': stats['success'],
                'client_errors': stats['client_err'],
                'server_errors': stats['server_err'],
                'avg_response_time': stats['avg_response'] or 0,
                'max_response_time': stats['max_response'] or 0,
                'min_response_time': stats['min_response'] or 0,
                'p95_response_time': p95,
                'unique_users': unique_users,
                'unique_ips': unique_ips,
            }
        )
        
        logger.info(f"Aggregated metrics for {target_date}: {stats['total']} requests")
    
    @staticmethod
    def aggregate_endpoints(target_date: date = None):
        """
        Endpoint bazlı metrikleri agrege eder.
        
        Args:
            target_date: Hedef tarih (default: dün)
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end = start + timedelta(days=1)
        
        endpoints = RequestMetric.objects.filter(
            timestamp__gte=start,
            timestamp__lt=end,
        ).values('path', 'method').annotate(
            count=Count('id'),
            errors=Count('id', filter=Q(status_code__gte=400)),
            avg_response=Avg('response_time'),
            max_response=Max('response_time'),
        )
        
        for ep in endpoints:
            EndpointMetric.objects.update_or_create(
                date=target_date,
                path=ep['path'],
                method=ep['method'],
                defaults={
                    'request_count': ep['count'],
                    'error_count': ep['errors'],
                    'avg_response_time': ep['avg_response'] or 0,
                    'max_response_time': ep['max_response'] or 0,
                }
            )
        
        logger.info(f"Aggregated {len(endpoints)} endpoints for {target_date}")

