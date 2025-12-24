"""
Metrik Agregasyon Komutu
========================

Request metriklerini günlük olarak agrege eder.

KULLANIM ÖRNEKLERİ
==================

  Temel:
  ------
  aggregate_metrics              # Dünün metriklerini agrege et
  aggregate_metrics --date 2024-01-15    # Belirli bir gün
  aggregate_metrics --days 7     # Son 7 günü agrege et

  Cron Job:
  ---------
  # Her gün gece 01:00'de
  0 1 * * * cd /app && python manage.py aggregate_metrics

  # Haftalık full agregasyon (Pazar)
  0 2 * * 0 cd /app && python manage.py aggregate_metrics --days 7
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '''Günlük request metriklerini agrege eder

Örnekler:
  %(prog)s aggregate_metrics                  Dün
  %(prog)s aggregate_metrics --date 2024-01-15    Belirli gün
  %(prog)s aggregate_metrics --days 7         Son 7 gün
'''
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date', '-d',
            type=str,
            metavar='YYYY-MM-DD',
            help='Agrege edilecek tarih',
        )
        parser.add_argument(
            '--days', '-n',
            type=int,
            metavar='N',
            help='Son N günü agrege et',
        )
        parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='Mevcut agregasyonları üzerine yaz',
        )
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Sessiz mod (sadece hatalar)',
        )
    
    def handle(self, *args, **options):
        quiet = options['quiet']
        
        if not quiet:
            self.stdout.write("\n📊 Metrik Agregasyonu Başlatılıyor...")
            self.stdout.write("-" * 40)
        
        dates_to_process = []
        
        if options['date']:
            dates_to_process.append(date.fromisoformat(options['date']))
        elif options['days']:
            for i in range(options['days'], 0, -1):
                dates_to_process.append(date.today() - timedelta(days=i))
        else:
            dates_to_process.append(date.today() - timedelta(days=1))
        
        success_count = 0
        error_count = 0
        
        for target_date in dates_to_process:
            result = self._aggregate_date(target_date, options['force'], quiet)
            if result:
                success_count += 1
            else:
                error_count += 1
        
        if not quiet:
            self.stdout.write("-" * 40)
            if error_count == 0:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ {success_count} gün başarıyla agrege edildi'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  {success_count} başarılı, {error_count} hata'
                ))
            self.stdout.write("")
    
    def _aggregate_date(self, target_date: date, force: bool, quiet: bool) -> bool:
        """Belirli bir tarihi agrege et."""
        try:
            from logs.analytics.services import MetricAggregator
            from logs.analytics.models import DailyMetricSummary
            
            # Mevcut kontrolü
            existing = DailyMetricSummary.objects.filter(date=target_date).exists()
            if existing and not force:
                if not quiet:
                    self.stdout.write(
                        f"  ⏭️  {target_date} zaten agrege edilmiş (--force ile üzerine yaz)"
                    )
                return True
            
            if not quiet:
                self.stdout.write(f"  📈 {target_date} işleniyor...")
            
            # Agregasyon
            MetricAggregator.aggregate_daily(target_date)
            MetricAggregator.aggregate_endpoints(target_date)
            
            # Özet bilgi
            summary = DailyMetricSummary.objects.filter(date=target_date).first()
            if summary and not quiet:
                self.stdout.write(
                    f"     ✓ {summary.total_requests} request, "
                    f"{summary.error_rate:.1f}% error, "
                    f"{summary.avg_response_time:.0f}ms avg"
                )
            elif not quiet:
                self.stdout.write(f"     ✓ {target_date} tamamlandı")
            
            return True
            
        except ImportError:
            if not quiet:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Analytics modülü bulunamadı"
                ))
            return False
        except Exception as e:
            if not quiet:
                self.stdout.write(self.style.ERROR(f"  ✗ {target_date}: {e}"))
            return False
