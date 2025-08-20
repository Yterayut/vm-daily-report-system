#!/usr/bin/env python3
"""
Mac Dashboard - Web interface for monitoring VM system
รัน Dashboard บน Mac สำหรับมอนิเตอร์ระบบ
"""

import os
import json
import glob
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

# Configuration
PROJECT_DIR = Path(__file__).parent
LOG_DIR = PROJECT_DIR / "logs"
SERVER_IP = "192.168.20.10"
SERVER_USER = "one-climate"
SERVER_PASS = "U8@1v3z#14"

# Dashboard template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VM Monitoring Dashboard - Mac</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 20px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        
        .status-card:hover {
            transform: translateY(-5px);
        }
        
        .card-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .status-online { background: #4CAF50; }
        .status-offline { background: #F44336; }
        .status-warning { background: #FF9800; }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .metric-value {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
            margin: 5px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s ease;
        }
        
        .progress-warning { background: linear-gradient(90deg, #FF9800, #FFC107); }
        .progress-critical { background: linear-gradient(90deg, #F44336, #E91E63); }
        
        .log-section {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
        }
        
        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .log-entries {
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .log-timestamp {
            color: #64B5F6;
            margin-right: 10px;
        }
        
        .log-level-success { color: #4CAF50; }
        .log-level-warning { color: #FF9800; }
        .log-level-error { color: #F44336; }
        
        .refresh-btn {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .last-updated {
            text-align: center;
            margin-top: 20px;
            opacity: 0.7;
            font-size: 0.9rem;
        }
        
        .cron-schedule {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .cron-job {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .status-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .container {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ VM Monitoring Dashboard</h1>
            <div class="subtitle">Mac Control Center - One Climate Infrastructure</div>
            <div class="last-updated" id="lastUpdated">Loading...</div>
        </div>
        
        <div class="status-grid">
            <!-- Server Status Card -->
            <div class="status-card">
                <div class="card-title">
                    <span class="status-indicator" id="serverStatus"></span>
                    Server Status
                </div>
                <div class="metric-row">
                    <span class="metric-label">Connection</span>
                    <span class="metric-value" id="serverConnection">Checking...</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">SSH Access</span>
                    <span class="metric-value" id="sshAccess">Checking...</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Cron Service</span>
                    <span class="metric-value" id="cronService">Checking...</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Last Report</span>
                    <span class="metric-value" id="lastReport">Checking...</span>
                </div>
            </div>
            
            <!-- Resources Card -->
            <div class="status-card">
                <div class="card-title">
                    <span class="status-indicator" id="resourceStatus"></span>
                    Server Resources
                </div>
                <div class="metric-row">
                    <span class="metric-label">Disk Usage</span>
                    <span class="metric-value" id="diskUsage">--%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="diskProgress"></div>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Inodes Usage</span>
                    <span class="metric-value" id="inodesUsage">--%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="inodesProgress"></div>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Free Inodes</span>
                    <span class="metric-value" id="freeInodes">--</span>
                </div>
            </div>
            
            <!-- VM Status Card -->
            <div class="status-card">
                <div class="card-title">
                    <span class="status-indicator" id="vmStatus"></span>
                    VM Infrastructure
                </div>
                <div class="metric-row">
                    <span class="metric-label">Total VMs</span>
                    <span class="metric-value" id="totalVMs">--</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Online VMs</span>
                    <span class="metric-value" id="onlineVMs">--</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Uptime</span>
                    <span class="metric-value" id="uptime">--%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="uptimeProgress"></div>
                </div>
            </div>
            
            <!-- Monitoring Config Card -->
            <div class="status-card">
                <div class="card-title">
                    <span class="status-indicator status-online"></span>
                    Monitoring Configuration
                </div>
                <div class="metric-row">
                    <span class="metric-label">Monitor Interval</span>
                    <span class="metric-value">15 minutes</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Email Recipients</span>
                    <span class="metric-value">2 recipients</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">LINE Bot</span>
                    <span class="metric-value">Quota Exceeded</span>
                </div>
                
                <div class="cron-schedule">
                    <strong>📅 Cron Schedule:</strong>
                    <div class="cron-job">
                        <span>Server Monitor</span>
                        <span>Every 15 min</span>
                    </div>
                    <div class="cron-job">
                        <span>Daily Report</span>
                        <span>8:00 AM & 5:30 PM</span>
                    </div>
                    <div class="cron-job">
                        <span>Log Cleanup</span>
                        <span>Daily 2:00 AM</span>
                    </div>
                    <div class="cron-job">
                        <span>Server Cleanup</span>
                        <span>Sunday 3:00 AM</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Log Section -->
        <div class="log-section">
            <div class="log-header">
                <h3>📋 Recent Monitor Logs</h3>
                <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
            </div>
            <div class="log-entries" id="logEntries">
                Loading logs...
            </div>
        </div>
    </div>
    
    <script>
        let lastUpdateTime = new Date();
        
        // Auto refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
        
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
                lastUpdateTime = new Date();
                document.getElementById('lastUpdated').textContent = 
                    `Last Updated: ${lastUpdateTime.toLocaleString('th-TH')}`;
            } catch (error) {
                console.error('Failed to fetch data:', error);
                document.getElementById('lastUpdated').textContent = 
                    `Update Failed: ${lastUpdateTime.toLocaleString('th-TH')}`;
            }
        }
        
        function updateDashboard(data) {
            // Server Status
            const serverIndicator = document.getElementById('serverStatus');
            const isServerOnline = data.server_connection && data.ssh_access;
            serverIndicator.className = `status-indicator ${isServerOnline ? 'status-online' : 'status-offline'}`;
            
            document.getElementById('serverConnection').textContent = data.server_connection ? '✅ Online' : '❌ Offline';
            document.getElementById('sshAccess').textContent = data.ssh_access ? '✅ Connected' : '❌ Failed';
            document.getElementById('cronService').textContent = data.cron_service ? '✅ Active' : '❌ Inactive';
            document.getElementById('lastReport').textContent = data.last_report || 'No data';
            
            // Resources
            const resourceIndicator = document.getElementById('resourceStatus');
            const isResourcesOK = data.disk_usage < 90 && data.inodes_usage < 99;
            resourceIndicator.className = `status-indicator ${isResourcesOK ? 'status-online' : 'status-warning'}`;
            
            document.getElementById('diskUsage').textContent = `${data.disk_usage}%`;
            document.getElementById('inodesUsage').textContent = `${data.inodes_usage}%`;
            document.getElementById('freeInodes').textContent = data.free_inodes || '--';
            
            // Progress bars
            updateProgressBar('diskProgress', data.disk_usage, 90);
            updateProgressBar('inodesProgress', data.inodes_usage, 99);
            
            // VM Status
            const vmIndicator = document.getElementById('vmStatus');
            const vmUptime = data.vm_uptime || 0;
            vmIndicator.className = `status-indicator ${vmUptime > 95 ? 'status-online' : 'status-warning'}`;
            
            document.getElementById('totalVMs').textContent = data.total_vms || '--';
            document.getElementById('onlineVMs').textContent = data.online_vms || '--';
            document.getElementById('uptime').textContent = `${vmUptime}%`;
            updateProgressBar('uptimeProgress', vmUptime, 100);
            
            // Update logs
            updateLogs(data.recent_logs || []);
        }
        
        function updateProgressBar(elementId, value, warningThreshold) {
            const progressBar = document.getElementById(elementId);
            progressBar.style.width = `${Math.min(value, 100)}%`;
            
            if (value >= warningThreshold) {
                progressBar.className = 'progress-fill progress-critical';
            } else if (value >= warningThreshold * 0.8) {
                progressBar.className = 'progress-fill progress-warning';
            } else {
                progressBar.className = 'progress-fill';
            }
        }
        
        function updateLogs(logs) {
            const logContainer = document.getElementById('logEntries');
            logContainer.innerHTML = '';
            
            logs.slice(-20).forEach(log => {
                const logDiv = document.createElement('div');
                logDiv.className = 'log-entry';
                
                let levelClass = 'log-level-success';
                if (log.includes('❌') || log.includes('🚨')) {
                    levelClass = 'log-level-error';
                } else if (log.includes('⚠️')) {
                    levelClass = 'log-level-warning';
                }
                
                const timestamp = log.match(/\\[(.*?)\\]/)?.[1] || '';
                const message = log.replace(/\\[.*?\\]/, '').trim();
                
                logDiv.innerHTML = `
                    <span class="log-timestamp">${timestamp}</span>
                    <span class="${levelClass}">${message}</span>
                `;
                logContainer.appendChild(logDiv);
            });
            
            // Auto scroll to bottom
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    </script>
</body>
</html>
"""

def get_status_data():
    """ดึงข้อมูลสถานะระบบ"""
    try:
        # Read monitor logs
        monitor_log = LOG_DIR / "server_monitor.log"
        recent_logs = []
        
        if monitor_log.exists():
            with open(monitor_log, 'r', encoding='utf-8') as f:
                recent_logs = f.readlines()[-50:]  # Last 50 lines
        
        # Parse latest status from logs
        server_connection = False
        ssh_access = False
        cron_service = False
        last_report = "Unknown"
        disk_usage = 0
        inodes_usage = 0
        free_inodes = "0"
        
        # Parse recent logs for status
        for line in reversed(recent_logs[-10:]):  # Check last 10 lines
            if "✅ Server" in line and "is reachable" in line:
                server_connection = True
            elif "❌ Server" in line and "unreachable" in line:
                server_connection = False
                break
            
            if "✅ SSH connection OK" in line:
                ssh_access = True
            elif "❌ SSH connection failed" in line:
                ssh_access = False
            
            if "✅ Remote cron service is active" in line:
                cron_service = True
            elif "❌ Remote cron service is not active" in line:
                cron_service = False
            
            if "Last report:" in line:
                import re
                match = re.search(r'Last report: ([\d-]+)', line)
                if match:
                    last_report = match.group(1)
            
            if "📊 Server resources:" in line:
                import re
                disk_match = re.search(r'Disk (\d+)%', line)
                inodes_match = re.search(r'Inodes ([\d.]+)%.*?(\d+) free', line)
                
                if disk_match:
                    disk_usage = int(disk_match.group(1))
                if inodes_match:
                    inodes_usage = float(inodes_match.group(1))
                    free_inodes = inodes_match.group(2)
        
        # Mock VM data (จะเชื่อมต่อจริงในอนาคต)
        total_vms = 32
        online_vms = 32
        vm_uptime = 100.0 if server_connection else 0
        
        return {
            'server_connection': server_connection,
            'ssh_access': ssh_access,
            'cron_service': cron_service,
            'last_report': last_report,
            'disk_usage': disk_usage,
            'inodes_usage': round(inodes_usage, 1),
            'free_inodes': free_inodes,
            'total_vms': total_vms,
            'online_vms': online_vms,
            'vm_uptime': vm_uptime,
            'recent_logs': [log.strip() for log in recent_logs[-20:]]  # Last 20 logs
        }
        
    except Exception as e:
        print(f"Error getting status data: {e}")
        return {
            'server_connection': False,
            'ssh_access': False,
            'cron_service': False,
            'last_report': 'Error',
            'disk_usage': 0,
            'inodes_usage': 0,
            'free_inodes': '0',
            'total_vms': 0,
            'online_vms': 0,
            'vm_uptime': 0,
            'recent_logs': []
        }

@app.route('/')
def dashboard():
    """แสดง Dashboard หลัก"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def api_status():
    """API สำหรับดึงข้อมูลสถานะ"""
    return jsonify(get_status_data())

@app.route('/api/logs')
def api_logs():
    """API สำหรับดึง logs"""
    try:
        monitor_log = LOG_DIR / "server_monitor.log"
        if monitor_log.exists():
            with open(monitor_log, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-50:]  # Last 50 lines
            return jsonify({'logs': [log.strip() for log in logs]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'logs': []})

def main():
    """เริ่มต้น Dashboard"""
    print("🚀 Starting Mac Dashboard...")
    print("📊 VM Monitoring Dashboard")
    print(f"🌐 URL: http://localhost:5001")
    print("🔄 Auto-refresh every 30 seconds")
    print("📱 Mobile responsive design")
    print("")
    print("Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")

if __name__ == '__main__':
    main()