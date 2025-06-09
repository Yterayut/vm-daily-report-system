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
                self.logger.info(f"⚠️ Received signal {signum}, shutting down gracefully...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self) -> bool:
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
            
            self.logger.info("🎯 Enhanced VM Daily Report System Starting...")
            
            # Validate required variables
            if not check_required_vars():
                self.logger.error("❌ Configuration validation failed")
                return False
            
            # Get configuration
            self.config = get_config_dict()
            self.logger.info("✅ Configuration loaded and validated")
            
            # Initialize Alert System - NEW
            self.logger.info("🚨 Initializing Enhanced Alert System...")
            try:
                self.alert_system = EnhancedAlertSystem()
                self.logger.info("✅ Alert system initialized successfully")
                
                # Log alert configuration
                if self.alert_system.config.to_emails:
                    self.logger.info(f"📧 Email alerts: {len(self.alert_system.config.to_emails)} recipients")
                if self.alert_system.line_bot_api:
                    self.logger.info("📱 LINE alerts: Configured and ready")
                else:
                    self.logger.warning("⚠️ LINE alerts: Not configured")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Alert system initialization failed: {e}")
                self.alert_system = None
            
            # Log system information
            self._log_system_info()
            
            return True
            
        except Exception as e:
            error_msg = f"Initialization failed: {e}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            else:
                print(f"❌ {error_msg}")
            return False
    
    def _log_system_info(self):
        """Log comprehensive system information including alert configuration"""
        self.logger.info("📋 System Information:")
        self.logger.info(f"   Python Version: {sys.version.split()[0]}")
        self.logger.info(f"   Working Directory: {Path.cwd()}")
        self.logger.info(f"   Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"   Zabbix URL: {self.config['zabbix']['url']}")
        total_email_recipients = len(self.config['email']['to_emails'])
        if hasattr(self.alert_system.config, 'cc_emails') and self.alert_system.config.cc_emails:
            total_email_recipients += len(self.alert_system.config.cc_emails)
        if hasattr(self.alert_system.config, 'bcc_emails') and self.alert_system.config.bcc_emails:
            total_email_recipients += len(self.alert_system.config.bcc_emails)
        
        self.logger.info(f"   Output Directory: {self.config['report']['output_dir']}")
        self.logger.info(f"   Email Recipients: {total_email_recipients}")
        
        # NEW: Alert system information
        if self.alert_system:
            self.logger.info("🚨 Alert System Configuration:")
            self.logger.info(f"   CPU Thresholds: Warning {self.alert_system.config.cpu_warning_threshold}%, Critical {self.alert_system.config.cpu_critical_threshold}%")
            self.logger.info(f"   Memory Thresholds: Warning {self.alert_system.config.memory_warning_threshold}%, Critical {self.alert_system.config.memory_critical_threshold}%")
            self.logger.info(f"   Disk Thresholds: Warning {self.alert_system.config.disk_warning_threshold}%, Critical {self.alert_system.config.disk_critical_threshold}%")
            self.logger.info(f"   Email Configured: {bool(self.alert_system.config.to_emails)}")
            self.logger.info(f"   LINE Configured: {bool(self.alert_system.line_bot_api)}")
    
    def collect_vm_data(self) -> Tuple[Optional[list], Optional[Dict[str, Any]]]:
        """Enhanced VM data collection with comprehensive monitoring"""
        self.logger.info("🔍 Step 1: Collecting VM data from Zabbix...")
        
        try:
            # Initialize Zabbix client
            zabbix_client = EnhancedZabbixClient()
            
            # Test connection
            if not zabbix_client.connect():
                self.logger.error("❌ Failed to connect to Zabbix API")
                self.stats['errors'] += 1
                return None, None
            
            self.logger.info("✅ Connected to Zabbix successfully")
            
            # Fetch hosts
            self.logger.info("📡 Fetching VM hosts...")
            hosts = zabbix_client.fetch_hosts()
            
            if not hosts:
                self.logger.warning("⚠️ No VM hosts found in Zabbix")
                self.stats['warnings'] += 1
                return [], {}
            
            self.logger.info(f"📊 Found {len(hosts)} hosts")
            
            # Enrich with performance data
            self.logger.info("🔍 Enriching hosts with performance metrics...")
            vm_data = zabbix_client.enrich_host_data(hosts)
            self.stats['vms_processed'] = len(vm_data)
            
            # Calculate enhanced summary
            self.logger.info("📈 Calculating performance summary...")
            summary = calculate_enhanced_summary(vm_data)
            
            # Generate charts
            self.logger.info("📊 Generating performance charts...")
            charts_success = generate_enhanced_charts(
                vm_data, 
                summary, 
                self.config['report']['static_dir']
            )
            
            if charts_success:
                self.stats['charts_generated'] = 4  # Status, performance, resource, alert charts
                self.logger.info("✅ Charts generated successfully")
            else:
                self.logger.warning("⚠️ Chart generation failed, continuing without charts")
                self.stats['warnings'] += 1
            
            # NEW: Alert Analysis and Immediate Notifications
            if self.alert_system:
                self.logger.info("🚨 Analyzing alerts and sending immediate notifications...")
                try:
                    alerts = self.alert_system.analyze_vm_alerts(vm_data)
                    
                    # Count total alerts
                    total_alerts = len(alerts['critical']) + len(alerts['warning']) + len(alerts['offline'])
                    self.stats['alerts_triggered'] = total_alerts
                    
                    # Send immediate alerts if critical issues found
                    if alerts['critical'] or alerts['offline']:
                        self.logger.warning(f"🚨 CRITICAL ISSUES DETECTED: {len(alerts['critical'])} critical, {len(alerts['offline'])} offline")
                        
                        # Send immediate critical alert
                        from enhanced_alert_system import AlertLevel
                        if alerts['offline']:
                            message = f"🔴 URGENT: {len(alerts['offline'])} VMs are OFFLINE!\n"
                            for alert in alerts['offline']:
                                message += f"• {alert['vm']}\n"
                        else:
                            message = f"🚨 CRITICAL: {len(alerts['critical'])} VMs need immediate attention!\n"
                            for alert in alerts['critical'][:3]:  # Show first 3
                                message += f"• {alert['message']}\n"
                        
                        # Send immediate LINE alert for critical issues
                        if self.alert_system.line_bot_api:
                            success = self.alert_system.send_line_alert(message, AlertLevel.CRITICAL)
                            if success:
                                self.stats['line_alerts_sent'] += 1
                                self.logger.info("✅ Immediate critical alert sent via LINE")
                    
                    elif alerts['warning']:
                        self.logger.info(f"⚠️ {len(alerts['warning'])} warning alerts detected")
                    
                    # Log alert summary
                    self.logger.info("🚨 Alert Analysis Summary:")
                    self.logger.info(f"   Critical Alerts: {len(alerts['critical'])}")
                    self.logger.info(f"   Warning Alerts: {len(alerts['warning'])}")
                    self.logger.info(f"   Offline VMs: {len(alerts['offline'])}")
                    self.logger.info(f"   Healthy VMs: {len(alerts['healthy'])}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Alert analysis failed: {e}")
                    self.stats['errors'] += 1
            
            # Log collection summary
            self.logger.info("📋 Data Collection Summary:")
            self.logger.info(f"   Total VMs: {summary['total']}")
            self.logger.info(f"   Online: {summary['online']} ({summary['online_percent']:.1f}%)")
            self.logger.info(f"   Offline: {summary['offline']} ({summary['offline_percent']:.1f}%)")
            self.logger.info(f"   Critical Alerts: {summary['alerts']['critical']}")
            self.logger.info(f"   Warning Alerts: {summary['alerts']['warning']}")
            self.logger.info(f"   System Status: {summary['system_status'].upper()}")
            
            return vm_data, summary
            
        except Exception as e:
            self.logger.error(f"❌ Data collection failed: {e}")
            self.logger.debug(traceback.format_exc())
            self.stats['errors'] += 1
            return None, None
        finally:
            # Cleanup connection
            try:
                zabbix_client.disconnect()
            except:
                pass
    
    def generate_pdf_report(self, vm_data: list, summary: Dict[str, Any]) -> Optional[Path]:
        """Enhanced PDF report generation"""
        self.logger.info("📄 Step 2: Generating PDF report...")
        
        try:
            # Initialize report generator
            report_generator = EnhancedReportGenerator(
                template_dir=self.config['report']['template_dir'],
                output_dir=self.config['report']['output_dir'],
                static_dir=self.config['report']['static_dir']
            )
            
            # Generate comprehensive report
            output_path = report_generator.generate_comprehensive_report(
                vm_data=vm_data,
                summary=summary,
                company_logo=self.config['report']['company_logo']
            )
            
            if output_path and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info(f"✅ PDF report generated: {output_path}")
                self.logger.info(f"   File size: {file_size:,} bytes")
                return Path(output_path)
            else:
                self.logger.error("❌ PDF generation failed - file not created")
                self.stats['errors'] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"❌ PDF generation failed: {e}")
            self.logger.debug(traceback.format_exc())
            self.stats['errors'] += 1
            return None
    
    def send_comprehensive_alerts(self, vm_data: list, summary: Dict[str, Any], pdf_path: Optional[Path] = None) -> bool:
        """NEW: Send comprehensive alerts through enhanced alert system"""
        self.logger.info("🚨 Step 3: Sending comprehensive alerts...")

        try:
            if not self.alert_system:
                self.logger.warning("⚠️ Alert system not available, falling back to basic email")
                return self._send_basic_email(summary, pdf_path)
            
            # Send comprehensive alerts through all configured channels
            pdf_path_str = str(pdf_path) if pdf_path else None
            results = self.alert_system.send_comprehensive_alert(vm_data, summary, pdf_path_str)
            
            # Update statistics
            if results.get('email', False):
                self.stats['emails_sent'] = len(self.alert_system.config.to_emails)
            
            if results.get('line_text', False) or results.get('line_card', False):
                self.stats['line_alerts_sent'] += 1
            
            # Log results
            successful_channels = [channel for channel, success in results.items() if success]
            failed_channels = [channel for channel, success in results.items() if not success]
            
            if successful_channels:
                self.logger.info(f"✅ Alerts sent successfully via: {', '.join(successful_channels)}")
            
            if failed_channels:
                self.logger.warning(f"⚠️ Failed to send alerts via: {', '.join(failed_channels)}")
                self.stats['errors'] += len(failed_channels)
            
            # Return True if any channel succeeded
            return any(results.values())
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive alert sending failed: {e}")
            self.logger.debug(traceback.format_exc())
            self.stats['errors'] += 1
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
                self.logger.info(f"✅ Basic email sent to {len(to_emails)} recipients")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Basic email sending failed: {e}")
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
            self.logger.info(f"Status: {exec_report['status']}")
            self.logger.info(f"Duration: {exec_report['duration_human']}")
            self.logger.info(f"VMs Processed: {self.stats['vms_processed']}")
            self.logger.info(f"Charts Generated: {self.stats['charts_generated']}")
            self.logger.info(f"Emails Sent: {self.stats['emails_sent']}")
            self.logger.info(f"LINE Alerts Sent: {self.stats['line_alerts_sent']}")  # NEW
            self.logger.info(f"Alerts Triggered: {self.stats['alerts_triggered']}")  # NEW
            self.logger.info(f"Errors: {self.stats['errors']}")
            self.logger.info(f"Warnings: {self.stats['warnings']}")
            
            if workflow_success:
                self.logger.info("✅ Enhanced workflow executed successfully!")
            else:
                self.logger.warning("⚠️ Workflow completed with issues")
            
            # Alert system summary
            if self.alert_system:
                self.logger.info("🚨 Alert System Summary:")
                self.logger.info(f"   Email Configured: {'✅' if self.alert_system.config.to_emails else '❌'}")
                self.logger.info(f"   LINE Configured: {'✅' if self.alert_system.line_bot_api else '❌'}")
                self.logger.info(f"   Total Alerts: {self.stats['alerts_triggered']}")
            
            self.logger.info("=" * 70)
            
            return workflow_success
            
        except Exception as e:
            self.logger.error(f"❌ Critical workflow failure: {e}")
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
            self.logger.info(f"   Test VMs: {len(test_vm_data)}")
            self.logger.info(f"   Online: {test_summary['online']}")
            self.logger.info(f"   Offline: {test_summary['offline']}")
            self.logger.info(f"   Critical Alerts: {test_summary['alerts']['critical']}")
            self.logger.info(f"   Warning Alerts: {test_summary['alerts']['warning']}")
            
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
            self.logger.info(f"🧪 Test completed in {exec_report['duration_human']}")
            
            return alert_success
            
        except Exception as e:
            self.logger.error(f"❌ Test mode failed: {e}")
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
                    'ip': f"10.0.1.{100 + i}",
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
                    'ip': f"10.0.1.{100 + i}",
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
                    'ip': f"10.0.1.{100 + i}",
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
                    'ip': f"10.0.1.{100 + i}",
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
                    'ip': f"10.0.1.{100 + i}",
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

def main():
    """Enhanced main entry point with comprehensive error handling and alert integration"""
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
                    orchestrator.logger.info(f"LINE test: {'✅ Success' if success else '❌ Failed'}")
                
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
                orchestrator.logger.info(f"Email test: {'✅ Success' if email_success else '❌ Failed'}")
                
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
            orchestrator.logger.info(f"🏁 Process completed: {status_msg} (exit code: {exit_code})")
        else:
            print(f"🏁 Process completed: {status_msg} (exit code: {exit_code})")
        
        return exit_code
        
    except KeyboardInterrupt:
        if orchestrator.logger:
            orchestrator.logger.info("⚠️ Process interrupted by user")
        else:
            print("⚠️ Process interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        error_msg = f"Critical system error: {e}"
        if orchestrator.logger:
            orchestrator.logger.critical(f"💥 {error_msg}")
            orchestrator.logger.debug(traceback.format_exc())
        else:
            print(f"💥 {error_msg}")
            print(traceback.format_exc())
        return 1

def print_usage():
    """Print usage information with new alert testing options"""
    print("""
🚀 Enhanced VM Daily Report System with Advanced Alert Integration

Usage:
    python3 daily_report.py [options]

Options:
    --test           Run in test mode with sample data
    --test-alerts    Test alert system connectivity only
    --debug          Enable debug logging
    --help           Show this help message

Examples:
    python3 daily_report.py                    # Normal production run
    python3 daily_report.py --test            # Test with sample data
    python3 daily_report.py --test-alerts     # Test alert system only
    python3 daily_report.py --debug           # Enable debug output
    python3 daily_report.py --test --debug    # Test mode with debug

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
    - CPU/Memory/Disk alert thresholds
    - Alert channel preferences

For more information, see the project documentation.
    """)

if __name__ == "__main__":
    # Handle help request
    if '--help' in sys.argv or '-h' in sys.argv:
        print_usage()
        sys.exit(0)
    
    # Run main function
    sys.exit(main())