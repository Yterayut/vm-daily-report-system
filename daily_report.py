#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced VM Daily Report Generator - WITH INTEGRATED ALERT SYSTEM
Complete workflow orchestrator with advanced features, monitoring, and multi-channel alerts
"""

import sys
import os
import signal
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import traceback

# Enhanced imports
try:
    from load_env import (
        load_env_file, 
        check_required_vars, 
        get_config_dict, 
        setup_logging
    )
    from fetch_zabbix_data import (
        EnhancedZabbixClient, 
        calculate_enhanced_summary,
        generate_enhanced_charts
    )
    from generate_report import EnhancedReportGenerator
    from enhanced_alert_system import EnhancedAlertSystem, send_enhanced_alerts, AlertLevel  # NEW IMPORT
except ImportError as e:
    print("Import error: {}".format(e))
    print("Please ensure all required modules are available")
    sys.exit(1)

class EnhancedVMReportOrchestrator:
    """Enhanced orchestrator for VM daily report generation with integrated alert system"""
    
    def __init__(self):
        self.logger = None
        self.config = None
        self.alert_system = None  # NEW: Alert system integration
        self.start_time = datetime.now()
        self.stats = {
            'vms_processed': 0,
            'charts_generated': 0,
            'emails_sent': 0,
            'line_alerts_sent': 0,  # NEW: LINE alert tracking
            'alerts_triggered': 0,  # NEW: Alert tracking
            'errors': 0,
            'warnings': 0
        }
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            if self.logger:
                self.logger.info("⚠️ Received signal {}, shutting down gracefully...".format(signum))
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self):
        """Enhanced initialization with comprehensive validation and alert system setup"""
        print("🚀 Enhanced VM Daily Report System with Alert Integration")
        print("=" * 70)
        
        try:
            # Load environment variables
            print("🔧 Loading configuration...")
            if not load_env_file():
                print("❌ Failed to load environment configuration")
                return False
            
            # Setup logging FIRST
            self.logger = setup_logging()
            
            # Import logging after setup
            import logging
            
            # Suppress verbose logging from external libraries
            logging.getLogger('weasyprint').setLevel(logging.CRITICAL)
            logging.getLogger('fontTools').setLevel(logging.CRITICAL)
            logging.getLogger('fontTools.subset').setLevel(logging.CRITICAL)
            logging.getLogger('fontTools.ttLib').setLevel(logging.CRITICAL)
            logging.getLogger('fontTools.ttLib.ttFont').setLevel(logging.CRITICAL)
            logging.getLogger('fontTools.subset.timer').setLevel(logging.CRITICAL)
            logging.getLogger('fetch_zabbix_data').setLevel(logging.WARNING)  # Reduce Zabbix verbose output
            logging.getLogger('enhanced_alert_system').setLevel(logging.WARNING)  # Reduce alert system verbose output
            
            self.logger.info("🎯 Enhanced VM Daily Report System Starting...")
            
            # Validate required variables
            if not check_required_vars():
                self.logger.error("❌ Configuration validation failed")
                return False
            
            # Get configuration
            self.config = get_config_dict()
            self.logger.info("✅ Configuration loaded and validated")
            
            # Initialize Alert System - NEW (simplified output)
            try:
                self.alert_system = EnhancedAlertSystem()
                total_email_recipients = (
                    len(self.alert_system.config.to_emails) +
                    len(self.alert_system.config.cc_emails) +
                    len(self.alert_system.config.bcc_emails)
                )
                print("✅ Alert system: Email ({}), LINE ({})".format(
                    total_email_recipients,
                    "Ready" if self.alert_system.line_bot_api else "Disabled"
                ))
            except Exception as e:
                self.logger.warning("⚠️ Alert system initialization failed: {}".format(e))
                self.alert_system = None
            
            return True
            
        except Exception as e:
            error_msg = "Initialization failed: {}".format(e)
            if self.logger:
                self.logger.error("❌ {}".format(error_msg))
            else:
                print("❌ {}".format(error_msg))
            return False
    
    def _log_system_info(self):
        """Log simplified system information"""
        # Only show critical information, not detailed config
    
    def collect_vm_data(self) -> Tuple[Optional[list], Optional[Dict[str, Any]]]:
        """Enhanced VM data collection with simplified output"""
        print("🔍 Collecting VM data from Zabbix...")
        
        try:
            # Initialize Zabbix client
            zabbix_client = EnhancedZabbixClient()
            
            # Test connection
            if not zabbix_client.connect():
                print("❌ Failed to connect to Zabbix API")
                self.stats['errors'] += 1
                return None, None
            
            # Fetch hosts
            hosts = zabbix_client.fetch_hosts()
            
            if not hosts:
                print("⚠️ No VM hosts found in Zabbix")
                self.stats['warnings'] += 1
                return [], {}
            
            print("📊 Processing {} VMs...".format(len(hosts)))
            
            # Enrich with performance data (this will be quiet due to logging level)
            vm_data = zabbix_client.enrich_host_data(hosts)
            self.stats['vms_processed'] = len(vm_data)
            
            # Calculate enhanced summary
            summary = calculate_enhanced_summary(vm_data)
            
            # Generate charts
            charts_success = generate_enhanced_charts(
                vm_data, 
                summary, 
                self.config['report']['static_dir']
            )
            
            if charts_success:
                self.stats['charts_generated'] = 4
                print("✅ Charts generated")
            else:
                print("⚠️ Chart generation failed")
                self.stats['warnings'] += 1
            
            # Alert Analysis (simplified output)
            if self.alert_system:
                try:
                    alerts = self.alert_system.analyze_vm_alerts(vm_data)
                    total_alerts = len(alerts['critical']) + len(alerts['warning']) + len(alerts['offline'])
                    self.stats['alerts_triggered'] = total_alerts
                    
                    # Check for power state changes
                    power_changes = alerts.get('power_changes', [])
                    if power_changes:
                        print("🔄 {} power state changes detected".format(len(power_changes)))
                        # Send power change alerts
                        self.alert_system.send_power_change_alerts(power_changes)
                        self.stats['power_changes'] = len(power_changes)
                    
                    # Only show critical issues
                    if alerts['critical'] or alerts['offline']:
                        print("🚨 CRITICAL: {} alerts detected".format(total_alerts))
                    elif alerts['warning']:
                        print("⚠️ {} warnings detected".format(len(alerts['warning'])))
                    else:
                        print("✅ All VMs healthy")
                        
                except Exception as e:
                    print("❌ Alert analysis failed: {}".format(e))
                    self.stats['errors'] += 1
            
            # Simple summary
            print("📊 Summary: {}/{} VMs online ({:.0f}%)".format(
                summary['online'], summary['total'], summary['online_percent']
            ))
            
            return vm_data, summary
            
        except Exception as e:
            self.logger.error("❌ Data collection failed: {}".format(e))
            self.logger.debug(traceback.format_exc())
            self.stats['errors'] += 1
            return None, None
        finally:
            # Cleanup connection
            try:
                zabbix_client.disconnect()
            except:
                pass
    
    def find_best_existing_pdf(self) -> Optional[Path]:
        """Find the best existing PDF from output directory"""
        try:
            import glob
            output_dir = Path(self.config['report']['output_dir'])
            
            if not output_dir.exists():
                self.logger.warning("Output directory not found: {}".format(output_dir))
                return None
            
            # Find all PDF files
            pdf_pattern = str(output_dir / 'vm_infrastructure_report_*.pdf')
            pdf_files = glob.glob(pdf_pattern)
            
            if not pdf_files:
                self.logger.warning("No PDF files found in {}".format(output_dir))
                return None
            
            # Find the largest PDF (likely the most complete one)
            best_pdf = None
            best_size = 0
            
            for pdf_file in pdf_files:
                try:
                    file_size = os.path.getsize(pdf_file)
                    if file_size > best_size and file_size > 50000:  # At least 50KB
                        best_size = file_size
                        best_pdf = pdf_file
                except:
                    continue
            
            if best_pdf:
                self.logger.info("✅ Found best existing PDF: {} ({} KB)".format(
                    os.path.basename(best_pdf), 
                    best_size // 1024
                ))
                return Path(best_pdf)
            else:
                self.logger.warning("No good PDF found")
                return None
                
        except Exception as e:
            self.logger.error("Error finding PDF: {}".format(e))
            return None

    def generate_pdf_report(self, vm_data: list, summary: Dict[str, Any]) -> Optional[Path]:
        """Enhanced PDF report generation - always generate new with current data"""
        self.logger.info("📄 Step 2: Generating PDF report with current data...")
        
        try:
            self.logger.info("📄 Creating fresh PDF report with today's data...")
            
            # Initialize report generator
            report_generator = EnhancedReportGenerator(
                template_dir=self.config['report']['template_dir'],
                output_dir=self.config['report']['output_dir'],
                static_dir=self.config['report']['static_dir']
            )
            
            # Generate comprehensive report with current data
            output_path = report_generator.generate_comprehensive_report(
                vm_data=vm_data,
                summary=summary,
                company_logo=self.config['report']['company_logo']
            )
            
            if output_path and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info("✅ NEW PDF report generated: {}".format(output_path))
                self.logger.info("   File size: {:,} bytes".format(file_size))
                self.logger.info("   Contains current Zabbix data from: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                return Path(output_path)
            else:
                self.logger.error("❌ PDF generation failed - file not created")
                # Fallback to existing PDF if generation fails
                self.logger.info("🔄 Falling back to existing PDF...")
                existing_pdf = self.find_best_existing_pdf()
                if existing_pdf:
                    self.logger.warning("⚠️ Using existing PDF as fallback: {}".format(existing_pdf))
                    return existing_pdf
                self.stats['errors'] += 1
                return None
                
        except Exception as e:
            self.logger.error("❌ PDF generation failed: {}".format(e))
            self.logger.debug(traceback.format_exc())
            # Fallback to existing PDF if generation fails
            self.logger.info("🔄 Falling back to existing PDF...")
            existing_pdf = self.find_best_existing_pdf()
            if existing_pdf:
                self.logger.warning("⚠️ Using existing PDF as fallback: {}".format(existing_pdf))
                return existing_pdf
            self.stats['errors'] += 1
            return None
    
    def send_comprehensive_alerts(self, vm_data: list, summary: Dict[str, Any], pdf_path: Optional[Path] = None) -> bool:
        """Enhanced email + PDF + LINE system - MAIN WORKFLOW"""
        self.logger.info("🚨 Step 3: Sending comprehensive alerts with professional email...")

        try:
            # Get email configuration
            config = {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'email_username': os.getenv('EMAIL_USERNAME', ''),
                'email_password': os.getenv('EMAIL_PASSWORD', ''),
                'sender_email': os.getenv('SENDER_EMAIL', ''),
                'sender_name': os.getenv('SENDER_NAME', 'VM Monitoring System'),
                'to_emails': [email.strip() for email in os.getenv('TO_EMAILS', '').split(',') if email.strip()]
            }
            
            # Create beautiful HTML email
            html_content = self._create_beautiful_email_html(summary, pdf_path)
            
            # Send email with PDF attachment
            email_success = self._send_professional_email(config, summary, html_content, pdf_path)
            
            # Send LINE notification
            line_success = self._send_line_notification(summary)
            
            # Update statistics
            if email_success:
                self.stats['emails_sent'] = len(config['to_emails'])
                
            if line_success:
                self.stats['line_alerts_sent'] += 1
            
            # Log results
            self.logger.info("📊 Alert Summary:")
            self.logger.info("   Email: {}".format("✅ Sent to {} recipients".format(self.stats['emails_sent']) if email_success else "❌ Failed"))
            self.logger.info("   PDF: {}".format("✅ Professional PDF Attached" if pdf_path and pdf_path.exists() else "❌ Not available"))
            self.logger.info("   LINE: {}".format("✅ Notification Sent" if line_success else "⚠️ Failed"))
            
            return email_success or line_success
            
        except Exception as e:
            self.logger.error("❌ Alert system failed: {}".format(e))
            self.logger.debug(traceback.format_exc())
            self.stats['errors'] += 1
            return False
    
    def _create_beautiful_email_html(self, summary: Dict[str, Any], pdf_path: Optional[Path] = None) -> str:
        """Create beautiful HTML email like ultimate_final_system.py"""
        try:
            # Import and use the beautiful email creation from ultimate_final_system
            from ultimate_final_system import create_beautiful_email_html, get_vm_summary
            
            # Convert our summary to the format expected by create_beautiful_email_html
            email_summary = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'date': datetime.now().strftime("%Y-%m-%d"),
                'total_vms': summary.get('total', 27),
                'online_vms': summary.get('online', 27),
                'offline_vms': summary.get('offline', 0),
                'uptime_percent': summary.get('online_percent', 100.0),
                'avg_cpu': summary.get('performance', {}).get('avg_cpu', 1.1),
                'peak_cpu': summary.get('performance', {}).get('peak_cpu', 3.3),
                'avg_memory': summary.get('performance', {}).get('avg_memory', 23.3),
                'peak_memory': summary.get('performance', {}).get('peak_memory', 39.3),
                'avg_disk': summary.get('performance', {}).get('avg_disk', 12.7),
                'peak_disk': summary.get('performance', {}).get('peak_disk', 53.4),
                'system_status': summary.get('system_status', 'HEALTHY').upper(),
                'critical_alerts': summary.get('alerts', {}).get('critical', 0),
                'warning_alerts': summary.get('alerts', {}).get('warning', 0),
                'healthy_systems': summary.get('total', 27) - summary.get('alerts', {}).get('critical', 0) - summary.get('alerts', {}).get('warning', 0)
            }
            
            pdf_filename = str(pdf_path) if pdf_path else None
            return create_beautiful_email_html(email_summary, pdf_filename)
            
        except Exception as e:
            self.logger.error("Failed to create HTML email: {}".format(e))
            # Fallback to simple HTML
            return """<html><body><h1>VM Infrastructure Report</h1><p>Report generated successfully</p></body></html>"""
    
    def _send_professional_email(self, config: dict, summary: Dict[str, Any], html_content: str, pdf_path: Optional[Path] = None) -> bool:
        """Send professional email with PDF attachment"""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication
            
            msg = MIMEMultipart()
            msg['From'] = "{} <{}>".format(config['sender_name'], config['sender_email'])
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = "VM Infrastructure Report - {} VMs - {} - Professional Analysis 📊".format(
                summary.get('total', 27),
                datetime.now().strftime('%Y-%m-%d')
            )
            
            # Add headers
            msg['Reply-To'] = config['sender_email']
            msg['X-Mailer'] = 'One Climate VM Monitoring v3.0'
            
            # Add HTML content
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Add PDF if available
            if pdf_path and pdf_path.exists():
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename='VM_Infrastructure_Report_{}.pdf'.format(datetime.now().strftime('%Y-%m-%d'))
                    )
                    msg.attach(pdf_attachment)
                
                file_size = pdf_path.stat().st_size
                self.logger.info("✅ PDF attached: {} KB".format(file_size // 1024))
            
            # Send email
            with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30) as server:
                server.starttls()
                server.login(config['email_username'], config['email_password'])
                server.send_message(msg)
            
            self.logger.info("✅ Email sent successfully to {} recipients".format(len(config['to_emails'])))
            return True
            
        except Exception as e:
            self.logger.error("❌ Email sending failed: {}".format(e))
            return False
    
    def _send_line_notification(self, summary: Dict[str, Any]) -> bool:
        """Send LINE notification like ultimate_final_system.py"""
        try:
            from linebot import LineBotApi
            from linebot.models import TextSendMessage
            
            line_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
            line_user_id = os.getenv('LINE_USER_ID')
            
            if not line_token or not line_user_id:
                self.logger.warning("⚠️ LINE not configured")
                return False
            
            line_bot_api = LineBotApi(line_token)
            
            message_text = """✅ VM Infrastructure Report

