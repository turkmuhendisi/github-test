"""
Log Viewer Views
================

Log dosyalarını görüntüleme ve streaming.
"""

import os
import re
import json
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator

from django.conf import settings
from django.http import (
    HttpRequest, 
    HttpResponse, 
    JsonResponse, 
    StreamingHttpResponse,
    FileResponse,
)
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

# Log dizini
LOG_DIR = getattr(settings, 'LOG_DIR', settings.BASE_DIR / 'logs')


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_log_files() -> List[Dict[str, Any]]:
    """Log dosyalarının listesini döndürür."""
    log_files = []
    log_path = Path(LOG_DIR)
    
    if not log_path.exists():
        return log_files
    
    for file in log_path.glob('*.log*'):
        if file.is_file():
            stat = file.stat()
            log_files.append({
                'name': file.name,
                'path': str(file),
                'size': stat.st_size,
                'size_human': _format_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'modified_human': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            })
    
    # Tarihe göre sırala (en yeni önce)
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    return log_files


def _format_size(size: int) -> str:
    """Dosya boyutunu okunabilir formata çevirir."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def parse_log_line(line: str) -> Dict[str, Any]:
    """
    Log satırını parse eder.
    
    Format: [2024-01-15 10:30:45] [INFO    ] [django.request] Message
    """
    # Regex pattern for standard log format
    pattern = r'\[(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})\]\s*\[(\w+)\s*\]\s*\[([^\]]+)\]\s*(.*)'
    match = re.match(pattern, line.strip())
    
    if match:
        timestamp, level, logger, message = match.groups()
        return {
            'timestamp': timestamp,
            'level': level.strip(),
            'logger': logger.strip(),
            'message': message.strip(),
            'raw': line,
        }
    
    # Basit format veya parse edilemedi
    return {
        'timestamp': None,
        'level': 'UNKNOWN',
        'logger': None,
        'message': line.strip(),
        'raw': line,
    }


def tail_file(filepath: Path, lines: int = 100) -> List[str]:
    """Dosyanın son N satırını okur (tail -n)."""
    try:
        with open(filepath, 'rb') as f:
            # Dosya sonuna git
            f.seek(0, 2)
            file_size = f.tell()
            
            if file_size == 0:
                return []
            
            # Geriye doğru oku
            buffer_size = 8192
            buffer = b''
            result_lines = []
            
            while len(result_lines) < lines and f.tell() > 0:
                # Okuma pozisyonunu ayarla
                to_read = min(buffer_size, f.tell())
                f.seek(-to_read, 1)
                chunk = f.read(to_read)
                f.seek(-to_read, 1)
                
                buffer = chunk + buffer
                
                # Satırları ayır
                while b'\n' in buffer and len(result_lines) < lines:
                    line, buffer = buffer.rsplit(b'\n', 1)
                    if line:
                        try:
                            result_lines.insert(0, line.decode('utf-8', errors='replace'))
                        except:
                            pass
            
            # Kalan buffer'ı ekle
            if buffer and len(result_lines) < lines:
                try:
                    result_lines.insert(0, buffer.decode('utf-8', errors='replace'))
                except:
                    pass
            
            return result_lines[-lines:]
            
    except Exception as e:
        return [f"Error reading file: {str(e)}"]


def stream_file(filepath: Path, start_pos: int = 0) -> Generator[bytes, None, None]:
    """Dosyayı streaming olarak okur."""
    try:
        with open(filepath, 'rb') as f:
            f.seek(start_pos)
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    except Exception:
        pass


def filter_logs(
    lines: List[str],
    level: Optional[str] = None,
    logger: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Log satırlarını filtreler."""
    result = []
    
    for line in lines:
        if not line.strip():
            continue
            
        parsed = parse_log_line(line)
        
        # Level filtresi
        if level and parsed['level'].upper() != level.upper():
            continue
        
        # Logger filtresi
        if logger and parsed['logger'] and logger.lower() not in parsed['logger'].lower():
            continue
        
        # Keyword filtresi
        if keyword and keyword.lower() not in parsed['message'].lower():
            continue
        
        # Tarih filtresi
        if parsed['timestamp']:
            try:
                log_date = parsed['timestamp'][:10]  # YYYY-MM-DD
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue
            except:
                pass
        
        result.append(parsed)
    
    return result


# =============================================================================
# VIEWS
# =============================================================================

@method_decorator(staff_member_required, name='dispatch')
class LogViewerView(TemplateView):
    """Log viewer ana sayfası."""
    template_name = 'logs/viewer/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['log_files'] = get_log_files()
        context['page_title'] = 'Log Viewer'
        return context


