#!/usr/bin/env python3
"""
Service Health Report Templates - One Climate Style
Templates for service monitoring with same styling as VM report
"""

def get_service_cover_template():
    """Cover template for Service Health report - One Climate Style"""
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
                <h1>Service Health</h1>
                <h1 class="highlight">Monitoring Report</h1>
            </div>
            
            <!-- Subtitle -->
            <div class="cover-subtitle">
                Comprehensive Service & API Monitoring Analysis
            </div>
            <div class="subtitle-features">
                Real-time Health Checks • API Monitoring • Service Availability
            </div>
            
            <!-- Date -->
            <div class="cover-date">{{ report_date }}</div>
            
            <!-- Stats Cards - Service Focus -->
            <div class="cover-stats">
                <div class="cover-section">
                    <div class="section-title">SERVICE HEALTH</div>
                    <div class="section-stats">
                        <span class="stat-item">{{ service_summary.total }} Total</span>
                        <span class="stat-divider">|</span>
                        <span class="stat-item">{{ service_summary.healthy }} Healthy</span>
                        <span class="stat-divider">|</span>
                        <span class="stat-item">{{ service_summary.availability|round(1) }}% Available</span>
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

def get_service_summary_template():
    """Service summary template - Same style as VM Report"""
    return """
    <div class="page summary-page">
        <div class="page-header">
            <h2>Executive Summary</h2>
        </div>
        
        <div class="summary-grid">
            <!-- Service Health Overview -->
            <div class="summary-section">
                <h3>🛡️ Service Health Monitoring</h3>
                
                <div class="metrics-grid">
                    <div class="metric-card healthy">
                        <div class="metric-value">{{ service_summary.total }}</div>
                        <div class="metric-label">TOTAL<br>SERVICES</div>
                    </div>
                    
                    <div class="metric-card {% if service_summary.healthy == service_summary.total %}healthy{% else %}warning{% endif %}">
                        <div class="metric-value">{{ service_summary.healthy }}</div>
                        <div class="metric-label">HEALTHY<br>SERVICES</div>
                        <div class="metric-percentage">{{ ((service_summary.healthy / service_summary.total) * 100)|round(1) }}%</div>
                    </div>
                    
                    <div class="metric-card {% if service_summary.warning > 0 %}warning{% else %}healthy{% endif %}">
                        <div class="metric-value">{{ service_summary.warning }}</div>
                        <div class="metric-label">WARNING<br>SERVICES</div>
                        <div class="metric-percentage">{{ ((service_summary.warning / service_summary.total) * 100)|round(1) }}%</div>
                    </div>
                    
                    <div class="metric-card {% if service_summary.critical > 0 %}critical{% else %}healthy{% endif %}">
                        <div class="metric-value">{{ service_summary.critical }}</div>
                        <div class="metric-label">CRITICAL<br>SERVICES</div>
                        <div class="metric-percentage">{{ ((service_summary.critical / service_summary.total) * 100)|round(1) }}%</div>
                    </div>
                </div>
            </div>
            
            <!-- API Performance Overview -->
            <div class="summary-section">
                <h3>⚡ API Performance Overview</h3>
                
                <div class="performance-grid">
                    <div class="perf-card">
                        <div class="perf-icon">⏱️</div>
                        <div class="perf-title">Response<br>Time</div>
                        <div class="perf-value">55ms</div>
                        <div class="perf-detail">Average Response<br>Peak: 156ms</div>
                    </div>
                    
                    <div class="perf-card">
                        <div class="perf-icon">🗄️</div>
                        <div class="perf-title">Database<br>Latency</div>
                        <div class="perf-value">26ms</div>
                        <div class="perf-detail">Average Latency<br>Peak: 125ms</div>
                    </div>
                    
                    <div class="perf-card">
                        <div class="perf-icon">🎯</div>
                        <div class="perf-title">Service<br>Availability</div>
                        <div class="perf-value">{{ service_summary.availability|round(1) }}%</div>
                        <div class="perf-detail">Overall Uptime<br>Last 24h</div>
                    </div>
                </div>
            </div>
            
            <!-- Alert Status -->
            <div class="summary-section">
                <h3>🚨 Alert Status</h3>
                
                <div class="metrics-grid alert-metrics">
                    <div class="metric-card critical">
                        <div class="metric-value">{{ service_summary.critical }}</div>
                        <div class="metric-label">CRITICAL<br>ALERTS</div>
                    </div>
                    
                    <div class="metric-card warning">
                        <div class="metric-value">{{ service_summary.warning }}</div>
                        <div class="metric-label">WARNING<br>ALERTS</div>
                    </div>
                    
                    <div class="metric-card healthy">
                        <div class="metric-value">{{ service_summary.healthy }}</div>
                        <div class="metric-label">HEALTHY<br>SERVICES</div>
                    </div>
                    
                    <div class="metric-card {% if service_summary.critical == 0 and service_summary.warning == 0 %}healthy{% else %}warning{% endif %}">
                        <div class="metric-value">{% if service_summary.critical == 0 and service_summary.warning == 0 %}Healthy{% else %}Issues{% endif %}</div>
                        <div class="metric-label">OVERALL<br>STATUS</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Status Summary -->
        <div class="status-summary">
            {% if service_summary.critical > 0 %}
            ❌ Service Issues: {{ service_summary.critical }} critical service(s) require immediate attention.
            {% elif service_summary.warning > 0 %}
            ⚠️ Service Warnings: {{ service_summary.warning }} service(s) showing degraded performance.
            {% else %}
            ✅ All Services Operational: All services are healthy and responding normally. Service availability is excellent with no immediate concerns.
            {% endif %}
        </div>
    </div>
    """

