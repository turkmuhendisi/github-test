#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GlobalMain System Monitor
==========================

Kapsamlı canlı sistem izleme aracı.
Docker container'ları, servisler ve metrikleri tek ekranda gösterir.

Kullanım:
    python tools/monitor/system_monitor.py

Özellikler:
- Docker container durumları (gerçek zamanlı)
- Sistem bilgileri (Python, Django, OS)
- Servis durumları (PostgreSQL, Redis, Nginx, vb.)
- Request metrikleri
- Kaynak kullanımı (CPU, Memory)
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime
from typing import Optional

# Rich imports
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.box import ROUNDED, DOUBLE, SIMPLE
    from rich.style import Style
    from rich.progress import SpinnerColumn, Progress, BarColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich kütüphanesi gerekli: pip install rich")
    sys.exit(1)


# =============================================================================
# DOCKER UTILITIES
# =============================================================================

def run_cmd(cmd: str, timeout: int = 5) -> tuple[bool, str]:
    """Komut çalıştır ve sonucu döndür."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def get_docker_containers() -> list[dict]:
    """Docker container bilgilerini al."""
    cmd = 'docker ps -a --format "{{.Names}}|{{.Status}}|{{.Ports}}|{{.Image}}" 2>/dev/null'
    success, output = run_cmd(cmd)
    
    if not success or not output:
        return []
    
    containers = []
    for line in output.split('\n'):
        if not line or '|' not in line:
            continue
        parts = line.split('|')
        if len(parts) >= 4:
            name = parts[0]
            status = parts[1]
            ports = parts[2]
            image = parts[3]
            
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
            
            containers.append({
                'name': name,
                'status': status,
                'state': state,
                'ports': ports,
                'image': image
            })
    
    return containers


def get_container_stats(name: str) -> dict:
    """Container kaynak kullanımını al."""
    cmd = f'docker stats {name} --no-stream --format "{{{{.CPUPerc}}}}|{{{{.MemUsage}}}}|{{{{.NetIO}}}}" 2>/dev/null'
    success, output = run_cmd(cmd, timeout=3)
    
    if not success or not output:
        return {'cpu': 'N/A', 'memory': 'N/A', 'network': 'N/A'}
    
    parts = output.split('|')
    if len(parts) >= 3:
        return {
            'cpu': parts[0],
            'memory': parts[1],
            'network': parts[2]
        }
    return {'cpu': 'N/A', 'memory': 'N/A', 'network': 'N/A'}


def check_service(host: str, port: int) -> bool:
    """Servis erişilebilirliğini kontrol et."""
    cmd = f'nc -z -w1 {host} {port} 2>/dev/null || curl -s -o /dev/null -w "%{{http_code}}" http://{host}:{port}/health/ 2>/dev/null | grep -q "200"'
    success, _ = run_cmd(cmd, timeout=2)
    return success


def get_system_info() -> dict:
    """Sistem bilgilerini al."""
    info = {}
    
    # Python version
    info['python'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # OS
    import platform
    info['os'] = f"{platform.system()} {platform.release()}"
    info['hostname'] = platform.node()
    
    # Django version (container'dan al)
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
            info['uptime'] = f"{hours}h {minutes}m {seconds}s"
        except:
            info['uptime'] = 'N/A'
    else:
        info['uptime'] = 'N/A'
    
    return info


def get_request_metrics() -> dict:
    """Request metriklerini al (nginx loglarından veya container'dan)."""
    metrics = {
        'total': 0,
        'success': 0,
        'errors': 0,
        'req_per_sec': 0.0
    }
    
    # Nginx access log'dan son 1 dakikayı oku
    cmd = '''docker exec globalmain_nginx_dev sh -c "tail -100 /var/log/nginx/access.log 2>/dev/null | wc -l" 2>/dev/null'''
    success, output = run_cmd(cmd, timeout=2)
    if success and output.isdigit():
        metrics['total'] = int(output)
    
    return metrics


# =============================================================================
# MONITOR UI
# =============================================================================

class SystemMonitor:
    """Kapsamlı sistem izleme arayüzü."""
    
    # Container ikonları
    ICONS = {
        'webapp': '🌐',
        'gunicorn': '🦄',
        'nginx': '🔀',
        'db': '🐘',
        'redis': '🔴',
        'celery': '🥬',
        'pgadmin': '📊',
        'mailhog': '📧',
        'backup': '💾',
    }
    
    # Durum renkleri
    COLORS = {
        'healthy': 'green',
        'running': 'yellow',
        'unhealthy': 'red',
        'stopped': 'dim red',
        'restarting': 'yellow',
        'unknown': 'dim',
    }
    
    def __init__(self):
        self.console = Console()
        self.frame = 0
        self._cache = {}
        self._last_update = 0
    
    def get_icon(self, name: str) -> str:
        """Container için ikon al."""
        name_lower = name.lower()
        for key, icon in self.ICONS.items():
            if key in name_lower:
                return icon
        return '📦'
    
    def build_header(self) -> Panel:
        """Header paneli."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][self.frame % 10]
        
        title = Text()
        title.append(f" {spinner} ", style="bold red")
        title.append("GLOBALMAIN SYSTEM MONITOR", style="bold white")
        title.append(f" {spinner} ", style="bold red")
        
        return Panel(
            Align.center(title),
            subtitle=f"[dim]{now}[/dim]",
            style="bold cyan"
        )
    
    def build_system_info(self) -> Panel:
        """Sistem bilgileri paneli."""
        # Cache'den al veya yenile (her 10 saniyede bir)
        if time.time() - self._last_update > 10 or 'system_info' not in self._cache:
            self._cache['system_info'] = get_system_info()
            self._last_update = time.time()
        
        info = self._cache['system_info']
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="cyan", width=12)
        table.add_column("Value", style="white")
        
        table.add_row("🐍 Python", info.get('python', 'N/A'))
        table.add_row("🎸 Django", info.get('django', 'N/A'))
        table.add_row("💻 OS", info.get('os', 'N/A')[:25])
        table.add_row("🏠 Host", info.get('hostname', 'N/A')[:20])
        table.add_row("⏱️  Uptime", info.get('uptime', 'N/A'))
        
        return Panel(table, title="[bold cyan]💻 SYSTEM[/]", border_style="cyan")
    
    def build_containers(self) -> Panel:
        """Container durumları paneli."""
        containers = get_docker_containers()
        
        # Sadece globalmain container'larını filtrele
        containers = [c for c in containers if 'globalmain' in c['name'].lower()]
        
        table = Table(show_header=True, header_style="bold cyan", box=ROUNDED)
        table.add_column("", width=3)  # Icon
        table.add_column("Container", width=22)
        table.add_column("Status", width=12)
        table.add_column("Ports", width=20)
        
        for c in containers:
            icon = self.get_icon(c['name'])
            name = c['name'].replace('globalmain_', '')
            
            # Durum stili
            state = c['state']
            color = self.COLORS.get(state, 'dim')
            
            if state == 'healthy':
                status = Text("● Running", style=f"bold {color}")
            elif state == 'running':
                status = Text("◐ Starting", style=f"bold {color}")
            elif state == 'stopped':
                status = Text("○ Stopped", style=f"{color}")
            elif state == 'restarting':
                spinner = ['⠋', '⠙', '⠹', '⠸'][self.frame % 4]
                status = Text(f"{spinner} Restart", style=f"bold {color}")
            else:
                status = Text("? Unknown", style="dim")
            
            # Port bilgisi
            ports = c['ports'][:20] if c['ports'] else '-'
            
            table.add_row(icon, name, status, ports)
        
        if not containers:
            table.add_row("", "[dim]No containers running[/]", "", "")
        
        return Panel(table, title="[bold cyan]🐳 DOCKER CONTAINERS[/]", border_style="cyan")
    
    def build_services(self) -> Panel:
        """Servis durumları paneli."""
        services = [
            ('🌐 Web App', 'localhost', 8000),
            ('🔀 Nginx', 'localhost', 80),
            ('🐘 PostgreSQL', 'localhost', 5432),
            ('🔴 Redis', 'localhost', 6379),
            ('📊 pgAdmin', 'localhost', 5050),
        ]
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Service", width=15)
        table.add_column("Status", width=10)
        table.add_column("Port", width=8)
        
        for name, host, port in services:
            # Basit port kontrolü
            cmd = f'nc -z -w1 localhost {port} 2>/dev/null'
            success, _ = run_cmd(cmd, timeout=1)
            
            if success:
                status = Text("● Online", style="bold green")
            else:
                status = Text("○ Offline", style="dim red")
            
            table.add_row(name, status, f":{port}")
        
        return Panel(table, title="[bold cyan]🔌 SERVICES[/]", border_style="cyan")
    
    def build_architecture(self) -> Panel:
        """Mimari diyagramı."""
        # Animasyonlu ok
        arrows = ['─', '─', '→', '→']
        arrow = arrows[self.frame % 4]
        
        diagram = f"""
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Client    │{arrow}{arrow}{arrow}{arrow}{arrow}│    Nginx    │{arrow}{arrow}{arrow}{arrow}{arrow}│  Gunicorn   │
    │  (Browser)  │     │   (proxy)   │     │  (ASGI)     │
    └─────────────┘     └─────────────┘     └──────┬──────┘
                                                   │
          ┌────────────────────────────────────────┼────────────────────────────────────────┐
          │                                        │                                        │
          ▼                                        ▼                                        ▼
    ┌─────────────┐                         ┌─────────────┐                         ┌─────────────┐
    │  PostgreSQL │                         │    Redis    │                         │   Celery    │
    │  (Database) │                         │   (Cache)   │                         │  (Tasks)    │
    └─────────────┘                         └─────────────┘                         └─────────────┘
"""
        return Panel(
            Text(diagram, style="cyan"),
            title="[bold cyan]📐 ARCHITECTURE[/]",
            border_style="cyan"
        )
    
    def build_metrics(self) -> Panel:
        """Metrik paneli."""
        # Container stats al (web container)
        stats = get_container_stats('globalmain_webapp_dev')
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", width=14)
        table.add_column("Value", width=15)
        
        table.add_row("🔥 CPU Usage", stats.get('cpu', 'N/A'))
        table.add_row("💾 Memory", stats.get('memory', 'N/A'))
        table.add_row("🌐 Network I/O", stats.get('network', 'N/A')[:15])
        
        # Ek metrikler
        table.add_row("", "")
        table.add_row("[cyan]📈 Endpoints[/]", "")
        table.add_row("  Health", "[green]✓[/] /health/")
        table.add_row("  Admin", "[green]✓[/] /admin/")
        table.add_row("  API", "[green]✓[/] /api/v1/")
        
        return Panel(table, title="[bold cyan]📊 METRICS[/]", border_style="cyan")
    
    def build_layout(self) -> Layout:
        """Ana layout."""
        layout = Layout()
        
        # Ana yapı
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(self.build_header())
        
        # Body - üst ve alt
        layout["body"].split_column(
            Layout(name="top", ratio=2),
            Layout(name="bottom", ratio=3)
        )
        
        # Üst: Sistem + Servisler + Metrikler
        layout["top"].split_row(
            Layout(self.build_system_info(), name="system", ratio=1),
            Layout(self.build_services(), name="services", ratio=1),
            Layout(self.build_metrics(), name="metrics", ratio=1)
        )
        
        # Alt: Containers + Architecture
        layout["bottom"].split_row(
            Layout(self.build_containers(), name="containers", ratio=2),
            Layout(self.build_architecture(), name="arch", ratio=3)
        )
        
        # Footer
        footer_text = Text()
        footer_text.append(" Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold yellow")
        footer_text.append(" to exit │ ", style="dim")
        footer_text.append("Refresh: 1s", style="dim")
        
        layout["footer"].update(Panel(Align.center(footer_text), style="dim"))
        
        return layout
    
    def run(self, refresh_rate: float = 1.0):
        """Monitor'u başlat."""
        self.console.clear()
        
        try:
            with Live(self.build_layout(), console=self.console, refresh_per_second=2) as live:
                while True:
                    self.frame += 1
                    live.update(self.build_layout())
                    time.sleep(refresh_rate)
        except KeyboardInterrupt:
            self.console.print("\n[bold green]Monitor durduruldu.[/]")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Ana fonksiyon."""
    if not RICH_AVAILABLE:
        print("Rich kütüphanesi gerekli: pip install rich")
        sys.exit(1)
    
    print("🔴 GlobalMain System Monitor başlatılıyor...")
    print("   Çıkmak için Ctrl+C")
    print()
    time.sleep(1)
    
    monitor = SystemMonitor()
    monitor.run()


if __name__ == '__main__':
    main()