@method_decorator(staff_member_required, name='dispatch')
class LogFileListView(View):
    """Log dosyalarını listeler (API)."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({
            'success': True,
            'files': get_log_files(),
        })


@method_decorator(staff_member_required, name='dispatch')
class LogFileReadView(View):
    """Log dosyası içeriğini okur (API)."""
    
    def get(self, request: HttpRequest, filename: str) -> JsonResponse:
        log_path = Path(LOG_DIR) / filename
        
        # Güvenlik kontrolü
        if not log_path.resolve().is_relative_to(Path(LOG_DIR).resolve()):
            return JsonResponse({'success': False, 'error': 'Invalid path'}, status=403)
        
        if not log_path.exists():
            return JsonResponse({'success': False, 'error': 'File not found'}, status=404)
        
        # Parametreler
        lines = int(request.GET.get('lines', 100))
        level = request.GET.get('level')
        logger = request.GET.get('logger')
        keyword = request.GET.get('keyword')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Dosyayı oku
        raw_lines = tail_file(log_path, lines * 2)  # Filtreleme için daha fazla oku
        
        # Filtrele
        filtered = filter_logs(
            raw_lines,
            level=level,
            logger=logger,
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
        )
        
        return JsonResponse({
            'success': True,
            'filename': filename,
            'total_lines': len(raw_lines),
            'filtered_lines': len(filtered),
            'logs': filtered[-lines:],  # Son N satır
        })


@method_decorator(staff_member_required, name='dispatch')
class LogFileDownloadView(View):
    """Log dosyasını indirir."""
    
    def get(self, request: HttpRequest, filename: str) -> HttpResponse:
        log_path = Path(LOG_DIR) / filename
        
        # Güvenlik kontrolü
        if not log_path.resolve().is_relative_to(Path(LOG_DIR).resolve()):
            return HttpResponse('Forbidden', status=403)
        
        if not log_path.exists():
            return HttpResponse('Not found', status=404)
        
        # Content type
        content_type, _ = mimetypes.guess_type(str(log_path))
        if not content_type:
            content_type = 'text/plain'
        
        response = FileResponse(
            open(log_path, 'rb'),
            content_type=content_type,
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


@method_decorator(staff_member_required, name='dispatch')
class LogFileStreamView(View):
    """Log dosyasını streaming olarak okur (SSE)."""
    
    def get(self, request: HttpRequest, filename: str) -> StreamingHttpResponse:
        log_path = Path(LOG_DIR) / filename
        
        # Güvenlik kontrolü
        if not log_path.resolve().is_relative_to(Path(LOG_DIR).resolve()):
            return HttpResponse('Forbidden', status=403)
        
        if not log_path.exists():
            return HttpResponse('Not found', status=404)
        
        # Başlangıç pozisyonu (dosya sonundan)
        start_pos = max(0, log_path.stat().st_size - 10000)
        
        def event_stream():
            """SSE event stream."""
            import time
            
            current_pos = start_pos
            
            while True:
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(current_pos)
                        new_content = f.read()
                        current_pos = f.tell()
                        
                        if new_content:
                            for line in new_content.splitlines():
                                if line.strip():
                                    data = json.dumps(parse_log_line(line))
                                    yield f"data: {data}\n\n"
                    
                    time.sleep(1)  # 1 saniye bekle
                except GeneratorExit:
                    break
                except Exception:
                    break
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


@method_decorator(staff_member_required, name='dispatch')
class LogStatisticsView(View):
    """Log istatistiklerini döndürür (API)."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        stats = {
            'files': [],
            'total_size': 0,
            'level_counts': {
                'DEBUG': 0,
                'INFO': 0,
                'WARNING': 0,
                'ERROR': 0,
                'CRITICAL': 0,
            }
        }
        
        log_path = Path(LOG_DIR)
        
        for file in log_path.glob('*.log'):
            if file.is_file():
                size = file.stat().st_size
                stats['total_size'] += size
                stats['files'].append({
                    'name': file.name,
                    'size': size,
                })
                
                # Level sayıları (son 1000 satır)
                lines = tail_file(file, 1000)
                for line in lines:
                    parsed = parse_log_line(line)
                    level = parsed['level'].upper()
                    if level in stats['level_counts']:
                        stats['level_counts'][level] += 1
        
        stats['total_size_human'] = _format_size(stats['total_size'])
        
        return JsonResponse({
            'success': True,
            'statistics': stats,
        })

