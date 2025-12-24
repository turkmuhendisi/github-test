# =============================================================================
# Gunicorn Configuration - GlobalMain
# =============================================================================
# Production WSGI/ASGI server yapılandırması
#
# Worker Türleri:
# - sync: Standart synchronous worker (default)
# - gevent: Gevent-based async worker
# - uvicorn.workers.UvicornWorker: ASGI + WebSocket desteği
#
# Önerilen: UvicornWorker (async I/O + WebSocket)
# =============================================================================

import multiprocessing
import os

# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'production')
IS_DEVELOPMENT = DJANGO_ENV == 'development'

# =============================================================================
# SERVER SOCKET
# =============================================================================
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048

# =============================================================================
# WORKER CONFIGURATION
# =============================================================================
# CPU sayısına göre worker hesapla
# Development: az worker (hot reload + debug için)
# Production: CPU * 2 + 1 (I/O bound workload için optimal)

if IS_DEVELOPMENT:
    workers = 2
    worker_class = 'uvicorn.workers.UvicornWorker'  # ASGI + async
else:
    workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
    worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

# Worker bağlantı limitleri
worker_connections = 1000
max_requests = 1000  # Memory leak koruması
max_requests_jitter = 50  # Aynı anda restart'ı önle

# =============================================================================
# TIMEOUTS
# =============================================================================
# Development: uzun timeout (debug için)
# Production: kısa timeout (DoS koruması)

if IS_DEVELOPMENT:
    timeout = 120  # 2 dakika (debug için)
    graceful_timeout = 30
else:
    timeout = 30  # 30 saniye
    graceful_timeout = 30

keepalive = 5  # Keep-alive bağlantı süresi

# =============================================================================
# PROCESS MANAGEMENT
# =============================================================================
proc_name = 'globalmain'
pidfile = '/tmp/gunicorn.pid'

# Daemon mode (Docker'da False olmalı)
daemon = False

# User/Group (production'da non-root user)
# user = 'appuser'
# group = 'appuser'

# =============================================================================
# LOGGING
# =============================================================================
accesslog = '-'  # stdout
errorlog = '-'   # stderr

if IS_DEVELOPMENT:
    loglevel = 'debug'
    access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'
else:
    loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
    access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)sμs'

# Capture output from Django
capture_output = True

# =============================================================================
# SECURITY
# =============================================================================
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Forwarded headers (nginx arkasında)
forwarded_allow_ips = '*'  # Nginx'ten gelen X-Forwarded-* header'larına güven

# =============================================================================
# SERVER HOOKS
# =============================================================================

def on_starting(server):
    """Server başlamadan önce."""
    print(f"🚀 Gunicorn starting with {workers} workers ({worker_class})")


def on_reload(server):
    """Server reload edildiğinde."""
    print("🔄 Gunicorn reloading...")


def worker_int(worker):
    """Worker SIGINT aldığında."""
    print(f"⚠️  Worker {worker.pid} interrupted")


def worker_abort(worker):
    """Worker abort olduğunda."""
    print(f"❌ Worker {worker.pid} aborted")


def post_fork(server, worker):
    """Worker fork edildikten sonra."""
    if IS_DEVELOPMENT:
        print(f"  → Worker {worker.pid} spawned")


def pre_exec(server):
    """Yeni master process başlamadan önce."""
    print("⚙️  Forked child, re-executing...")


def when_ready(server):
    """Server hazır olduğunda."""
    print(f"✅ Gunicorn ready at {bind}")
    print(f"   Workers: {workers} x {worker_class}")
    print(f"   Environment: {DJANGO_ENV}")


def worker_exit(server, worker):
    """Worker çıkış yaptığında."""
    if IS_DEVELOPMENT:
        print(f"  ← Worker {worker.pid} exited")


# =============================================================================
# UVICORN SPECIFIC (UvicornWorker için)
# =============================================================================
# UvicornWorker kullanıldığında bu ayarlar geçerli

# ASGI application path (uvicorn için)
# Not: Gunicorn'a command line'dan verilen wsgi/asgi app bu ayarı override eder

# =============================================================================
# SSL (Production - Nginx arkasında genelde gerekli değil)
# =============================================================================
# SSL nginx'te terminate edilir, gunicorn'a gerek yok
# Direkt SSL gerekiyorsa:
# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'
# ssl_version = 'TLSv1_2'
