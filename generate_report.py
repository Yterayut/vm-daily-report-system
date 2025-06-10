#!/usr/bin/env python3
"""
Enhanced Professional VM Report Generator - FIXED FILTERS
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
            'company_logo': 'tech_corp'
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
        import os

        # Get absolute path to project directory
        project_dir = Path(__file__).parent.absolute()
        
        # Try to use uploaded logo files first with absolute paths
        logo_files = [
            project_dir / 'static/assets/company_logo.jpg',
            project_dir / 'static/company_logo.jpg',
            project_dir / 'static/assets/company_logo.png',
            project_dir / 'static/company_logo.png',
            project_dir / 'static/assets/logo.jpg',
            project_dir / 'static/logo.jpg'
        ]

        for logo_path in logo_files:
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

                    safe_log_info(f"✅ Using logo from: {logo_path}")
                    return (
                        f'<img src="data:{mime_type};base64,{logo_data}" '
                        'style="width: 280px; height: 87px; object-fit: contain; '
                        'filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));" '
                        'alt="One Climate Logo">'
                    )

                except Exception as e:
                    safe_log_error(f"⚠️ Could not load logo from {logo_path}: {e}")
                    continue

        # Fallback to enhanced SVG version if no file found
        safe_log_warning("ℹ️ No logo file found, using SVG fallback")
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

        .kpi-number {
            font-size: 32px;
            font-weight: 300;
            margin-bottom: 8px;
        }

        .kpi-number.online { color: #2ecc71; }
        .kpi-number.offline { color: #e74c3c; }
        .kpi-number.warning { color: #f39c12; }
        .kpi-number.critical { color: #e74c3c; }

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
            background: #27ae60;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 8pt;
            font-weight: bold;
        }

        .status-offline {
            background: #e74c3c;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 8pt;
            font-weight: bold;
        }

        /* Health Indicators */
        .health-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
            vertical-align: middle;
        }
        
        .health-excellent { background: #27ae60; }
        .health-good { background: #f39c12; }
        .health-poor { background: #e74c3c; }

        .metric-value {
            font-weight: 500;
        }

        .metric-high { color: #e74c3c; }
        .metric-medium { color: #f39c12; }
        .metric-normal { color: #2ecc71; }

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
        .mb-20 { margin-bottom: 20px; }
        .mt-20 { margin-top: 20px; }

        /* Responsive adjustments */
        @media print {
            .cover-page {
                page-break-after: always;
            }
        }
        """


    def get_cover_template(self) -> str:
        """Professional One Climate cover page"""
        return """
        <div class="cover-page">
            <!-- Header Section -->
            <div class="cover-header">
                <div class="cover-logo">{{ company_logo|safe }}</div>
                <div class="cover-badge">Infrastructure Daily Report</div>
            </div>
            
            <!-- Main Content -->
            <div class="cover-content">
                <h1 class="cover-title">
                    Virtual Machine<br>
                    <span class="title-highlight">Infrastructure Report</span>
                </h1>
                
                <div class="cover-subtitle">
                    Comprehensive Operations & Performance Analysis<br>
                    <span class="subtitle-detail">Real-time Monitoring • System Health • Performance Metrics</span>
                </div>
                
                <div class="cover-info">
                    <div class="cover-date">{{ report_date }}</div>
                    <div class="cover-stats">
                        <div class="stat-box">
                            <div class="stat-number">{{ summary.total or '0' }}</div>
                            <div class="stat-label">Total Systems</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{{ summary.online or '0' }}</div>
                            <div class="stat-label">Online</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{{ ((summary.online or 0) / (summary.total or 1) * 100)|round(1) }}%</div>
                            <div class="stat-label">Uptime</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="cover-footer">
                <div class="footer-left">
                    <div class="department">IT Infrastructure Department</div>
                    <div class="company">One Climate Solutions</div>
                </div>
                <div class="footer-right">
                    <div class="confidential">Confidential - Internal Use Only</div>
                </div>
            </div>
        </div>
        """
    
    def get_summary_template(self) -> str:
        """Enhanced executive summary template - FIXED FILTERS"""
        return """
        <div class="summary-page">
            <h1 class="page-title">Executive Summary</h1>
            
            <!-- KPI Overview -->
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-number">{{ summary.total }}</div>
                    <div class="kpi-label">Total Virtual Machines</div>
                </div>
                <div class="kpi-card online">
                    <div class="kpi-number online">{{ summary.online }}</div>
                    <div class="kpi-label">Online Systems</div>
                    <div class="kpi-percentage online">{{ summary.online_percent|round(1) }}%</div>
                </div>
                <div class="kpi-card offline">
                    <div class="kpi-number offline">{{ summary.offline }}</div>
                    <div class="kpi-label">Offline Systems</div>
                    <div class="kpi-percentage offline">{{ summary.offline_percent|round(1) }}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-number">{{ ((summary.online / summary.total * 100) if summary.total > 0 else 100)|round(1) }}%</div>
                    <div class="kpi-label">System Uptime</div>
                </div>
            </div>
            
 
            
            <!-- Performance Metrics -->
            {% if summary.performance %}
            <h2 class="section-title">Performance Overview</h2>
            <div class="performance-grid">
                <div class="performance-card">
                    <h4 style="color: #3498db;">💻 CPU Performance</h4>
                    <div class="performance-value" style="color: #3498db;">{{ summary.performance.avg_cpu|round(1) }}%</div>
                    <div class="performance-detail">Average Usage</div>
                    <div class="performance-detail">Peak: {{ summary.performance.peak_cpu|round(1) }}%</div>
                </div>
                <div class="performance-card">
                    <h4 style="color: #e74c3c;">🧠 Memory Performance</h4>
                    <div class="performance-value" style="color: #e74c3c;">{{ summary.performance.avg_memory|round(1) }}%</div>
                    <div class="performance-detail">Average Usage</div>
                    <div class="performance-detail">Peak: {{ summary.performance.peak_memory|round(1) }}%</div>
                </div>
                <div class="performance-card">
                    <h4 style="color: #9b59b6;">💽 Storage Performance</h4>
                    <div class="performance-value" style="color: #9b59b6;">{{ summary.performance.avg_disk|round(1) }}%</div>
                    <div class="performance-detail">Average Usage</div>
                    <div class="performance-detail">Peak: {{ summary.performance.peak_disk|round(1) }}%</div>
                </div>
            </div>
            {% endif %}
            
            <!-- Alert Summary -->
            <h2 class="section-title">Alert Status</h2>
            <div class="kpi-grid">
                <div class="kpi-card critical">
                    <div class="kpi-number critical">{{ summary.alerts.critical }}</div>
                    <div class="kpi-label">Critical Alerts</div>
                </div>
                <div class="kpi-card warning">
                    <div class="kpi-number warning">{{ summary.alerts.warning }}</div>
                    <div class="kpi-label">Warning Alerts</div>
                </div>
                <div class="kpi-card online">
                    <div class="kpi-number online">{{ summary.alerts.ok }}</div>
                    <div class="kpi-label">Healthy Systems</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-number">{{ summary.system_status|title }}</div>
                    <div class="kpi-label">Overall Status</div>
                </div>
            </div>
            
            <!-- System Health Alert -->
            {% if summary.offline > 0 or summary.alerts.critical > 0 %}
            <div class="alert alert-danger">
                <strong>⚠️ Attention Required:</strong>
                {% if summary.offline > 0 %}
                {{ summary.offline }} virtual machine(s) are currently offline.
                {% endif %}
                {% if summary.alerts.critical > 0 %}
                {{ summary.alerts.critical }} system(s) showing critical resource usage.
                {% endif %}
                Please review the detailed analysis for specific recommendations.
            </div>
            {% elif summary.alerts.warning > 0 %}
            <div class="alert alert-warning">
                <strong>⚠️ Monitoring Required:</strong>
                {{ summary.alerts.warning }} system(s) showing warning-level resource usage.
                Consider proactive maintenance to prevent issues.
            </div>
            {% else %}
            <div class="alert alert-success">
                <strong>✅ All Systems Operational:</strong>
                All virtual machines are online and performing within normal parameters.
                System health is excellent with no immediate concerns.
            </div>
            {% endif %}
        </div>
        """
    
    def get_details_template(self) -> str:
        """Enhanced VM details template - FIXED FILTERS"""
        return """
        <div class="page-break"></div>
        <div class="details-page">
            <h1 class="page-title">Virtual Machine Inventory</h1>
            
            <h2 class="section-title">📋 Complete System Inventory</h2>
            
            <table class="vm-table">
                <thead>
                    <tr>
                        <th style="width: 5%;">#</th>
                        <th style="width: 25%;">VM Name</th>
                        <th style="width: 15%;">IP Address</th>
                        <th style="width: 10%;">CPU %</th>
                        <th style="width: 10%;">Memory %</th>
                        <th style="width: 10%;">Disk %</th>
                        <th style="width: 10%;">Health</th>
                        <th style="width: 15%;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for vm in vm_data %}
                    <tr>
                        <td class="text-center">{{ loop.index }}</td>
                        <td class="font-bold">
                            {% if vm.name|length > 25 %}
                                {{ vm.name[:25] }}...
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
                            <span class="metric-value {{ disk_class }}">{{ vm.disk_used|round(1) }}%</span>
                        </td>
                        <td class="text-center">
                            {% set health_class = 'health-excellent' if vm.health_score >= 90 else 'health-good' if vm.health_score >= 70 else 'health-poor' %}
                            <span class="health-indicator {{ health_class }}"></span>{{ vm.health_score or 0 }}
                        </td>
                        <td class="text-center">
                            {% if vm.is_online %}
                                <span class="status-online">ONLINE</span>
                            {% else %}
                                <span class="status-offline">OFFLINE</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <!-- Performance Analysis -->
            <h2 class="section-title">📈 Performance Analysis</h2>
            
            {% if summary.performance %}
            <div class="performance-grid">
                <div class="performance-card">
                    <h4 style="color: #27ae60;">CPU Analysis</h4>
                    <table style="width: 100%; font-size: 10px;">
                        <tr><td>Peak Usage:</td><td class="text-right font-bold">{{ summary.performance.peak_cpu|round(1) }}%</td></tr>
                        <tr><td>Average:</td><td class="text-right">{{ summary.performance.avg_cpu|round(1) }}%</td></tr>
                        <tr><td>High Usage VMs:</td><td class="text-right" style="color: #e74c3c;">{{ (vm_data|selectattr('cpu_load', '>', 80)|list|length) }}</td></tr>
                    </table>
                </div>
                <div class="performance-card">
                    <h4 style="color: #e74c3c;">Memory Analysis</h4>
                    <table style="width: 100%; font-size: 10px;">
                        <tr><td>Peak Usage:</td><td class="text-right font-bold">{{ summary.performance.peak_memory|round(1) }}%</td></tr>
                        <tr><td>Average:</td><td class="text-right">{{ summary.performance.avg_memory|round(1) }}%</td></tr>
                        <tr><td>High Usage VMs:</td><td class="text-right" style="color: #e74c3c;">{{ (vm_data|selectattr('memory_used', '>', 85)|list|length) }}</td></tr>
                    </table>
                </div>
                <div class="performance-card">
                    <h4 style="color: #9b59b6;">Storage Analysis</h4>
                    <table style="width: 100%; font-size: 10px;">
                        <tr><td>Peak Usage:</td><td class="text-right font-bold">{{ summary.performance.peak_disk|round(1) }}%</td></tr>
                        <tr><td>Average:</td><td class="text-right">{{ summary.performance.avg_disk|round(1) }}%</td></tr>
                        <tr><td>Space Warnings:</td><td class="text-right" style="color: #f39c12;">{{ (vm_data|selectattr('disk_used', '>', 85)|list|length) }}</td></tr>
                    </table>
                </div>
            </div>
            {% endif %}
            
            <!-- Recommendations -->
            <div class="recommendations">
                <h4>🔍 Key Recommendations</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <p><strong>High Priority Actions:</strong></p>
                        <ul>
                            {% set high_cpu_vms = vm_data|selectattr('cpu_load', '>', 80)|list %}
                            {% set high_mem_vms = vm_data|selectattr('memory_used', '>', 85)|list %}
                            {% set high_disk_vms = vm_data|selectattr('disk_used', '>', 85)|list %}
                            {% if high_cpu_vms %}
                            <li>Monitor {{ high_cpu_vms|length }} VMs with CPU usage > 80%</li>
                            {% endif %}
                            {% if high_mem_vms %}
                            <li>Review {{ high_mem_vms|length }} VMs with high memory usage</li>
                            {% endif %}
                            {% if high_disk_vms %}
                            <li>Plan disk expansion for {{ high_disk_vms|length }} VMs</li>
                            {% endif %}
                            {% if summary.offline > 0 %}
                            <li>Investigate {{ summary.offline }} offline systems immediately</li>
                            {% endif %}
                            {% if not (high_cpu_vms or high_mem_vms or high_disk_vms or summary.offline > 0) %}
                            <li>No immediate high-priority actions required</li>
                            {% endif %}
                        </ul>
                    </div>
                    <div>
                        <p><strong>Optimization Opportunities:</strong></p>
                        <ul>
                            <li>Consider load balancing for high-usage VMs</li>
                            <li>Implement automated scaling policies</li>
                            <li>Schedule maintenance during low-usage periods</li>
                            <li>Review resource allocations quarterly</li>
                            <li>Set up proactive monitoring alerts</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="report-footer">
                <p>Generated by Enhanced VM Infrastructure Monitoring System</p>
                <p>Report Date: {{ report_date }} | Total Systems: {{ summary.total }} | Status: {{ summary.system_status|title }}</p>
            </div>
        </div>
        """
    
    def embed_chart_as_base64(self, chart_path: Path) -> str:
        """Convert chart to base64 for PDF embedding"""
        try:
            if chart_path.exists():
                with open(chart_path, 'rb') as f:
                    chart_data = base64.b64encode(f.read()).decode()
                return f'<img src="data:image/png;base64,{chart_data}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;" alt="Chart">'
            else:
                return '<div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px;">📊 Chart not available</div>'
        except Exception as e:
            logger.warning(f"Could not embed chart {chart_path}: {e}")
            return '<div style="background: #fff3cd; padding: 20px; text-align: center; border-radius: 8px;">⚠️ Chart loading failed</div>'
    
    def generate_comprehensive_report(
        self, 
        vm_data: List[Dict[str, Any]], 
        summary: Dict[str, Any],
        company_logo: str = 'tech_corp',
        output_filename: str = None
    ) -> Optional[str]:
        """Generate comprehensive PDF report with all enhancements"""
        
        try:
            if output_filename is None:
                today_str = datetime.now().strftime("%Y-%m-%d")
                output_filename = f"vm_infrastructure_report_{today_str}.pdf"
            
            output_path = self.output_dir / output_filename
            
            safe_log_info(f"🎨 Generating comprehensive PDF report: {output_filename}")
            
            # Prepare template data
            template_data = {
                'company_logo': self.get_company_logo(company_logo),
                'report_date': datetime.now().strftime("%B %d, %Y"),
                'vm_data': vm_data or [],
                'summary': summary,
                'status_chart': self.embed_chart_as_base64(self.static_dir / 'vm_status_chart.png'),
                'performance_chart': self.embed_chart_as_base64(self.static_dir / 'performance_distribution.png'),
                'resource_chart': self.embed_chart_as_base64(self.static_dir / 'resource_overview.png'),
                'alert_chart': self.embed_chart_as_base64(self.static_dir / 'alert_status.png')
            }
            
            # Render templates using Jinja2 environment with custom filters
            cover_html = self.jinja_env.from_string(self.get_cover_template()).render(**template_data)
            summary_html = self.jinja_env.from_string(self.get_summary_template()).render(**template_data)
            details_html = self.jinja_env.from_string(self.get_details_template()).render(**template_data)
            
            # Combine all content
            full_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>VM Infrastructure Report - {template_data['report_date']}</title>
                <style>
                    {self.get_enhanced_css()}
                </style>
            </head>
            <body>
                {cover_html}
                <div class="page-break"></div>
                {summary_html}
                {details_html}
            </body>
            </html>
            """
            
            # Generate PDF
            html_doc = HTML(string=full_html, base_url=str(Path.cwd()))
            css_doc = CSS(string=self.get_enhanced_css())
            
            html_doc.write_pdf(
                target=str(output_path),
                stylesheets=[css_doc],
                optimize_size=('fonts', 'images'),
                presentational_hints=True
            )
            
            # Verify file creation
            if output_path.exists():
                file_size = output_path.stat().st_size
                safe_log_info(f"✅ PDF report generated successfully")
                safe_log_info(f"   Output: {output_path}")
                safe_log_info(f"   Size: {file_size:,} bytes")
                safe_log_info(f"   VMs: {len(vm_data)} systems")
                safe_log_info(f"   Status: {summary.get('system_status', 'unknown').title()}")
                
                return str(output_path)
            else:
                safe_log_error("❌ PDF file was not created")
                return None
                
        except Exception as e:
            safe_log_error(f"❌ PDF generation failed: {e}")
            logger.debug(f"Error details: {e.__class__.__name__}: {e}")
            return None

# Backward compatibility function
def main():
    """Main function for backward compatibility and testing"""
    try:
        # Import required modules for testing
        from fetch_zabbix_data import fetch_vm_data, calculate_enhanced_summary, generate_enhanced_charts
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        safe_log_info("🎨 Enhanced Report Generator - Testing Mode")
        safe_log_info("=" * 60)
        
        # Initialize generator
        generator = EnhancedReportGenerator()
        
        # Fetch VM data
        safe_log_info("📡 Fetching VM data...")
        vm_data = fetch_vm_data()
        
        if not vm_data:
            logger.warning("⚠️ No VM data available, using sample data")
            vm_data = []
        
        # Calculate summary
        safe_log_info("📊 Calculating summary...")
        summary = calculate_enhanced_summary(vm_data)
        
        # Generate charts
        safe_log_info("📈 Generating charts...")
        generate_enhanced_charts(vm_data, summary)
        
        # Generate report
        safe_log_info("📄 Generating PDF report...")
        report_path = generator.generate_comprehensive_report(vm_data, summary)
        
        if report_path:
            safe_log_info("✅ Report generation completed successfully!")
            safe_log_info(f"📁 Report saved: {report_path}")
            return vm_data, summary
        else:
            safe_log_error("❌ Report generation failed")
            return None, None
            
    except Exception as e:
        safe_log_error(f"❌ Error in main: {e}")
        return None, None

if __name__ == "__main__":
    main()
