#!/usr/bin/env python3
"""
VM Infrastructure Report Generator - One Climate Style
Using enhanced templates that match the provided PDF sample exactly
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

# Import One Climate style templates
try:
    from vm_templates_oneclimate import (
        get_vm_cover_template,
        get_vm_summary_template, 
        get_vm_inventory_template,
        get_vm_recommendations_template
    )
except ImportError:
    print("Error: Could not import One Climate VM templates")
    exit(1)

class VMInfrastructureReportGenerator(EnhancedReportGenerator):
    """VM Infrastructure Report Generator - One Climate Style"""
    
    def generate_vm_infrastructure_report(
        self, 
        vm_data: List[Dict[str, Any]], 
        summary: Dict[str, Any],
        company_logo: str = 'one_climate',
        output_filename: str = None
    ) -> Optional[str]:
        """Generate VM Infrastructure PDF report"""
        
        try:
            if output_filename is None:
                today_str = datetime.now().strftime("%Y-%m-%d")
                output_filename = "VM_Infrastructure_Report_{}.pdf".format(today_str)
            
            # Use custom VM-only report generation
            return self.generate_vm_only_report(
                vm_data=vm_data,
                summary=summary,
                company_logo=company_logo,
                output_filename=output_filename
            )
                
        except Exception as e:
            print("❌ VM Infrastructure PDF generation failed: {}".format(e))
            return None
    
    def generate_vm_only_report(
        self, 
        vm_data: List[Dict[str, Any]], 
        summary: Dict[str, Any],
        company_logo: str = 'one_climate',
        output_filename: str = None
    ) -> Optional[str]:
        """Generate VM-only PDF report without any service health content"""
        
        try:
            if output_filename is None:
                today_str = datetime.now().strftime("%Y-%m-%d")
                output_filename = "VM_Infrastructure_Report_{}.pdf".format(today_str)
            
            output_path = self.output_dir / output_filename
            
            print("🎨 Generating VM-only PDF report: {}".format(output_filename))
            
            # Prepare template data (VM only)
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
            
            # Render One Climate style templates
            cover_html = self.jinja_env.from_string(get_vm_cover_template()).render(**template_data)
            summary_html = self.jinja_env.from_string(get_vm_summary_template()).render(**template_data)
            inventory_html = self.jinja_env.from_string(get_vm_inventory_template()).render(**template_data)
            recommendations_html = self.jinja_env.from_string(get_vm_recommendations_template()).render(**template_data)
            
            # Combine One Climate style content
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
                {summary_html}
                {inventory_html}
                {recommendations_html}
            </body>
            </html>
            """
            
            # Generate PDF
            from weasyprint import HTML
            html_doc = HTML(string=full_html, base_url=str(self.output_dir))
            pdf_file = html_doc.write_pdf(optimize_size=('fonts', 'images'))
            
            with open(output_path, 'wb') as f:
                f.write(pdf_file)
            
            print("✅ VM-only PDF report generated successfully")
            print("   Output: {}".format(output_path))
            print("   Size: {:,} bytes".format(len(pdf_file)))
            print("   VMs: {} systems".format(len(vm_data)))
            
            return str(output_path)
            
        except Exception as e:
            print("❌ VM-only PDF generation failed: {}".format(e))
            import traceback
            traceback.print_exc()
            return None
            
    def get_vm_cover_template(self):
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
        
    def get_vm_summary_template(self):
        """VM summary template without Service Health section"""
        return """
        <div class="page summary-page">
            <div class="page-header">
                <h2>Executive Summary</h2>
            </div>
            
            <div class="summary-grid">
                <!-- VM Infrastructure Overview -->
                <div class="summary-section">
                    <h3>🖥️ Virtual Machine Infrastructure</h3>
                    
                    <div class="metrics-grid">
                        <div class="metric-card healthy">
                            <div class="metric-value">{{ summary.total }}</div>
                            <div class="metric-label">TOTAL<br>VIRTUAL<br>MACHINES</div>
                        </div>
                        
                        <div class="metric-card healthy">
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
                        
                        <div class="metric-card status-healthy">
                            <div class="metric-value">Healthy</div>
                            <div class="metric-label">OVERALL<br>STATUS</div>
                        </div>
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

# Backward compatibility function for testing
def main():
    """Main function for testing VM Infrastructure report generation"""
    try:
        # Import required modules for testing
        from fetch_zabbix_data import fetch_vm_data, calculate_enhanced_summary, generate_enhanced_charts
        
        print("🎨 VM Infrastructure Report Generator - Testing Mode")
        print("=" * 60)
        
        # Initialize generator
        generator = VMInfrastructureReportGenerator()
        
        # Fetch VM data
        print("📡 Fetching VM data...")
        vm_data = fetch_vm_data()
        
        if not vm_data:
            print("⚠️ No VM data available, using sample data")
            vm_data = []
        
        # Calculate summary
        print("📊 Calculating summary...")
        summary = calculate_enhanced_summary(vm_data)
        
        # Generate charts
        print("📈 Generating charts...")
        generate_enhanced_charts(vm_data, summary)
        
        # Generate VM Infrastructure report
        print("📄 Generating VM Infrastructure PDF report...")
        report_path = generator.generate_vm_infrastructure_report(vm_data, summary)
        
        if report_path:
            print("✅ VM Infrastructure report generation completed successfully!")
            print("📁 Report saved: {}".format(report_path))
            return vm_data, summary
        else:
            print("❌ VM Infrastructure report generation failed")
            return None, None
            
    except Exception as e:
        print("❌ Error in VM Infrastructure report main: {}".format(e))
        return None, None

if __name__ == "__main__":
    main()
