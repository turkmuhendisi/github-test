"""
Startup Banner ve Sistem Bilgileri
==================================

Tüm Django startup bilgilerini merkezi olarak yönetir.
Tek bir çağrı ile tüm sistem durumunu gösterir.

Kullanım:
--------
from config.startup import print_startup_banner
print_startup_banner()

Veya settings/__init__.py'da otomatik çağrılır.

Webapp Entegrasyonu:
------------------
from config.startup import print_startup_banner
print_startup_banner(project='webapp')
"""

import sys
import os
import platform
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# =============================================================================
# DUPLICATE PREVENTION
# =============================================================================
# Django runserver iki process başlatır:
# 1. Ana process (ayarları yükler, reloader'ı başlatır)
# 2. Reloader process (RUN_MAIN=true ile çalışır, asıl sunucu)
#
# Banner'ı sadece RELOADER process'te gösteriyoruz (RUN_MAIN=true)
# Bu şekilde banner sadece 1 kez yazdırılır.

def _should_print_banner() -> bool:
    """
    Banner yazdırılmalı mı kontrol et.
    
    Sadece şu durumlarda True döner:
    1. RUN_MAIN=true ise (Django reloader process'i)
    2. Veya runserver değilse (manage.py shell, migrate vb.)
    """
    # Django reloader process'i mi?
    run_main = os.environ.get('RUN_MAIN', '')
    
    # RUN_MAIN varsa, sadece 'true' olduğunda yazdır
    if run_main:
        return run_main == 'true'
    
    # RUN_MAIN yoksa (runserver değil veya --noreload ile çalışıyor)
    # Banner'ı yazdır
    return True


# Environment variable key for tracking banner print status
_BANNER_ENV_KEY = '_GLOBALMAIN_BANNER_PRINTED'


def _is_banner_printed() -> bool:
    """
    Banner daha önce yazdırıldı mı kontrol et.
    Environment variable kullanarak process'ler arası iletişim sağlar.
    """
    return os.environ.get(_BANNER_ENV_KEY, '') == 'true'


def _mark_banner_printed() -> None:
    """
    Banner'ın yazdırıldığını işaretle.
    Environment variable set ederek diğer process'lerin görmesini sağlar.
    """
    os.environ[_BANNER_ENV_KEY] = 'true'

# =============================================================================
# TERMINAL COLORS (ANSI Escape Codes)
# =============================================================================

