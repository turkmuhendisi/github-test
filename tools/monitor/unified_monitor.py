#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GlobalMain Unified Monitor
===========================

Tüm monitoring özelliklerini birleştiren kapsamlı canlı izleme aracı.

Özellikler:
- 🔄 Animasyonlu sistem akış diyagramı (hareketli data flow)
- 🐳 Docker container durumları (gerçek zamanlı)
- 🔌 Servis sağlık kontrolleri
- 📊 Request metrikleri ve istatistikler
- 📜 Son istekler listesi
- 💻 Sistem bilgileri
- 📐 Mimari diyagramı

Kullanım:
    python tools/monitor/unified_monitor.py
    make monitor

Keyboard:
    q, Ctrl+C - Çıkış
    r - Yenile
"""

import os
import sys
import time
import subprocess
import socket
import threading
import queue
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

# Rich imports
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.box import ROUNDED, DOUBLE, SIMPLE, HEAVY
    from rich.style import Style
    from rich.progress import SpinnerColumn, Progress, BarColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class ComponentState(Enum):
    """Bileşen durumları."""
    IDLE = "idle"
    ACTIVE = "active"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ServiceStatus(Enum):
    """Servis durumları."""
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    UNKNOWN = "unknown"


@dataclass
class ContainerInfo:
    """Docker container bilgisi."""
    name: str
    status: str
    state: str
    ports: str
    image: str
    cpu: str = "N/A"
    memory: str = "N/A"
    network: str = "N/A"


@dataclass
class ServiceInfo:
    """Servis bilgisi."""
    name: str
    host: str
    port: int
    status: ServiceStatus = ServiceStatus.UNKNOWN
    icon: str = "🔌"


@dataclass
class RequestInfo:
    """Request bilgisi."""
    id: str
    method: str
    path: str
    timestamp: datetime
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    user: Optional[str] = None


@dataclass
class SystemMetrics:
    """Sistem metrikleri."""
    total_requests: int = 0
    active_requests: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    db_queries: int = 0
    cache_hit_rate: float = 0.0
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=50))


# =============================================================================
# SYSTEM UTILITIES
# =============================================================================

def run_cmd(cmd: str, timeout: int = 5) -> tuple[bool, str]:
    """Komut çalıştır."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def check_port(host: str, port: int, timeout: float = 0.5) -> bool:
    """Port erişilebilirlik kontrolü."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


# =============================================================================
# DATA COLLECTORS
# =============================================================================

class DataCollector:
    """Verileri toplayan sınıf."""
    
    def __init__(self):
        self._cache: Dict = {}
        self._last_update: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def _should_update(self, key: str, interval: float = 2.0) -> bool:
        """Cache güncellemesi gerekli mi?"""
        now = time.time()
        if key not in self._last_update:
            return True
        return now - self._last_update[key] > interval
    
    def get_docker_containers(self) -> List[ContainerInfo]:
        """Docker container bilgilerini al."""
        if not self._should_update('containers', interval=3.0):
            return self._cache.get('containers', [])
        
        cmd = 'docker ps -a --filter "name=globalmain" --format "{{.Names}}|{{.Status}}|{{.Ports}}|{{.Image}}" 2>/dev/null'
        success, output = run_cmd(cmd)
        
        containers = []
        if success and output:
            for line in output.split('\n'):
                if not line or '|' not in line:
                    continue
                parts = line.split('|')
                if len(parts) >= 4:
                    name = parts[0]
                    status = parts[1]
                    
                    # Durumu belirle
                    if 'Up' in status:
                        if 'healthy' in status:
                            state = 'healthy'
                        elif 'unhealthy' in status:
                            state = 'unhealthy'
                        else:
                            state = 'running'
                    elif 'Exited' in status:
                        state = 'stopped'
                    elif 'Restarting' in status:
                        state = 'restarting'
                    else:
                        state = 'unknown'
                    
                    containers.append(ContainerInfo(
                        name=name,
                        status=status,
                        state=state,
                        ports=parts[2],
                        image=parts[3]
                    ))
        
        with self._lock:
            self._cache['containers'] = containers
            self._last_update['containers'] = time.time()
        
        return containers
    
    def get_container_stats(self, name: str) -> Dict:
        """Container kaynak kullanımı."""
        cache_key = f'stats_{name}'
        if not self._should_update(cache_key, interval=5.0):
            return self._cache.get(cache_key, {})
        
        cmd = f'docker stats {name} --no-stream --format "{{{{.CPUPerc}}}}|{{{{.MemUsage}}}}|{{{{.NetIO}}}}" 2>/dev/null'
        success, output = run_cmd(cmd, timeout=3)
        
        stats = {'cpu': 'N/A', 'memory': 'N/A', 'network': 'N/A'}
        if success and output:
            parts = output.split('|')
            if len(parts) >= 3:
                stats = {
                    'cpu': parts[0],
                    'memory': parts[1],
                    'network': parts[2]
                }
        
        with self._lock:
            self._cache[cache_key] = stats
            self._last_update[cache_key] = time.time()
        
        return stats
    
    def get_services(self) -> List[ServiceInfo]:
        """Servislerin durumlarını kontrol et."""
        if not self._should_update('services', interval=5.0):
            return self._cache.get('services', [])
        
        services = [
            ServiceInfo("Web App", "localhost", 8000, icon="🌐"),
            ServiceInfo("Nginx", "localhost", 80, icon="🔀"),
            ServiceInfo("PostgreSQL", "localhost", 5432, icon="🐘"),
            ServiceInfo("Redis", "localhost", 6379, icon="🔴"),
            ServiceInfo("pgAdmin", "localhost", 5050, icon="📊"),
            ServiceInfo("Mailhog", "localhost", 8025, icon="📧"),
        ]
        
        for service in services:
            if check_port(service.host, service.port):
                service.status = ServiceStatus.ONLINE
            else:
                service.status = ServiceStatus.OFFLINE
        
        with self._lock:
            self._cache['services'] = services
            self._last_update['services'] = time.time()
        
        return services
    
    def get_system_info(self) -> Dict:
        """Sistem bilgilerini al."""
        if not self._should_update('system_info', interval=30.0):
            return self._cache.get('system_info', {})
        
        info = {}
        
        # Python
        info['python'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # OS
        import platform
        info['os'] = f"{platform.system()} {platform.release()}"
        info['hostname'] = platform.node()[:20]
        
        # Django version
        cmd = 'docker exec globalmain_webapp_dev python -c "import django; print(django.get_version())" 2>/dev/null'
        success, output = run_cmd(cmd, timeout=3)
        info['django'] = output if success else 'N/A'
        
        # Uptime
        cmd = 'docker inspect --format "{{.State.StartedAt}}" globalmain_webapp_dev 2>/dev/null'
        success, output = run_cmd(cmd, timeout=2)
        if success and output:
            try:
                started = datetime.fromisoformat(output.replace('Z', '+00:00'))
                uptime = datetime.now(started.tzinfo) - started
                hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                info['uptime'] = f"{hours}h {minutes}m"
            except:
                info['uptime'] = 'N/A'
        else:
            info['uptime'] = 'N/A'
        
        with self._lock:
            self._cache['system_info'] = info
            self._last_update['system_info'] = time.time()
        
        return info


# =============================================================================
# UNIFIED MONITOR
# =============================================================================

class UnifiedMonitor:
    """
    Kapsamlı birleşik sistem monitörü.
    Tüm özellikleri tek ekranda gösterir.
    """
    
    # Animasyon kareleri
    SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    PULSE = ['○', '◔', '◑', '◕', '●', '◕', '◑', '◔']
    FLOW = ['▸', '▹', '►', '▻', '▸']
    DATA_FLOW = ['·', '•', '●', '•']
    WAVE = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃', '▂']
    
    # Container ikonları
    CONTAINER_ICONS = {
        'webapp': '🌐', 'web': '🌐',
        'gunicorn': '🦄', 
        'nginx': '🔀',
        'db': '🐘', 'postgres': '🐘',
        'redis': '🔴',
        'celery': '🥬',
        'pgadmin': '📊',
        'mailhog': '📧', 'mail': '📧',
        'backup': '💾',
    }
    
    # Durum renkleri
    STATE_COLORS = {
        'healthy': 'bold green',
        'running': 'bold yellow',
        'unhealthy': 'bold red',
        'stopped': 'dim red',
        'restarting': 'bold orange1',
        'unknown': 'dim',
    }
    
    def __init__(self):
        self.console = Console()
        self.collector = DataCollector()
        self.frame = 0
        self.flow_position = 0
        self.metrics = SystemMetrics()
        self._running = False
    
    def get_container_icon(self, name: str) -> str:
        """Container için ikon."""
        name_lower = name.lower()
        for key, icon in self.CONTAINER_ICONS.items():
            if key in name_lower:
                return icon
        return '📦'
    
    # ─────────────────────────────────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_header(self) -> Panel:
        """Animasyonlu header."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spinner = self.SPINNER[self.frame % len(self.SPINNER)]
        pulse = self.PULSE[self.frame % len(self.PULSE)]
        
        title = Text()
        title.append(f" {pulse} ", style="bold red")
        title.append("GLOBALMAIN ", style="bold white")
        title.append("UNIFIED ", style="bold cyan")
        title.append("MONITOR ", style="bold white")
        title.append(f" {spinner} ", style="bold green")
        
        return Panel(
            Align.center(title),
            subtitle=f"[dim]{now}[/dim]",
            style="bold cyan",
            box=DOUBLE
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # SYSTEM INFO
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_system_info(self) -> Panel:
        """Sistem bilgileri."""
        info = self.collector.get_system_info()
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", width=12)
        table.add_column("", style="white")
        
        table.add_row("🐍 Python", info.get('python', 'N/A'))
        table.add_row("🎸 Django", info.get('django', 'N/A'))
        table.add_row("💻 OS", info.get('os', 'N/A')[:22])
        table.add_row("⏱️  Uptime", info.get('uptime', 'N/A'))
        
        return Panel(table, title="[bold cyan]💻 SYSTEM[/]", border_style="cyan")
    
    # ─────────────────────────────────────────────────────────────────────────
    # SERVICES
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_services(self) -> Panel:
        """Servis durumları."""
        services = self.collector.get_services()
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", width=16)
        table.add_column("", width=10)
        table.add_column("", width=6)
        
        for svc in services:
            if svc.status == ServiceStatus.ONLINE:
                status = Text("● Online", style="bold green")
            else:
                status = Text("○ Offline", style="dim red")
            
            table.add_row(f"{svc.icon} {svc.name}", status, f":{svc.port}")
        
        return Panel(table, title="[bold cyan]🔌 SERVICES[/]", border_style="cyan")
    
    # ─────────────────────────────────────────────────────────────────────────
    # METRICS
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_metrics(self) -> Panel:
        """Request metrikleri."""
        # Web container stats
        stats = self.collector.get_container_stats('globalmain_webapp_dev')
        
        # Wave animasyonu
        wave_idx = self.frame % len(self.WAVE)
        wave = ''.join([self.WAVE[(wave_idx + i) % len(self.WAVE)] for i in range(8)])
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", width=14)
        table.add_column("", width=12)
        
        table.add_row("🔥 CPU", stats.get('cpu', 'N/A'))
        table.add_row("💾 Memory", stats.get('memory', 'N/A')[:12])
        table.add_row("🌐 Network", stats.get('network', 'N/A')[:12])
        table.add_row("", "")
        table.add_row("[cyan]Activity[/]", f"[green]{wave}[/]")
        
        return Panel(table, title="[bold cyan]📊 METRICS[/]", border_style="cyan")
    
    # ─────────────────────────────────────────────────────────────────────────
    # DOCKER CONTAINERS
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_containers(self) -> Panel:
        """Docker container durumları."""
        containers = self.collector.get_docker_containers()
        
        table = Table(show_header=True, header_style="bold cyan", box=ROUNDED, padding=(0, 1))
        table.add_column("", width=2)
        table.add_column("Container", width=20)
        table.add_column("Status", width=12)
        table.add_column("Ports", width=25)
        
        for c in containers:
            icon = self.get_container_icon(c.name)
            name = c.name.replace('globalmain_', '').replace('_dev', '')
            
            state = c.state
            color = self.STATE_COLORS.get(state, 'dim')
            
            if state == 'healthy':
                status = Text("● Running", style=color)
            elif state == 'running':
                spin = self.SPINNER[self.frame % len(self.SPINNER)]
                status = Text(f"{spin} Starting", style=color)
            elif state == 'stopped':
                status = Text("○ Stopped", style=color)
            elif state == 'restarting':
                spin = self.SPINNER[self.frame % len(self.SPINNER)]
                status = Text(f"{spin} Restart", style=color)
            else:
                status = Text("? Unknown", style="dim")
            
            ports = c.ports[:25] if c.ports else '-'
            table.add_row(icon, name, status, ports)
        
        if not containers:
            table.add_row("", "[dim]Docker çalışmıyor[/]", "", "")
        
        return Panel(table, title="[bold cyan]🐳 DOCKER CONTAINERS[/]", border_style="cyan")
    
    # ─────────────────────────────────────────────────────────────────────────
    # ANIMATED ARCHITECTURE DIAGRAM
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_architecture(self) -> Panel:
        """Animasyonlu mimari diyagramı - kompakt versiyon."""
        # Akış animasyonu
        flow = self.FLOW[self.flow_position % len(self.FLOW)]
        data = self.DATA_FLOW[self.frame % len(self.DATA_FLOW)]
        
        # Containers durumlarını al
        containers = self.collector.get_docker_containers()
        cont_names = [c.name.lower() for c in containers if c.state in ['running', 'healthy']]
        
        def is_active(keyword: str) -> bool:
            return any(keyword in n for n in cont_names)
        
        # Servis stilleri
        def style(keyword: str) -> str:
            return "[bold green]" if is_active(keyword) else "[dim]"
        
        # Animasyonlu oklar
        arrows = f"─{data}─{flow}─{data}─"
        
        # Kompakt diyagram
        nginx_s = style('nginx')
        gunicorn_s = style('gunicorn') if is_active('gunicorn') else style('web')
        db_s = style('db')
        redis_s = style('redis')
        celery_s = style('celery')
        
        # Data flow animasyonu
        flow_dots = " ".join([self.DATA_FLOW[(self.frame + i) % len(self.DATA_FLOW)] for i in range(15)])
        
        diagram = f"""
  [bold white]┌──────────┐[/]    {arrows}    {nginx_s}┌──────────┐[/]    {arrows}    {gunicorn_s}┌───────────┐[/]    {arrows}    [bold cyan]┌──────────┐[/]
  [bold white]│  Client  │[/]  {data}    {data}  {nginx_s}│  Nginx   │[/]  {data}    {data}  {gunicorn_s}│ Gunicorn  │[/]  {data}    {data}  [bold cyan]│  Django  │[/]
  [bold white]└──────────┘[/]            {nginx_s}└──────────┘[/]            {gunicorn_s}└───────────┘[/]            [bold cyan]└─────┬────┘[/]
                                                                                    │
                          ┌─────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┐
                          │                                                         {flow}                                                         │
                          ▼                                                         ▼                                                         ▼
                   {db_s}┌────────────┐[/]                                    {redis_s}┌────────────┐[/]                                    {celery_s}┌────────────┐[/]
                   {db_s}│ PostgreSQL │[/]                                    {redis_s}│   Redis    │[/]                                    {celery_s}│   Celery   │[/]
                   {db_s}│ (Database) │[/]                                    {redis_s}│  (Cache)   │[/]                                    {celery_s}│  (Tasks)   │[/]
                   {db_s}└────────────┘[/]                                    {redis_s}└────────────┘[/]                                    {celery_s}└────────────┘[/]

  [dim]Data Flow:[/] [cyan]{flow_dots}[/]                                                    [dim]Yeşil = Aktif | Gri = Kapalı[/]
"""
        return Panel(
            Text.from_markup(diagram),
            title="[bold cyan]📐 SYSTEM ARCHITECTURE[/]",
            border_style="cyan"
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # REQUEST FLOW DIAGRAM (Django internal)
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_django_flow(self) -> Panel:
        """Django iç akış diyagramı."""
        flow = self.FLOW[self.frame % len(self.FLOW)]
        
        diagram = f"""
    ┌──────────┐      ┌────────────┐      ┌──────────┐
    │ Request  │──{flow}──│ Middleware │──{flow}──│   URLs   │
    └──────────┘      └────────────┘      └────┬─────┘
                                               │
    ┌──────────┐      ┌────────────┐      ┌────▼─────┐
    │ Response │←─{flow}──│  Template  │←─{flow}──│  Views   │
    └──────────┘      └────────────┘      └────┬─────┘
                                               │
                      ┌────────────┐      ┌────▼─────┐
                      │  Database  │←─{flow}──│  Models  │
                      └────────────┘      └──────────┘
"""
        return Panel(
            Text(diagram, style="cyan"),
            title="[bold cyan]🔄 DJANGO REQUEST FLOW[/]",
            border_style="dim cyan"
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # ENDPOINTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_endpoints(self) -> Panel:
        """API endpoints."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", width=12)
        table.add_column("", width=20)
        
        endpoints = [
            ("🏥 Health", "/health/, /ready/"),
            ("⚙️  Admin", "/admin/"),
            ("🔌 API v1", "/api/v1/"),
            ("🔐 Auth", "/accounts/"),
            ("🐞 Debug", "/__debug__/"),
        ]
        
        for name, path in endpoints:
            table.add_row(name, f"[dim]{path}[/]")
        
        return Panel(table, title="[bold cyan]🔗 ENDPOINTS[/]", border_style="cyan")
    
    # ─────────────────────────────────────────────────────────────────────────
    # QUICK COMMANDS
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_commands(self) -> Panel:
        """Hızlı komutlar."""
        commands = """[dim]
 make dev         → Başlat
 make stop        → Durdur
 make logs        → Loglar
 make shell       → Bash
 make pgadmin     → pgAdmin
 make backup      → Yedekle
[/]"""
        return Panel(
            Text.from_markup(commands),
            title="[bold cyan]⌨️  COMMANDS[/]",
            border_style="cyan"
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # LAYOUT
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_layout(self) -> Layout:
        """Ana layout."""
        layout = Layout()
        
        # Ana yapı: Header, Body, Footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(self.build_header())
        
        # Body - Üst, Orta, Alt
        layout["body"].split_column(
            Layout(name="top", size=7),
            Layout(name="middle"),
            Layout(name="bottom", size=16)
        )
        
        # Üst: Sistem + Servisler + Metrikler
        layout["top"].split_row(
            Layout(self.build_system_info(), name="system", ratio=1),
            Layout(self.build_services(), name="services", ratio=1),
            Layout(self.build_metrics(), name="metrics", ratio=1)
        )
        
        # Orta: Containers + Endpoints + Commands
        layout["middle"].split_row(
            Layout(self.build_containers(), name="containers", ratio=3),
            Layout(name="right_panel", ratio=1)
        )
        
        layout["right_panel"].split_column(
            Layout(self.build_endpoints(), name="endpoints"),
            Layout(self.build_commands(), name="commands")
        )
        
        # Alt: Architecture
        layout["bottom"].update(self.build_architecture())
        
        # Footer
        footer_text = Text()
        footer_text.append(" Press ", style="dim")
        footer_text.append("q", style="bold yellow")
        footer_text.append(" or ", style="dim")
        footer_text.append("Ctrl+C", style="bold yellow")
        footer_text.append(" to exit │ ", style="dim")
        footer_text.append("r", style="bold cyan")
        footer_text.append(" to refresh │ ", style="dim")
        footer_text.append("Auto-refresh: 1s", style="dim green")
        
        layout["footer"].update(Panel(Align.center(footer_text), style="dim"))
        
        return layout
    
    # ─────────────────────────────────────────────────────────────────────────
    # RUN
    # ─────────────────────────────────────────────────────────────────────────
    
    def run(self, refresh_rate: float = 1.0):
        """Monitor'u başlat."""
        if not RICH_AVAILABLE:
            print("❌ Rich kütüphanesi gerekli!")
            print("   pip install rich")
            return
        
        self._running = True
        self.console.clear()
        
        try:
            with Live(
                self.build_layout(),
                console=self.console,
                refresh_per_second=4,
                screen=True
            ) as live:
                while self._running:
                    self.frame += 1
                    
                    # Her 3 frame'de flow pozisyonunu güncelle
                    if self.frame % 3 == 0:
                        self.flow_position += 1
                    
                    # Layout'u güncelle
                    live.update(self.build_layout())
                    
                    time.sleep(refresh_rate)
                    
        except KeyboardInterrupt:
            self._running = False
            self.console.clear()
            self.console.print("\n[bold green]✅ Monitor kapatıldı.[/]\n")
    
    def stop(self):
        """Monitor'u durdur."""
        self._running = False


# =============================================================================
# SIMPLE MONITOR (Rich olmadan)
# =============================================================================

class SimpleMonitor:
    """Rich olmadan basit terminal monitor."""
    
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'cyan': '\033[36m',
    }
    
    def __init__(self):
        self.collector = DataCollector()
        self.frame = 0
        self._running = False
    
    def _c(self, text: str, color: str = '', bold: bool = False) -> str:
        """Renklendir."""
        prefix = self.COLORS['bold'] if bold else ''
        return f"{prefix}{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def run(self, refresh_rate: float = 2.0):
        """Basit monitor çalıştır."""
        self._running = True
        
        try:
            while self._running:
                self._clear()
                self.frame += 1
                
                spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][self.frame % 10]
                
                print(self._c("\n╔══════════════════════════════════════════════════════════════╗", 'cyan'))
                print(self._c("║", 'cyan') + self._c(f"  {spinner} GLOBALMAIN UNIFIED MONITOR                              ", 'cyan', True) + self._c("║", 'cyan'))
                print(self._c("╠══════════════════════════════════════════════════════════════╣", 'cyan'))
                
                # Services
                services = self.collector.get_services()
                for svc in services:
                    status = self._c("●", 'green') if svc.status.value == 'online' else self._c("○", 'red')
                    print(self._c("║", 'cyan') + f"  {svc.icon} {svc.name:<15} {status}  :{svc.port:<6}" + " " * 25 + self._c("║", 'cyan'))
                
                print(self._c("╠══════════════════════════════════════════════════════════════╣", 'cyan'))
                
                # Containers
                containers = self.collector.get_docker_containers()
                for c in containers[:5]:
                    name = c.name.replace('globalmain_', '')[:15]
                    state = self._c("●", 'green') if c.state in ['running', 'healthy'] else self._c("○", 'red')
                    print(self._c("║", 'cyan') + f"  📦 {name:<15} {state}  {c.ports[:25]:<25}" + self._c("║", 'cyan'))
                
                print(self._c("╠══════════════════════════════════════════════════════════════╣", 'cyan'))
                print(self._c("║", 'cyan') + "  Press Ctrl+C to exit" + " " * 40 + self._c("║", 'cyan'))
                print(self._c("╚══════════════════════════════════════════════════════════════╝", 'cyan'))
                
                time.sleep(refresh_rate)
                
        except KeyboardInterrupt:
            self._running = False
            print(self._c("\n✅ Monitor kapatıldı.\n", 'green'))


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Ana fonksiyon."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GlobalMain Unified Monitor')
    parser.add_argument('--simple', action='store_true', help='Basit mod (Rich olmadan)')
    parser.add_argument('--refresh', type=float, default=1.0, help='Yenileme aralığı (saniye)')
    args = parser.parse_args()
    
    print("🔴 GlobalMain Unified Monitor başlatılıyor...")
    print("   Çıkmak için Ctrl+C veya q tuşuna basın.")
    print()
    time.sleep(1)
    
    if args.simple or not RICH_AVAILABLE:
        monitor = SimpleMonitor()
    else:
        monitor = UnifiedMonitor()
    
    monitor.run(refresh_rate=args.refresh)


if __name__ == '__main__':
    main()

