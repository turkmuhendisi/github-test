# =============================================================================
# Gunicorn Development Configuration - GlobalMain
# =============================================================================
# Development ortamı için özel yapılandırma
# Hot reload, debug, az worker
#
# Kullanım:
#   gunicorn --config infra/gunicorn/gunicorn.dev.conf.py config.hub.wsgi:application
#
# ASGI için (WebSocket/async):
#   gunicorn --config infra/gunicorn/gunicorn.dev.conf.py config.hub.asgi:application
# =============================================================================

import os

# =============================================================================
# ENVIRONMENT
# =============================================================================
os.environ.setdefault('DJANGO_ENV', 'development')
os.environ.setdefault('DJANGO_DEBUG', 'True')

# =============================================================================
# SERVER SOCKET
# =============================================================================
bind = '0.0.0.0:8000'
backlog = 512

# =============================================================================
# WORKERS (Development - az worker, hızlı restart)
# =============================================================================
workers = 2
worker_class = 'uvicorn.workers.UvicornWorker'  # ASGI + WebSocket desteği
worker_connections = 100

# Development'ta az request ile restart (memory leak tespiti için)
max_requests = 500
max_requests_jitter = 25

# =============================================================================
# HOT RELOAD
# =============================================================================
reload = True  # Kod değişikliklerinde otomatik restart
reload_engine = 'auto'  # 'auto', 'poll', 'inotify'
reload_extra_files = [
    'config/settings/',
    'webapp/templates/',
]

# =============================================================================
# TIMEOUTS (Development - uzun)
# =============================================================================
timeout = 120  # Debug için 2 dakika
graceful_timeout = 30
keepalive = 5

# =============================================================================
# LOGGING (Detaylı)
# =============================================================================
accesslog = '-'
errorlog = '-'
loglevel = 'debug'

# Detaylı access log formatı
access_log_format = (
    '\033[36m%(h)s\033[0m '  # IP (cyan)
    '%(t)s '  # Timestamp
    '"\033[33m%(r)s\033[0m" '  # Request (yellow)
    '\033[%(s)s%(s)s\033[0m '  # Status (renkli)
    '%(b)s '  # Bytes
    '%(D)sμs'  # Duration
)

# Django output'u yakala
capture_output = True

# =============================================================================
# PROCESS
# =============================================================================
proc_name = 'globalmain-dev'
daemon = False  # Docker'da foreground

# =============================================================================
# SECURITY (Development - gevşek)
# =============================================================================
limit_request_line = 8190
limit_request_fields = 200
limit_request_field_size = 16380

# Tüm forwarded header'lara güven (development)
forwarded_allow_ips = '*'

# =============================================================================
# HOOKS
# =============================================================================

def on_starting(server):
    print("\n" + "=" * 60)
    print("🚀 GUNICORN DEVELOPMENT SERVER")
    print("=" * 60)
    print(f"   Workers: {workers} x {worker_class}")
    print(f"   Bind: {bind}")
    print(f"   Reload: {'✓ Enabled' if reload else '✗ Disabled'}")
    print("=" * 60 + "\n")


def when_ready(server):
    print(f"✅ Server ready at http://localhost:8000")
    print(f"   Health: http://localhost:8000/health/")
    print(f"   Admin: http://localhost:8000/admin/")
    print()


def on_reload(server):
    print("\n🔄 Code change detected, reloading workers...\n")


def post_fork(server, worker):
    print(f"   → Worker {worker.pid} spawned")


def worker_exit(server, worker):
    print(f"   ← Worker {worker.pid} stopped")

