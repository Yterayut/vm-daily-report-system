#!/usr/bin/env python3
"""
Service Health Report Generator
Dedicated PDF generation for service health monitoring only
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from the working generate_report.py
try:
    from generate_report import EnhancedReportGenerator
except ImportError:
    print("Error: Could not import EnhancedReportGenerator from generate_report.py")
    exit(1)

try:
    from service_health_adapter import get_service_health_data as get_service_health_data_from_core
except ImportError:
    get_service_health_data_from_core = None

class ServiceHealthReportGenerator(EnhancedReportGenerator):
    """Service Health Report Generator - inherits from working generator"""

    def _fetch_service_api_data(self) -> Optional[Dict[str, Any]]:
        """Fetch service health data from API"""
        try:
            import requests
            print("📡 Fetching from http://127.0.0.1:5000/api/services/health...")
            response = requests.get('http://127.0.0.1:5000/api/services/health', timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Got API response: {len(data.get('groups', {}))} service groups")
                return data
            else:
                print(f"⚠️ API returned status {response.status_code}")
            return None
        except Exception as e:
            print(f"⚠️ Failed to fetch service API data: {e}")
            return None

    def _transform_api_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API data to report format"""
        try:
            groups = api_data.get('groups', {})
            summary = api_data.get('summary', {})

            # Transform services
            services = {}
            total_response_time = 0
            total_db_latency = 0
            service_count = 0
            healthy_count = 0
            warning_count = 0
            critical_count = 0

            for group_key, group_data in groups.items():
                main_service = group_data.get('main_service', {})
                if main_service:
                    # Get status from main service
                    status = main_service.get('status', 'unknown')

                    # Count service health
                    if status == 'ok':
                        healthy_count += 1
                    elif 'warning' in status.lower():
                        warning_count += 1
                    else:
                        critical_count += 1

                    # Create service entry
                    services[group_key] = {
                        'name': group_data.get('title', main_service.get('name', '')),
                        'status': status,
                        'database': main_service.get('database', 'Unknown'),
                        'db_latency_ms': main_service.get('db_latency_ms', 0),
                        'response_time': main_service.get('response_time', 0),
                        'uptime': main_service.get('uptime', 'N/A'),
                        'icon': group_data.get('icon', '🔧'),
                        'sub_services': group_data.get('sub_services', [])
                    }

                    # Accumulate for averages
                    total_response_time += main_service.get('response_time', 0)
                    total_db_latency += main_service.get('db_latency_ms', 0)
                    service_count += 1

            # Calculate averages
            avg_response_time = (total_response_time / service_count) if service_count > 0 else 0
            avg_db_latency = (total_db_latency / service_count) if service_count > 0 else 0

            # Use API summary if available, otherwise use counted values
            total_services = summary.get('total_services', service_count)
            availability_pct = summary.get('availability_percentage', 100.0)

            return {
                'services': services,
                'summary': {
                    'total': total_services,
                    'healthy': summary.get('healthy_services', healthy_count),
                    'warning': summary.get('warning_services', warning_count),
                    'critical': summary.get('error_services', critical_count),
                    'availability': availability_pct
                },
                'performance': {
                    'avg_response_time': avg_response_time,
                    'avg_db_latency': avg_db_latency
                },
                'demo_mode': False
            }
        except Exception as e:
            print(f"⚠️ Failed to transform API data: {e}")
            import traceback
            traceback.print_exc()
            return {'services': {}, 'summary': {}, 'demo_mode': True, 'error': str(e)}

    def generate_service_health_report(
        self,
        service_health_data: Dict[str, Any] = None,
        company_logo: str = 'one_climate',
        output_filename: str = None
    ) -> Optional[str]:
        """Generate Service Health PDF report"""

        try:
            if output_filename is None:
                today_str = datetime.now().strftime("%Y-%m-%d")
                output_filename = "Service_Health_Report_{}.pdf".format(today_str)

            # Fetch from single source adapter if not provided
            if service_health_data is None:
                print("📡 Fetching service health data from core adapter...")
                if get_service_health_data_from_core:
                    service_health_data = get_service_health_data_from_core()
                    print("✅ Using service data from adapter ({} services)".format(
                        len(service_health_data.get('services', {}))
                    ))
                else:
                    # Legacy fallback path
                    api_data = self._fetch_service_api_data()
                    if api_data:
                        service_health_data = self._transform_api_data(api_data)
                    else:
                        service_health_data = None

                if not service_health_data:
                    service_health_data = {
                        'services': {},
                        'summary': {
                            'total': 0,
                            'healthy': 0,
                            'warning': 0,
                            'critical': 0,
                            'availability': 0.0
                        },
                        'demo_mode': True,
                        'error': 'Service adapter/API unavailable'
                    }
                    print("⚠️ Using fallback structure")

            # Create empty VM data for service report - focus only on services
            vm_data = []

            # Get service summary from actual service health data
            if service_health_data and service_health_data.get('summary'):
                service_summary = service_health_data['summary']
                total_services = service_summary.get('total', 0)
                healthy_services = service_summary.get('healthy', 0)
            else:
                total_services = 0
                healthy_services = 0
            
            summary = {
                'total': total_services,  # Show service count as main metrics
                'online': healthy_services,
                'offline': total_services - healthy_services,
                'online_percent': (healthy_services / max(total_services, 1) * 100) if total_services > 0 else 100.0,
                'offline_percent': ((total_services - healthy_services) / max(total_services, 1) * 100) if total_services > 0 else 0.0,
                'system_status': 'healthy',
                'alerts': {'critical': 0, 'warning': 0, 'ok': healthy_services},
                'performance': {
                    'avg_cpu': 0, 
                    'avg_memory': 0, 
                    'avg_disk': 0,
                    'peak_cpu': 0,
                    'peak_memory': 0,
                    'peak_disk': 0
                }
            }
            
            # Use custom Service-only report generation
            return self.generate_service_only_report(
                service_health_data=service_health_data,
                company_logo=company_logo,
                output_filename=output_filename
            )
                
        except Exception as e:
            print("❌ Service Health PDF generation failed: {}".format(e))
            return None
    
    def generate_service_only_report(
        self, 
        service_health_data: Dict[str, Any] = None,
        company_logo: str = 'one_climate',
        output_filename: str = None
    ) -> Optional[str]:
        """Generate Service-only PDF report without any VM infrastructure content"""
        
        try:
            if output_filename is None:
                today_str = datetime.now().strftime("%Y-%m-%d")
                output_filename = "Service_Health_Report_{}.pdf".format(today_str)
            
            output_path = self.output_dir / output_filename
            
            print("🎨 Generating Service-only PDF report: {}".format(output_filename))
            
            # Get service summary from actual service health data
            if service_health_data and service_health_data.get('summary'):
                service_summary = service_health_data['summary']
                total_services = service_summary.get('total', 0)
                healthy_services = service_summary.get('healthy', 0)
                warning_services = service_summary.get('warning', 0)
                critical_services = service_summary.get('critical', 0)
                availability_percent = service_summary.get('availability', 100.0)
            else:
                total_services = 0
                healthy_services = 0
                warning_services = 0
                critical_services = 0
                availability_percent = 0.0

            # Get performance metrics
            performance = service_health_data.get('performance', {}) if service_health_data else {}
            avg_response_time = performance.get('avg_response_time', 0)
            avg_db_latency = performance.get('avg_db_latency', 0)

            # Prepare template data (Service only)
            template_data = {
                'company_logo': self.get_company_logo(company_logo),
                'report_date': datetime.now().strftime("%B %d, %Y"),
                'service_health_data': service_health_data or {},
                'service_summary': {
                    'total': total_services,
                    'healthy': healthy_services,
                    'warning': warning_services,
                    'critical': critical_services,
                    'availability': availability_percent
                },
                'performance': {
                    'avg_response_time': avg_response_time,
                    'avg_db_latency': avg_db_latency
                },
                'total_services': total_services,
                'healthy_services': healthy_services,
                'availability_percent': availability_percent,
                # Add summary for parent template compatibility
                'summary': {
                    'total': total_services,
                    'online': healthy_services,
                    'offline': total_services - healthy_services,
                    'online_percent': (healthy_services / max(total_services, 1) * 100) if total_services > 0 else 100.0,
                    'offline_percent': ((total_services - healthy_services) / max(total_services, 1) * 100) if total_services > 0 else 0.0,
                    'alerts': {'critical': critical_services, 'warning': warning_services, 'ok': healthy_services}
                }
            }
            
            # Import One Climate style templates
            from service_templates_oneclimate import (
                get_service_cover_template,
                get_service_summary_template,
                get_service_details_template,
                get_service_recommendations_template
            )
            
            # Render One Climate style templates
            cover_html = self.jinja_env.from_string(get_service_cover_template()).render(**template_data)
            service_summary_html = self.jinja_env.from_string(get_service_summary_template()).render(**template_data)
            service_details_html = self.jinja_env.from_string(get_service_details_template()).render(**template_data)
            
            # Combine Service-only content
            full_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Service Health Report - {template_data['report_date']}</title>
                <style>
                    {self.get_enhanced_css()}
                </style>
            </head>
            <body>
                {cover_html}
                {service_summary_html}
                {service_details_html}
            </body>
            </html>
            """
            
            # Generate PDF
            from weasyprint import HTML
            html_doc = HTML(string=full_html, base_url=str(self.output_dir))
            pdf_file = html_doc.write_pdf(optimize_size=('fonts', 'images'))
            
            with open(output_path, 'wb') as f:
                f.write(pdf_file)
            
            # Get actual service count from data
            actual_service_count = len(service_health_data.get('services', {})) if service_health_data else 0

            print("✅ Service-only PDF report generated successfully")
            print("   Output: {}".format(output_path))
            print("   Size: {:,} bytes".format(len(pdf_file)))
            print("   Services: {} services (from API)".format(actual_service_count))
            print("   Summary: {} total, {} healthy, {} warning, {} critical".format(
                total_services, healthy_services, warning_services, critical_services
            ))
            
            return str(output_path)
            
        except Exception as e:
            print("❌ Service-only PDF generation failed: {}".format(e))
            import traceback
            traceback.print_exc()
            return None
            
    def get_service_cover_template(self):
        """Cover template for Service Health report - One Climate Style with A4 size"""
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
                
                <!-- Stats Cards - One Climate Style -->
                <div class="cover-stats">
                    <div class="cover-section">
                        <div class="section-title">SERVICE HEALTH</div>
                        <div class="section-stats">
                            <span class="stat-item">{{ total_services }} Total</span>
                            <span class="stat-divider">|</span>
                            <span class="stat-item">{{ healthy_services }} Healthy</span>
                            <span class="stat-divider">|</span>
                            <span class="stat-item">{{ availability_percent|round(1) }}% Available</span>
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

# Backward compatibility function for testing
def main():
    """Main function for testing Service Health report generation"""
    try:
        print("🎨 Service Health Report Generator - Production Mode")
        print("=" * 60)

        # Initialize generator
        generator = ServiceHealthReportGenerator()

        # Let generate_service_health_report fetch data from API directly
        # Pass None to trigger API fetch inside the method
        print("📡 Will fetch Service Health data from API...")

        # Generate Service Health report (will fetch API data internally)
        print("📄 Generating Service Health PDF report...")
        report_path = generator.generate_service_health_report(service_health_data=None)

        if report_path:
            print("✅ Service Health report generation completed successfully!")
            print("📁 Report saved: {}".format(report_path))
            return True
        else:
            print("❌ Service Health report generation failed")
            return None

    except Exception as e:
        print("❌ Error in Service Health report main: {}".format(e))
        import traceback
        traceback.print_exc()
        return None
        
def get_service_summary_template(self):
        """Service summary template without Performance Overview"""
        return """
        <div class="page summary-page">
            <div class="page-header">
                <h2>Service Health Summary</h2>
            </div>
            
            <div class="summary-grid">
                <!-- Service Health Overview -->
                <div class="summary-section">
                    <h3>🛡️ Service Health Monitoring</h3>
                    
                    <div class="metrics-grid service-metrics">
                        <div class="metric-card healthy">
                            <div class="metric-value">{{ total_services }}</div>
                            <div class="metric-label">TOTAL<br>SERVICES</div>
                        </div>
                        
                        <div class="metric-card healthy">
                            <div class="metric-value">{{ healthy_services }}</div>
                            <div class="metric-label">HEALTHY<br>SERVICES</div>
                        </div>
                        
                        <div class="metric-card warning">
                            <div class="metric-value">{{ service_summary.warning_count or 0 }}</div>
                            <div class="metric-label">WARNING<br>SERVICES</div>
                        </div>
                        
                        <div class="metric-card critical">
                            <div class="metric-value">{{ service_summary.critical_count or 0 }}</div>
                            <div class="metric-label">CRITICAL<br>SERVICES</div>
                        </div>
                    </div>
                </div>
                
                <!-- Availability Overview -->
                <div class="summary-section">
                    <h3>📊 Availability Overview</h3>
                    <div class="availability-display">
                        <div class="availability-percent">{{ availability_percent|round(1) }}%</div>
                        <div class="availability-label">SERVICE<br>AVAILABILITY</div>
                    </div>
                </div>
                
                <!-- API Response Times -->
                <div class="summary-section">
                    <h3>⚡ API Performance</h3>
                    <div class="api-performance">
                        <div class="api-metric">
                            <div class="api-title">Average Response</div>
                            <div class="api-value">~45ms</div>
                        </div>
                        <div class="api-metric">
                            <div class="api-title">Database Latency</div>
                            <div class="api-value">~2ms</div>
                        </div>
                        <div class="api-metric">
                            <div class="api-title">Uptime Range</div>
                            <div class="api-value">29m - 15d</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Status Summary -->
            <div class="status-summary service-status">
                {% if service_summary.critical_count > 0 %}
                ❌ Critical Issues: {{ service_summary.critical_count }} service(s) require immediate attention.
                {% elif service_summary.warning_count > 0 %}
                ⚠️ Service Warnings: {{ service_summary.warning_count }} service(s) showing degraded performance.
                {% else %}
                ✅ All Services Operational: All services are running normally with excellent availability.
                {% endif %}
            </div>
        </div>
        """
        """Service summary template"""
        return """
        <div class="page summary-page">
            <div class="page-header">
                <h2>Service Health Summary</h2>
            </div>
            
            <div class="summary-grid">
                <!-- Service Health Overview -->
                <div class="summary-section">
                    <h3>🛡️ Service Health Monitoring</h3>
                    
                    <div class="metrics-grid service-metrics">
                        <div class="metric-card healthy">
                            <div class="metric-value">{{ total_services }}</div>
                            <div class="metric-label">TOTAL<br>SERVICES</div>
                        </div>
                        
                        <div class="metric-card healthy">
                            <div class="metric-value">{{ healthy_services }}</div>
                            <div class="metric-label">HEALTHY<br>SERVICES</div>
                        </div>
                        
                        <div class="metric-card warning">
                            <div class="metric-value">{{ service_summary.warning_count or 0 }}</div>
                            <div class="metric-label">WARNING<br>SERVICES</div>
                        </div>
                        
                        <div class="metric-card critical">
                            <div class="metric-value">{{ service_summary.critical_count or 0 }}</div>
                            <div class="metric-label">CRITICAL<br>SERVICES</div>
                        </div>
                    </div>
                </div>
                
                <!-- Availability Overview -->
                <div class="summary-section">
                    <h3>📊 Availability Overview</h3>
                    <div class="availability-display">
                        <div class="availability-percent">{{ availability_percent|round(1) }}%</div>
                        <div class="availability-label">SERVICE<br>AVAILABILITY</div>
                    </div>
                </div>
            </div>
            
            <!-- Status Summary -->
            <div class="status-summary service-status">
                {% if service_summary.critical_count > 0 %}
                ❌ Critical Issues: {{ service_summary.critical_count }} service(s) require immediate attention.
                {% elif service_summary.warning_count > 0 %}
                ⚠️ Service Warnings: {{ service_summary.warning_count }} service(s) showing degraded performance.
                {% else %}
                ✅ All Services Operational: All services are running normally with excellent availability.
                {% endif %}
            </div>
        </div>
        """

if __name__ == "__main__":
    main()
