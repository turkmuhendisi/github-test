# -*- coding: utf-8 -*-
"""
Live System Monitor
====================

Terminal tabanlı canlı Django izleme aracı.
Request flow'u animasyonlu diyagram üzerinde gösterir.

Özellikler:
- Gerçek zamanlı request akışı görselleştirme
- Animasyonlu sistem diyagramı
- Canlı metrikler (request/s, response time, etc.)
- Aktif bileşen vurgulama
- Veritabanı sorgu izleme
"""

import os
import sys
import time
import threading
import queue
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Deque
from enum import Enum

# Rich imports (opsiyonel - yoksa basit mod kullan)
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.table import Table
    from rich.text import Text
    from rich.style import Style
    from rich.align import Align
    from rich.box import ROUNDED, DOUBLE, HEAVY
    from rich.progress import SpinnerColumn, Progress
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# =============================================================================
# DATA CLASSES
# =============================================================================

class ComponentState(Enum):
    """Bileşen durumları."""
    IDLE = "idle"
    ACTIVE = "active"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class RequestEvent:
    """Request olayı."""
    id: str
    method: str
    path: str
    timestamp: datetime
    component: str = "request"
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    db_queries: int = 0
    user: Optional[str] = None


@dataclass
class SystemMetrics:
    """Sistem metrikleri."""
    total_requests: int = 0
    active_requests: int = 0
    requests_per_second: float = 0.0
    avg_response_time_ms: float = 0.0
    error_count: int = 0
    db_query_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    # Son 60 saniyenin verileri
    recent_requests: Deque[RequestEvent] = field(default_factory=lambda: deque(maxlen=100))
    response_times: Deque[float] = field(default_factory=lambda: deque(maxlen=100))


# =============================================================================
# REQUEST TRACKER (Thread-safe)
# =============================================================================