def get_service_details_template():
    """Service details template - Enhanced design like VM Report"""
    return """
    <div class="page details-page">
        <div class="details-header">
            <h2>🔍 Service Status Details</h2>
        </div>
        
        <!-- Service Cards Grid -->
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
            <!-- Carbon Footprint (UAT) -->
            <div class="service-card">
                <div class="service-header">
                    <h3>Carbon Footprint (UAT)</h3>
                    <span class="status-badge status-ok">OK</span>
                </div>
                <div class="service-metrics">
                    <div class="metric-item">
                        <span class="metric-label">DATABASE:</span>
                        <span class="metric-value">Connect</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">DB LATENCY:</span>
                        <span class="metric-value">0ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">RESPONSE TIME:</span>
                        <span class="metric-value">45.2ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">UPTIME:</span>
                        <span class="metric-value">29m18s</span>
                    </div>
                </div>
                <div class="service-endpoints">
                    <div class="endpoints-title">API ENDPOINTS</div>
                    <div class="endpoints-grid">
                        <div class="endpoint-item"><span>One Api</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Industrial Api</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Report Api</span><span class="endpoint-ok">OK</span></div>
                    </div>
                </div>
            </div>
            
            <!-- Carbon Footprint (PRD) -->
            <div class="service-card">
                <div class="service-header">
                    <h3>Carbon Footprint (PRD)</h3>
                    <span class="status-badge status-ok">OK</span>
                </div>
                <div class="service-metrics">
                    <div class="metric-item">
                        <span class="metric-label">DATABASE:</span>
                        <span class="metric-value">Connect</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">DB LATENCY:</span>
                        <span class="metric-value">2ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">RESPONSE TIME:</span>
                        <span class="metric-value">38.7ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">UPTIME:</span>
                        <span class="metric-value">2d15h42m</span>
                    </div>
                </div>
                <div class="service-endpoints">
                    <div class="endpoints-title">API ENDPOINTS</div>
                    <div class="endpoints-grid">
                        <div class="endpoint-item"><span>One Api</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Industrial Api</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Report Api</span><span class="endpoint-ok">OK</span></div>
                    </div>
                </div>
            </div>
            
            <!-- E-Tax Software -->
            <div class="service-card">
                <div class="service-header">
                    <h3>E-Tax Software</h3>
                    <span class="status-badge status-ok">OK</span>
                </div>
                <div class="service-metrics">
                    <div class="metric-item">
                        <span class="metric-label">DATABASE:</span>
                        <span class="metric-value">Connect</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">DB LATENCY:</span>
                        <span class="metric-value">1ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">RESPONSE TIME:</span>
                        <span class="metric-value">23.1ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">UPTIME:</span>
                        <span class="metric-value">5d8h15m</span>
                    </div>
                </div>
                <div class="service-endpoints">
                    <div class="endpoints-title">API ENDPOINTS</div>
                    <div class="endpoints-grid">
                        <div class="endpoint-item"><span>Authentication</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Tax Processing</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Report Generation</span><span class="endpoint-ok">OK</span></div>
                    </div>
                </div>
            </div>
            
            <!-- Rancher Management -->
            <div class="service-card">
                <div class="service-header">
                    <h3>Rancher Management</h3>
                    <span class="status-badge status-ok">OK</span>
                </div>
                <div class="service-metrics">
                    <div class="metric-item">
                        <span class="metric-label">DATABASE:</span>
                        <span class="metric-value">Connect</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">DB LATENCY:</span>
                        <span class="metric-value">125ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">RESPONSE TIME:</span>
                        <span class="metric-value">156.3ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">UPTIME:</span>
                        <span class="metric-value">12d3h27m</span>
                    </div>
                </div>
                <div class="service-endpoints">
                    <div class="endpoints-title">API ENDPOINTS</div>
                    <div class="endpoints-grid">
                        <div class="endpoint-item"><span>Cluster Api</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Kubernetes Api</span><span class="endpoint-ok">OK</span></div>
                        <div class="endpoint-item"><span>Management UI</span><span class="endpoint-ok">OK</span></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Database Cluster - Full Width -->
        <div class="service-card" style="grid-column: 1 / -1;">
            <div class="service-header">
                <h3>Database Cluster</h3>
                <span class="status-badge status-ok">OK</span>
            </div>
            <div class="service-metrics">
                <div class="metric-item">
                    <span class="metric-label">DATABASE:</span>
                    <span class="metric-value">Connect</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">DB LATENCY:</span>
                    <span class="metric-value">3ms</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">RESPONSE TIME:</span>
                    <span class="metric-value">12.8ms</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">UPTIME:</span>
                    <span class="metric-value">15d22h45m</span>
                </div>
            </div>
            <div class="service-endpoints">
                <div class="endpoints-title">API ENDPOINTS</div>
                <div class="endpoints-grid">
                    <div class="endpoint-item"><span>PostgreSQL Primary</span><span class="endpoint-ok">OK</span></div>
                    <div class="endpoint-item"><span>MongoDB Replica</span><span class="endpoint-ok">OK</span></div>
                    <div class="endpoint-item"><span>Redis Cluster</span><span class="endpoint-ok">OK</span></div>
                </div>
            </div>
        </div>
        
        <!-- Demo Note -->
        <div class="demo-note">
            <span>Note: Service health data is currently running in demo mode.</span>
        </div>
    </div>
    """

