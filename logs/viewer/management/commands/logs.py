"""
Log Yönetim Komutu
==================

Log dosyalarını görüntüleme, filtreleme ve yönetme.

KULLANIM ÖRNEKLERİ
==================

  Temel Görüntüleme:
  ------------------
  logs                          # global.log'un son 50 satırı
  logs -n 100                   # Son 100 satır
  logs -f error.log             # error.log dosyasını görüntüle
  logs -F                       # Canlı takip (tail -f)

  Filtreleme:
  -----------
  logs -l ERROR                 # Sadece ERROR seviyesi
  logs -l WARNING -n 20         # Son 20 WARNING
  logs -s "database"            # "database" içeren satırlar
  logs --logger django.request  # Belirli logger
  logs --since 2024-01-15       # Belirli tarihten sonra

  Dosya Yönetimi:
  ---------------
  logs --list                   # Dosyaları listele
  logs --stats                  # İstatistikler
  logs --clean --days 30        # 30 günden eski dosyaları sil
  logs --archive                # Logları arşivle (gzip)

  Audit Loglar:
  -------------
  logs --audit                  # Son audit logları
  logs --audit --user admin     # Belirli kullanıcının logları
  logs --audit --action LOGIN   # Belirli aksiyon

  Analitik:
  ---------
  logs --metrics                # Request metrikleri özeti
  logs --errors                 # Son hatalar

  Çıktı Formatları:
  -----------------
  logs --json                   # JSON formatında çıktı
  logs --plain                  # Renksiz çıktı
"""

import os
import re
import time
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# ANSI renk kodları
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
    'DIM': '\033[2m',
    'HEADER': '\033[94m',    # Light Blue
    'SUCCESS': '\033[92m',   # Light Green
}


