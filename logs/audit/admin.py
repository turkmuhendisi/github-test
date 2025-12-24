"""
Audit Log Admin
===============

Django admin paneli konfigürasyonu.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import AuditLog, UserSession, ModelChangeLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit Log admin paneli."""
    
    list_display = [
        'created_at',
        'username',
        'action_badge',
        'content_type',
        'object_repr',
        'ip_address',
    ]
    list_filter = [
        'action',
        'created_at',
        'content_type',
    ]
    search_fields = [
        'username',
        'object_repr',
        'ip_address',
    ]
    readonly_fields = [
        'user',
        'username',
        'action',
        'content_type',
        'object_id',
        'object_repr',
        'changes_display',
        'ip_address',
        'user_agent',
        'extra_data_display',
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user', 'username', 'ip_address', 'user_agent'),
        }),
        ('İşlem Bilgileri', {
            'fields': ('action', 'content_type', 'object_id', 'object_repr'),
        }),
        ('Detaylar', {
            'fields': ('changes_display', 'extra_data_display'),
            'classes': ('collapse',),
        }),
        ('Zaman', {
            'fields': ('created_at',),
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Sadece superuser silebilir
        return request.user.is_superuser
    
    def action_badge(self, obj):
        """İşlem tipini renkli badge olarak göster."""
        colors = {
            'CREATE': '#28a745',
            'UPDATE': '#17a2b8',
            'DELETE': '#dc3545',
            'LOGIN': '#007bff',
            'LOGOUT': '#6c757d',
            'LOGIN_FAILED': '#ffc107',
            'VIEW': '#20c997',
            'EXPORT': '#6610f2',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_action_display()
        )
    action_badge.short_description = 'İşlem'
    
    def changes_display(self, obj):
        """Değişiklikleri formatlanmış göster."""
        if not obj.changes:
            return '-'
        
        import json
        formatted = json.dumps(obj.changes, indent=2, ensure_ascii=False)
        return format_html('<pre style="margin:0; white-space:pre-wrap;">{}</pre>', formatted)
    changes_display.short_description = 'Değişiklikler'
    
    def extra_data_display(self, obj):
        """Ek verileri formatlanmış göster."""
        if not obj.extra_data:
            return '-'
        
        import json
        formatted = json.dumps(obj.extra_data, indent=2, ensure_ascii=False)
        return format_html('<pre style="margin:0; white-space:pre-wrap;">{}</pre>', formatted)
    extra_data_display.short_description = 'Ek Veriler'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session admin paneli."""
    
    list_display = [
        'user',
        'login_at',
        'last_activity',
        'ip_address',
        'device_badge',
        'browser',
        'os',
        'is_active',
    ]
    list_filter = [
        'is_active',
        'device_type',
        'browser',
        'os',
        'login_at',
    ]
    search_fields = [
        'user__username',
        'user__email',
        'ip_address',
    ]
    readonly_fields = [
        'user',
        'session_key',
        'ip_address',
        'user_agent',
        'device_type',
        'browser',
        'os',
        'location',
        'login_at',
        'logout_at',
        'last_activity',
    ]
    date_hierarchy = 'login_at'
    ordering = ['-login_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def device_badge(self, obj):
        """Cihaz tipini ikon ile göster."""
        icons = {
            'mobile': '📱',
            'tablet': '📲',
            'desktop': '🖥️',
        }
        icon = icons.get(obj.device_type, '❓')
        return f"{icon} {obj.device_type.title()}"
    device_badge.short_description = 'Cihaz'


@admin.register(ModelChangeLog)
class ModelChangeLogAdmin(admin.ModelAdmin):
    """Model Change Log admin paneli."""
    
    list_display = [
        'created_at',
        'content_type',
        'object_id',
        'change_type_badge',
        'user',
    ]
    list_filter = [
        'change_type',
        'content_type',
        'created_at',
    ]
    search_fields = [
        'object_id',
        'object_repr',
        'user__username',
    ]
    readonly_fields = [
        'content_type',
        'object_id',
        'object_repr',
        'change_type',
        'field_name',
        'old_value',
        'new_value',
        'changes_display',
        'user',
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def change_type_badge(self, obj):
        """Değişiklik tipini renkli badge olarak göster."""
        colors = {
            'CREATE': '#28a745',
            'UPDATE': '#17a2b8',
            'DELETE': '#dc3545',
        }
        color = colors.get(obj.change_type, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_change_type_display()
        )
    change_type_badge.short_description = 'Tip'
    
    def changes_display(self, obj):
        """Değişiklikleri formatlanmış göster."""
        if not obj.changes:
            return '-'
        
        import json
        formatted = json.dumps(obj.changes, indent=2, ensure_ascii=False)
        return format_html('<pre style="margin:0; white-space:pre-wrap;">{}</pre>', formatted)
    changes_display.short_description = 'Değişiklikler'