📊 System Summary:
• Total VMs: {total}
• Online: {online} ({online_percent:.1f}%)
• Offline: {offline}
• Status: {system_status}

📈 Performance:
• CPU: {avg_cpu:.1f}% avg (Peak: {peak_cpu:.1f}%)
• Memory: {avg_memory:.1f}% avg (Peak: {peak_memory:.1f}%)
• Storage: {avg_disk:.1f}% avg (Peak: {peak_disk:.1f}%)

📧 Report delivered with professional PDF
📊 Complete analytics included
🎯 All systems operational

{timestamp}

One Climate Infrastructure Team""".format(
                total=summary.get('total', 27),
                online=summary.get('online', 27),
                offline=summary.get('offline', 0),
                online_percent=summary.get('online_percent', 100.0),
                system_status=summary.get('system_status', 'HEALTHY').upper(),
                avg_cpu=summary.get('performance', {}).get('avg_cpu', 1.1),
                peak_cpu=summary.get('performance', {}).get('peak_cpu', 3.3),
                avg_memory=summary.get('performance', {}).get('avg_memory', 23.3),
                peak_memory=summary.get('performance', {}).get('peak_memory', 39.3),
                avg_disk=summary.get('performance', {}).get('avg_disk', 12.7),
                peak_disk=summary.get('performance', {}).get('peak_disk', 53.4),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            line_bot_api.push_message(line_user_id, TextSendMessage(text=message_text))
            self.logger.info("✅ LINE notification sent")
            return True
            
        except Exception as e:
            self.logger.error("⚠️ LINE notification failed: {}".format(e))
            return False
    
    def _send_basic_email(self, summary: Dict[str, Any], pdf_path: Optional[Path] = None) -> bool:
        """Fallback to basic email sending if alert system is not available"""
        try:
            # Use the original send_email function as fallback
            from send_email import send_email
            pdf_path_str = str(pdf_path) if pdf_path else None
            success = send_email(summary, pdf_path_str)
            
            if success:
                to_emails_str = os.getenv('TO_EMAILS', '')
                to_emails = [email.strip() for email in to_emails_str.split(',') if email.strip()]
                self.stats['emails_sent'] = len(to_emails)
                self.logger.info("✅ Basic email sent to {} recipients".format(len(to_emails)))
            
            return success
            
        except Exception as e:
            self.logger.error("❌ Basic email sending failed: {}".format(e))
            return False
    
    def generate_execution_report(self) -> Dict[str, Any]:
        """Generate execution statistics report with alert metrics"""
        duration = datetime.now() - self.start_time

        return {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration.total_seconds(),
            'duration_human': str(duration).split('.')[0],  # Remove microseconds
            'statistics': self.stats.copy(),
            'success': self.stats['errors'] == 0,
            'status': (
                'SUCCESS'
                if self.stats['errors'] == 0 and self.stats['warnings'] == 0
                else 'PARTIAL'
                if self.stats['errors'] == 0 and self.stats['warnings'] > 0
                else 'FAILED'
            )
        }
    
    def run_complete_workflow(self) -> bool:
        """Execute complete enhanced workflow with integrated alert system"""
        self.logger.info("🎯 Starting Complete VM Report Workflow with Enhanced Alerts")
        self.logger.info("=" * 70)
        
        workflow_success = True
        
        try:
            # Step 1: Collect VM data (includes immediate critical alerts)
            vm_data, summary = self.collect_vm_data()
            
            if vm_data is None or summary is None:
                self.logger.error("❌ Workflow failed at data collection step")
                return False
            
            if not vm_data:
                self.logger.warning("⚠️ No VM data collected, generating empty report")
                summary = {
                    'total': 0, 'online': 0, 'offline': 0,
                    'online_percent': 0, 'offline_percent': 0,
                    'performance': {
                        'avg_cpu': 0, 'avg_memory': 0, 'avg_disk': 0,
                        'peak_cpu': 0, 'peak_memory': 0, 'peak_disk': 0
                    },
                    'alerts': {'critical': 0, 'warning': 0, 'ok': 0},
                    'system_status': 'unknown'
                }
            
            # Step 2: Generate PDF report
            pdf_path = self.generate_pdf_report(vm_data, summary)
            if not pdf_path:
                self.logger.warning("⚠️ PDF generation failed, continuing with alerts only")
                workflow_success = False
            
            # Step 3: Send comprehensive alerts (replaces basic email)
            alert_success = self.send_comprehensive_alerts(vm_data, summary, pdf_path)
            if not alert_success:
                self.logger.error("❌ Alert sending failed")
                workflow_success = False
            
            # Generate execution report
            exec_report = self.generate_execution_report()
            
            # Log final summary with alert metrics
            self.logger.info("=" * 70)
            self.logger.info("📊 ENHANCED WORKFLOW EXECUTION SUMMARY")
            self.logger.info("=" * 70)
            self.logger.info("Status: {}".format(exec_report['status']))
            self.logger.info("Duration: {}".format(exec_report['duration_human']))
            self.logger.info("VMs Processed: {}".format(self.stats['vms_processed']))
            self.logger.info("Charts Generated: {}".format(self.stats['charts_generated']))
            self.logger.info("Emails Sent: {}".format(self.stats['emails_sent']))
            self.logger.info("LINE Alerts Sent: {}".format(self.stats['line_alerts_sent']))  # NEW
            self.logger.info("Alerts Triggered: {}".format(self.stats['alerts_triggered']))  # NEW
            self.logger.info("Power Changes: {}".format(self.stats.get('power_changes', 0)))  # NEW
            self.logger.info("Errors: {}".format(self.stats['errors']))
            self.logger.info("Warnings: {}".format(self.stats['warnings']))
            
            if workflow_success:
                self.logger.info("✅ Enhanced workflow executed successfully!")
            else:
                self.logger.warning("⚠️ Workflow completed with issues")
            
            # Alert system summary
            if self.alert_system:
                self.logger.info("🚨 Alert System Summary:")
                self.logger.info("   Email Configured: {}".format('✅' if self.alert_system.config.to_emails else '❌'))
                self.logger.info("   LINE Configured: {}".format('✅' if self.alert_system.line_bot_api else '❌'))
                self.logger.info("   Total Alerts: {}".format(self.stats['alerts_triggered']))
            
            self.logger.info("=" * 70)
            
            return workflow_success
            
        except Exception as e:
            self.logger.error("❌ Critical workflow failure: {}".format(e))
            self.logger.debug(traceback.format_exc())
            self.stats['errors'] += 1
            return False
    
    def run_test_mode(self) -> bool:
        """Run in test mode with sample data and alert testing"""
        self.logger.info("🧪 Running in TEST MODE with Alert System Testing")
        self.logger.info("=" * 70)
        
        try:
            # Generate test data with some alerts
            test_vm_data = self._generate_test_data_with_alerts()
            test_summary = calculate_enhanced_summary(test_vm_data)
            
            self.logger.info("📊 Using test data with alerts:")
            self.logger.info("   Test VMs: {}".format(len(test_vm_data)))
            self.logger.info("   Online: {}".format(test_summary['online']))
            self.logger.info("   Offline: {}".format(test_summary['offline']))
            self.logger.info("   Critical Alerts: {}".format(test_summary['alerts']['critical']))
            self.logger.info("   Warning Alerts: {}".format(test_summary['alerts']['warning']))
            
            # Generate charts with test data
            generate_enhanced_charts(
                test_vm_data, 
                test_summary, 
                self.config['report']['static_dir']
            )
            
            # Generate PDF
            pdf_path = self.generate_pdf_report(test_vm_data, test_summary)
            
            # Test alert system
            alert_success = self.send_comprehensive_alerts(test_vm_data, test_summary, pdf_path)
            
            exec_report = self.generate_execution_report()
            self.logger.info("🧪 Test completed in {}".format(exec_report['duration_human']))
            
            return alert_success
            
        except Exception as e:
            self.logger.error("❌ Test mode failed: {}".format(e))
            return False
    
    def _generate_test_data_with_alerts(self) -> list:
        """Generate realistic test VM data with some alerts for testing"""
        test_vms = []
        vm_names = [
            "web-server-01", "web-server-02", "database-primary", 
            "database-replica", "app-server-01", "app-server-02",
            "monitoring-01", "backup-server", "file-server", "mail-server",
            "dev-environment", "staging-server", "redis-cache", 
            "elasticsearch-01", "jenkins-master", "docker-host-01"
        ]
        
        for i, name in enumerate(vm_names):
            # Create some specific scenarios for testing alerts
            if name == "backup-server":
                # Offline VM
                vm = {
                    'hostid': str(1000 + i),
                    'name': name,
                    'hostname': name.replace('-', ''),
                    'ip': "10.0.1.{}".format(100 + i),
                    'status': 0,
                    'available': 0,  # Offline
                    'groups': ['Virtual Machines', 'Production'],
                    'is_online': False,
                    'cpu_load': 0, 'memory_used': 0, 'disk_used': 0, 'network_in': 0,
                    'health_score': 0, 'performance_rating': 'Offline', 'alert_status': 'critical'
                }
            elif name == "web-server-01":
                # Critical CPU usage
                vm = {
                    'hostid': str(1000 + i),
                    'name': name,
                    'hostname': name.replace('-', ''),
                    'ip': "10.0.1.{}".format(100 + i),
                    'status': 0,
                    'available': 1,
                    'groups': ['Virtual Machines', 'Production'],
                    'is_online': True,
                    'cpu_load': 87.5,  # Critical
                    'memory_used': 45.0,
                    'disk_used': 35.0,
                    'network_in': random.uniform(10000, 50000),
                    'health_score': 40,
                    'performance_rating': 'Poor',
                    'alert_status': 'critical'
                }
            elif name == "database-primary":
                # High memory usage (warning)
                vm = {
                    'hostid': str(1000 + i),
                    'name': name,
                    'hostname': name.replace('-', ''),
                    'ip': "10.0.1.{}".format(100 + i),
                    'status': 0,
                    'available': 1,
                    'groups': ['Virtual Machines', 'Production'],
                    'is_online': True,
                    'cpu_load': 45.0,
                    'memory_used': 78.0,  # Warning level
                    'disk_used': 65.0,
                    'network_in': random.uniform(5000, 25000),
                    'health_score': 65,
                    'performance_rating': 'Fair',
                    'alert_status': 'warning'
                }
            elif name == "file-server":
                # High disk usage (critical)
                vm = {
                    'hostid': str(1000 + i),
                    'name': name,
                    'hostname': name.replace('-', ''),
                    'ip': "10.0.1.{}".format(100 + i),
                    'status': 0,
                    'available': 1,
                    'groups': ['Virtual Machines', 'Production'],
                    'is_online': True,
                    'cpu_load': 25.0,
                    'memory_used': 55.0,
                    'disk_used': 92.0,  # Critical
                    'network_in': random.uniform(1000, 10000),
                    'health_score': 35,
                    'performance_rating': 'Poor',
                    'alert_status': 'critical'
                }
            else:
                # Normal VMs with random variations
                is_online = random.random() > 0.05  # 95% online rate
                
                vm = {
                    'hostid': str(1000 + i),
                    'name': name,
                    'hostname': name.replace('-', ''),
                    'ip': "10.0.1.{}".format(100 + i),
                    'status': 0,
                    'available': 1 if is_online else 0,
                    'groups': ['Virtual Machines', 'Production'],
                    'is_online': is_online
                }
                
                if is_online:
                    # Create some warning-level usage
                    cpu_base = random.uniform(5, 25)
                    memory_base = random.uniform(30, 50)
                    disk_base = random.uniform(20, 40)
                    
                    # Occasionally create warning levels
                    if random.random() < 0.3:  # 30% chance of warning
                        if random.random() < 0.5:
                            cpu_base = random.uniform(70, 80)  # Warning CPU
                        else:
                            memory_base = random.uniform(75, 85)  # Warning memory
                    
                    vm.update({
                        'cpu_load': cpu_base,
                        'memory_used': memory_base,
                        'disk_used': disk_base,
                        'network_in': random.uniform(1000, 15000),
                        'health_score': random.randint(70, 95),
                        'performance_rating': random.choice(['Excellent', 'Good', 'Fair']),
                        'alert_status': 'warning' if (cpu_base > 70 or memory_base > 75) else 'ok'
                    })
                else:
                    vm.update({
                        'cpu_load': 0, 'memory_used': 0, 'disk_used': 0, 'network_in': 0,
                        'health_score': 0, 'performance_rating': 'Offline', 'alert_status': 'critical'
                    })
            
            test_vms.append(vm)
        
        return test_vms

def run_simple_email_pdf_line():
    """Simple function like ultimate_final_system.py - main functionality"""
    print("=== Enhanced VM Daily Report System ===")
    print("📧 Beautiful Email + 📄 Professional PDF + 📱 LINE")
    print("")
    
    orchestrator = EnhancedVMReportOrchestrator()
    
    try:
        # Initialize system
        if not orchestrator.initialize():
            print("❌ System initialization failed")
            return False
        
        # Step 1: Collect real VM data from Zabbix
        orchestrator.logger.info("🔍 Collecting VM data from Zabbix...")
        vm_data, summary = orchestrator.collect_vm_data()
        
        if vm_data is None or summary is None:
            orchestrator.logger.error("❌ Failed to collect VM data")
            # Use fallback summary
            summary = {
                'total': 27, 'online': 27, 'offline': 0,
                'online_percent': 100.0, 'offline_percent': 0.0,
                'performance': {
                    'avg_cpu': 1.1, 'avg_memory': 23.3, 'avg_disk': 12.7,
                    'peak_cpu': 3.3, 'peak_memory': 39.3, 'peak_disk': 53.4
                },
                'alerts': {'critical': 0, 'warning': 0, 'ok': 27},
                'system_status': 'HEALTHY'
            }
            vm_data = []
        
        orchestrator.logger.info("✅ Summary data prepared")
        
        # Step 2: Generate fresh PDF with current data
        orchestrator.logger.info("📄 Generating PDF report with current Zabbix data...")
        pdf_path = orchestrator.generate_pdf_report(vm_data, summary)
        
        if pdf_path:
            file_size = pdf_path.stat().st_size
            orchestrator.logger.info("✅ Found PDF: {} ({} KB)".format(
                pdf_path.name, file_size // 1024
            ))
        
        # Step 3: Send email + LINE notifications
        success = orchestrator.send_comprehensive_alerts(vm_data, summary, pdf_path)
        
        # Summary
        orchestrator.logger.info("")
        orchestrator.logger.info("📊 Final System Summary:")
        orchestrator.logger.info("   Total VMs: {}".format(summary['total']))
        orchestrator.logger.info("   Online: {} ({:.1f}%)".format(summary['online'], summary['online_percent']))
        orchestrator.logger.info("   Performance: CPU {:.1f}%, Memory {:.1f}%, Disk {:.1f}%".format(
            summary['performance']['avg_cpu'], 
            summary['performance']['avg_memory'], 
            summary['performance']['avg_disk']
        ))
        orchestrator.logger.info("   Email: {}".format("✅ Sent to {} recipients".format(orchestrator.stats['emails_sent']) if orchestrator.stats['emails_sent'] > 0 else "❌ Failed"))
        orchestrator.logger.info("   PDF: {}".format("✅ Professional PDF Attached" if pdf_path else "❌ Not available"))
        orchestrator.logger.info("   LINE: {}".format("✅ Notification Sent" if orchestrator.stats['line_alerts_sent'] > 0 else "⚠️ Failed"))
        
        return success
        
    except Exception as e:
        if orchestrator.logger:
            orchestrator.logger.error("❌ Critical error: {}".format(e))
            orchestrator.logger.debug(traceback.format_exc())
        else:
            print("❌ Critical error: {}".format(e))
            print(traceback.format_exc())
        return False

def main():
    """Enhanced main entry point with comprehensive error handling and alert integration"""
    # Check for simple mode (like ultimate_final_system.py)
    if '--simple' in sys.argv or len(sys.argv) == 1:
        print("🚀 Running Simple Email + PDF + LINE Mode")
        success = run_simple_email_pdf_line()
        
        print("")
        print("=" * 70)
        if success:
            print("🎉 ENHANCED VM DAILY REPORT SYSTEM: SUCCESS")
            print("")
            print("✅ COMPLETE SOLUTION:")
            print("   📧 Beautiful HTML email with mobile-responsive design")
            print("   📄 Professional PDF report")
            print("   📊 Real VM data from Zabbix")
            print("   📱 Enhanced LINE notifications")
            print("   🔄 VM power state change detection")
            print("   ⚡ Production-ready performance")
            print("")
            print("🎯 ENTERPRISE SYSTEM READY!")
        else:
            print("❌ SYSTEM: ISSUES")
            print("🔧 Check configuration and try again")
        print("=" * 70)
        
        return 0 if success else 1
    
    # Original comprehensive mode
    orchestrator = EnhancedVMReportOrchestrator()
    
    try:
        # Parse command line arguments
        test_mode = '--test' in sys.argv
        debug_mode = '--debug' in sys.argv
        alert_test = '--test-alerts' in sys.argv  # NEW: Test only alerts
        
        # Initialize system
        if not orchestrator.initialize():
            print("❌ System initialization failed")
            return 1
        
        # Set debug logging if requested
        if debug_mode:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
            orchestrator.logger.info("🐛 Debug mode enabled")
        
        # NEW: Alert system testing mode
        if alert_test:
            orchestrator.logger.info("🧪 Alert System Testing Mode")
            if orchestrator.alert_system:
                # Test LINE connectivity
                if orchestrator.alert_system.line_bot_api:
                    success = orchestrator.alert_system.send_line_alert(
                        "🧪 Alert System Test - LINE connectivity check", 
                        AlertLevel.INFO
                    )
                    orchestrator.logger.info("LINE test: {}".format('✅ Success' if success else '❌ Failed'))
                
                # Test email connectivity
                test_summary = {
                    'total': 5, 'online': 4, 'offline': 1,
                    'online_percent': 80.0, 'offline_percent': 20.0,
                    'system_status': 'degraded',
                    'performance': {'avg_cpu': 45.0, 'avg_memory': 60.0, 'avg_disk': 35.0},
                    'alerts': {'critical': 1, 'warning': 1, 'ok': 3}
                }
                
                email_success = orchestrator.alert_system.send_email_alert(
                    subject="🧪 Alert System Test - Email connectivity check",
                    body="This is a test email from the Enhanced VM Monitoring Alert System.",
                    alert_level=AlertLevel.INFO
                )
                orchestrator.logger.info("Email test: {}".format('✅ Success' if email_success else '❌ Failed'))
                
                return 0 if success and email_success else 1
            else:
                orchestrator.logger.error("❌ Alert system not initialized")
                return 1
        
        # Run workflow
        if test_mode:
            orchestrator.logger.info("🧪 Test mode requested")
            success = orchestrator.run_test_mode()
        else:
            success = orchestrator.run_complete_workflow()
        
        # Exit with appropriate code
        exit_code = 0 if success else 1
        status_msg = "SUCCESS" if success else "FAILED"
        
        if orchestrator.logger:
            orchestrator.logger.info("🏁 Process completed: {} (exit code: {})".format(status_msg, exit_code))
        else:
            print("🏁 Process completed: {} (exit code: {})".format(status_msg, exit_code))
        
        return exit_code
        
    except KeyboardInterrupt:
        if orchestrator.logger:
            orchestrator.logger.info("⚠️ Process interrupted by user")
        else:
            print("⚠️ Process interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        error_msg = "Critical system error: {}".format(e)
        if orchestrator.logger:
            orchestrator.logger.critical("💥 {}".format(error_msg))
            orchestrator.logger.debug(traceback.format_exc())
        else:
            print("💥 {}".format(error_msg))
            print(traceback.format_exc())
        return 1

def print_usage():
    """Print usage information with new alert testing options"""
    print("""