class Colors:
    """Terminal renk kodları."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


def _supports_color() -> bool:
    """Terminal renk desteği kontrolü."""
    # Windows'ta renk desteği
    if sys.platform == 'win32':
        return os.environ.get('TERM') == 'xterm' or os.environ.get('ANSICON')
    # Unix-like sistemlerde
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


def c(text: str, color: str = '', bold: bool = False) -> str:
    """Metni renklendir."""
    if not _supports_color():
        return text
    prefix = ''
    if bold:
        prefix += Colors.BOLD
    if color:
        prefix += color
    if prefix:
        return f"{prefix}{text}{Colors.RESET}"
    return text


# =============================================================================
# BOX DRAWING CHARACTERS
# =============================================================================

class Box:
    """Unicode box drawing karakterleri."""
    # Double line
    TL = '╔'  # Top Left
    TR = '╗'  # Top Right
    BL = '╚'  # Bottom Left
    BR = '╝'  # Bottom Right
    H = '═'   # Horizontal
    V = '║'   # Vertical
    LT = '╠'  # Left T
    RT = '╣'  # Right T
    TT = '╦'  # Top T
    BT = '╩'  # Bottom T
    X = '╬'   # Cross
    
    # Single line
    STL = '┌'  # Single Top Left
    STR = '┐'  # Single Top Right
    SBL = '└'  # Single Bottom Left
    SBR = '┘'  # Single Bottom Right
    SH = '─'   # Single Horizontal
    SV = '│'   # Single Vertical
    SLT = '├'  # Single Left T
    SRT = '┤'  # Single Right T
    
    # Mixed
    DHV = '╟'  # Double Horizontal, Vertical connect
    
    # Arrows
    AR = '→'
    AL = '←'
    AU = '↑'
    AD = '↓'


# =============================================================================
# STARTUP INFO COLLECTOR
# =============================================================================

class StartupInfo:
    """Startup bilgilerini toplayan sınıf."""
    
    def __init__(self, project: Optional[str] = None, settings_dict: Optional[dict] = None):
        self._data: dict[str, Any] = {}
        self._collected = False
        self._project = project  # 'webapp', 'api', etc.
        self._settings_dict = settings_dict  # Direkt settings dict'i (circular import'u önler)
    
    def collect(self) -> None:
        """Tüm bilgileri topla."""
        if self._collected:
            return
        
        # Settings'i al (dict olarak veya Django'dan)
        if self._settings_dict:
            settings = type('Settings', (), self._settings_dict)()
        else:
            try:
                from django.conf import settings
            except Exception:
                settings = type('Settings', (), {})()
        
        # Project Info
        self._data['project'] = self._project or self._detect_project(settings)
        self._data['settings_module'] = os.environ.get('DJANGO_SETTINGS_MODULE', 'N/A')
        
        # System Info
        self._data['python_version'] = platform.python_version()
        self._data['django_version'] = self._get_django_version()
        self._data['os'] = f"{platform.system()} {platform.release()}"
        self._data['hostname'] = platform.node()
        self._data['started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Environment
        self._data['env'] = getattr(settings, 'DJANGO_ENV', os.environ.get('DJANGO_ENV', 'unknown'))
        self._data['debug'] = getattr(settings, 'DEBUG', False)
        self._data['base_dir'] = str(getattr(settings, 'BASE_DIR', 'N/A'))
        
        # Database
        self._data['databases'] = self._get_database_info(settings)
        
        # Cache
        self._data['cache'] = self._get_cache_info(settings)
        
        # Apps
        self._data['installed_apps'] = len(getattr(settings, 'INSTALLED_APPS', []))
        
        # URLs
        self._data['root_urlconf'] = getattr(settings, 'ROOT_URLCONF', 'N/A')
        
        # Logging
        self._data['log_level'] = os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        
        # Middleware
        self._data['middleware_count'] = len(getattr(settings, 'MIDDLEWARE', []))
        
        # Security indicators
        self._data['https_enforced'] = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        self._data['hsts_enabled'] = getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0
        
        # Optional features
        self._data['celery'] = self._check_celery(settings)
        self._data['redis'] = self._check_redis(settings)
        self._data['aws_s3'] = bool(getattr(settings, 'AWS_STORAGE_BUCKET_NAME', ''))
        self._data['sentry'] = bool(getattr(settings, 'SENTRY_DSN', None))
        
        self._collected = True
    
    def _get_django_version(self) -> str:
        try:
            import django
            return django.get_version()
        except ImportError:
            return 'N/A'
    
    def _get_database_info(self, settings) -> dict:
        databases = getattr(settings, 'DATABASES', {})
        info = {}
        for alias, config in databases.items():
            engine = config.get('ENGINE', '')
            if 'sqlite' in engine:
                info[alias] = 'SQLite'
            elif 'postgresql' in engine:
                info[alias] = 'PostgreSQL'
            elif 'mysql' in engine:
                info[alias] = 'MySQL'
            else:
                info[alias] = engine.split('.')[-1] if engine else 'Unknown'
        return info
    
    def _get_cache_info(self, settings) -> str:
        caches = getattr(settings, 'CACHES', {})
        default = caches.get('default', {})
        backend = default.get('BACKEND', '')
        if 'redis' in backend.lower():
            return 'Redis'
        elif 'memcached' in backend.lower():
            return 'Memcached'
        elif 'locmem' in backend.lower():
            return 'Local Memory'
        elif 'dummy' in backend.lower():
            return 'Dummy (Disabled)'
        elif 'filebased' in backend.lower():
            return 'File Based'
        return 'Default'
    
    def _check_celery(self, settings) -> bool:
        return bool(getattr(settings, 'CELERY_BROKER_URL', ''))
    
    def _check_redis(self, settings) -> bool:
        return bool(getattr(settings, 'REDIS_URL', ''))
    
    def _detect_project(self, settings) -> str:
        """Proje tipini tespit et."""
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')
        
        if 'webapp' in settings_module:
            return 'webapp'
        elif 'api' in settings_module:
            return 'api'
        elif 'admin' in settings_module:
            return 'admin'
        
        # ROOT_URLCONF'a göre tespit
        root_urlconf = getattr(settings, 'ROOT_URLCONF', '')
        if 'webapp' in root_urlconf:
            return 'webapp'
        elif 'api' in root_urlconf:
            return 'api'
        
        return 'core'
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    @property
    def data(self) -> dict:
        return self._data


# =============================================================================
# BANNER COMPONENTS
# =============================================================================

def _header(width: int = 80, project: str = 'core') -> str:
    """Ana başlık."""
    # Proje tipine göre başlık ve emoji
    project_titles = {
        'webapp': ('🌐 GLOBALMAIN WEBAPP', Colors.BRIGHT_CYAN),
        'api': ('🔌 GLOBALMAIN API', Colors.BRIGHT_GREEN),
        'admin': ('⚙️ GLOBALMAIN ADMIN', Colors.BRIGHT_YELLOW),
        'core': ('🚀 GLOBALMAIN DJANGO', Colors.BRIGHT_WHITE),
    }
    
    title, title_color = project_titles.get(project, project_titles['core'])
    inner_width = width - 2
    padding = (inner_width - len(title)) // 2
    
    lines = [
        c(f"{Box.TL}{Box.H * (width - 2)}{Box.TR}", Colors.CYAN),
        c(f"{Box.V}", Colors.CYAN) + c(f"{' ' * padding}{title}{' ' * (inner_width - padding - len(title))}", title_color, bold=True) + c(f"{Box.V}", Colors.CYAN),
        c(f"{Box.LT}{Box.H * (width - 2)}{Box.RT}", Colors.CYAN),
    ]
    return '\n'.join(lines)


def _section_title(title: str, width: int = 80, icon: str = '') -> str:
    """Bölüm başlığı."""
    inner_width = width - 2
    full_title = f"{icon} {title}" if icon else title
    padding = 2
    remaining = inner_width - len(full_title) - padding * 2
    
    return c(f"{Box.V}", Colors.CYAN) + c(f"  {full_title}", Colors.YELLOW, bold=True) + f"{' ' * remaining}  " + c(f"{Box.V}", Colors.CYAN)


def _divider(width: int = 80) -> str:
    """Bölüm ayırıcı."""
    return c(f"{Box.LT}{Box.H * (width - 2)}{Box.RT}", Colors.CYAN)


def _strip_ansi(text: str) -> str:
    """ANSI renk kodlarını kaldır ve gerçek uzunluğu hesapla."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def _row(label: str, value: str, width: int = 80, label_width: int = 20, indent: int = 4) -> str:
    """Bilgi satırı."""
    inner_width = width - 2
    value_width = inner_width - label_width - indent - 3  # 3 = ' : '
    
    # Value'yu kırp (ANSI kodları olmadan)
    value_str = str(value)
    value_clean = _strip_ansi(value_str)
    if len(value_clean) > value_width:
        value_str = value_str[:len(value_clean) - (len(value_clean) - value_width + 3)] + '...'
        value_clean = _strip_ansi(value_str)
    
    # Label ve value'yu birleştir
    label_part = f"{' ' * indent}{label:<{label_width}}: "
    content = label_part + value_str
    
    # Gerçek uzunluğu hesapla (ANSI kodları olmadan)
    content_clean = _strip_ansi(content)
    padding_needed = inner_width - len(content_clean)
    
    # Padding ekle
    content = content + ' ' * max(0, padding_needed)
    
    return c(f"{Box.V}", Colors.CYAN) + content + c(f"{Box.V}", Colors.CYAN)


