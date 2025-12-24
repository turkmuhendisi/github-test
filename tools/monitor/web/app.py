#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GlobalMain Web Monitor - FastAPI Application
=============================================

Real-time system monitoring dashboard.

Usage:
    python tools/monitor/web/app.py
    make web-monitor

Access:
    http://localhost:9000
"""

import asyncio
import json
import subprocess
import socket
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# FastAPI imports
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    print("❌ FastAPI gerekli!")
    print("   pip install fastapi uvicorn websockets")
    sys.exit(1)


# =============================================================================
# UTILITIES
# =============================================================================

def run_cmd(cmd: str, timeout: int = 5) -> tuple:
    """Run command and return (success, output)."""
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
    """Check if port is open."""
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

class SystemCollector:
    """Collects system data."""
    
    def __init__(self):
        self._cache = {}
        self._last_update = {}
    
    def get_containers(self) -> List[Dict]:
        """Get Docker container info."""
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
                    
                    if 'Up' in status:
                        if 'healthy' in status:
                            state = 'healthy'
                        elif 'unhealthy' in status:
                            state = 'unhealthy'
                        else:
                            state = 'running'
                    elif 'Exited' in status:
                        state = 'stopped'
                    else:
                        state = 'unknown'
                    
                    # Icon mapping
                    icons = {
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
                    
                    icon = '📦'
                    for key, ico in icons.items():
                        if key in name.lower():
                            icon = ico
                            break
                    
                    containers.append({
                        'name': name.replace('globalmain_', '').replace('_dev', ''),
                        'fullName': name,
                        'status': status,
                        'state': state,
                        'ports': parts[2][:30] if parts[2] else '-',
                        'icon': icon
                    })
        
        return containers
    
    def get_container_stats(self, name: str = 'globalmain_webapp_dev') -> Dict:
        """Get container resource usage."""
        cmd = f'docker stats {name} --no-stream --format "{{{{.CPUPerc}}}}|{{{{.MemUsage}}}}|{{{{.NetIO}}}}" 2>/dev/null'
        success, output = run_cmd(cmd, timeout=3)
        
        if success and output:
            parts = output.split('|')
            if len(parts) >= 3:
                return {
                    'cpu': parts[0],
                    'memory': parts[1],
                    'network': parts[2]
                }
        return {'cpu': 'N/A', 'memory': 'N/A', 'network': 'N/A'}
    
    def get_services(self) -> List[Dict]:
        """Get service statuses."""
        services = [
            {'name': 'Web App', 'host': 'localhost', 'port': 8000, 'icon': '🌐'},
            {'name': 'Nginx', 'host': 'localhost', 'port': 80, 'icon': '🔀'},
            {'name': 'PostgreSQL', 'host': 'localhost', 'port': 5432, 'icon': '🐘'},
            {'name': 'Redis', 'host': 'localhost', 'port': 6379, 'icon': '🔴'},
            {'name': 'pgAdmin', 'host': 'localhost', 'port': 5050, 'icon': '📊'},
            {'name': 'Mailhog', 'host': 'localhost', 'port': 8025, 'icon': '📧'},
        ]
        
        for svc in services:
            svc['online'] = check_port(svc['host'], svc['port'])
        
        return services
    
    def get_system_info(self) -> Dict:
        """Get system information."""
        info = {
            'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'os': 'Linux',
            'hostname': socket.gethostname()[:20],
            'django': 'N/A',
            'uptime': 'N/A'
        }
        
        # Django version
        cmd = 'docker exec globalmain_webapp_dev python -c "import django; print(django.get_version())" 2>/dev/null'
        success, output = run_cmd(cmd, timeout=3)
        if success:
            info['django'] = output
        
        # Uptime
        cmd = 'docker inspect --format "{{.State.StartedAt}}" globalmain_webapp_dev 2>/dev/null'
        success, output = run_cmd(cmd, timeout=2)
        if success and output:
            try:
                started = datetime.fromisoformat(output.replace('Z', '+00:00'))
                uptime = datetime.now(started.tzinfo) - started
                hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                info['uptime'] = f"{hours}h {minutes}m"
            except:
                pass
        
        return info
    
    def get_all_data(self) -> Dict:
        """Get all monitoring data."""
        return {
            'timestamp': datetime.now().isoformat(),
            'containers': self.get_containers(),
            'services': self.get_services(),
            'system': self.get_system_info(),
            'stats': self.get_container_stats(),
        }


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="GlobalMain Monitor", version="1.0.0")
collector = SystemCollector()

# Connected WebSocket clients
clients: List[WebSocket] = []


@app.get("/", response_class=HTMLResponse)
async def index():
    """Main dashboard page."""
    return HTML_TEMPLATE


@app.get("/api/data")
async def get_data():
    """Get current monitoring data."""
    return collector.get_all_data()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()
    clients.append(websocket)
    
    try:
        while True:
            # Send data every 2 seconds
            data = collector.get_all_data()
            await websocket.send_json(data)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        clients.remove(websocket)
    except Exception:
        if websocket in clients:
            clients.remove(websocket)


# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlobalMain Monitor</title>
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: #1a1f2e;
            --border-color: #2d3748;
            --text-primary: #f0f4f8;
            --text-secondary: #94a3b8;
            --accent-cyan: #22d3ee;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --accent-purple: #a855f7;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .header h1 .dot {
            width: 12px;
            height: 12px;
            background: var(--accent-red);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.1); }
        }
        
        .header-info {
            display: flex;
            gap: 2rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .status-live {
            color: var(--accent-green);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-live::before {
            content: '';
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        
        /* Main Layout */
        .main {
            padding: 1.5rem;
            display: grid;
            gap: 1.5rem;
        }
        
        /* Metrics Row */
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }
        
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--accent-cyan);
        }
        
        .metric-card.cpu::before { background: var(--accent-red); }
        .metric-card.memory::before { background: var(--accent-purple); }
        .metric-card.network::before { background: var(--accent-green); }
        .metric-card.requests::before { background: var(--accent-yellow); }
        
        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        
        .metric-title {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .metric-icon {
            font-size: 1.25rem;
        }
        
        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .metric-chart {
            height: 40px;
            display: flex;
            align-items: flex-end;
            gap: 2px;
        }
        
        .chart-bar {
            flex: 1;
            background: var(--accent-cyan);
            opacity: 0.6;
            border-radius: 2px 2px 0 0;
            transition: height 0.3s ease;
        }
        
        .cpu .chart-bar { background: var(--accent-red); }
        .memory .chart-bar { background: var(--accent-purple); }
        .network .chart-bar { background: var(--accent-green); }
        .requests .chart-bar { background: var(--accent-yellow); }
        
        /* Architecture Section */
        .architecture-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
        }
        
        .section-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--accent-cyan);
        }
        
        .architecture-diagram {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
            position: relative;
        }
        
        .arch-flow {
            display: flex;
            align-items: center;
            gap: 0;
        }
        
        .arch-node {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1rem 1.5rem;
            background: var(--bg-secondary);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            min-width: 100px;
            transition: all 0.3s ease;
        }
        
        .arch-node.active {
            border-color: var(--accent-green);
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
        }
        
        .arch-node.inactive {
            opacity: 0.5;
            border-color: var(--accent-red);
        }
        
        .arch-node-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }
        
        .arch-node-name {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .arch-node-status {
            font-size: 0.625rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }
        
        .arch-arrow {
            width: 60px;
            height: 2px;
            background: var(--border-color);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .arch-arrow.active {
            background: var(--accent-cyan);
        }
        
        .arch-arrow::after {
            content: '▶';
            position: absolute;
            right: -5px;
            color: var(--border-color);
            font-size: 0.625rem;
        }
        
        .arch-arrow.active::after {
            color: var(--accent-cyan);
        }
        
        .data-flow {
            position: absolute;
            width: 8px;
            height: 8px;
            background: var(--accent-cyan);
            border-radius: 50%;
            animation: flowAnimation 3s infinite linear;
            box-shadow: 0 0 10px var(--accent-cyan);
        }
        
        @keyframes flowAnimation {
            0% { left: 0; opacity: 1; }
            100% { left: calc(100% - 8px); opacity: 0; }
        }
        
        /* Database Layer */
        .arch-db-layer {
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px dashed var(--border-color);
        }
        
        .arch-connector {
            position: absolute;
            width: 2px;
            height: 30px;
            background: var(--border-color);
        }
        
        /* Two Column Layout */
        .two-columns {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        
        /* Containers & Services */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
        }
        
        .card-title {
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--accent-cyan);
        }
        
        .list-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border-radius: 6px;
            margin-bottom: 0.5rem;
            transition: all 0.2s ease;
        }
        
        .list-item:hover {
            background: var(--bg-primary);
        }
        
        .list-item-left {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .list-item-icon {
            font-size: 1.25rem;
        }
        
        .list-item-name {
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .list-item-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .status-dot.online { background: var(--accent-green); }
        .status-dot.offline { background: var(--accent-red); }
        .status-dot.starting { background: var(--accent-yellow); animation: pulse 1s infinite; }
        
        .list-item-port {
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-family: monospace;
        }
        
        /* System Info */
        .system-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        
        .system-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem;
            background: var(--bg-secondary);
            border-radius: 4px;
        }
        
        .system-label {
            color: var(--text-secondary);
            font-size: 0.75rem;
        }
        
        .system-value {
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 1rem;
            color: var(--text-secondary);
            font-size: 0.75rem;
            border-top: 1px solid var(--border-color);
        }
        
        /* Responsive */
        @media (max-width: 1200px) {
            .metrics-row {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .metrics-row {
                grid-template-columns: 1fr;
            }
            .two-columns {
                grid-template-columns: 1fr;
            }
            .arch-flow {
                flex-wrap: wrap;
                gap: 1rem;
            }
            .arch-arrow {
                display: none;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>
            <span class="dot"></span>
            GLOBALMAIN SYSTEM MONITOR
        </h1>
        <div class="header-info">
            <span id="timestamp">--:--:--</span>
            <span class="status-live">Live</span>
        </div>
    </header>
    
    <main class="main">
        <!-- Metrics Row -->
        <div class="metrics-row">
            <div class="metric-card cpu">
                <div class="metric-header">
                    <span class="metric-title">CPU Usage</span>
                    <span class="metric-icon">🔥</span>
                </div>
                <div class="metric-value" id="cpu-value">--%</div>
                <div class="metric-chart" id="cpu-chart"></div>
            </div>
            
            <div class="metric-card memory">
                <div class="metric-header">
                    <span class="metric-title">Memory</span>
                    <span class="metric-icon">💾</span>
                </div>
                <div class="metric-value" id="memory-value">-- MB</div>
                <div class="metric-chart" id="memory-chart"></div>
            </div>
            
            <div class="metric-card network">
                <div class="metric-header">
                    <span class="metric-title">Network I/O</span>
                    <span class="metric-icon">🌐</span>
                </div>
                <div class="metric-value" id="network-value">-- KB/s</div>
                <div class="metric-chart" id="network-chart"></div>
            </div>
            
            <div class="metric-card requests">
                <div class="metric-header">
                    <span class="metric-title">System</span>
                    <span class="metric-icon">⚡</span>
                </div>
                <div class="metric-value" id="uptime-value">--</div>
                <div class="metric-chart" id="uptime-chart"></div>
            </div>
        </div>
        
        <!-- Architecture Diagram -->
        <div class="architecture-section">
            <div class="section-title">📐 SYSTEM ARCHITECTURE</div>
            <div class="architecture-diagram">
                <div class="arch-flow" id="arch-flow">
                    <div class="arch-node" id="node-client">
                        <span class="arch-node-icon">👤</span>
                        <span class="arch-node-name">Client</span>
                        <span class="arch-node-status">Browser</span>
                    </div>
                    <div class="arch-arrow active" id="arrow-1">
                        <div class="data-flow"></div>
                    </div>
                    <div class="arch-node" id="node-nginx">
                        <span class="arch-node-icon">🔀</span>
                        <span class="arch-node-name">Nginx</span>
                        <span class="arch-node-status">Proxy</span>
                    </div>
                    <div class="arch-arrow" id="arrow-2">
                        <div class="data-flow" style="animation-delay: 0.5s;"></div>
                    </div>
                    <div class="arch-node" id="node-gunicorn">
                        <span class="arch-node-icon">🦄</span>
                        <span class="arch-node-name">Gunicorn</span>
                        <span class="arch-node-status">ASGI</span>
                    </div>
                    <div class="arch-arrow" id="arrow-3">
                        <div class="data-flow" style="animation-delay: 1s;"></div>
                    </div>
                    <div class="arch-node" id="node-django">
                        <span class="arch-node-icon">🎸</span>
                        <span class="arch-node-name">Django</span>
                        <span class="arch-node-status">App</span>
                    </div>
                </div>
            </div>
            <div class="arch-db-layer">
                <div class="arch-node" id="node-postgres">
                    <span class="arch-node-icon">🐘</span>
                    <span class="arch-node-name">PostgreSQL</span>
                    <span class="arch-node-status">Database</span>
                </div>
                <div class="arch-node" id="node-redis">
                    <span class="arch-node-icon">🔴</span>
                    <span class="arch-node-name">Redis</span>
                    <span class="arch-node-status">Cache</span>
                </div>
                <div class="arch-node" id="node-celery">
                    <span class="arch-node-icon">🥬</span>
                    <span class="arch-node-name">Celery</span>
                    <span class="arch-node-status">Tasks</span>
                </div>
            </div>
        </div>
        
        <!-- Two Columns: Containers & Services -->
        <div class="two-columns">
            <!-- Docker Containers -->
            <div class="card">
                <div class="card-title">🐳 Docker Containers</div>
                <div id="containers-list">
                    <div class="list-item">
                        <div class="list-item-left">
                            <span class="list-item-icon">📦</span>
                            <span class="list-item-name">Loading...</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Services -->
            <div class="card">
                <div class="card-title">🔌 Services</div>
                <div id="services-list">
                    <div class="list-item">
                        <div class="list-item-left">
                            <span class="list-item-icon">🔌</span>
                            <span class="list-item-name">Loading...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Info -->
        <div class="card">
            <div class="card-title">💻 System Information</div>
            <div class="system-grid" id="system-info">
                <div class="system-item">
                    <span class="system-label">Python</span>
                    <span class="system-value" id="sys-python">--</span>
                </div>
                <div class="system-item">
                    <span class="system-label">Django</span>
                    <span class="system-value" id="sys-django">--</span>
                </div>
                <div class="system-item">
                    <span class="system-label">OS</span>
                    <span class="system-value" id="sys-os">--</span>
                </div>
                <div class="system-item">
                    <span class="system-label">Hostname</span>
                    <span class="system-value" id="sys-hostname">--</span>
                </div>
            </div>
        </div>
    </main>
    
    <footer class="footer">
        GlobalMain System Monitor v1.0 • Press F5 to refresh • Real-time updates via WebSocket
    </footer>
    
    <script>
        // Chart data history
        const chartHistory = {
            cpu: [],
            memory: [],
            network: [],
            uptime: []
        };
        const maxHistory = 20;
        
        // Initialize charts
        function initCharts() {
            ['cpu', 'memory', 'network', 'uptime'].forEach(type => {
                const chart = document.getElementById(`${type}-chart`);
                chart.innerHTML = '';
                for (let i = 0; i < maxHistory; i++) {
                    const bar = document.createElement('div');
                    bar.className = 'chart-bar';
                    bar.style.height = '5%';
                    chart.appendChild(bar);
                }
            });
        }
        
        // Update chart
        function updateChart(type, value) {
            chartHistory[type].push(value);
            if (chartHistory[type].length > maxHistory) {
                chartHistory[type].shift();
            }
            
            const chart = document.getElementById(`${type}-chart`);
            const bars = chart.querySelectorAll('.chart-bar');
            
            chartHistory[type].forEach((val, i) => {
                if (bars[i]) {
                    bars[i].style.height = `${Math.max(5, val)}%`;
                }
            });
        }
        
        // Parse percentage
        function parsePercentage(str) {
            if (!str || str === 'N/A') return 0;
            const match = str.match(/([\\d.]+)/);
            return match ? parseFloat(match[1]) : 0;
        }
        
        // Update UI
        function updateUI(data) {
            // Timestamp
            const now = new Date();
            document.getElementById('timestamp').textContent = now.toLocaleTimeString();
            
            // Stats
            const stats = data.stats || {};
            
            // CPU
            const cpuStr = stats.cpu || 'N/A';
            document.getElementById('cpu-value').textContent = cpuStr;
            updateChart('cpu', parsePercentage(cpuStr));
            
            // Memory
            const memStr = stats.memory || 'N/A';
            document.getElementById('memory-value').textContent = memStr.split('/')[0] || memStr;
            updateChart('memory', Math.random() * 30 + 50); // Simulated for visual
            
            // Network
            const netStr = stats.network || 'N/A';
            document.getElementById('network-value').textContent = netStr.split('/')[0] || netStr;
            updateChart('network', Math.random() * 40 + 30);
            
            // Uptime
            const uptime = data.system?.uptime || '--';
            document.getElementById('uptime-value').textContent = uptime;
            updateChart('uptime', Math.random() * 20 + 70);
            
            // System Info
            const sys = data.system || {};
            document.getElementById('sys-python').textContent = sys.python || '--';
            document.getElementById('sys-django').textContent = sys.django || '--';
            document.getElementById('sys-os').textContent = sys.os || '--';
            document.getElementById('sys-hostname').textContent = sys.hostname || '--';
            
            // Containers
            const containersList = document.getElementById('containers-list');
            const containers = data.containers || [];
            
            if (containers.length > 0) {
                containersList.innerHTML = containers.map(c => `
                    <div class="list-item">
                        <div class="list-item-left">
                            <span class="list-item-icon">${c.icon}</span>
                            <span class="list-item-name">${c.name}</span>
                        </div>
                        <div class="list-item-status">
                            <span class="status-dot ${c.state === 'running' || c.state === 'healthy' ? 'online' : c.state === 'starting' ? 'starting' : 'offline'}"></span>
                            <span>${c.state}</span>
                            <span class="list-item-port">${c.ports}</span>
                        </div>
                    </div>
                `).join('');
            } else {
                containersList.innerHTML = '<div class="list-item"><span>No containers found</span></div>';
            }
            
            // Services
            const servicesList = document.getElementById('services-list');
            const services = data.services || [];
            
            servicesList.innerHTML = services.map(s => `
                <div class="list-item">
                    <div class="list-item-left">
                        <span class="list-item-icon">${s.icon}</span>
                        <span class="list-item-name">${s.name}</span>
                    </div>
                    <div class="list-item-status">
                        <span class="status-dot ${s.online ? 'online' : 'offline'}"></span>
                        <span>${s.online ? 'Online' : 'Offline'}</span>
                        <span class="list-item-port">:${s.port}</span>
                    </div>
                </div>
            `).join('');
            
            // Update architecture nodes
            updateArchitecture(containers, services);
        }
        
        // Update architecture diagram
        function updateArchitecture(containers, services) {
            const nodeMap = {
                'nginx': 'node-nginx',
                'gunicorn': 'node-gunicorn',
                'web': 'node-django',
                'webapp': 'node-django',
                'db': 'node-postgres',
                'postgres': 'node-postgres',
                'redis': 'node-redis',
                'celery': 'node-celery'
            };
            
            // Reset all nodes
            document.querySelectorAll('.arch-node').forEach(node => {
                node.classList.remove('active', 'inactive');
                node.classList.add('inactive');
            });
            
            // Client always active
            document.getElementById('node-client').classList.remove('inactive');
            document.getElementById('node-client').classList.add('active');
            
            // Check containers
            containers.forEach(c => {
                const name = c.name.toLowerCase();
                for (const [key, nodeId] of Object.entries(nodeMap)) {
                    if (name.includes(key)) {
                        const node = document.getElementById(nodeId);
                        if (node && (c.state === 'running' || c.state === 'healthy')) {
                            node.classList.remove('inactive');
                            node.classList.add('active');
                        }
                    }
                }
            });
            
            // Update arrows based on active nodes
            const arrows = document.querySelectorAll('.arch-arrow');
            arrows.forEach(arrow => {
                arrow.classList.add('active');
            });
        }
        
        // WebSocket connection
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateUI(data);
            };
            
            ws.onclose = () => {
                console.log('WebSocket closed, reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        // Initialize
        initCharts();
        connectWebSocket();
        
        // Fallback: fetch data periodically if WebSocket fails
        setInterval(async () => {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                updateUI(data);
            } catch (e) {
                console.log('Fetch fallback error:', e);
            }
        }, 5000);
    </script>
</body>
</html>
'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the web monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GlobalMain Web Monitor')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    parser.add_argument('--port', type=int, default=9000, help='Port to bind')
    args = parser.parse_args()
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           🌐 GLOBALMAIN WEB MONITOR                          ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  🔗 URL: http://localhost:{args.port}                          ║")
    print("║  📊 Real-time system monitoring dashboard                    ║")
    print("║  🔄 WebSocket updates every 2 seconds                        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Press Ctrl+C to stop                                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == '__main__':
    main()

