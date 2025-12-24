"""
Database Routers
================

Multi-database yapısı için routing sınıfları.
"""

class PrimaryReplicaRouter:
    """
    Primary/Replica okuma-yazma yönlendirmesi.
    
    - Yazma işlemleri: default (primary)
    - Okuma işlemleri: replica (varsa)
    """
    
    # Özel veritabanlarına yönlendirilecek app'ler
    SPECIAL_APPS = {'analytics', 'reports', 'metrics', 'audit', 'activity', 'system_logs', 'log_analytics'}
    
    def db_for_read(self, model, **hints):
        """Okuma işlemlerini replica'ya yönlendir."""
        # Özel app'ler için diğer router'lara bırak
        if model._meta.app_label in self.SPECIAL_APPS:
            return None
        
        # Replica aktifse ve model uygunsa
        from django.conf import settings
        if 'replica' in settings.DATABASES:
            return 'replica'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Yazma işlemlerini primary'ye yönlendir."""
        # Özel app'ler için diğer router'lara bırak
        if model._meta.app_label in self.SPECIAL_APPS:
            return None
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """İlişkilere izin ver."""
        db_set = {'default', 'replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Primary'de migration yap.
        
        Analytics ve Logs app'leri için None döndür (diğer router'lara bırak).
        logs/analytics veritabanlarına Django core app'leri de migrate edilebilir.
        """
        # Analytics ve Logs app'leri için diğer router'lara bırak
        SPECIAL_APPS = {'analytics', 'reports', 'metrics', 'audit', 'activity', 'system_logs', 'log_analytics'}
        if app_label in SPECIAL_APPS:
            return None
        
        # logs veya analytics veritabanına core app'lerin migrate edilmesine izin ver
        # (ForeignKey bağımlılıkları için gerekli)
        CORE_APPS = {'contenttypes', 'auth'}
        if app_label in CORE_APPS and db in ('logs', 'analytics'):
            return True
        
        # Diğer app'ler için sadece default'a izin ver
        return db == 'default'


class AnalyticsRouter:
    """
    Analytics veritabanı routing.
    
    Belirli app'leri analytics veritabanına yönlendirir.
    """
    
    ANALYTICS_APPS = {'analytics', 'reports', 'metrics'}
    
    def db_for_read(self, model, **hints):
        """Analytics app'lerini analytics db'ye yönlendir."""
        if model._meta.app_label in self.ANALYTICS_APPS:
            return 'analytics'
        return None
    
    def db_for_write(self, model, **hints):
        """Analytics app'lerini analytics db'ye yönlendir."""
        if model._meta.app_label in self.ANALYTICS_APPS:
            return 'analytics'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Aynı db'deki ilişkilere izin ver."""
        if obj1._state.db == 'analytics' or obj2._state.db == 'analytics':
            return obj1._state.db == obj2._state.db
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Analytics app'leri sadece analytics db'de migrate."""
        if app_label in self.ANALYTICS_APPS:
            return db == 'analytics'
        elif db == 'analytics':
            return False
        return None


class LogsRouter:
    """
    Logs veritabanı routing.
    
    Log app'lerini logs veritabanına yönlendirir.
    
    Logs DB'ye yönlendirilen app'ler:
    - audit: Audit log sistemi
    - activity: Kullanıcı aktivite logları
    - system_logs: Sistem logları
    - log_analytics: Request metrikleri (opsiyonel)
    """
    
    LOGS_APPS = {'audit', 'activity', 'system_logs', 'log_analytics'}
    
    def db_for_read(self, model, **hints):
        """Logs app'lerini logs db'ye yönlendir."""
        if model._meta.app_label in self.LOGS_APPS:
            return 'logs'
        return None
    
    def db_for_write(self, model, **hints):
        """Logs app'lerini logs db'ye yönlendir."""
        if model._meta.app_label in self.LOGS_APPS:
            return 'logs'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Logs db içindeki ilişkilere izin ver."""
        if obj1._state.db == 'logs' or obj2._state.db == 'logs':
            return obj1._state.db == obj2._state.db
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Logs app'leri sadece logs db'de migrate."""
        if app_label in self.LOGS_APPS:
            return db == 'logs'
        elif db == 'logs':
            return False
        return None