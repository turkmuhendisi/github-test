"""
Audit Log Temizleme Komutu
==========================

Eski audit loglarını ve metrikleri temizler.

KULLANIM ÖRNEKLERİ
==================

  Temel:
  ------
  clean_audit_logs               # 90 günden eski tüm logları temizle
  clean_audit_logs --days 30     # 30 günden eskiler
  clean_audit_logs --dry-run     # Silmeden göster

  Seçici Temizlik:
  ----------------
  clean_audit_logs --model audit     # Sadece audit logları
  clean_audit_logs --model session   # Sadece oturum kayıtları
  clean_audit_logs --model change    # Sadece model değişiklikleri
  clean_audit_logs --model metrics   # Sadece request metrikleri
  clean_audit_logs --model errors    # Sadece error logları

  Cron Job:
  ---------
  # Haftalık temizlik (Pazar gece 02:00)
  0 2 * * 0 cd /app && python manage.py clean_audit_logs --days 90

  # Günlük metrik temizliği
  0 3 * * * cd /app && python manage.py clean_audit_logs --model metrics --days 30
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = '''Eski audit loglarını ve metrikleri temizler

Örnekler:
  %(prog)s clean_audit_logs                   90 günden eski
  %(prog)s clean_audit_logs --days 30         30 günden eski
  %(prog)s clean_audit_logs --dry-run         Silmeden göster
  %(prog)s clean_audit_logs --model audit     Sadece audit
'''
    
    MODELS = {
        'audit': {
            'path': 'logs.audit.models.AuditLog',
            'name': 'Audit Logs',
            'date_field': 'created_at',
            'icon': '📝',
        },
        'session': {
            'path': 'logs.audit.models.UserSession',
            'name': 'User Sessions',
            'date_field': 'login_at',
            'icon': '👤',
        },
        'change': {
            'path': 'logs.audit.models.ModelChangeLog',
            'name': 'Model Changes',
            'date_field': 'created_at',
            'icon': '🔄',
        },
        'metrics': {
            'path': 'logs.analytics.models.RequestMetric',
            'name': 'Request Metrics',
            'date_field': 'timestamp',
            'icon': '📊',
        },
        'errors': {
            'path': 'logs.analytics.models.ErrorLog',
            'name': 'Error Logs',
            'date_field': 'timestamp',
            'icon': '🚨',
        },
        'daily': {
            'path': 'logs.analytics.models.DailyMetricSummary',
            'name': 'Daily Summaries',
            'date_field': 'date',
            'icon': '📈',
        },
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days', '-d',
            type=int,
            default=90,
            metavar='N',
            help='Kaç günden eski loglar silinsin (varsayılan: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Silmeden sadece göster',
        )
        parser.add_argument(
            '--model', '-m',
            type=str,
            choices=['audit', 'session', 'change', 'metrics', 'errors', 'daily', 'all'],
            default='all',
            metavar='MODEL',
            help='Temizlenecek model (audit, session, change, metrics, errors, daily, all)',
        )
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Sessiz mod',
        )
        parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='Onay sormadan sil (script için)',
        )
    
    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options['days'])
        dry_run = options['dry_run']
        model_filter = options['model']
        quiet = options['quiet']
        
        if not quiet:
            self.stdout.write(f"\n🗑️  Log Temizliği")
            self.stdout.write("-" * 50)
            self.stdout.write(f"  📅 Kesim Tarihi : {cutoff.strftime('%Y-%m-%d %H:%M')}")
            self.stdout.write(f"  📆 Silinecek    : {options['days']} günden eski")
            
            if dry_run:
                self.stdout.write(self.style.WARNING("  ⚠️  DRY-RUN modu - kayıtlar silinmeyecek"))
            
            self.stdout.write("-" * 50)
            self.stdout.write("")
        
        # Hangi modeller temizlenecek
        if model_filter == 'all':
            models_to_clean = self.MODELS.keys()
        else:
            models_to_clean = [model_filter]
        
        results = []
        total_count = 0
        
        for model_key in models_to_clean:
            config = self.MODELS[model_key]
            count, error = self._clean_model(config, cutoff, dry_run, quiet)
            results.append({
                'key': model_key,
                'name': config['name'],
                'icon': config['icon'],
                'count': count,
                'error': error,
            })
            if count > 0:
                total_count += count
        
        if not quiet:
            self.stdout.write("")
            self.stdout.write("-" * 50)
            
            # Özet
            if total_count > 0:
                if dry_run:
                    self.stdout.write(self.style.WARNING(
                        f"📝 Toplam {total_count:,} kayıt silinecek (dry-run)"
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Toplam {total_count:,} kayıt silindi"
                    ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    "🎉 Temizlenecek kayıt bulunamadı"
                ))
            
            # Hatalar varsa göster
            errors = [r for r in results if r['error']]
            if errors:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️  {len(errors)} model için hata oluştu"
                ))
            
            self.stdout.write("")
    
    def _clean_model(self, config: dict, cutoff, dry_run: bool, quiet: bool) -> tuple:
        """Model verilerini temizle."""
        try:
            # Dinamik import
            module_path, class_name = config['path'].rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            Model = getattr(module, class_name)
            
            # Filtreleme
            date_field = config['date_field']
            filter_kwargs = {f'{date_field}__lt': cutoff}
            
            # Sayı
            queryset = Model.objects.filter(**filter_kwargs)
            count = queryset.count()
            
            if not quiet:
                if count > 0:
                    status = '🔴' if not dry_run else '🟡'
                    action = 'siliniyor' if not dry_run else 'silinecek'
                    self.stdout.write(
                        f"  {config['icon']} {config['name']:<20} "
                        f"{status} {count:>8,} kayıt {action}"
                    )
                else:
                    self.stdout.write(
                        f"  {config['icon']} {config['name']:<20} "
                        f"✅ temiz"
                    )
            
            # Silme
            if count > 0 and not dry_run:
                # Büyük veri setleri için batch silme
                if count > 10000:
                    self._batch_delete(queryset, quiet)
                else:
                    queryset.delete()
            
            return count, None
            
        except ImportError as e:
            if not quiet:
                self.stdout.write(self.style.ERROR(
                    f"  {config['icon']} {config['name']:<20} "
                    f"❌ modül yüklenemedi"
                ))
            return 0, str(e)
        except Exception as e:
            if not quiet:
                self.stdout.write(self.style.ERROR(
                    f"  {config['icon']} {config['name']:<20} "
                    f"❌ {str(e)[:30]}"
                ))
            return 0, str(e)
    
    def _batch_delete(self, queryset, quiet: bool, batch_size: int = 5000):
        """Büyük veri setlerini batch halinde sil."""
        deleted_total = 0
        while True:
            # ID'leri al
            ids = list(queryset.values_list('id', flat=True)[:batch_size])
            if not ids:
                break
            
            # Batch sil
            count, _ = queryset.filter(id__in=ids).delete()
            deleted_total += count
            
            if not quiet:
                self.stdout.write(f"     ... {deleted_total:,} silindi")
        
        return deleted_total
