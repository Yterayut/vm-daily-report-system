#!/usr/bin/env python3
"""
VM Infrastructure Report Templates - One Climate Style
Enhanced templates matching the provided PDF sample exactly
"""

def get_vm_cover_template():
    """Cover template for VM Infrastructure report - One Climate Style"""
    return """
    <div class="page cover-page">
        <!-- Header -->
        <div class="cover-header">
            <div class="cover-logo">{{ company_logo | safe }}</div>
            <div class="cover-badge">INFRASTRUCTURE DAILY REPORT</div>
        </div>
        
        <!-- Main Content -->
        <div class="cover-content">
            <!-- Main Title -->
            <div class="cover-title">
                <h1>Virtual Machine</h1>
                <h1 class="highlight">Infrastructure Report</h1>
            </div>
            
            <!-- Subtitle -->
            <div class="cover-subtitle">
                Comprehensive Operations & Performance Analysis
            </div>
            <div class="subtitle-features">
                Real-time Monitoring • System Health • Performance Metrics
            </div>
            
            <!-- Date -->
            <div class="cover-date">{{ report_date }}</div>
            
            <!-- Stats Cards - One Climate Style -->
            <div class="cover-stats">
                <div class="cover-section">
                    <div class="section-title">VM INFRASTRUCTURE</div>
                    <div class="section-stats">
                        <span class="stat-item">{{ summary.total }} Total</span>
                        <span class="stat-divider">|</span>
                        <span class="stat-item">{{ summary.online }} Online</span>
                        <span class="stat-divider">|</span>
                        <span class="stat-item">{{ summary.online_percent|round(1) }}% Uptime</span>
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
                <div class="confidential">CONFIDENTIAL - INTERNAL USE ONLY</div>
            </div>
        </div>
    </div>
    """

def get_vm_summary_template():
    """VM summary template - One Climate Style exactly matching the sample"""
    return """
    <div class="page summary-page">
        <div class="page-header">
            <h2>Executive Summary</h2>
        </div>
        
        <!-- VM Infrastructure Overview -->
        <div class="summary-section">
            <h3>🖥️ Virtual Machine Infrastructure</h3>
            
            <div class="metrics-grid">
                <div class="metric-card healthy">
                    <div class="metric-value">{{ summary.total }}</div>
                    <div class="metric-label">TOTAL<br>VIRTUAL<br>MACHINES</div>
                </div>
                
                <div class="metric-card {% if summary.online == summary.total %}healthy{% else %}warning{% endif %}">
                    <div class="metric-value">{{ summary.online }}</div>
                    <div class="metric-label">ONLINE<br>SYSTEMS</div>
                    <div class="metric-percentage">{{ summary.online_percent|round(1) }}%</div>
                </div>
                
                <div class="metric-card {% if summary.offline > 0 %}critical{% else %}healthy{% endif %}">
                    <div class="metric-value">{{ summary.offline }}</div>
                    <div class="metric-label">OFFLINE<br>SYSTEMS</div>
                    <div class="metric-percentage">{{ summary.offline_percent|round(1) }}%</div>
                </div>
                
                <div class="metric-card healthy">
                    <div class="metric-value">{{ summary.online_percent|round(1) }}%</div>
                    <div class="metric-label">SYSTEM<br>UPTIME</div>
                </div>
            </div>
        </div>
        
        <!-- Performance Overview -->
        <div class="summary-section">
            <h3>📊 Performance Overview</h3>
            
            <div class="performance-grid">
                <div class="perf-card">
                    <div class="perf-icon">💻</div>
                    <div class="perf-title">CPU<br>Performance</div>
                    <div class="perf-value">{{ summary.performance.avg_cpu|round(1) }}%</div>
                    <div class="perf-detail">Average Usage<br>Peak: {{ summary.performance.peak_cpu|round(1) }}%</div>
                </div>
                
                <div class="perf-card">
                    <div class="perf-icon">🧠</div>
                    <div class="perf-title">Memory<br>Performance</div>
                    <div class="perf-value">{{ summary.performance.avg_memory|round(1) }}%</div>
                    <div class="perf-detail">Average Usage<br>Peak: {{ summary.performance.peak_memory|round(1) }}%</div>
                </div>
                
                <div class="perf-card">
                    <div class="perf-icon">💾</div>
                    <div class="perf-title">Storage<br>Performance</div>
                    <div class="perf-value">{{ summary.performance.avg_disk|round(1) }}%</div>
                    <div class="perf-detail">Average Usage<br>Peak: {{ summary.performance.peak_disk|round(1) }}%</div>
                </div>
            </div>
        </div>
        
        <!-- Alert Status -->
        <div class="summary-section">
            <h3>🚨 Alert Status</h3>
            
            <div class="metrics-grid alert-metrics">
                <div class="metric-card critical">
                    <div class="metric-value">{{ summary.alerts.critical }}</div>
                    <div class="metric-label">CRITICAL<br>ALERTS</div>
                </div>
                
                <div class="metric-card warning">
                    <div class="metric-value">{{ summary.alerts.warning }}</div>
                    <div class="metric-label">WARNING<br>ALERTS</div>
                </div>
                
                <div class="metric-card healthy">
                    <div class="metric-value">{{ summary.alerts.ok }}</div>
                    <div class="metric-label">HEALTHY<br>SYSTEMS</div>
                </div>
                
                <div class="metric-card healthy">
                    <div class="metric-value">{% if summary.alerts.critical == 0 and summary.alerts.warning == 0 %}Healthy{% else %}Issues{% endif %}</div>
                    <div class="metric-label">OVERALL<br>STATUS</div>
                </div>
            </div>
        </div>
        
        <!-- Status Summary -->
        <div class="status-summary">
            {% if summary.alerts.critical > 0 %}
            ❌ Critical Issues: {{ summary.alerts.critical }} system(s) require immediate attention.
            {% elif summary.alerts.warning > 0 %}
            ⚠️ System Warnings: {{ summary.alerts.warning }} system(s) showing degraded performance.
            {% else %}
            ✅ All Systems Operational: All virtual machines are online and performing within normal parameters. System health is excellent with no immediate concerns.
            {% endif %}
        </div>
    </div>
    """

