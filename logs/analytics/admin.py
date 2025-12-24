"""
Log Analytics Admin
===================

Django admin paneli konfigürasyonu.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import RequestMetric, DailyMetricSummary, EndpointMetric, ErrorLog


@admin.register(RequestMetric)
class RequestMetricAdmin(admin.ModelAdmin):
    """Request Metric admin."""
    
    list_display = [
        'timestamp',
        'method',
        'path_short',
        'status_badge',
        'response_time_display',
        'ip_address',
    ]
    list_filter = [
        'method',
        'status_code',
        'timestamp',
    ]
    search_fields = [
        'path',
        'ip_address',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 100
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def path_short(self, obj):
        path = obj.path
        return path[:50] + '...' if len(path) > 50 else path
    path_short.short_description = 'Path'
    
    def status_badge(self, obj):
        status = obj.status_code
        if status < 300:
            color = '#28a745'
        elif status < 400:
            color = '#17a2b8'
        elif status < 500:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; '
            'border-radius:3px; font-size:11px;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'
    
    def response_time_display(self, obj):
        time = obj.response_time
        if time < 100:
            color = '#28a745'
        elif time < 500:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color:{};">{:.0f}ms</span>',
            color, time
        )
    response_time_display.short_description = 'Response Time'


@admin.register(DailyMetricSummary)
class DailyMetricSummaryAdmin(admin.ModelAdmin):
    """Daily Metric Summary admin."""
    
    list_display = [
        'date',
        'total_requests',
        'successful_requests',
        'client_errors',
        'server_errors',
        'error_rate_display',
        'avg_response_display',
        'unique_users',
    ]
    ordering = ['-date']
    date_hierarchy = 'date'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def error_rate_display(self, obj):
        rate = obj.error_rate
        if rate < 1:
            color = '#28a745'
        elif rate < 5:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color:{};">{:.1f}%</span>',
            color, rate
        )
    error_rate_display.short_description = 'Error Rate'
    
    def avg_response_display(self, obj):
        return f"{obj.avg_response_time:.0f}ms"
    avg_response_display.short_description = 'Avg Response'


@admin.register(EndpointMetric)
class EndpointMetricAdmin(admin.ModelAdmin):
    """Endpoint Metric admin."""
    
    list_display = [
        'date',
        'method',
        'path_short',
        'request_count',
        'error_count',
        'error_rate_display',
        'avg_response_display',
    ]
    list_filter = [
        'method',
        'date',
    ]
    search_fields = [
        'path',
    ]
    ordering = ['-date', '-request_count']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def path_short(self, obj):
        path = obj.path
        return path[:50] + '...' if len(path) > 50 else path
    path_short.short_description = 'Path'
    
    def error_rate_display(self, obj):
        rate = obj.error_rate
        if rate < 1:
            color = '#28a745'
        elif rate < 5:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color:{};">{:.1f}%</span>',
            color, rate
        )
    error_rate_display.short_description = 'Error Rate'
    
    def avg_response_display(self, obj):
        return f"{obj.avg_response_time:.0f}ms"
    avg_response_display.short_description = 'Avg Response'


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """Error Log admin."""
    
    list_display = [
        'timestamp',
        'level_badge',
        'exception_type',
        'message_short',
        'path',
        'occurrence_count',
        'is_resolved',
    ]
    list_filter = [
        'level',
        'is_resolved',
        'timestamp',
    ]
    search_fields = [
        'message',
        'exception_type',
        'path',
    ]
    readonly_fields = [
        'timestamp',
        'level',
        'logger_name',
        'message',
        'exception_type',
        'exception_message',
        'traceback',
        'path',
        'method',
        'user_id',
        'ip_address',
        'occurrence_count',
        'last_seen',
        'resolved_at',
        'resolved_by',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 50
    
    actions = ['mark_resolved']
    
    def has_add_permission(self, request):
        return False
    
    def level_badge(self, obj):
        colors = {
            'WARNING': '#ffc107',
            'ERROR': '#dc3545',
            'CRITICAL': '#6f42c1',
        }
        color = colors.get(obj.level, '#6c757d')
        text_color = 'black' if obj.level == 'WARNING' else 'white'
        
        return format_html(
            '<span style="background:{}; color:{}; padding:2px 6px; '
            'border-radius:3px; font-size:11px;">{}</span>',
            color, text_color, obj.level
        )
    level_badge.short_description = 'Level'
    
    def message_short(self, obj):
        msg = obj.message
        return msg[:80] + '...' if len(msg) > 80 else msg
    message_short.short_description = 'Message'
    
    @admin.action(description='Seçilenleri çözüldü olarak işaretle')
    def mark_resolved(self, request, queryset):
        count = queryset.update(is_resolved=True)
        self.message_user(request, f'{count} hata çözüldü olarak işaretlendi.')

