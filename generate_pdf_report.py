def get_details_template(self) -> str:
        """Enhanced VM details template with FIXED Storage column and filesystem details"""
        return """
        <div class="page-break"></div>
        <div class="details-page">
            <h1 class="page-title">Virtual Machine Inventory</h1>
            
            <h2 class="section-title">📋 Complete System Inventory</h2>
            
            <table class="vm-table">
                <thead>
                    <tr>
                        <th style="width: 4%;">#</th>
                        <th style="width: 20%;">VM Name</th>
                        <th style="width: 12%;">IP Address</th>
                        <th style="width: 8%;">CPU %</th>
                        <th style="width: 8%;">Memory %</th>
                        <th style="width: 18%;">Storage Details</th>
                        <th style="width: 10%;">Health</th>
                        <th style="width: 12%;">Status</th>
                        <th style="width: 8%;">Performance</th>
                    </tr>
                </thead>
                <tbody>
                    {% for vm in vm_data %}
                    <tr>
                        <td class="text-center">{{ loop.index }}</td>
                        <td class="font-bold">
                            {% if vm.name|length > 20 %}
                                {{ vm.name[:20] }}...
                            {% else %}
                                {{ vm.name }}
                            {% endif %}
                        </td>
                        <td>{{ vm.ip or vm.hostname or 'N/A' }}</td>
                        <td class="text-center">
                            {% set cpu_class = 'metric-high' if vm.cpu_load > 80 else 'metric-medium' if vm.cpu_load > 60 else 'metric-normal' %}
                            <span class="metric-value {{ cpu_class }}">{{ vm.cpu_load|round(1) }}%</span>
                        </td>
                        <td class="text-center">
                            {% set mem_class = 'metric-high' if vm.memory_used > 85 else 'metric-medium' if vm.memory_used > 70 else 'metric-normal' %}
                            <span class="metric-value {{ mem_class }}">{{ vm.memory_used|round(1) }}%</span>
                        </td>
                        <td class="text-center">
                            {% set disk_class = 'metric-high' if vm.disk_used > 85 else 'metric-medium' if vm.disk_used > 70 else 'metric-normal' %}
                            <div>
                                <span class="metric-value {{ disk_class }}">{{ vm.disk_used|round(1) }}%</span>
                                {% if vm.storage_performance and vm.storage_performance.total_gb > 0 %}
                                <div class="storage-info">
                                    {{ vm.storage_performance.used_gb|round(1) }}/{{ vm.storage_performance.total_gb|round(1) }} GB
                                </div>
                                {% if vm.storage_performance.filesystems %}
                                <div class="storage-info">
                                    {{ vm.storage_performance.filesystems|length }} filesystem(s)
                                </div>
                                {% endif %}
                                {% endif %}
                            </div>
                        </td>
                        <td class="text-center">
                            {{ vm.performance_rating|performance_icon }} {{ vm.health_score or 0 }}
                        </td>
                        <td class="text-center">
                            {% if vm.is_online %}
                                <span class="status-badge status-online">🟢 Online</span>
                            {% else %}
                                <span class="status-badge status-offline">🔴 Offline</span>
                            {% endif %}
                        </td>
                        <td class="text-center">
                            <small>{{ vm.performance_rating or 'Unknown' }}</small>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <!-- ENHANCED Performance Analysis WITH STORAGE -->
            <h2 class="section-title">📈 Performance Analysis</h2>
            
            {% if summary.performance %}
            <div class="performance-grid">
                <div class="performance-card">
                    <h4 style="color: #27ae60;">💻 CPU Analysis</h4>
                    <table style="width: 100%; font-size: 10px;">
                        <tr><td>Peak Usage:</td><td class="text-right font-bold">{{ summary.performance.peak_cpu|round(1) }}%</td></tr>
                        <tr><td>Average:</td><td class="text-right">{{ summary.performance.avg_cpu|round(1) }}%</td></tr>
                        <tr><td>High Usage VMs:</td><td class="text-right" style="color: #e74c3c;">{{ (vm_data|selectattr('cpu_load', '>', 80)|list|length) }}</td></tr>
                    </table>
                </div>
                <div class="performance-card">
                    <h4 style="color: #e74c3c;">🧠 Memory Analysis</h4>
                    <table style="width: 100%; font-size: 10px;">
                        <tr><td>Peak Usage:</td><td class="text-right font-bold">{{ summary.performance.peak_memory|round(1) }}%</td></tr>
                        <tr><td>Average:</td><td class="text-right">{{ summary.performance.avg_memory|round(1) }}%</td></tr>
                        <tr><td>High Usage VMs:</td><td class="text-right" style="color: #e74c3c;">{{ (vm_data|selectattr('memory_used', '>', 85)|list|length) }}</td></tr>
                    </table>
                </div>
                <div class="performance-card">
                    <h4 style="color: #9b59b6;">💾 Storage Analysis</h4>
                    <table style="width: 100%; font-size: 10px;">
                        <tr><td>Peak Usage:</td><td class="text-right font-bold">{{ summary.performance.peak_disk|round(1) }}%</td></tr>
                        <tr><td>Average:</td><td class="text-right">{{ summary.performance.avg_disk|round(1) }}%</td></tr>
                        <tr><td>Space Warnings:</td><td class="text-right" style="color: #f39c12;">{{ summary.storage.warnings if summary.storage else 0 }}</td></tr>
                        <tr><td>Total Filesystems:</td><td class="text-right">{{ summary.storage.filesystems if summary.storage else 0 }}</td></tr>
                    </table>
                </div>
            </div>
            {% endif %}
            
            <!-- ENHANCED Storage Overview Section -->
            {% if summary.storage and summary.storage.total_gb > 0 %}
            <h2 class="section-title">💾 Storage Infrastructure Overview</h2>
            <div class="storage-grid">
                <div class="storage-card">
                    <div class="storage-value">{{ summary.storage.total_gb|round(1) }}</div>
                    <div class="storage-label">Total Storage (GB)</div>
                </div>
                <div class="storage-card">
                    <div class="storage-value">{{ summary.storage.used_gb|round(1) }}</div>
                    <div class="storage-label">Used Storage (GB)</div>
                </div>
                <div class="storage-card">
                    <div class="storage-value">{{ summary.storage.free_gb|round(1) }}</div>
                    <div class="storage-label">Free Storage (GB)</div>
                </div>
                <div class="storage-card">
                    <div class="storage-value" style="color: {{ summary.storage.usage_percent|storage_color }};">{{ summary.storage.usage_percent|round(1) }}%</div>
                    <div class="storage-label">Overall Usage</div>
                </div>
            </div>
            
            <!-- Top Storage Consumers -->
            {% set storage_vms = vm_data|selectattr('is_online')|selectattr('disk_used', '>', 0)|sort(attribute='disk_used', reverse=true) %}
            {% if storage_vms %}
            <h3 class="section-title">🔝 Top Storage Consumers</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                {% for vm in storage_vms[:10] %}
                <div class="storage-filesystem">
                    <div class="filesystem-path">{{ vm.name[:25] }}{% if vm.name|length > 25 %}...{% endif %}</div>
                    <div class="filesystem-usage">
                        <span>Usage: <strong style="color: {{ vm.disk_used|storage_color }};">{{ vm.disk_used|round(1) }}%</strong></span>
                        {% if vm.storage_performance and vm.storage_performance.total_gb > 0 %}
                        <span>{{ vm.storage_performance.used_gb|round(1) }}/{{ vm.storage_performance.total_gb|round(1) }} GB</span>
                        {% endif %}
                    </div>
                    {% if vm.storage_performance and vm.storage_performance.filesystems %}
                    <div style="font-size: 9px; color: #6c757d; margin-top: 3px;">
                        {{ vm.storage_performance.filesystems|length }} filesystem(s)
                        {% if vm.storage_performance.filesystems|length > 0 %}
                        - Main: {{ vm.storage_performance.filesystems[0].path }}
                        {% endif %}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            {% endif %}
            
            <!-- ENHANCED Recommendations with Storage -->
            <div class="recommendations">
                <h4>🔍 Key Recommendations</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <p><strong>High Priority Actions:</strong></p>
                        <ul>
                            {% set high_cpu_vms = vm_data|selectattr('cpu_load', '>', 80)|list %}
                            {% set high_mem_vms = vm_data|selectattr('memory_used', '>', 85)|list %}
                            {% set high_disk_vms = vm_data|selectattr('disk_used', '>', 85)|list %}
                            {% set critical_disk_vms = vm_data|selectattr('disk_used', '>', 90)|list %}
                            {% if high_cpu_vms %}
                            <li>Monitor {{ high_cpu_vms|length }} VMs with CPU usage > 80%</li>
                            {% endif %}
                            {% if high_mem_vms %}
                            <li>Review {{ high_mem_vms|length }} VMs with high memory usage (>85%)</li>
                            {% endif %}
                            {% if critical_disk_vms %}
                            <li><strong>URGENT:</strong> {{ critical_disk_vms|length }} VMs critically low on storage (>90%)</li>
                            {% elif high_disk_vms %}
                            <li>Plan storage expansion for {{ high_disk_vms|length }} VMs (>85% full)</li>
                            {% endif %}
                            {% if summary.offline > 0 %}
                            <li><strong>URGENT:</strong> Investigate {{ summary.offline }} offline systems</li>
                            {% endif %}
                            {% if summary.storage and summary.storage.warnings > 5 %}
                            <li>Consider implementing storage monitoring automation</li>
                            {% endif %}
                            {% if not (high_cpu_vms or high_mem_vms or high_disk_vms or summary.offline > 0) %}
                            <li>✅ No immediate high-priority actions required</li>
                            {% endif %}
                        </ul>
                    </div>
                    <div>
                        <p><strong>Storage & Optimization:</strong></p>
                        <ul>
                            {% if summary.storage and summary.storage.total_gb > 0 %}
                            <li>Total infrastructure storage: {{ summary.storage.total_gb|round(0) }} GB</li>
                            <li>Current utilization: {{ summary.storage.usage_percent|round(1) }}%</li>
                            {% if summary.storage.usage_percent > 70 %}
                            <li>⚠️ Consider planning storage expansion</li>
                            {% endif %}
                            {% endif %}
                            <li>Implement log rotation and cleanup policies</li>
                            <li>Set up automated storage alerts at 80% and 90%</li>
                            <li>Consider distributed storage solutions for growth</li>
                            <li>Review backup retention policies to free space</li>
                            <li>Schedule quarterly capacity planning reviews</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="report-footer">
                <p>Generated by Enhanced VM Infrastructure Monitoring System with Storage Analytics</p>
                <p>Report Date: {{ report_date }} | Total Systems: {{ summary.total }} | Status: {{ summary.system_status|title }}</p>
                {% if summary.storage and summary.storage.total_gb > 0 %}
                <p>Storage Infrastructure: {{ summary.storage.used_gb|round(1) }}/{{ summary.storage.total_gb|round(1) }} GB used ({{ summary.storage.usage_percent|round(1) }}%)</p>
                {% endif %}
            </div>
        </div>
        """#!/usr/bin/env python3