def _status_row(label: str, value: Any, width: int = 80, label_width: int = 20, indent: int = 4) -> str:
    """Durum satırı (renkli)."""
    inner_width = width - 2
    
    # Boolean değerler için renk
    if isinstance(value, bool):
        if value:
            display = c("✓ Enabled", Colors.GREEN)
        else:
            display = c("✗ Disabled", Colors.DIM)
    else:
        display = str(value)
    
    # Label ve value'yu birleştir
    label_part = f"{' ' * indent}{label:<{label_width}}: "
    content = label_part + display
    
    # Gerçek uzunluğu hesapla (ANSI kodları olmadan)
    content_clean = _strip_ansi(content)
    padding_needed = inner_width - len(content_clean)
    
    # Padding ekle
    content = content + ' ' * max(0, padding_needed)
    
    return c(f"{Box.V}", Colors.CYAN) + content + c(f"{Box.V}", Colors.CYAN)


def _empty_row(width: int = 80) -> str:
    """Boş satır."""
    inner_width = width - 2
    return c(f"{Box.V}", Colors.CYAN) + ' ' * inner_width + c(f"{Box.V}", Colors.CYAN)


def _footer(width: int = 80) -> str:
    """Alt çizgi."""
    return c(f"{Box.BL}{Box.H * (width - 2)}{Box.BR}", Colors.CYAN)


