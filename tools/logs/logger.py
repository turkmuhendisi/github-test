"""
Custom Logging Handlers, Formatters ve Filters
==============================================

Renkli console output, kullanıcı bilgili formatlar ve
çeşitli filtreleme özellikleri sağlar.

Handlers:
---------
- ColorizingStreamHandler: Renkli console output
- ColorizingFileHandler: Renkli file output
- RotatingColorizingFileHandler: Rotasyonlu file output

Formatters:
----------
- RequestFormatter: User/IP bilgili formatter
- JSONFormatter: JSON formatında log output

Filters:
-------
- StaticFileFilter: Static file isteklerini filtrele
- SSLErrorFilter: SSL hatalarını özelleştir
- StatusFilter: Belirli status code'ları filtrele
- ExcludeRoute53HealthCheckFilter: AWS health check'leri filtrele
- SensitiveDataFilter: Hassas verileri maskele
"""

import sys
import ssl
import json
import traceback
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import List, Set, Optional

from colorama import init, Fore, Style

from .user_local import get_username, get_ip_address, get_request_id

# Colorama'yı başlat
init(autoreset=True)


# =============================================================================
# FORMATTERS
# =============================================================================

class RequestFormatter(logging.Formatter):
    """
    User, IP ve Request ID bilgilerini içeren formatter.
    
    Format Değişkenleri:
    -------------------
    - {username}: Kullanıcı adı
    - {ip_address}: Client IP
    - {request_id}: Unique request ID
    - Standart logging değişkenleri (asctime, levelname, message, vb.)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Thread-local'den bilgileri al
        record.username = get_username()
        record.ip_address = get_ip_address()
        record.request_id = get_request_id()
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatında log output.
    Log aggregation sistemleri (ELK, CloudWatch) için ideal.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'username': get_username(),
            'ip_address': get_ip_address(),
            'request_id': get_request_id(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Extra fields
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        
        # Exception bilgisi
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


# =============================================================================
# HANDLERS
# =============================================================================

class ColorizingStreamHandler(logging.StreamHandler):
    """
    Renkli console output handler.
    
    Renkler:
    -------
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Magenta (Bold)
    """
    
    COLOR_MAP = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }
    
    def __init__(self, stream=None):
        super().__init__(stream or sys.stdout)
    
    def emit(self, record: logging.LogRecord) -> None:
        try:
            # User bilgilerini ekle (formatter'dan önce)
            record.username = get_username()
            record.ip_address = get_ip_address()
            record.request_id = get_request_id()
            
            message = self.format(record)
            color = self.COLOR_MAP.get(record.levelno, Fore.WHITE)
            
            self.stream.write(color + message + Style.RESET_ALL + '\n')
            self.flush()
        except Exception:
            self.handleError(record)


class ColorizingFileHandler(logging.FileHandler):
    """
    Dosyaya yazan handler (renk kodları olmadan).
    Console'daki ANSI kodları dosyada sorun yaratır.
    """
    
    def __init__(self, filename: str, mode: str = 'a', encoding: str = 'utf-8', delay: bool = False):
        super().__init__(filename, mode, encoding, delay)
    
    def emit(self, record: logging.LogRecord) -> None:
        # User bilgilerini ekle
        record.username = get_username()
        record.ip_address = get_ip_address()
        record.request_id = get_request_id()
        
        super().emit(record)


class RotatingColorizingFileHandler(RotatingFileHandler):
    """
    Boyut bazlı rotasyonlu file handler.
    
    Args:
        filename: Log dosya yolu
        maxBytes: Maksimum dosya boyutu (default: 10MB)
        backupCount: Saklanacak backup sayısı (default: 5)
    """
    
    def __init__(
        self,
        filename: str,
        mode: str = 'a',
        maxBytes: int = 10 * 1024 * 1024,  # 10MB
        backupCount: int = 5,
        encoding: str = 'utf-8',
        delay: bool = False
    ):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
    
    def emit(self, record: logging.LogRecord) -> None:
        record.username = get_username()
        record.ip_address = get_ip_address()
        record.request_id = get_request_id()
        
        super().emit(record)


class TimedRotatingColorizingFileHandler(TimedRotatingFileHandler):
    """
    Zaman bazlı rotasyonlu file handler.
    
    Args:
        filename: Log dosya yolu
        when: Rotasyon zamanı ('midnight', 'H', 'D', 'W0'-'W6')
        interval: Interval sayısı
        backupCount: Saklanacak backup sayısı
    """
    
    def __init__(
        self,
        filename: str,
        when: str = 'midnight',
        interval: int = 1,
        backupCount: int = 30,
        encoding: str = 'utf-8',
        delay: bool = False
    ):
        super().__init__(filename, when, interval, backupCount, encoding, delay)
    
    def emit(self, record: logging.LogRecord) -> None:
        record.username = get_username()
        record.ip_address = get_ip_address()
        record.request_id = get_request_id()
        
        super().emit(record)


# =============================================================================
# FILTERS
# =============================================================================

class StaticFileFilter(logging.Filter):
    """Static file isteklerini filtreler."""
    
    STATIC_EXTENSIONS = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf'}
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        # /static/ veya /media/ içeren mesajları filtrele
        if '/static/' in message or '/media/' in message:
            return False
        # Static dosya uzantılarını filtrele
        for ext in self.STATIC_EXTENSIONS:
            if ext in message:
                return False
        return True


class SSLErrorFilter(logging.Filter):
    """
    SSL hatalarını yakalar ve detaylı bilgi ekler.
    Hataları filtrelemez, zenginleştirir.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            if isinstance(exc_value, ssl.SSLError):
                detailed_error = f"{exc_type.__name__}: {exc_value}"
                traceback_details = ''.join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
                record.msg = f"SSL Error: {record.msg} | Details: {detailed_error}"
        return True