def get_vm_inventory_template():
    """VM Inventory template - One Climate table style"""
    return """
    <div class="page details-page">
        <div class="details-header">
            <h2>📋 Virtual Machine Inventory</h2>
        </div>
        
        <table class="vm-table">
            <thead>
                <tr>
                    <th>No</th>
                    <th>VM Name</th>
                    <th>IP Address</th>
                    <th>CPU %</th>
                    <th>Memory %</th>
                    <th>Disk %</th>
                    <th>Health</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for vm in vm_data %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ vm.name[:35] if vm.name else 'N/A' }}{% if vm.name and vm.name|length > 35 %}...{% endif %}</td>
                    <td>{{ vm.ip or vm.ip_address or 'N/A' }}</td>
                    <td>{{ (vm.cpu_load or vm.cpu or vm.cpu_usage or 0)|round(1) }}%</td>
                    <td>{{ (vm.memory_used or vm.memory or vm.memory_usage or 0)|round(1) }}%</td>
                    <td>{{ (vm.disk_used or vm.disk or vm.disk_usage or 0)|round(1) }}%</td>
                    <td class="health-score">{{ vm.health_score or vm.health or 100 }}</td>
                    <td class="{% if vm.is_online %}status-online{% else %}status-offline{% endif %}">
                        ● {% if vm.is_online %}ONLINE{% else %}OFFLINE{% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """

def get_vm_recommendations_template():
    """Key Recommendations template - One Climate style"""
    return """
    <div class="page recommendations-page">
        <div class="recommendations-box">
            <div class="recommendations-title">
                🔍 Key Recommendations
            </div>
            
            <div class="recommendations-grid">
                <div class="recommendation-section">
                    <h4>High Priority Actions:</h4>
                    <ul>
                        {% if summary.alerts.critical > 0 or summary.alerts.warning > 0 %}
                        <li>Address {{ summary.alerts.critical }} critical and {{ summary.alerts.warning }} warning alerts immediately</li>
                        {% else %}
                        <li>No immediate high-priority actions required</li>
                        {% endif %}
                    </ul>
                </div>
                
                <div class="recommendation-section">
                    <h4>Optimization Opportunities:</h4>
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
            Generated by Enhanced VM Infrastructure Monitoring System<br>
            Report Date: {{ report_date }} | Total Systems: {{ summary.total }} | Status: {% if summary.alerts.critical == 0 and summary.alerts.warning == 0 %}Healthy{% else %}Needs Attention{% endif %}
        </div>
    </div>
    """