class Command(BaseCommand):
    help = '''Log yönetim aracı - Görüntüleme, filtreleme ve yönetim

Örnekler:
  %(prog)s logs                     Son logları göster
  %(prog)s logs -f error.log        Error log'u göster
  %(prog)s logs -l ERROR -n 50      Son 50 ERROR
  %(prog)s logs --list              Dosyaları listele
  %(prog)s logs --audit             Audit logları
'''
    
    def add_arguments(self, parser):
        # === GÖRÜNTÜLEME ===
        view_group = parser.add_argument_group('📄 Görüntüleme')
        view_group.add_argument(
            '--file', '-f',
            type=str,
            metavar='DOSYA',
            help='Log dosyası (error.log, global.log, vb.)',
        )
        view_group.add_argument(
            '--tail', '-n',
            type=int,
            default=50,
            metavar='N',
            help='Son N satır (varsayılan: 50)',
        )
        view_group.add_argument(
            '--follow', '-F',
            action='store_true',
            help='Canlı takip (tail -f)',
        )
        view_group.add_argument(
            '--head',
            type=int,
            metavar='N',
            help='İlk N satır',
        )
        
        # === FİLTRELEME ===
        filter_group = parser.add_argument_group('🔍 Filtreleme')
        filter_group.add_argument(
            '--level', '-l',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            metavar='LEVEL',
            help='Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
        )
        filter_group.add_argument(
            '--search', '-s',
            type=str,
            metavar='TEXT',
            help='Metin araması',
        )
        filter_group.add_argument(
            '--logger',
            type=str,
            metavar='NAME',
            help='Logger adı filtresi (örn: django.request)',
        )
        filter_group.add_argument(
            '--since',
            type=str,
            metavar='YYYY-MM-DD',
            help='Bu tarihten sonra',
        )
        filter_group.add_argument(
            '--until',
            type=str,
            metavar='YYYY-MM-DD',
            help='Bu tarihe kadar',
        )
        filter_group.add_argument(
            '--today',
            action='store_true',
            help='Sadece bugünün logları',
        )
        
        # === DOSYA YÖNETİMİ ===
        manage_group = parser.add_argument_group('📁 Dosya Yönetimi')
        manage_group.add_argument(
            '--list', '-L',
            action='store_true',
            help='Log dosyalarını listele',
        )
        manage_group.add_argument(
            '--stats',
            action='store_true',
            help='Log istatistiklerini göster',
        )
        manage_group.add_argument(
            '--clean',
            action='store_true',
            help='Eski log dosyalarını temizle',
        )
        manage_group.add_argument(
            '--days',
            type=int,
            default=30,
            metavar='N',
            help='--clean için gün sayısı (varsayılan: 30)',
        )
        manage_group.add_argument(
            '--archive',
            action='store_true',
            help='Log dosyalarını arşivle (gzip)',
        )
        
        # === AUDİT LOGLAR ===
        audit_group = parser.add_argument_group('🔐 Audit Loglar')
        audit_group.add_argument(
            '--audit',
            action='store_true',
            help='Audit loglarını göster',
        )
        audit_group.add_argument(
            '--user', '-u',
            type=str,
            metavar='USERNAME',
            help='Kullanıcıya göre filtrele',
        )
        audit_group.add_argument(
            '--action', '-a',
            type=str,
            metavar='ACTION',
            help='Aksiyona göre filtrele (LOGIN, LOGOUT, CREATE, UPDATE, DELETE)',
        )
        
        # === ANALİTİK ===
        analytics_group = parser.add_argument_group('📊 Analitik')
        analytics_group.add_argument(
            '--metrics',
            action='store_true',
            help='Request metrikleri özeti',
        )
        analytics_group.add_argument(
            '--errors',
            action='store_true',
            help='Son hata logları',
        )
        
        # === ÇIKTI FORMATI ===
        format_group = parser.add_argument_group('🎨 Çıktı Formatı')
        format_group.add_argument(
            '--plain',
            action='store_true',
            help='Renksiz çıktı',
        )
        format_group.add_argument(
            '--json',
            action='store_true',
            help='JSON formatında çıktı',
        )
        format_group.add_argument(
            '--compact',
            action='store_true',
            help='Kompakt çıktı (sadece mesaj)',
        )
    
    def handle(self, *args, **options):
        # LOG_DIR settings'ten al, yoksa varsayılan kullan
        self.log_dir = getattr(settings, 'LOG_DIR', settings.BASE_DIR / 'logs' / 'data')
        self.log_dir = Path(self.log_dir)
        
        # Alt dizinler
        self.log_levels_dir = self.log_dir / 'levels'
        self.log_database_dir = self.log_dir / 'database'
        self.log_archive_dir = self.log_dir / 'archive'
        
        self.use_color = not options['plain'] and not options.get('no_color', False)
        self.json_output = options['json']
        self.compact = options['compact']
        
        # Bugün filtresi
        if options['today']:
            options['since'] = datetime.now().strftime('%Y-%m-%d')
        
        # Ana işlemler
        if options['list']:
            return self.list_files()
        
        if options['stats']:
            return self.show_stats()
        
        if options['clean']:
            return self.clean_logs(options['days'])
        
        if options['archive']:
            return self.archive_logs()
        
        if options['audit']:
            return self.show_audit_logs(options)
        
        if options['metrics']:
            return self.show_metrics()
        
        if options['errors']:
            return self.show_errors()
        
        # Varsayılan: log dosyası göster
        return self.view_logs(options)
    
    def _color(self, text: str, color: str) -> str:
        """Metni renklendir."""
        if not self.use_color:
            return text
        return f"{COLORS.get(color, '')}{text}{COLORS['RESET']}"
    
    def _header(self, text: str):
        """Başlık yazdır."""
        if self.json_output:
            return
        self.stdout.write(self._color(f"\n{text}", 'HEADER'))
        self.stdout.write(self._color("-" * 60, 'DIM'))
    
    def list_files(self):
        """Log dosyalarını listele."""
        log_path = Path(self.log_dir)
        
        if not log_path.exists():
            self.stderr.write(self.style.ERROR(f"Log dizini bulunamadı: {log_path}"))
            return
        
        # Tüm .log dosyalarını topla (alt klasörler dahil)
        all_files = []
        
        # Kategorize et
        categories = {
            'main': {'name': '📁 Ana Loglar', 'path': log_path, 'files': []},
            'levels': {'name': '📊 Seviye Logları', 'path': self.log_levels_dir, 'files': []},
            'database': {'name': '🗄️  Veritabanı Logları', 'path': self.log_database_dir, 'files': []},
            'archive': {'name': '📦 Arşiv', 'path': self.log_archive_dir, 'files': []},
        }
        
        for cat_key, cat_info in categories.items():
            cat_path = cat_info['path']
            if cat_path.exists():
                for f in sorted(cat_path.glob('*.log*')):
                    if f.is_file():
                        stat = f.stat()
                        file_info = {
                            'name': f.name,
                            'path': str(f.relative_to(log_path)),
                            'category': cat_key,
                            'size': stat.st_size,
                            'size_human': self._format_size(stat.st_size),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'modified_human': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        }
                        cat_info['files'].append(file_info)
                        all_files.append(file_info)
        
        if self.json_output:
            import json
            self.stdout.write(json.dumps(all_files, indent=2))
            return
        
        self._header(f"📁 Log Dosyaları ({log_path})")
        
        total_size = 0
        total_files = 0
        
        for cat_key, cat_info in categories.items():
            if cat_info['files']:
                self.stdout.write(f"\n  {self._color(cat_info['name'], 'HEADER')}")
                
                for f in cat_info['files']:
                    icon = "📄" if f['size'] > 0 else "📃"
                    name_colored = self._color(f"{f['name']:<25}", 'BOLD')
                    size_colored = self._color(f"{f['size_human']:>10}", 'DIM')
                    self.stdout.write(f"    {icon} {name_colored} {size_colored}  {f['modified_human']}")
                    total_size += f['size']
                    total_files += 1
        
        self.stdout.write("")
        self.stdout.write(self._color("-" * 60, 'DIM'))
        self.stdout.write(self._color(f"  📊 Toplam: {total_files} dosya, {self._format_size(total_size)}", 'SUCCESS'))
        self.stdout.write("")
    
    def show_stats(self):
        """Log istatistiklerini göster."""
        log_path = Path(self.log_dir)
        
        stats = {
            'files': 0,
            'total_size': 0,
            'total_size_human': '',
            'levels': {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0},
            'by_file': {},
        }
        
        # Tüm .log dosyalarını tara (alt klasörler dahil)
        for f in log_path.glob('**/*.log'):
            if f.is_file():
                stats['files'] += 1
                file_size = f.stat().st_size
                stats['total_size'] += file_size
                relative_path = str(f.relative_to(log_path))
                stats['by_file'][relative_path] = {'size': file_size, 'lines': 0}
                
                # Son 1000 satırı analiz et
                try:
                    lines = self._tail_file(f, 1000)
                    stats['by_file'][relative_path]['lines'] = len(lines)
                    for line in lines:
                        for level in stats['levels']:
                            if f'[{level}' in line:
                                stats['levels'][level] += 1
                                break
                except:
                    pass
        
        stats['total_size_human'] = self._format_size(stats['total_size'])
        
        if self.json_output:
            import json
            self.stdout.write(json.dumps(stats, indent=2))
            return
        
        self._header("📊 Log İstatistikleri")
        
        self.stdout.write(f"  📁 Dosya sayısı : {self._color(str(stats['files']), 'BOLD')}")
        self.stdout.write(f"  💾 Toplam boyut : {self._color(stats['total_size_human'], 'BOLD')}")
        self.stdout.write("")
        self.stdout.write("  📈 Level Dağılımı (son loglardan):")
        
        max_count = max(stats['levels'].values()) if stats['levels'].values() else 1
        for level, count in stats['levels'].items():
            bar_len = int((count / max_count) * 20) if max_count > 0 else 0
            bar = "█" * bar_len + "░" * (20 - bar_len)
            level_colored = self._color(f"{level:<10}", level)
            self.stdout.write(f"    {level_colored} {count:>5} {self._color(bar, level)}")
        
        self.stdout.write("")
    
    def clean_logs(self, days: int):
        """Eski log dosyalarını temizle."""
        log_path = Path(self.log_dir)
        cutoff = datetime.now() - timedelta(days=days)
        
        deleted = []
        for f in log_path.glob('*.log.*'):
            mod_time = datetime.fromtimestamp(f.stat().st_mtime)
            if mod_time < cutoff:
                size = f.stat().st_size
                f.unlink()
                deleted.append({'name': f.name, 'size': size})
        
        if self.json_output:
            import json
            self.stdout.write(json.dumps({'deleted': deleted, 'count': len(deleted)}))
            return
        
        if deleted:
            total_size = sum(d['size'] for d in deleted)
            self._header(f"🗑️  Temizlik Tamamlandı")
            self.stdout.write(self._color(f"  {len(deleted)} dosya silindi ({self._format_size(total_size)})", 'SUCCESS'))
            for d in deleted:
                self.stdout.write(f"    ✗ {d['name']}")
        else:
            self.stdout.write(self.style.WARNING(f"\n⚠️  {days} günden eski dosya bulunamadı"))
        self.stdout.write("")
    
    def archive_logs(self):
        """Log dosyalarını arşivle."""
        log_path = Path(self.log_dir)
        archive_dir = log_path / 'archive'
        archive_dir.mkdir(exist_ok=True)
        
        archived = []
        for f in log_path.glob('*.log'):
            if f.stat().st_size > 0:
                mod_time = datetime.fromtimestamp(f.stat().st_mtime)
                if mod_time.date() < datetime.now().date():
                    archive_name = f"{f.stem}_{mod_time.strftime('%Y%m%d')}.log.gz"
                    archive_path = archive_dir / archive_name
                    
                    with open(f, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    original_size = f.stat().st_size
                    compressed_size = archive_path.stat().st_size
                    
                    f.write_text('')
                    
                    archived.append({
                        'name': archive_name,
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                    })
        
        if self.json_output:
            import json
            self.stdout.write(json.dumps({'archived': archived, 'count': len(archived)}))
            return
        
        if archived:
            self._header("📦 Arşivleme Tamamlandı")
            for a in archived:
                ratio = (1 - a['compressed_size'] / a['original_size']) * 100 if a['original_size'] > 0 else 0
                self.stdout.write(
                    f"  ✓ {a['name']} "
                    f"({self._format_size(a['original_size'])} → "
                    f"{self._format_size(a['compressed_size'])}, "
                    f"{self._color(f'%{ratio:.0f}', 'SUCCESS')} sıkıştırma)"
                )
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  Arşivlenecek dosya bulunamadı"))
        self.stdout.write("")
    
    def show_audit_logs(self, options):
        """Audit loglarını göster."""
        try:
            from logs.audit.models import AuditLog
        except ImportError:
            self.stderr.write(self.style.ERROR("Audit modülü bulunamadı"))
            return
        
        queryset = AuditLog.objects.all().order_by('-created_at')
        
        # Filtreler
        if options.get('user'):
            queryset = queryset.filter(username__icontains=options['user'])
        
        if options.get('action'):
            queryset = queryset.filter(action=options['action'].upper())
        
        if options.get('since'):
            queryset = queryset.filter(created_at__date__gte=options['since'])
        
        if options.get('until'):
            queryset = queryset.filter(created_at__date__lte=options['until'])
        
        # Limit
        limit = options.get('tail', 50)
        logs = queryset[:limit]
        
        if self.json_output:
            import json
            data = [
                {
                    'id': log.id,
                    'timestamp': log.created_at.isoformat(),
                    'user': log.username,
                    'action': log.action,
                    'object': log.object_repr,
                    'ip': log.ip_address,
                }
                for log in logs
            ]
            self.stdout.write(json.dumps(data, indent=2))
            return
        
        self._header(f"🔐 Audit Loglar (son {limit})")
        
        action_colors = {
            'LOGIN': 'SUCCESS',
            'LOGOUT': 'DIM',
            'CREATE': 'INFO',
            'UPDATE': 'WARNING',
            'DELETE': 'ERROR',
            'LOGIN_FAILED': 'ERROR',
        }
        
        for log in logs:
            time_str = log.created_at.strftime('%m-%d %H:%M')
            action_color = action_colors.get(log.action, 'DIM')
            action_str = self._color(f"{log.action:<12}", action_color)
            user_str = self._color(f"{log.username:<15}", 'BOLD')
            
            if self.compact:
                self.stdout.write(f"  {time_str} {action_str} {user_str}")
            else:
                obj_str = log.object_repr[:30] + '...' if len(log.object_repr) > 30 else log.object_repr
                self.stdout.write(f"  {time_str} {action_str} {user_str} {obj_str}")
        
        self.stdout.write("")
    
    def show_metrics(self):
        """Request metriklerini göster."""
        try:
            from logs.analytics.services import AnalyticsService
        except ImportError:
            self.stderr.write(self.style.ERROR("Analytics modülü bulunamadı"))
            return
        
        overview = AnalyticsService.get_overview(days=7)
        
        if self.json_output:
            import json
            self.stdout.write(json.dumps(overview, indent=2))
            return
        
        self._header("📊 Request Metrikleri (Son 7 gün)")
        
        self.stdout.write(f"  📈 Toplam Request   : {self._color(str(overview['total_requests']), 'BOLD')}")
        self.stdout.write(f"  ✅ Başarılı         : {self._color(str(overview['successful_requests']), 'SUCCESS')}")
        self.stdout.write(f"  ⚠️  Client Error     : {self._color(str(overview['client_errors']), 'WARNING')}")
        self.stdout.write(f"  ❌ Server Error     : {self._color(str(overview['server_errors']), 'ERROR')}")
        error_rate = overview['error_rate']
        error_color = 'WARNING' if error_rate > 1 else 'SUCCESS'
        self.stdout.write(f"  📉 Hata Oranı       : {self._color(f'{error_rate:.1f}%', error_color)}")
        avg_response = overview['avg_response_time']
        self.stdout.write(f"  ⏱️  Ort. Response    : {self._color(f'{avg_response:.0f}ms', 'BOLD')}")
        self.stdout.write(f"  👥 Unique Users     : {overview['unique_users']}")
        self.stdout.write(f"  🌐 Unique IPs       : {overview['unique_ips']}")
        self.stdout.write("")
    
    def show_errors(self):
        """Son hataları göster."""
        try:
            from logs.analytics.models import ErrorLog
        except ImportError:
            self.stderr.write(self.style.ERROR("Analytics modülü bulunamadı"))
            return
        
        errors = ErrorLog.objects.filter(is_resolved=False).order_by('-timestamp')[:20]
        
        if self.json_output:
            import json
            data = [
                {
                    'id': e.id,
                    'timestamp': e.timestamp.isoformat(),
                    'level': e.level,
                    'message': e.message[:200],
                    'path': e.path,
                    'count': e.occurrence_count,
                }
                for e in errors
            ]
            self.stdout.write(json.dumps(data, indent=2))
            return
        
        self._header("🚨 Son Hatalar (çözülmemiş)")
        
        if not errors:
            self.stdout.write(self._color("  🎉 Çözülmemiş hata yok!", 'SUCCESS'))
        else:
            for e in errors:
                time_str = e.timestamp.strftime('%m-%d %H:%M')
                level_color = 'ERROR' if e.level == 'ERROR' else 'CRITICAL' if e.level == 'CRITICAL' else 'WARNING'
                level_str = self._color(f"[{e.level}]", level_color)
                msg = e.message[:50] + '...' if len(e.message) > 50 else e.message
                count_str = self._color(f"x{e.occurrence_count}", 'DIM') if e.occurrence_count > 1 else ""
                self.stdout.write(f"  {time_str} {level_str} {msg} {count_str}")
        
        self.stdout.write("")
    
    def _find_log_file(self, name: str) -> Optional[Path]:
        """Log dosyasını bul. Kısayolları destekler."""
        log_path = Path(self.log_dir)
        
        # Dosya kısayolları
        shortcuts = {
            'error': self.log_levels_dir / 'error.log',
            'warning': self.log_levels_dir / 'warning.log',
            'info': self.log_levels_dir / 'info.log',
            'debug': self.log_levels_dir / 'debug.log',
            'sql': self.log_database_dir / 'sql.log',
            'global': log_path / 'global.log',
        }
        
        # Kısayol kontrolü
        name_lower = name.lower().replace('.log', '')
        if name_lower in shortcuts:
            target = shortcuts[name_lower]
            if target.exists():
                return target
        
        # Tam yol kontrolü
        if (log_path / name).exists():
            return log_path / name
        
        # Alt klasörlerde ara
        for f in log_path.glob(f'**/{name}'):
            if f.is_file():
                return f
        
        # .log ekleyerek dene
        if not name.endswith('.log'):
            return self._find_log_file(f'{name}.log')
        
        return None
    
    def view_logs(self, options):
        """Log dosyalarını görüntüle."""
        log_path = Path(self.log_dir)
        
        # Dosya seçimi
        if options['file']:
            requested_file = options['file']
            log_file = self._find_log_file(requested_file)
            if not log_file:
                raise CommandError(f"Dosya bulunamadı: {requested_file}")
        else:
            log_file = log_path / 'global.log'
            if not log_file.exists():
                # Tüm .log dosyalarını ara
                log_files = list(log_path.glob('**/*.log'))
                if not log_files:
                    raise CommandError("Log dosyası bulunamadı")
                log_file = log_files[0]
        
        # Follow mode
        if options['follow']:
            return self._follow_log(log_file, options)
        
        # Head mode
        if options.get('head'):
            lines = self._head_file(log_file, options['head'] * 3)
            filtered = self._filter_lines(lines, options)
            filtered = filtered[:options['head']]
        else:
            # Tail mode (varsayılan)
            lines = self._tail_file(log_file, options['tail'] * 3)
            filtered = self._filter_lines(lines, options)
            filtered = filtered[-options['tail']:]
        
        # Çıktı
        if self.json_output:
            import json
            parsed = [self._parse_line(l) for l in filtered]
            self.stdout.write(json.dumps(parsed, indent=2))
            return
        
        self._header(f"📄 {log_file.name} ({len(filtered)} satır)")
        
        for line in filtered:
            self._print_line(line)
        
        self.stdout.write("")
    
    def _follow_log(self, log_file: Path, options):
        """Log dosyasını canlı takip et."""
        self._header(f"📡 {log_file.name} takip ediliyor... (Ctrl+C ile çık)")
        
        try:
            with open(log_file, 'r') as f:
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        if self._should_show(line, options):
                            self._print_line(line.strip())
                    else:
                        time.sleep(0.3)
        except KeyboardInterrupt:
            self.stdout.write(self._color("\n\n✋ Takip durduruldu", 'DIM'))
    
    def _head_file(self, filepath: Path, lines: int = 100) -> List[str]:
        """Dosyanın ilk N satırını oku."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return [f.readline().strip() for _ in range(lines) if f.readline()]
        except Exception as e:
            return [f"Error reading file: {e}"]
    
    def _tail_file(self, filepath: Path, lines: int = 100) -> List[str]:
        """Dosyanın son N satırını oku."""
        try:
            with open(filepath, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                
                if file_size == 0:
                    return []
                
                buffer_size = 8192
                buffer = b''
                result = []
                
                while len(result) < lines and f.tell() > 0:
                    to_read = min(buffer_size, f.tell())
                    f.seek(-to_read, 1)
                    chunk = f.read(to_read)
                    f.seek(-to_read, 1)
                    buffer = chunk + buffer
                    
                    while b'\n' in buffer and len(result) < lines:
                        line, buffer = buffer.rsplit(b'\n', 1)
                        if line:
                            try:
                                result.insert(0, line.decode('utf-8', errors='replace'))
                            except:
                                pass
                
                if buffer and len(result) < lines:
                    try:
                        result.insert(0, buffer.decode('utf-8', errors='replace'))
                    except:
                        pass
                
                return result[-lines:]
        except Exception as e:
            return [f"Error reading file: {e}"]
    
    def _filter_lines(self, lines: List[str], options) -> List[str]:
        """Satırları filtrele."""
        return [line for line in lines if self._should_show(line, options)]
    
    def _should_show(self, line: str, options) -> bool:
        """Satırın gösterilip gösterilmeyeceğini kontrol et."""
        if options.get('level'):
            if f'[{options["level"]}' not in line:
                return False
        
        if options.get('logger'):
            if options['logger'].lower() not in line.lower():
                return False
        
        if options.get('search'):
            if options['search'].lower() not in line.lower():
                return False
        
        if options.get('since') or options.get('until'):
            match = re.search(r'\[(\d{4}-\d{2}-\d{2})', line)
            if match:
                log_date = match.group(1)
                if options.get('since') and log_date < options['since']:
                    return False
                if options.get('until') and log_date > options['until']:
                    return False
        
        return True
    
    def _parse_line(self, line: str) -> dict:
        """Log satırını parse et."""
        pattern = r'\[(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})\]\s*\[(\w+)\s*\]\s*\[([^\]]+)\]\s*(.*)'
        match = re.match(pattern, line.strip())
        
        if match:
            return {
                'timestamp': match.group(1),
                'level': match.group(2).strip(),
                'logger': match.group(3).strip(),
                'message': match.group(4).strip(),
            }
        
        return {'message': line.strip()}
    
    def _print_line(self, line: str):
        """Satırı renkli yazdır."""
        if self.compact:
            # Sadece mesajı göster
            parsed = self._parse_line(line)
            self.stdout.write(f"  {parsed.get('message', line)}")
            return
        
        if not self.use_color:
            self.stdout.write(line)
            return
        
        # Level'a göre renklendir
        for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
            if f'[{level}' in line:
                self.stdout.write(f"{COLORS.get(level, '')}{line}{COLORS['RESET']}")
                return
        
        self.stdout.write(line)
    
    def _format_size(self, size: int) -> str:
        """Boyutu okunabilir formata çevir."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