class StatusFilter(logging.Filter):
    """
    Belirli HTTP status code'larını veya mesajları filtreler.
    
    Args:
        status_codes: Filtrelenecek status code listesi
        messages: Filtrelenecek mesaj parçaları
    """
    
    def __init__(
        self,
        status_codes: Optional[List[int]] = None,
        messages: Optional[List[str]] = None,
        name: str = ''
    ):
        super().__init__(name)
        self.status_codes: Set[int] = set(status_codes or [])
        self.messages: List[str] = messages or []
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Status code kontrolü
        if hasattr(record, 'status_code') and record.status_code in self.status_codes:
            return False
        
        # Mesaj kontrolü
        message = record.getMessage()
        for msg in self.messages:
            if msg in message:
                return False
        
        return True


class ExcludeRoute53HealthCheckFilter(logging.Filter):
    """AWS Route53 health check isteklerini filtreler."""
    
    HEALTH_CHECK_PATTERNS = [
        'Amazon-Route53-Health-Check-Service',
        'ELB-HealthChecker',
        '/health',
        '/ready',
        '/live',
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self.HEALTH_CHECK_PATTERNS:
            if pattern in message:
                return False
        return True


class SensitiveDataFilter(logging.Filter):
    """
    Hassas verileri maskeler.
    Password, token, secret gibi alanları gizler.
    """
    
    SENSITIVE_PATTERNS = [
        'password',
        'passwd',
        'secret',
        'token',
        'api_key',
        'apikey',
        'authorization',
        'auth',
        'credit_card',
        'ssn',
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Hassas veriyi maskele
                record.msg = self._mask_sensitive_data(record.msg, pattern)
        return True
    
    def _mask_sensitive_data(self, message: str, pattern: str) -> str:
        """Hassas veriyi *** ile maskeler."""
        import re
        # pattern=value veya pattern: value formatlarını maskele
        masked = re.sub(
            rf'({pattern}["\']?\s*[:=]\s*["\']?)([^"\'\s,}}]+)',
            r'\1***MASKED***',
            message,
            flags=re.IGNORECASE
        )
        return masked


class LevelFilter(logging.Filter):
    """
    Sadece belirli bir seviyedeki logları geçirir.
    
    Örnek:
        'filters': {
            'info_only': {
                '()': 'tools.logs.LevelFilter',
                'level': 'INFO',
            },
        }
    """
    
    def __init__(self, level: str = 'INFO', name: str = ''):
        super().__init__(name)
        self.level = getattr(logging, level.upper(), logging.INFO)
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Sadece tam olarak bu seviyedeki logları geçir
        return record.levelno == self.level


class MinLevelFilter(logging.Filter):
    """
    Minimum seviye ve üstündeki logları geçirir.
    DEBUG loglarını filtrelemek için kullanışlı.
    
    Örnek:
        'filters': {
            'info_and_above': {
                '()': 'tools.logs.MinLevelFilter',
                'min_level': 'INFO',
            },
        }
    """
    
    def __init__(self, min_level: str = 'INFO', name: str = ''):
        super().__init__(name)
        self.min_level = getattr(logging, min_level.upper(), logging.INFO)
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Min seviye ve üstünü geçir
        return record.levelno >= self.min_level


class MaxLevelFilter(logging.Filter):
    """
    Maksimum seviye ve altındaki logları geçirir.
    
    Örnek:
        'filters': {
            'below_error': {
                '()': 'tools.logs.MaxLevelFilter',
                'max_level': 'WARNING',
            },
        }
    """
    
    def __init__(self, max_level: str = 'WARNING', name: str = ''):
        super().__init__(name)
        self.max_level = getattr(logging, max_level.upper(), logging.WARNING)
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Max seviye ve altını geçir
        return record.levelno <= self.max_level


class ExcludeLoggerFilter(logging.Filter):
    """
    Belirli logger'ları hariç tutar.
    
    Örnek:
        'filters': {
            'exclude_noisy': {
                '()': 'tools.logs.ExcludeLoggerFilter',
                'loggers': ['django.utils.autoreload', 'django.db.backends'],
            },
        }
    """
    
    def __init__(self, loggers: List[str] = None, name: str = ''):
        super().__init__(name)
        self.excluded_loggers = set(loggers or [])
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Logger adı hariç tutulanlar listesinde mi?
        for excluded in self.excluded_loggers:
            if record.name.startswith(excluded):
                return False
        return True


# =============================================================================
# LOGGER INSTANCE
# =============================================================================

def get_logger(name: str = 'django') -> logging.Logger:
    """Named logger döndürür."""
    return logging.getLogger(name)


# Default logger
logger = get_logger('django')