"""
Enhanced Professional VM Report Generator - WITH FIXED STORAGE SUPPORT
Comprehensive PDF generation with bilingual support and advanced layouts
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template
from weasyprint import HTML, CSS
import base64
from io import BytesIO

# Load configuration
try:
    from load_env import load_env_file, get_config_dict
    load_env_file()
    config = get_config_dict()
except ImportError:
    config = {
        'report': {
            'output_dir': 'output',
            'template_dir': 'templates',
            'static_dir': 'static',
            'company_logo': 'one_climate'
        }
    }


# Safe logger setup
logger = None

def get_logger():
    """Get logger instance safely"""
    global logger
    if logger is None:
        try:
            import logging
            logger = logging.getLogger(__name__)
        except:
            logger = None
    return logger

def safe_log_info(message):
    """Safe logging info"""
    try:
        log = get_logger()
        if log:
            log.info(message)
        else:
            print(f"INFO: {message}")
    except:
        print(f"INFO: {message}")

def safe_log_error(message):
    """Safe logging error"""
    try:
        log = get_logger()
        if log:
            log.error(message)
        else:
            print(f"ERROR: {message}")
    except:
        print(f"ERROR: {message}")

def safe_log_warning(message):
    """Safe logging warning"""
    try:
        log = get_logger()
        if log:
            log.warning(message)
        else:
            print(f"WARNING: {message}")
    except:
        print(f"WARNING: {message}")


class EnhancedReportGenerator:
    """Enhanced professional report generator with comprehensive features"""
    
    def __init__(self, template_dir: str = None, output_dir: str = None, static_dir: str = None):
        self.template_dir = Path(template_dir or config['report']['template_dir'])
        self.output_dir = Path(output_dir or config['report']['output_dir'])
        self.static_dir = Path(static_dir or config['report']['static_dir'])
        
        # Create directories
        self.setup_directories()
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader([self.template_dir, Path(__file__).parent]),
            autoescape=True
        )
        
        # Add custom filters - FIXED
        self.jinja_env.filters['datetime'] = self._format_datetime
        self.jinja_env.filters['percentage'] = self._format_percentage
        self.jinja_env.filters['round'] = self._round_number
        self.jinja_env.filters['status_color'] = self._get_status_color
        self.jinja_env.filters['performance_icon'] = self._get_performance_icon
        self.jinja_env.filters['storage_color'] = self._get_storage_color  # NEW
        self.jinja_env.filters['format_gb'] = self._format_gb  # NEW
    
    def setup_directories(self):
        """Create necessary directories"""
        for directory in [self.template_dir, self.output_dir, self.static_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create archive directory
        (self.output_dir / 'archive').mkdir(exist_ok=True)
    
    def _format_datetime(self, dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format datetime for templates"""
        if isinstance(dt, str):
            return dt
        return dt.strftime(format_str)
    
    def _format_percentage(self, value: float, decimals: int = 1) -> str:
        """Format percentage values - FIXED"""
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return "0.0%"
    
    def _round_number(self, value: float, decimals: int = 1) -> float:
        """Round number to specified decimals"""
        try:
            return round(float(value), decimals)
        except (ValueError, TypeError):
            return 0.0
    
    def _format_gb(self, value: float, decimals: int = 1) -> str:
        """Format GB values - NEW"""
        try:
            return f"{float(value):.{decimals}f} GB"
        except (ValueError, TypeError):
            return "0.0 GB"
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status indicators"""
        colors = {
            'online': '#27ae60',
            'offline': '#e74c3c',
            'ok': '#27ae60',
            'warning': '#f39c12',
            'critical': '#e74c3c',
            'excellent': '#27ae60',
            'good': '#2ecc71',
            'fair': '#f39c12',
            'poor': '#e67e22',
            'unknown': '#95a5a6'
        }
        return colors.get(status.lower(), '#95a5a6')
    
    def _get_storage_color(self, usage: float) -> str:
        """Get color for storage usage - NEW"""
        try:
            usage_val = float(usage)
            if usage_val > 90:
                return '#e74c3c'  # Critical red
            elif usage_val > 80:
                return '#f39c12'  # Warning orange
            elif usage_val > 70:
                return '#f1c40f'  # Caution yellow
            else:
                return '#27ae60'  # Normal green
        except (ValueError, TypeError):
            return '#95a5a6'  # Gray for unknown
    
    def _get_performance_icon(self, rating: str) -> str:
        """Get icon for performance ratings"""
        icons = {
            'excellent': '🟢',
            'good': '🟡',
            'fair': '🟠',
            'poor': '🔴',
            'critical': '🚨',
            'offline': '⚫',
            'unknown': '❓'
        }
        return icons.get(rating.lower(), '❓')
    
    def get_company_logo(self, logo_type: str = 'one_climate') -> str:
        """Get One Climate logo from file or SVG fallback"""

        from pathlib import Path
        import base64

        # Try to use uploaded logo files first
        logo_files = [
            'static/assets/logo_oneclimate.jpg',
            'static/logo_oneclimate.jpg',
            'static/assets/logo_oneclimate.png',
            'static/logo_oneclimate.png',
            'static/assets/one_climate_logo.jpg',
            'static/one_climate_logo.jpg'
        ]

        for logo_file in logo_files:
            logo_path = Path(logo_file)
            if logo_path.exists():
                try:
                    with open(logo_path, 'rb') as f:
                        logo_data = base64.b64encode(f.read()).decode()

                    # Determine MIME type
                    if logo_path.suffix.lower() in ['.jpg', '.jpeg']:
                        mime_type = 'image/jpeg'
                    elif logo_path.suffix.lower() == '.png':
                        mime_type = 'image/png'
                    else:
                        continue

                    return (
                        f'<img src="data:{mime_type};base64,{logo_data}" '
                        'style="width: 280px; height: 87px; object-fit: contain; '
                        'filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));" '
                        'alt="One Climate Logo">'
                    )

                except Exception as e:
                    print(f"⚠️ Could not load logo from {logo_file}: {e}")
                    continue

        # Fallback to enhanced SVG version if no file found
        print("ℹ️ Using SVG fallback logo")
        return '''
        <svg viewBox="0 0 320 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <filter id="logoShadow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="2" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.4"/>
                </filter>
                <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>
            <!-- Logo Background -->
            <rect x="10" y="10" width="80" height="80" rx="40" fill="rgba(255,255,255,0.2)" filter="url(#logoShadow)"/>
            <!-- Enhanced Circular Logo -->
            <g transform="translate(50, 50)" filter="url(#glow)">
                <path d="M 0 -30 A 30 30 0 0 1 21 -21" stroke="#2ECC71" stroke-width="5" fill="none" stroke-linecap="round"/>
                <path d="M 21 -21 A 30 30 0 0 1 30 0" stroke="#3498DB" stroke-width="5" fill="none" stroke-linecap="round"/>
                <path d="M 30 0 A 30 30 0 0 1 21 21" stroke="#9B59B6" stroke-width="5" fill="none" stroke-linecap="round"/>
                <path d="M 21 21 A 30 30 0 0 1 0 30" stroke="#E74C3C" stroke-width="5" fill="none" stroke-linecap="round"/>
                <path d="M 0 30 A 30 30 0 0 1 -21 21" stroke="#F39C12" stroke-width="5" fill="none" stroke-linecap="round"/>
                <path d="M -21 21 A 30 30 0 0 1 -30 0" stroke="#1ABC9C" stroke-width="5" fill="none" stroke-linecap="round"/>
                <path d="M -30 0 A 30 30 0 0 1 -21 -21" stroke="#3498DB" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.8"/>
                <path d="M -21 -21 A 30 30 0 0 1 0 -30" stroke="#2ECC71" stroke-width="5" fill="none" stroke-linecap="round"/>
                <!-- Center leaf -->
                <circle cx="0" cy="0" r="12" fill="rgba(46, 204, 113, 0.3)"/>
                <path d="M -6 -3 Q 0 -9 6 -3 Q 3 3 0 6 Q -3 3 -6 -3" fill="white"/>
            </g>
            <!-- Company Name -->
            <text x="120" y="35" font-family="'Helvetica Neue', Arial, sans-serif" font-size="32" font-weight="300" fill="white" filter="url(#logoShadow)">One</text>
            <text x="120" y="70" font-family="'Helvetica Neue', Arial, sans-serif" font-size="32" font-weight="300" fill="white" filter="url(#logoShadow)">Climate</text>
            <text x="120" y="87" font-family="Arial, sans-serif" font-size="12" fill="rgba(255,255,255,0.9)" font-weight="500">MONITORING SOLUTIONS</text>
        </svg>
        '''
    
    def get_enhanced_css(self) -> str:
        """Get enhanced CSS with One Climate professional branding"""
        return """
        @page {
            size: A4;
            margin: 20mm;
            @top-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #666;
                font-family: Arial, sans-serif;
            }
            @bottom-left {
                content: "Generated: " string(report-date);
                font-size: 10px;
                color: #666;
                font-family: Arial, sans-serif;
            }
            @bottom-right {
                content: "One Climate VM Infrastructure Report";
                font-size: 10px;
                color: #666;
                font-family: Arial, sans-serif;
            }
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Helvetica Neue', Arial, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            font-size: 11px;
        }

        .page-break {
            page-break-before: always;
        }

        /* Professional One Climate Cover Page */
        .cover-page {
            height: 100vh;
            margin: -20mm;
            padding: 0;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 25%, #3498db 50%, #2ecc71 75%, #27ae60 100%);
            color: white;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }

        .cover-page::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 20%, rgba(255,255,255,0.1) 0%, transparent 40%),
                radial-gradient(circle at 80% 80%, rgba(255,255,255,0.05) 0%, transparent 40%);
        }

        .cover-header {
            padding: 60px 80px 20px 80px;
            position: relative;
            z-index: 2;
        }

        .cover-logo {
            width: 280px;
            height: 87px;
            margin-bottom: 20px;
        }

        .cover-badge {
            background: rgba(255,255,255,0.25);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.3);
            display: inline-block;
        }

        .cover-content {
            flex-grow: 1;
            padding: 60px 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            z-index: 2;
        }

        .cover-title {
            font-size: 52px;
            font-weight: 200;
            line-height: 1.1;
            margin-bottom: 30px;
            text-shadow: 0 3px 6px rgba(0,0,0,0.3);
        }

        .title-highlight {
            font-weight: 600;
            background: linear-gradient(45deg, #2ecc71, #3498db, #9b59b6);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .cover-subtitle {
            font-size: 24px;
            font-weight: 300;
            margin-bottom: 50px;
            line-height: 1.4;
            opacity: 0.95;
        }

        .subtitle-detail {
            font-size: 18px;
            opacity: 0.8;
        }

        .cover-info {
            display: flex;
            align-items: center;
            gap: 40px;
            flex-wrap: wrap;
        }

        .cover-date {
            background: rgba(255,255,255,0.2);
            padding: 20px 35px;
            border-radius: 35px;
            font-size: 20px;
            font-weight: 500;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        }

        .cover-stats {
            display: flex;
            gap: 25px;
        }

        .stat-box {
            text-align: center;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .stat-number {
            font-size: 28px;
            font-weight: 700;
            display: block;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.9;
        }

        .cover-footer {
            padding: 40px 80px 60px 80px;
            display: flex;
            justify-content: space-between;
            align-items: end;
            position: relative;
            z-index: 2;
            background: linear-gradient(0deg, rgba(0,0,0,0.2) 0%, transparent 100%);
        }

        .footer-left {
            color: rgba(255,255,255,0.9);
        }

        .department {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .company {
            font-size: 14px;
            opacity: 0.8;
        }

        .confidential {
            background: rgba(231,76,60,0.25);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid rgba(231,76,60,0.4);
            backdrop-filter: blur(15px);
        }

        /* Summary Page Styles */
        .summary-page {
            padding: 20px 0;
        }

        .page-title {
            font-size: 28px;
            font-weight: 300;
            color: #2c3e50;
            border-bottom: 4px solid #2ecc71;
            padding-bottom: 12px;
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 20px;
            font-weight: 500;
            color: #2c3e50;
            margin: 25px 0 15px 0;
            border-bottom: 2px solid #2ecc71;
            padding-bottom: 8px;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 25px 0;
        }

        .kpi-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #c3e6cb;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #2ecc71;
            box-shadow: 0 4px 12px rgba(46, 204, 113, 0.1);
        }

        .kpi-card.online { border-left-color: #2ecc71; }
        .kpi-card.offline { border-left-color: #e74c3c; }
        .kpi-card.warning { border-left-color: #f39c12; }
        .kpi-card.critical { border-left-color: #e74c3c; }
        .kpi-card.storage { border-left-color: #9b59b6; }

        .kpi-number {
            font-size: 32px;
            font-weight: 300;
            margin-bottom: 8px;
        }

        .kpi-number.online { color: #2ecc71; }
        .kpi-number.offline { color: #e74c3c; }
        .kpi-number.warning { color: #f39c12; }
        .kpi-number.critical { color: #e74c3c; }
        .kpi-number.storage { color: #9b59b6; }

        .kpi-label {
            font-size: 12px;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .kpi-percentage {
            font-size: 14px;
            font-weight: 500;
            margin-top: 5px;
        }

        .chart-container {
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: rgba(46, 204, 113, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(46, 204, 113, 0.2);
        }

        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }

        .performance-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
        }

        .performance-card {
            background: white;
            border: 1px solid rgba(46, 204, 113, 0.3);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(46, 204, 113, 0.1);
        }

        .performance-card h4 {
            margin: 0 0 12px 0;
            font-size: 14px;
            font-weight: 500;
        }

        .performance-value {
            font-size: 24px;
            font-weight: 300;
            margin-bottom: 5px;
            color: #2ecc71;
        }

        .performance-detail {
            font-size: 11px;
            color: #6c757d;
        }

        /* Enhanced Storage Grid */
        .storage-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }

        .storage-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #d6baed;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #9b59b6;
            box-shadow: 0 4px 12px rgba(155, 89, 182, 0.1);
        }

        .storage-value {
            font-size: 24px;
            font-weight: 300;
            margin-bottom: 8px;
            color: #9b59b6;
        }

        .storage-label {
            font-size: 11px;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .vm-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(46, 204, 113, 0.1);
            font-size: 10px;
        }

        .vm-table th {
            background: linear-gradient(135deg, #2ecc71 0%, #3498db 100%);
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 500;
            font-size: 11px;
        }

        .vm-table td {
            padding: 10px 8px;
            border-bottom: 1px solid rgba(46, 204, 113, 0.1);
            vertical-align: middle;
        }

        .vm-table tr:nth-child(even) {
            background: rgba(46, 204, 113, 0.03);
        }

        .vm-table tr:hover {
            background: rgba(46, 204, 113, 0.08);
        }

        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 9px;
            font-weight: 500;
            text-transform: uppercase;
        }

        .status-online {
            background: rgba(46, 204, 113, 0.2);
            color: #155724;
            border: 1px solid #2ecc71;
        }

        .status-offline {
            background: rgba(231, 76, 60, 0.2);
            color: #721c24;
            border: 1px solid #e74c3c;
        }

        .metric-value {
            font-weight: 500;
        }

        .metric-high { color: #e74c3c; }
        .metric-medium { color: #f39c12; }
        .metric-normal { color: #2ecc71; }

        /* Storage-specific styles */
        .storage-info {
            font-size: 9px;
            color: #6c757d;
            margin-top: 2px;
        }

        .storage-filesystem {
            background: rgba(155, 89, 182, 0.1);
            padding: 8px;
            margin: 5px 0;
            border-radius: 6px;
            border-left: 3px solid #9b59b6;
        }

        .filesystem-path {
            font-weight: 600;
            color: #2c3e50;
            font-size: 11px;
        }

        .filesystem-usage {
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #6c757d;
            margin-top: 3px;
        }

        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid;
        }

        .alert-success {
            background: rgba(46, 204, 113, 0.1);
            border-color: #2ecc71;
            color: #155724;
        }

        .alert-warning {
            background: rgba(243, 156, 18, 0.1);
            border-color: #f39c12;
            color: #856404;
        }

        .alert-danger {
            background: rgba(231, 76, 60, 0.1);
            border-color: #e74c3c;
            color: #721c24;
        }

        .recommendations {
            background: linear-gradient(135deg, rgba(46, 204, 113, 0.1) 0%, rgba(52, 152, 219, 0.05) 100%);
            border: 1px solid #2ecc71;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }

        .recommendations h4 {
            color: #2ecc71;
            margin-bottom: 15px;
            font-size: 16px;
            font-weight: 500;
        }

        .recommendations ul {
            margin: 10px 0 10px 20px;
        }

        .recommendations li {
            margin: 5px 0;
            font-size: 11px;
            color: #2c3e50;
        }

        .report-footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid rgba(46, 204, 113, 0.3);
            text-align: center;
            color: #6c757d;
            font-size: 10px;
        }

        /* Utility Classes */
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .font-bold { font-weight: 600; }
        .font-light { font-weight: 300; }
        .text-muted { color: #6c757d; }
        .text-primary { color: #2ecc71; }
        .text-storage { color: #9b59b6; }
        .mb-20 { margin-bottom: 20px; }
        .mt-20 { margin-top: 20px; }

        /* Responsive adjustments */
        @media print {
            .cover-page {
                page-break-after: always;
            }
        }
        """