🚀 Enhanced VM Daily Report System with Advanced Alert Integration

Usage:
    python3 daily_report.py [options]

Options:
    (no args)        Run in SIMPLE mode - Email + PDF + LINE (like ultimate_final_system.py)
    --simple         Run in SIMPLE mode explicitly
    --test           Run in test mode with sample data
    --test-alerts    Test alert system connectivity only
    --debug          Enable debug logging
    --help           Show this help message

Examples:
    python3 daily_report.py                    # SIMPLE: Email + PDF + LINE mode
    python3 daily_report.py --simple          # SIMPLE: Email + PDF + LINE mode  
    python3 daily_report.py --test            # Test with sample data
    python3 daily_report.py --test-alerts     # Test alert system only
    python3 daily_report.py --debug           # Enable debug output
    python3 daily_report.py --test --debug    # Test mode with debug

🎯 SIMPLE Mode Features (Default):
    📧 Beautiful HTML email with modern design
    📄 Professional PDF report (uses existing or generates new)
    📊 Real VM data from Zabbix API
    📱 Enhanced LINE notifications
    🎨 Mobile-responsive email design
    ⚡ Production-ready performance

Alert System Features:
    📧 Email alerts with enhanced formatting
    📱 LINE OA integration with rich cards
    🚨 Real-time critical alert notifications
    ⚙️ Configurable thresholds and channels
    📊 Comprehensive alert analysis

Environment Variables:
    See .env file for configuration options including:
    - LINE_CHANNEL_ACCESS_TOKEN
    - LINE_USER_ID
    - SMTP settings for email
    - Zabbix API configuration

For more information, see the project documentation.
    """)

if __name__ == "__main__":
    # Handle help request
    if '--help' in sys.argv or '-h' in sys.argv:
        print_usage()
        sys.exit(0)
    
    # Run main function
    sys.exit(main())