# =============================================================================
# FLOW DIAGRAM
# =============================================================================

def _flow_diagram(width: int = 80) -> list[str]:
    """Sistem akış diyagramı."""
    lines = [
        _section_title("SYSTEM ARCHITECTURE", width, "📐"),
        _empty_row(width),
    ]
    
    # Flow diagram içeriği - geliştirilmiş versiyon
    diagram = [
        "       ┌──────────┐      ┌────────────┐      ┌──────────┐",
        "       │ Request  │─────→│ Middleware │─────→│   URLs   │",
        "       └──────────┘      └────────────┘      └────┬─────┘",
        "                                                  │",
        "       ┌──────────┐      ┌────────────┐      ┌────▼─────┐",
        "       │ Response │←─────│  Template  │←─────│  Views   │",
        "       └──────────┘      └────────────┘      └────┬─────┘",
        "                                                  │",
        "                         ┌────────────┐      ┌────▼─────┐",
        "                         │  Database  │←─────│  Models  │",
        "                         └────────────┘      └──────────┘",
        "",
        "    💡 Unified Monitor: make monitor",
        "    📊 Request Flow:    python manage.py monitor --live --demo",
    ]
    
    inner_width = width - 2
    for line in diagram:
        padding = inner_width - len(line)
        lines.append(c(f"{Box.V}", Colors.CYAN) + c(line, Colors.DIM) + ' ' * padding + c(f"{Box.V}", Colors.CYAN))
    
    lines.append(_empty_row(width))
    return lines


def _config_flow_diagram(width: int = 80) -> list[str]:
    """Ayar yükleme akış diyagramı."""
    lines = [
        _section_title("SETTINGS LOAD ORDER", width, "⚙️"),
        _empty_row(width),
    ]
    
    # Settings flow
    flow = [
        "    ┌────────────────────────────────────────────────────┐",
        "    │  1. env.py      → Environment Variables            │",
        "    │  2. base.py     → Core Django Settings             │",
        "    │  3. security.py → Security Configuration           │",
        "    │  4. apps.py     → INSTALLED_APPS                   │",
        "    │  5. middleware  → MIDDLEWARE Stack                 │",
        "    │  6. templates   → Template Engine                  │",
        "    │  7. static.py   → Static & Media Files             │",
        "    │  8. data.py     → Database Configuration           │",
        "    │  9. cache.py    → Cache Backend                    │",
        "    │ 10. auth.py     → Authentication                   │",
        "    │ 11. i18n.py     → Internationalization             │",
        "    │ 12. logging.py  → Logging Configuration            │",
        "    │ 13. urls.py     → URL Configuration                │",
        "    │ 14. dev/prod.py → Environment Overrides            │",
        "    └────────────────────────────────────────────────────┘",
    ]
    
    inner_width = width - 2
    for line in flow:
        padding = inner_width - len(line)
        lines.append(c(f"{Box.V}", Colors.CYAN) + c(line, Colors.BRIGHT_BLACK) + ' ' * padding + c(f"{Box.V}", Colors.CYAN))
    
    lines.append(_empty_row(width))
    return lines


# =============================================================================
# MAIN BANNER FUNCTION
# =============================================================================