class RequestTracker:
    """
    Thread-safe request izleyici.
    Middleware'den gelen olayları toplar.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._event_queue: queue.Queue = queue.Queue()
        self._metrics = SystemMetrics()
        self._active_components: dict[str, ComponentState] = {
            'request': ComponentState.IDLE,
            'middleware': ComponentState.IDLE,
            'urls': ComponentState.IDLE,
            'views': ComponentState.IDLE,
            'models': ComponentState.IDLE,
            'database': ComponentState.IDLE,
            'templates': ComponentState.IDLE,
            'response': ComponentState.IDLE,
        }
        self._current_request: Optional[RequestEvent] = None
        self._listeners: list = []
    
    def track_request_start(self, request_id: str, method: str, path: str, user: str = None):
        """Request başlangıcını izle."""
        event = RequestEvent(
            id=request_id,
            method=method,
            path=path,
            timestamp=datetime.now(),
            component='request',
            user=user
        )
        self._metrics.total_requests += 1
        self._metrics.active_requests += 1
        self._metrics.recent_requests.append(event)
        self._current_request = event
        self._set_component_state('request', ComponentState.ACTIVE)
        self._event_queue.put(('request_start', event))
    
    def track_component(self, component: str, state: ComponentState = ComponentState.ACTIVE):
        """Bileşen durumunu güncelle."""
        self._set_component_state(component, state)
        self._event_queue.put(('component', (component, state)))
    
    def track_db_query(self, query_time_ms: float = 0):
        """Veritabanı sorgusunu izle."""
        self._metrics.db_query_count += 1
        if self._current_request:
            self._current_request.db_queries += 1
        self._set_component_state('database', ComponentState.ACTIVE)
        self._event_queue.put(('db_query', query_time_ms))
    
    def track_request_end(self, request_id: str, status_code: int, duration_ms: float):
        """Request bitişini izle."""
        self._metrics.active_requests = max(0, self._metrics.active_requests - 1)
        self._metrics.response_times.append(duration_ms)
        
        # Ortalama hesapla
        if self._metrics.response_times:
            self._metrics.avg_response_time_ms = sum(self._metrics.response_times) / len(self._metrics.response_times)
        
        # Hata sayısı
        if status_code >= 400:
            self._metrics.error_count += 1
        
        # Tüm bileşenleri idle yap
        for component in self._active_components:
            self._set_component_state(component, ComponentState.IDLE)
        
        # Son bileşeni duruma göre ayarla
        final_state = ComponentState.ERROR if status_code >= 400 else ComponentState.SUCCESS
        self._set_component_state('response', final_state)
        
        if self._current_request:
            self._current_request.status_code = status_code
            self._current_request.duration_ms = duration_ms
        
        self._event_queue.put(('request_end', (request_id, status_code, duration_ms)))
        self._current_request = None
    
    def _set_component_state(self, component: str, state: ComponentState):
        """Bileşen durumunu güncelle."""
        if component in self._active_components:
            self._active_components[component] = state
    
    def get_metrics(self) -> SystemMetrics:
        """Metrikleri al."""
        # Requests per second hesapla
        now = datetime.now()
        recent = [r for r in self._metrics.recent_requests 
                  if (now - r.timestamp).total_seconds() < 1]
        self._metrics.requests_per_second = len(recent)
        return self._metrics
    
    def get_component_states(self) -> dict[str, ComponentState]:
        """Bileşen durumlarını al."""
        return self._active_components.copy()
    
    def get_events(self, timeout: float = 0.1) -> list:
        """Bekleyen olayları al."""
        events = []
        try:
            while True:
                event = self._event_queue.get(timeout=timeout)
                events.append(event)
        except queue.Empty:
            pass
        return events


# =============================================================================
# LIVE MONITOR (Rich-based)
# =============================================================================

class LiveMonitor:
    """
    Rich kütüphanesi ile canlı terminal izleme.
    """
    
    # Bileşen renkleri
    COLORS = {
        ComponentState.IDLE: "dim white",
        ComponentState.ACTIVE: "bold yellow",
        ComponentState.SUCCESS: "bold green",
        ComponentState.ERROR: "bold red",
        ComponentState.WARNING: "bold orange1",
    }
    
    # Box karakterleri
    BOX = {
        'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
        'h': '═', 'v': '║', 'lt': '╠', 'rt': '╣',
        'stl': '┌', 'str': '┐', 'sbl': '└', 'sbr': '┘',
        'sh': '─', 'sv': '│', 'slt': '├', 'srt': '┤',
        'ar': '→', 'al': '←', 'au': '↑', 'ad': '↓',
        'arr': '───→', 'arl': '←───',
    }
    
    # Animasyon kareleri
    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    PULSE_FRAMES = ['○', '◔', '◑', '◕', '●', '◕', '◑', '◔']
    FLOW_FRAMES = ['▸', '▹', '►', '▻']
    
    def __init__(self):
        self.tracker = RequestTracker()
        self.console = Console() if RICH_AVAILABLE else None
        self._running = False
        self._frame = 0
        self._flow_position = 0
        self._last_activity = datetime.now()
    
    def _get_component_box(self, name: str, state: ComponentState, width: int = 13) -> Text:
        """Bileşen kutusunu oluştur."""
        color = self.COLORS[state]
        
        # Animasyon
        if state == ComponentState.ACTIVE:
            spinner = self.SPINNER_FRAMES[self._frame % len(self.SPINNER_FRAMES)]
            icon = f" {spinner} "
        elif state == ComponentState.SUCCESS:
            icon = " ✓ "
        elif state == ComponentState.ERROR:
            icon = " ✗ "
        else:
            icon = "   "
        
        # Kutu çiz
        inner_width = width - 2
        name_padded = name.center(inner_width)
        
        lines = [
            f"┌{'─' * inner_width}┐",
            f"│{name_padded}│",
            f"│{icon.center(inner_width)}│",
            f"└{'─' * inner_width}┘",
        ]
        
        text = Text()
        for line in lines:
            text.append(line + "\n", style=color)
        
        return text
    
    def _build_flow_diagram(self) -> Panel:
        """Animasyonlu akış diyagramını oluştur."""
        states = self.tracker.get_component_states()
        
        # Akış animasyonu
        flow_char = self.FLOW_FRAMES[self._flow_position % len(self.FLOW_FRAMES)]
        
        def arrow(active: bool = False) -> str:
            if active:
                return f"──{flow_char}─"
            return "────"
        
        def vline(active: bool = False) -> str:
            if active:
                return f"  {flow_char}  "
            return "  │  "
        
        # Aktif bileşenleri kontrol et
        req_active = states.get('request') == ComponentState.ACTIVE
        mid_active = states.get('middleware') == ComponentState.ACTIVE
        url_active = states.get('urls') == ComponentState.ACTIVE
        view_active = states.get('views') == ComponentState.ACTIVE
        model_active = states.get('models') == ComponentState.ACTIVE
        db_active = states.get('database') == ComponentState.ACTIVE
        tpl_active = states.get('templates') == ComponentState.ACTIVE
        res_active = states.get('response') in [ComponentState.ACTIVE, ComponentState.SUCCESS, ComponentState.ERROR]
        
        # Renk fonksiyonu
        def c(text: str, component: str) -> Text:
            state = states.get(component, ComponentState.IDLE)
            return Text(text, style=self.COLORS[state])
        
        # Diyagram
        diagram = Table.grid(padding=0)
        diagram.add_column(justify="center")
        
        # Satır satır ekle
        # Row 1: Request → Middleware → URLs → Views
        row1 = Text()
        row1.append("    ")
        row1.append(self._mini_box("Request", states.get('request', ComponentState.IDLE)))
        row1.append(arrow(req_active or mid_active), style="cyan" if req_active else "dim")
        row1.append(self._mini_box("Middleware", states.get('middleware', ComponentState.IDLE)))
        row1.append(arrow(mid_active or url_active), style="cyan" if mid_active else "dim")
        row1.append(self._mini_box("URLs", states.get('urls', ComponentState.IDLE)))
        row1.append(arrow(url_active or view_active), style="cyan" if url_active else "dim")
        row1.append(self._mini_box("Views", states.get('views', ComponentState.IDLE)))
        diagram.add_row(row1)
        
        # Row 2: Vertical lines
        row2 = Text()
        row2.append(" " * 60)
        row2.append("│", style="cyan" if view_active else "dim")
        diagram.add_row(row2)
        
        # Row 3: Response ← Templates ← Models
        row3 = Text()
        row3.append("    ")
        row3.append(self._mini_box("Response", states.get('response', ComponentState.IDLE)))
        row3.append("←───", style="cyan" if res_active else "dim")
        row3.append(self._mini_box("Templates", states.get('templates', ComponentState.IDLE)))
        row3.append("←───", style="cyan" if tpl_active else "dim")
        row3.append(self._mini_box("Models", states.get('models', ComponentState.IDLE)))
        row3.append("←───", style="cyan" if model_active else "dim")
        row3.append("┘", style="cyan" if view_active else "dim")
        diagram.add_row(row3)
        
        # Row 4: Vertical line to DB
        row4 = Text()
        row4.append(" " * 48)
        row4.append("│", style="cyan" if model_active or db_active else "dim")
        diagram.add_row(row4)
        
        # Row 5: Database
        row5 = Text()
        row5.append(" " * 35)
        row5.append("┌" + "─" * 26 + "┐", style=self.COLORS[states.get('database', ComponentState.IDLE)])
        diagram.add_row(row5)
        
        row6 = Text()
        row6.append(" " * 35)
        db_state = states.get('database', ComponentState.IDLE)
        db_icon = self.SPINNER_FRAMES[self._frame % len(self.SPINNER_FRAMES)] if db_state == ComponentState.ACTIVE else "🗄️ "
        db_text = f"│  {db_icon} Database             │"
        row6.append(db_text, style=self.COLORS[db_state])
        diagram.add_row(row6)
        
        row7 = Text()
        row7.append(" " * 35)
        row7.append("└" + "─" * 26 + "┘", style=self.COLORS[states.get('database', ComponentState.IDLE)])
        diagram.add_row(row7)
        
        return Panel(
            diagram,
            title="[bold cyan]📐 SYSTEM FLOW[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
    
    def _mini_box(self, name: str, state: ComponentState) -> Text:
        """Mini bileşen kutusu."""
        color = self.COLORS[state]
        icon = ""
        
        if state == ComponentState.ACTIVE:
            icon = self.SPINNER_FRAMES[self._frame % len(self.SPINNER_FRAMES)]
        elif state == ComponentState.SUCCESS:
            icon = "✓"
        elif state == ComponentState.ERROR:
            icon = "✗"
        
        text = Text()
        text.append("[", style=color)
        text.append(f"{icon}{name}" if icon else name, style=color)
        text.append("]", style=color)
        return text
    
    def _build_metrics_panel(self) -> Panel:
        """Metrik panelini oluştur."""
        metrics = self.tracker.get_metrics()
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="cyan")
        table.add_column("Value", justify="right")
        
        # Pulse animasyonu aktif request varsa
        pulse = self.PULSE_FRAMES[self._frame % len(self.PULSE_FRAMES)] if metrics.active_requests > 0 else "○"
        
        table.add_row("🚀 Total Requests", f"[bold white]{metrics.total_requests:,}[/]")
        table.add_row(f"{pulse} Active", f"[bold yellow]{metrics.active_requests}[/]")
        table.add_row("⚡ Req/sec", f"[bold green]{metrics.requests_per_second:.1f}[/]")
        table.add_row("⏱️  Avg Response", f"[bold cyan]{metrics.avg_response_time_ms:.1f}ms[/]")
        table.add_row("❌ Errors", f"[bold red]{metrics.error_count}[/]")
        table.add_row("🗃️  DB Queries", f"[bold blue]{metrics.db_query_count:,}[/]")
        
        return Panel(
            table,
            title="[bold cyan]📊 METRICS[/bold cyan]",
            border_style="cyan"
        )
    
    def _build_recent_requests(self) -> Panel:
        """Son istekleri göster."""
        metrics = self.tracker.get_metrics()
        
        table = Table(box=ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Time", style="dim", width=10)
        table.add_column("Method", width=7)
        table.add_column("Path", width=30, overflow="ellipsis")
        table.add_column("Status", width=7, justify="center")
        table.add_column("Time", width=8, justify="right")
        
        # Son 10 request
        recent = list(metrics.recent_requests)[-10:]
        for req in reversed(recent):
            time_str = req.timestamp.strftime("%H:%M:%S")
            
            # Method rengi
            method_style = "green" if req.method == "GET" else "yellow" if req.method == "POST" else "blue"
            
            # Status rengi
            if req.status_code:
                if req.status_code < 300:
                    status_style = "green"
                elif req.status_code < 400:
                    status_style = "yellow"
                else:
                    status_style = "red"
                status = str(req.status_code)
            else:
                status_style = "yellow"
                status = "..."
            
            # Duration
            if req.duration_ms:
                duration = f"{req.duration_ms:.0f}ms"
            else:
                duration = "..."
            
            table.add_row(
                time_str,
                Text(req.method, style=method_style),
                req.path[:30],
                Text(status, style=status_style),
                duration
            )
        
        return Panel(
            table,
            title="[bold cyan]📜 RECENT REQUESTS[/bold cyan]",
            border_style="cyan"
        )
    
    def _build_layout(self) -> Layout:
        """Ana layout'u oluştur."""
        layout = Layout()
        
        # Üst kısım: Header
        header = Panel(
            Align.center(
                Text("🔴 LIVE SYSTEM MONITOR", style="bold white on red") if self._frame % 20 < 10
                else Text("🟢 LIVE SYSTEM MONITOR", style="bold white on green")
            ),
            style="bold"
        )
        
        layout.split_column(
            Layout(header, name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Body: Diyagram ve Metrikler
        layout["body"].split_row(
            Layout(name="main", ratio=3),
            Layout(name="sidebar", ratio=1)
        )
        
        layout["main"].split_column(
            Layout(self._build_flow_diagram(), name="diagram"),
            Layout(self._build_recent_requests(), name="requests")
        )
        
        layout["sidebar"].update(self._build_metrics_panel())
        
        # Footer
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = Panel(
            Align.center(Text(f"Press Ctrl+C to exit │ {now}", style="dim")),
            style="dim"
        )
        layout["footer"].update(footer)
        
        return layout
    
    def start(self, refresh_rate: float = 0.1):
        """Monitor'u başlat."""
        if not RICH_AVAILABLE:
            print("Rich kütüphanesi gerekli: pip install rich")
            return
        
        self._running = True
        self.console.clear()
        
        try:
            with Live(self._build_layout(), console=self.console, refresh_per_second=10) as live:
                while self._running:
                    self._frame += 1
                    
                    # Her 2 frame'de akış pozisyonunu güncelle
                    if self._frame % 2 == 0:
                        self._flow_position += 1
                    
                    # Event'leri işle
                    events = self.tracker.get_events(timeout=0.05)
                    
                    # Layout'u güncelle
                    live.update(self._build_layout())
                    
                    time.sleep(refresh_rate)
                    
        except KeyboardInterrupt:
            self._running = False
            self.console.print("\n[bold green]Monitor durduruldu.[/bold green]")
    
    def stop(self):
        """Monitor'u durdur."""
        self._running = False


# =============================================================================
# SIMPLE MONITOR (Rich olmadan)
# =============================================================================

class SimpleMonitor:
    """
    Rich olmadan basit ANSI tabanlı monitor.
    """
    
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'cyan': '\033[36m',
        'white': '\033[37m',
    }
    
    def __init__(self):
        self.tracker = RequestTracker()
        self._running = False
        self._frame = 0
    
    def _clear(self):
        """Ekranı temizle."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _c(self, text: str, color: str = 'white', bold: bool = False) -> str:
        """Renklendir."""
        prefix = self.COLORS['bold'] if bold else ''
        return f"{prefix}{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _draw(self):
        """Ekranı çiz."""
        self._clear()
        metrics = self.tracker.get_metrics()
        states = self.tracker.get_component_states()
        
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][self._frame % 10]
        
        print(self._c("\n╔══════════════════════════════════════════════════════════════════╗", 'cyan'))
        print(self._c("║", 'cyan') + self._c("                    🔴 LIVE SYSTEM MONITOR                       ", 'white', True) + self._c("║", 'cyan'))
        print(self._c("╠══════════════════════════════════════════════════════════════════╣", 'cyan'))
        
        # Metrikler
        print(self._c("║", 'cyan') + f"  {spinner} Total: {metrics.total_requests:5d}  │  Active: {metrics.active_requests:2d}  │  " +
              f"Errors: {metrics.error_count:3d}  │  Avg: {metrics.avg_response_time_ms:6.1f}ms  " + self._c("║", 'cyan'))
        
        print(self._c("╠══════════════════════════════════════════════════════════════════╣", 'cyan'))
        
        # Basit diyagram
        def box(name, state):
            if state.value == 'active':
                return self._c(f"[{spinner}{name}]", 'yellow', True)
            elif state.value == 'success':
                return self._c(f"[✓{name}]", 'green')
            elif state.value == 'error':
                return self._c(f"[✗{name}]", 'red')
            return self._c(f"[ {name}]", 'dim')
        
        print(self._c("║", 'cyan') + "                                                                  " + self._c("║", 'cyan'))
        print(self._c("║", 'cyan') + f"  {box('Req', states['request'])}→{box('Mid', states['middleware'])}→" +
              f"{box('URL', states['urls'])}→{box('View', states['views'])}                    " + self._c("║", 'cyan'))
        print(self._c("║", 'cyan') + "                                               │                   " + self._c("║", 'cyan'))
        print(self._c("║", 'cyan') + f"  {box('Res', states['response'])}←{box('Tpl', states['templates'])}←" +
              f"{box('Mdl', states['models'])}←──────────┘                   " + self._c("║", 'cyan'))
        print(self._c("║", 'cyan') + "                           │                                       " + self._c("║", 'cyan'))
        print(self._c("║", 'cyan') + f"                      {box('Database', states['database'])}                               " + self._c("║", 'cyan'))
        print(self._c("║", 'cyan') + "                                                                  " + self._c("║", 'cyan'))
        
        print(self._c("╠══════════════════════════════════════════════════════════════════╣", 'cyan'))
        print(self._c("║", 'cyan') + "  Press Ctrl+C to exit                                            " + self._c("║", 'cyan'))
        print(self._c("╚══════════════════════════════════════════════════════════════════╝", 'cyan'))
    
    def start(self, refresh_rate: float = 0.2):
        """Monitor'u başlat."""
        self._running = True
        
        try:
            while self._running:
                self._frame += 1
                self._draw()
                time.sleep(refresh_rate)
        except KeyboardInterrupt:
            self._running = False
            print("\n" + self._c("Monitor durduruldu.", 'green'))
    
    def stop(self):
        """Monitor'u durdur."""
        self._running = False


# =============================================================================
# FACTORY
# =============================================================================

def create_monitor() -> LiveMonitor | SimpleMonitor:
    """
    Uygun monitor'u oluştur.
    Rich varsa LiveMonitor, yoksa SimpleMonitor.
    """
    if RICH_AVAILABLE:
        return LiveMonitor()
    return SimpleMonitor()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point."""
    monitor = create_monitor()
    print("🔴 Live System Monitor başlatılıyor...")
    print("   Ctrl+C ile durdurun.\n")
    time.sleep(1)
    monitor.start()


if __name__ == '__main__':
    main()

