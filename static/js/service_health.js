/**
 * Service Health Monitoring JavaScript Module
 * Part of VM Daily Report Dashboard v2.1
 */

// Service Health Data Management
let serviceHealthData = null;
let serviceHealthCache = {
    data: null,
    timestamp: null,
    ttl: 60000 // 60 seconds
};

/**
 * Load service health data from API
 */
async function loadServiceHealthData() {
    const startTime = performance.now();
    
    try {
        console.log('🛡️ Loading service health data...');
        
        // Check cache first
        if (isServiceHealthCacheValid()) {
            console.log('📋 Using cached service health data');
            updateServiceHealthView(serviceHealthCache.data);
            return;
        }
        
        const response = await fetch('/api/services', {
            headers: {
                'Accept-Encoding': 'gzip, deflate',
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const endTime = performance.now();
        const loadTime = endTime - startTime;
        
        // Update cache
        serviceHealthCache.data = data;
        serviceHealthCache.timestamp = Date.now();
        serviceHealthData = data;
        
        updateServiceHealthView(data);
        
        console.log(`✅ Service health data loaded in ${loadTime.toFixed(1)}ms`);
        
    } catch (error) {
        console.error('❌ Error loading service health data:', error);
        showServiceHealthError(`Failed to load service health: ${error.message}`);
    }
}

/**
 * Check if service health cache is valid
 */
function isServiceHealthCacheValid() {
    if (!serviceHealthCache.data || !serviceHealthCache.timestamp) {
        return false;
    }
    
    const age = Date.now() - serviceHealthCache.timestamp;
    return age < serviceHealthCache.ttl;
}

/**
 * Update service health view with data
 */
function updateServiceHealthView(data) {
    if (!data || data.error) {
        showServiceHealthError(data ? data.error : 'Unknown error');
        return;
    }

    // Update service summary stats
    updateServiceSummaryStats(data.summary);
    
    // Update service health grid
    updateServiceHealthGrid(data.services);
    
    // Update service alerts
    updateServiceAlerts(data);
}

/**
 * Update service summary statistics
 */
function updateServiceSummaryStats(summary) {
    const elements = {
        'totalServices': summary?.total_count || 0,
        'healthyServices': summary?.healthy_count || 0,
        'warningServices': summary?.warning_count || 0,
        'criticalServices': summary?.critical_count || 0,
        'serviceAvailability': (summary?.availability_percentage || 0) + '%'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

/**
 * Update service health grid
 */
function updateServiceHealthGrid(services) {
    const serviceGrid = document.getElementById('serviceHealthGrid');
    if (!serviceGrid) return;
    
    serviceGrid.innerHTML = '';

    if (!services || Object.keys(services).length === 0) {
        serviceGrid.innerHTML = `
            <div class="service-loading">
                <p>🔍 No services configured for monitoring</p>
                <button onclick="loadServiceHealthData()" class="refresh-btn">
                    🔄 Retry
                </button>
            </div>
        `;
        return;
    }

    Object.entries(services).forEach(([serviceId, serviceData]) => {
        const serviceCard = createServiceHealthCard(serviceId, serviceData);
        serviceGrid.appendChild(serviceCard);
    });
}

/**
 * Create service health card element
 */
function createServiceHealthCard(serviceId, data) {
    const card = document.createElement('div');
    card.className = `service-card status-${data.health_level || 'unknown'}`;
    
    const statusBadgeClass = `service-status-badge status-${data.health_level || 'unknown'}`;
    const statusText = (data.status || 'unknown').toUpperCase();
    
    // Format metrics
    const metrics = {
        database: data.database || 'N/A',
        dbLatency: data.db_latency_ms ? `${data.db_latency_ms}ms` : 'N/A',
        responseTime: data.response_time_ms ? `${data.response_time_ms}ms` : 'N/A',
        uptime: data.uptime || 'N/A'
    };
    
    card.innerHTML = `
        <div class="service-header">
            <div class="service-name">${data.name || serviceId}</div>
            <div class="${statusBadgeClass}">${statusText}</div>
        </div>
        
        <div class="service-metrics">
            <div class="service-metric">
                <div class="service-metric-value">${metrics.database}</div>
                <div class="service-metric-label">Database</div>
            </div>
            <div class="service-metric">
                <div class="service-metric-value">${metrics.dbLatency}</div>
                <div class="service-metric-label">DB Latency</div>
            </div>
            <div class="service-metric">
                <div class="service-metric-value">${metrics.responseTime}</div>
                <div class="service-metric-label">Response Time</div>
            </div>
            <div class="service-metric">
                <div class="service-metric-value">${metrics.uptime}</div>
                <div class="service-metric-label">Uptime</div>
            </div>
        </div>
        
        ${generateServiceEndpoints(data.endpoints)}
        ${generateServiceError(data.error)}
        
        <div class="service-footer">
            <span class="service-type">${data.type || 'service'}</span>
            <span class="service-last-check">${formatTimestamp(data.last_check)}</span>
        </div>
    `;
    
    return card;
}

/**
 * Generate service endpoints HTML
 */
function generateServiceEndpoints(endpoints) {
    if (!endpoints || Object.keys(endpoints).length === 0) {
        return '';
    }
    
    const endpointItems = Object.entries(endpoints).map(([endpoint, status]) => `
        <div class="service-endpoint">
            <span class="endpoint-name">${formatEndpointName(endpoint)}</span>
            <span class="endpoint-status status-${status === 'ok' ? 'ok' : 'error'}">${status}</span>
        </div>
    `).join('');
    
    return `
        <div class="service-endpoints">
            <div class="endpoints-header">Endpoints</div>
            ${endpointItems}
        </div>
    `;
}

/**
 * Generate service error HTML
 */
function generateServiceError(error) {
    if (!error) return '';
    
    return `
        <div class="service-error-info">
            <div class="error-header">🚨 Error Details</div>
            <div class="error-message">${error}</div>
        </div>
    `;
}

/**
 * Format endpoint names for display
 */
function formatEndpointName(endpoint) {
    return endpoint
        .replace(/_/g, ' ')
        .replace(/status|api/gi, '')
        .replace(/\s+/g, ' ')
        .trim()
        .replace(/^./, str => str.toUpperCase()) || endpoint;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        
        if (diffMs < 60000) { // Less than 1 minute
            return 'Just now';
        } else if (diffMs < 3600000) { // Less than 1 hour
            const minutes = Math.floor(diffMs / 60000);
            return `${minutes}m ago`;
        } else if (diffMs < 86400000) { // Less than 1 day
            const hours = Math.floor(diffMs / 3600000);
            return `${hours}h ago`;
        } else {
            return date.toLocaleDateString();
        }
    } catch (e) {
        return 'Unknown';
    }
}

/**
 * Update service alerts
 */
function updateServiceAlerts(data) {
    const container = document.getElementById('serviceAlerts');
    if (!container) return;
    
    container.innerHTML = '';

    // Generate alerts from service data
    const alerts = generateServiceAlerts(data.services);

    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="service-loading">
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 24px; margin-bottom: 10px;">✅</div>
                    <div>No active service alerts</div>
                    <div style="font-size: 12px; opacity: 0.7; margin-top: 5px;">
                        All services are operating normally
                    </div>
                </div>
            </div>
        `;
        return;
    }

    alerts.forEach(alert => {
        const alertDiv = document.createElement('div');
        alertDiv.className = `service-alert alert-${alert.level}`;
        
        alertDiv.innerHTML = `
            <div class="alert-header">
                <strong>${alert.service}</strong>
                <span class="alert-level ${alert.level}">${alert.level}</span>
            </div>
            <div class="alert-message">${alert.message}</div>
            ${alert.details ? `<div class="alert-details">${alert.details}</div>` : ''}
            <div class="alert-timestamp">${formatTimestamp(alert.timestamp)}</div>
        `;
        
        container.appendChild(alertDiv);
    });
}

/**
 * Generate alerts from service data
 */
function generateServiceAlerts(services) {
    const alerts = [];
    
    if (!services) return alerts;
    
    Object.entries(services).forEach(([serviceId, service]) => {
        if (service.health_level === 'critical' || service.status === 'error') {
            alerts.push({
                level: 'critical',
                service: service.name || serviceId,
                message: service.error || 'Service is in critical state',
                details: service.error ? 'Check service logs for more details' : null,
                timestamp: service.last_check
            });
        } else if (service.health_level === 'warning') {
            const issues = [];
            
            if (service.db_latency_ms > 100) {
                issues.push(`High database latency: ${service.db_latency_ms}ms`);
            }
            if (service.response_time_ms > 5000) {
                issues.push(`Slow response time: ${service.response_time_ms}ms`);
            }
            
            if (issues.length > 0) {
                alerts.push({
                    level: 'warning',
                    service: service.name || serviceId,
                    message: issues.join(', '),
                    details: 'Performance degradation detected',
                    timestamp: service.last_check
                });
            }
        }
    });
    
    return alerts.sort((a, b) => {
        // Sort by severity: critical first, then warning
        if (a.level === 'critical' && b.level === 'warning') return -1;
        if (a.level === 'warning' && b.level === 'critical') return 1;
        return 0;
    });
}

/**
 * Show service health error
 */
function showServiceHealthError(errorMessage) {
    const serviceGrid = document.getElementById('serviceHealthGrid');
    const serviceAlerts = document.getElementById('serviceAlerts');
    
    if (serviceGrid) {
        serviceGrid.innerHTML = `
            <div class="service-error">
                <div style="text-align: center; padding: 30px;">
                    <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
                    <h3>Service Health Unavailable</h3>
                    <p style="margin: 15px 0; opacity: 0.8;">${errorMessage}</p>
                    <button onclick="loadServiceHealthData()" class="refresh-btn" style="background: #F44336; margin-top: 10px;">
                        🔄 Retry
                    </button>
                </div>
            </div>
        `;
    }
    
    if (serviceAlerts) {
        serviceAlerts.innerHTML = `
            <div class="service-loading">
                <div style="text-align: center; padding: 20px;">
                    <div style="color: #F44336;">❌ Service alerts unavailable</div>
                </div>
            </div>
        `;
    }
    
    // Clear service stats
    const statElements = ['totalServices', 'healthyServices', 'warningServices', 'criticalServices', 'serviceAvailability'];
    statElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = id === 'serviceAvailability' ? '--%' : '--';
        }
    });
}

/**
 * Force refresh service health data
 */
function refreshServiceHealthData() {
    // Clear cache to force fresh data
    serviceHealthCache.data = null;
    serviceHealthCache.timestamp = null;
    
    // Load fresh data
    loadServiceHealthData();
}

/**
 * Initialize service health monitoring
 */
function initServiceHealth() {
    console.log('🛡️ Initializing service health monitoring...');
    
    // Load initial data
    loadServiceHealthData();
    
    // Set up auto-refresh (every 2 minutes)
    setInterval(() => {
        if (currentTab === 'services') {
            loadServiceHealthData();
        }
    }, 120000);
    
    console.log('✅ Service health monitoring initialized');
}

// Export functions for global use
window.loadServiceHealthData = loadServiceHealthData;
window.refreshServiceHealthData = refreshServiceHealthData;
window.initServiceHealth = initServiceHealth;