def print_startup_banner(
    show_flow: bool = True,
    show_config_flow: bool = False,
    width: int = 80,
    project: Optional[str] = None,
    force: bool = False,
    settings_dict: Optional[dict] = None
) -> None:
    """
    Startup banner'ı yazdır.
    
    Args:
        show_flow: Sistem akış diyagramını göster
        show_config_flow: Settings yükleme sırasını göster
        width: Banner genişliği
        project: Proje tipi ('webapp', 'api', 'admin', 'core')
        force: Mükerrer kontrolünü atla
        settings_dict: Settings değerleri (circular import'u önlemek için)
    """
    # DEBUG kontrolü
    if settings_dict:
        debug_mode = settings_dict.get('DEBUG', False)
    else:
        try:
            from django.conf import settings
            debug_mode = getattr(settings, 'DEBUG', False)
        except Exception:
            debug_mode = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'
    
    # Sadece DEBUG modunda göster
    if not debug_mode:
        return
    
    # Mükerrer yazdırmayı önle (runserver hem ana hem reloader process'te çağırır)
    # Environment variable ile process'ler arası kontrol
    if _is_banner_printed() and not force:
        return
    
    _mark_banner_printed()
    
    try:
        # Bilgileri topla
        info = StartupInfo(project=project, settings_dict=settings_dict)
        info.collect()
        
        # Proje tipini al
        detected_project = info.get('project', 'core')
        
        lines = []
        
        # Header
        lines.append('')
        lines.append(_header(width, project=detected_project))
    except Exception as e:
        # Hata durumunda basit banner göster
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🚀 GlobalMain Django - Startup Banner Error                     ║
║  Error: {str(e)[:54]:<54} ║
╚══════════════════════════════════════════════════════════════════╝
""", flush=True)
        return
    
    # ─────────────────────────────────────────────────────────────────────────
    # SYSTEM INFO
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_section_title("SYSTEM INFORMATION", width, "💻"))
    lines.append(_row("Python", info.get('python_version'), width))
    lines.append(_row("Django", info.get('django_version'), width))
    lines.append(_row("OS", info.get('os'), width))
    lines.append(_row("Hostname", info.get('hostname'), width))
    lines.append(_row("Started At", info.get('started_at'), width))
    
    # ─────────────────────────────────────────────────────────────────────────
    # PROJECT INFO (Webapp, API, etc.)
    # ─────────────────────────────────────────────────────────────────────────
    project_type = info.get('project', 'core')
    settings_module = info.get('settings_module', 'N/A')
    
    if project_type != 'core':
        lines.append(_section_title(f"PROJECT: {project_type.upper()}", width, "📂"))
        lines.append(_row("Settings Module", settings_module, width))
        lines.append(_row("Root URLConf", info.get('root_urlconf'), width))
        
        # Webapp-specific info
        if project_type == 'webapp':
            lines.append(_row("Static", "webapp/static/", width))
            lines.append(_row("Templates", "webapp/templates/", width))
        
        lines.append(_divider(width))
    
    # ─────────────────────────────────────────────────────────────────────────
    # ENVIRONMENT
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_section_title("ENVIRONMENT", width, "🌍"))
    
    env_value = info.get('env', 'unknown')
    if env_value == 'development':
        env_display = c("DEVELOPMENT", Colors.YELLOW, bold=True)
    elif env_value == 'production':
        env_display = c("PRODUCTION", Colors.RED, bold=True)
    elif env_value == 'staging':
        env_display = c("STAGING", Colors.MAGENTA, bold=True)
    else:
        env_display = env_value
    
    inner_width = width - 2
    label_part = f"    {'Environment':<20}: "
    content = label_part + env_display
    
    # Gerçek uzunluğu hesapla (ANSI kodları olmadan)
    content_clean = _strip_ansi(content)
    padding_needed = inner_width - len(content_clean)
    
    # Padding ekle
    content = content + ' ' * max(0, padding_needed)
    
    lines.append(c(f"{Box.V}", Colors.CYAN) + content + c(f"{Box.V}", Colors.CYAN))
    
    lines.append(_status_row("Debug Mode", info.get('debug'), width))
    lines.append(_row("Base Directory", info.get('base_dir'), width))
    
    # Core projede URL bilgisi göster
    if project_type == 'core':
        lines.append(_row("Root URLConf", info.get('root_urlconf'), width))
    
    # ─────────────────────────────────────────────────────────────────────────
    # DATABASE
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_divider(width))
    lines.append(_section_title("DATABASE", width, "🗄️"))
    
    databases = info.get('databases', {})
    for alias, db_type in databases.items():
        label = f"  {alias}"
        lines.append(_row(label, db_type, width, label_width=18, indent=2))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SERVICES
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_divider(width))
    lines.append(_section_title("SERVICES & FEATURES", width, "🔧"))
    
    lines.append(_row("Cache Backend", info.get('cache'), width))
    lines.append(_status_row("Redis", info.get('redis'), width))
    lines.append(_status_row("Celery", info.get('celery'), width))
    lines.append(_status_row("AWS S3", info.get('aws_s3'), width))
    lines.append(_status_row("Sentry", info.get('sentry'), width))
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECURITY
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_divider(width))
    lines.append(_section_title("SECURITY", width, "🔒"))
    
    lines.append(_status_row("HTTPS Enforced", info.get('https_enforced'), width))
    lines.append(_status_row("HSTS Enabled", info.get('hsts_enabled'), width))
    
    # ─────────────────────────────────────────────────────────────────────────
    # COMPONENTS
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_divider(width))
    lines.append(_section_title("LOADED COMPONENTS", width, "📦"))
    
    lines.append(_row("Installed Apps", str(info.get('installed_apps', 0)), width))
    lines.append(_row("Middleware", str(info.get('middleware_count', 0)), width))
    lines.append(_row("Log Level", info.get('log_level'), width))
    
    # ─────────────────────────────────────────────────────────────────────────
    # URL PATTERNS
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_divider(width))
    lines.append(_section_title("URL PATTERNS", width, "🔗"))
    
    url_patterns = [
        ("Health", "/health/, /ready/, /live/"),
        ("Admin", "/admin/"),
        ("API", "/api/v1/, /api/v2/"),
        ("Auth", "/accounts/"),
        ("i18n", "/i18n/setlang/"),
        ("Debug", "/__debug__/ (dev only)"),
    ]
    
    for label, value in url_patterns:
        lines.append(_row(f"  {label}", value, width, label_width=12, indent=2))
    
    # ─────────────────────────────────────────────────────────────────────────
    # LOG FILES
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_divider(width))
    lines.append(_section_title("LOG FILES", width, "📋"))
    
    log_files = [
        ("global.log", "INFO+  → All important logs"),
        ("debug.log", "DEBUG  → Detailed debug info"),
        ("error.log", "ERROR+ → Error & critical logs"),
        ("sql.log", "SQL    → Database queries"),
    ]
    
    for filename, desc in log_files:
        lines.append(_row(f"  {filename}", desc, width, label_width=16, indent=2))
    
    # ─────────────────────────────────────────────────────────────────────────
    # FLOW DIAGRAMS (Optional)
    # ─────────────────────────────────────────────────────────────────────────
    if show_flow:
        lines.append(_divider(width))
        lines.extend(_flow_diagram(width))
    
    if show_config_flow:
        lines.append(_divider(width))
        lines.extend(_config_flow_diagram(width))
    
    # ─────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────────────────────
    lines.append(_footer(width))
    lines.append('')
    
    # Yazdır (flush=True ile buffer'ı hemen boşalt)
    try:
        print('\n'.join(lines), flush=True)
    except Exception as e:
        # Unicode sorunu olabilir, basit banner göster
        print(f"[Banner print error: {e}]", flush=True)


def print_minimal_banner(project: Optional[str] = None, force: bool = False) -> None:
    """Minimal startup banner (sadece temel bilgiler)."""
    from django.conf import settings
    
    if not getattr(settings, 'DEBUG', False):
        return
    
    # Mükerrer yazdırmayı önle
    if _is_banner_printed() and not force:
        return
    
    _mark_banner_printed()
    
    info = StartupInfo(project=project)
    info.collect()
    
    project_type = info.get('project', 'core')
    env = info.get('env', 'unknown')
    
    # Proje tipine göre emoji ve renk
    project_icons = {
        'webapp': ('🌐', 'Webapp', Colors.BRIGHT_CYAN),
        'api': ('🔌', 'API', Colors.BRIGHT_GREEN),
        'admin': ('⚙️', 'Admin', Colors.BRIGHT_YELLOW),
        'core': ('🚀', 'Django', Colors.BRIGHT_WHITE),
    }
    
    icon, name, proj_color = project_icons.get(project_type, project_icons['core'])
    
    if env == 'development':
        env_color = Colors.YELLOW
    elif env == 'production':
        env_color = Colors.RED
    else:
        env_color = Colors.MAGENTA
    
    print(f"""
{c('╔══════════════════════════════════════════════════════════════╗', Colors.CYAN)}
{c('║', Colors.CYAN)}  {icon} {c(f'GlobalMain {name}', proj_color, bold=True)} │ {c(env.upper(), env_color, bold=True):<30}   {c('║', Colors.CYAN)}
{c('║', Colors.CYAN)}     Python {info.get('python_version')} │ Django {info.get('django_version'):<24} {c('║', Colors.CYAN)}
{c('╚══════════════════════════════════════════════════════════════╝', Colors.CYAN)}
""")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def reset_banner_flag() -> None:
    """Banner flag'ını sıfırla (test için)."""
    if _BANNER_ENV_KEY in os.environ:
        del os.environ[_BANNER_ENV_KEY]


def is_banner_printed() -> bool:
    """Banner yazdırıldı mı kontrol et."""
    return _is_banner_printed()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'print_startup_banner',
    'print_minimal_banner',
    'StartupInfo',
    'Colors',
    'reset_banner_flag',
    'is_banner_printed',
]