def get_service_recommendations_template():
    """Service recommendations template - One Climate style"""
    return """
    <div class="page recommendations-page">
        <div class="recommendations-box">
            <div class="recommendations-title">
                🔍 Service Health Recommendations
            </div>
            
            <div class="recommendations-grid">
                <div class="recommendation-section">
                    <h4>High Priority Actions:</h4>
                    <ul>
                        {% if service_summary.critical > 0 %}
                        <li>Investigate {{ service_summary.critical }} critical service(s) immediately</li>
                        <li>Check API endpoints and database connections</li>
                        {% elif service_summary.warning > 0 %}
                        <li>Monitor {{ service_summary.warning }} warning service(s) for stability</li>
                        {% else %}
                        <li>No immediate service issues requiring attention</li>
                        {% endif %}
                    </ul>
                </div>
                
                <div class="recommendation-section">
                    <h4>Optimization Opportunities:</h4>
                    <ul>
                        <li>Implement automated health check monitoring</li>
                        <li>Set up API response time alerts</li>
                        <li>Configure service dependency mapping</li>
                        <li>Establish SLA monitoring thresholds</li>
                        <li>Create automated service recovery procedures</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="report-footer">
            Generated by Enhanced Service Health Monitoring System<br>
            Report Date: {{ report_date }} | Total Services: {{ service_summary.total }} | Availability: {{ service_summary.availability|round(1) }}%
        </div>
    </div>
    """
