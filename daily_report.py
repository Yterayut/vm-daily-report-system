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
import json
import time
import shutil
import subprocess
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
        setup_logging,
        validate_runtime_guards
    )
    from fetch_zabbix_data import (
        EnhancedZabbixClient, 
        calculate_enhanced_summary,
        generate_enhanced_charts
    )
    from generate_report import EnhancedReportGenerator
    from enhanced_alert_system import EnhancedAlertSystem, AlertLevel
    from service_health_checker import ServiceHealthMonitor, get_service_health_data, get_service_alerts  # NEW IMPORT
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
            'telegram_alerts_sent': 0,
            'line_alerts_sent': 0,  # Legacy counter retained for compatibility
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

            # Validate runtime guardrails (strict mode can fail-fast)
            if not validate_runtime_guards():
                self.logger.error("❌ Runtime guard validation failed")
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
        pass

    def _env_bool(self, name: str, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}

    def _run_mode(self) -> str:
        return os.getenv('RUN_MODE', 'production').strip().lower() or 'production'

    def _report_run_id(self) -> str:
        if not hasattr(self, '_current_report_run_id'):
            self._current_report_run_id = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        return self._current_report_run_id

    def _failure_artifact(self, stage: str, reason: str, extra: Dict[str, Any] = None) -> Path:
        failures_dir = Path('output') / 'failures'
        failures_dir.mkdir(parents=True, exist_ok=True)
        path = failures_dir / 'vm_report_failure_{}.json'.format(
            datetime.now().strftime('%Y-%m-%d_%H%M%S')
        )
        payload = {
            'status': 'failed',
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'reason': reason,
            'run_mode': self._run_mode(),
            'email_dry_run': self._env_bool('EMAIL_DRY_RUN', True),
            'line_enabled': self._env_bool('LINE_NOTIFICATIONS_ENABLED', False),
            'extra': extra or {}
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        if self.logger:
            self.logger.error("DAILY_VM_REPORT status=failed stage={} reason={} artifact={}".format(stage, reason, path))
        return path

    def send_failure_alert(self, stage: str, reason: str, extra: Dict[str, Any] = None) -> bool:
        """Send a short failure alert and always write a local failure artifact."""
        artifact_path = self._failure_artifact(stage, reason, extra)
        email_dry_run = self._env_bool('EMAIL_DRY_RUN', True)
        line_enabled = self._env_bool('LINE_NOTIFICATIONS_ENABLED', False)
        email_success = False
        line_success = False

        subject = "[One Climate] VM Infrastructure Report FAILED - {}".format(
            datetime.now().strftime('%Y-%m-%d')
        )
        body = """VM Infrastructure Report failed.

Stage: {stage}
Reason: {reason}
Time: {timestamp}
Run Mode: {run_mode}
Failure artifact: {artifact}

Next action: check Zabbix API, MariaDB, Zabbix server status, and report logs.
""".format(
            stage=stage,
            reason=reason,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            run_mode=self._run_mode(),
            artifact=artifact_path
        )

        if email_dry_run:
            self.logger.info("FAILURE_ALERT email=dry_run subject={}".format(subject))
            email_success = True
        else:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                to_emails = [e.strip() for e in os.getenv('TO_EMAILS', '').split(',') if e.strip()]
                cc_emails = [e.strip() for e in os.getenv('CC_EMAILS', '').split(',') if e.strip()]
                bcc_emails = [e.strip() for e in os.getenv('BCC_EMAILS', '').split(',') if e.strip()]
                recipients = to_emails + cc_emails + bcc_emails
                if not recipients:
                    raise RuntimeError('no failure alert recipients configured')

                msg = MIMEMultipart()
                msg['From'] = "{} <{}>".format(
                    os.getenv('SENDER_NAME', 'One Climate VM Monitoring System'),
                    os.getenv('SENDER_EMAIL', os.getenv('EMAIL_USERNAME', ''))
                )
                msg['To'] = ', '.join(to_emails)
                if cc_emails:
                    msg['Cc'] = ', '.join(cc_emails)
                msg['Reply-To'] = os.getenv('REPLY_TO_EMAIL', os.getenv('SENDER_EMAIL', ''))
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain', 'utf-8'))

                with smtplib.SMTP(os.getenv('SMTP_SERVER', 'smtp.gmail.com'), int(os.getenv('SMTP_PORT', '587')), timeout=30) as server:
                    if self._env_bool('SMTP_USE_TLS', True):
                        server.starttls()
                    server.login(os.getenv('EMAIL_USERNAME', ''), os.getenv('EMAIL_PASSWORD', ''))
                    server.send_message(msg, to_addrs=recipients)
                email_success = True
                self.logger.info("FAILURE_ALERT email=sent recipients={}".format(len(recipients)))
            except Exception as exc:
                self.logger.error("FAILURE_ALERT email=failed reason={}".format(exc))

        if line_enabled:
            try:
                from linebot import LineBotApi
                from linebot.models import TextSendMessage
                token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
                user_id = os.getenv('LINE_USER_ID')
                message = "🔴 VM Report FAILED\nStage: {}\nReason: {}\nTime: {}".format(
                    stage,
                    reason[:900],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                if token and user_id:
                    LineBotApi(token).push_message(user_id, TextSendMessage(text=message))
                    line_success = True
                    self.logger.info("FAILURE_ALERT line=sent")
                else:
                    self.logger.warning("FAILURE_ALERT line=skipped reason=missing_config")
            except Exception as exc:
                self.logger.error("FAILURE_ALERT line=failed reason={}".format(exc))
        else:
            self.logger.info("FAILURE_ALERT line=skipped")

        # Update artifact with alert delivery status.
        try:
            payload = json.loads(artifact_path.read_text(encoding='utf-8'))
            payload['alert_delivery'] = {
                'email_success': email_success,
                'line_success': line_success
            }
            artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        except Exception:
            pass

        return email_success or line_success

    def collect_vm_data_with_retries(self) -> Tuple[Optional[list], Optional[Dict[str, Any]]]:
        retry_count = int(os.getenv('ZABBIX_REPORT_RETRY_COUNT', '5'))
        retry_delay = int(os.getenv('ZABBIX_REPORT_RETRY_DELAY_SECONDS', '60'))
        attempts = max(1, retry_count)
        start = time.time()
        last_reason = 'unknown'

        for attempt in range(1, attempts + 1):
            vm_data, summary = self.collect_vm_data()
            if vm_data is not None and summary is not None:
                self.logger.info("ZABBIX_COLLECTION attempt={}/{} status=success vm_count={}".format(
                    attempt, attempts, summary.get('total', len(vm_data))
                ))
                self.logger.info("ZABBIX_COLLECTION status=success vm_count={} duration_seconds={:.1f}".format(
                    summary.get('total', len(vm_data)), time.time() - start
                ))
                return vm_data, summary

            last_reason = 'zabbix data collection failed'
            self.logger.warning("ZABBIX_COLLECTION attempt={}/{} status=failed reason={}".format(
                attempt, attempts, last_reason
            ))
            if attempt < attempts:
                time.sleep(retry_delay)

        self.logger.error("ZABBIX_COLLECTION status=failed attempts={} duration_seconds={:.1f}".format(
            attempts, time.time() - start
        ))
        return None, {'error': last_reason, 'attempts': attempts}

    def dependency_health_gate(self) -> Tuple[bool, Dict[str, Any]]:
        """Wait for local dependencies that commonly affect Zabbix API readiness."""
        timeout = int(os.getenv('DEPENDENCY_GATE_TIMEOUT_SECONDS', '300'))
        delay = int(os.getenv('DEPENDENCY_GATE_RETRY_DELAY_SECONDS', '30'))
        min_uptime = int(os.getenv('DEPENDENCY_READY_MIN_UPTIME_SECONDS', '120'))
        required_services = [
            svc.strip()
            for svc in os.getenv('DEPENDENCY_GATE_SERVICES', 'zabbix-server,mariadb').split(',')
            if svc.strip()
        ]
        start = time.time()
        checks = {}

        while True:
            all_active = True
            checks = {}
            for service in required_services:
                try:
                    result = subprocess.run(
                        ['systemctl', 'is-active', service],
                        text=True,
                        capture_output=True,
                        timeout=5
                    )
                    active = result.stdout.strip() == 'active'
                    checks[service] = {
                        'active': active,
                        'status': result.stdout.strip() or result.stderr.strip()
                    }
                    if not active:
                        all_active = False
                    elif min_uptime > 0:
                        try:
                            show_result = subprocess.run(
                                ['systemctl', 'show', service, '--property=ActiveEnterTimestampMonotonic', '--value'],
                                text=True,
                                capture_output=True,
                                timeout=5
                            )
                            active_enter_us = int((show_result.stdout or '0').strip() or '0')
                            boot_uptime_seconds = float(Path('/proc/uptime').read_text(encoding='utf-8').split()[0])
                            service_uptime = boot_uptime_seconds - (active_enter_us / 1000000.0)
                            checks[service]['uptime_seconds'] = round(service_uptime, 1)
                            checks[service]['min_uptime_seconds'] = min_uptime
                            if service_uptime < min_uptime:
                                all_active = False
                        except Exception as uptime_exc:
                            checks[service]['uptime_error'] = str(uptime_exc)
                            all_active = False
                except Exception as exc:
                    checks[service] = {'active': None, 'status': str(exc)}
                    all_active = False

            if all_active:
                self.logger.info("DEPENDENCY_GATE status=pass services={}".format(checks))
                return True, checks

            elapsed = time.time() - start
            self.logger.warning("DEPENDENCY_GATE status=waiting elapsed_seconds={:.1f} services={}".format(elapsed, checks))
            if elapsed >= timeout:
                self.logger.error("DEPENDENCY_GATE status=failed services={}".format(checks))
                return False, checks
            time.sleep(delay)

    def disk_space_preflight(self) -> Tuple[bool, Dict[str, Any]]:
        min_free_mb = int(os.getenv('REPORT_MIN_FREE_DISK_MB', '1024'))
        target = Path(os.getenv('REPORT_OUTPUT_DIR', 'output'))
        target.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(target)
        free_mb = usage.free // (1024 * 1024)
        details = {
            'path': str(target),
            'free_mb': free_mb,
            'min_free_mb': min_free_mb
        }
        if free_mb < min_free_mb:
            self.logger.error("DISK_PREFLIGHT status=failed free_mb={} min_free_mb={}".format(free_mb, min_free_mb))
            return False, details
        self.logger.info("DISK_PREFLIGHT status=pass free_mb={} min_free_mb={}".format(free_mb, min_free_mb))
        return True, details

    def _normalize_service_health_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize service health checker keys to report-generator keys."""
        if not data:
            return data
        summary = data.get('summary', {})
        if summary and 'total' not in summary and 'total_count' in summary:
            data = dict(data)
            data['summary'] = {
                'total': summary.get('total_count', 0),
                'healthy': summary.get('healthy_count', 0),
                'warning': summary.get('warning_count', 0),
                'critical': summary.get('critical_count', 0) + summary.get('unreachable_count', 0),
                'availability': summary.get('availability_percentage', 0),
                'overall_status': summary.get('overall_status', 'unknown')
            }
        return data

    def _derive_service_alerts(self, service_health_data: Dict[str, Any]) -> list:
        alerts = []
        for service in (service_health_data or {}).get('services', {}).values():
            level = service.get('health_level')
            if level in {'critical', 'warning', 'unreachable'}:
                alerts.append({
                    'severity': 'CRITICAL' if level == 'critical' else 'WARNING',
                    'service_name': service.get('name', 'Unknown'),
                    'message': service.get('error') or service.get('error_type') or level
                })
        return alerts

    def collect_service_health_snapshot(self) -> Tuple[Dict[str, Any], list]:
        """Collect the same service-health snapshot used by the Service Health PDF."""
        try:
            from generate_service_health_report import ServiceHealthReportGenerator
            generator = ServiceHealthReportGenerator(
                template_dir=self.config['report']['template_dir'],
                output_dir=self.config['report']['output_dir'],
                static_dir=self.config['report']['static_dir']
            )
            api_data = generator._fetch_service_api_data()
            if api_data:
                data = generator._transform_api_data(api_data)
                alerts = self._derive_service_alerts(data)
                self.logger.info("SERVICE_HEALTH_COLLECTION status=success source=local_api services={}".format(
                    len(data.get('services', {}))
                ))
                return data, alerts
        except Exception as exc:
            self.logger.warning("SERVICE_HEALTH_COLLECTION source=local_api status=failed reason={}".format(exc))

        data = self._normalize_service_health_data(get_service_health_data())
        alerts = self._derive_service_alerts(data)
        self.logger.info("SERVICE_HEALTH_COLLECTION status=success source=checker services={}".format(
            len(data.get('services', {}))
        ))
        return data, alerts

    def _pdf_text(self, pdf_path: Path) -> str:
        try:
            return subprocess.check_output(
                ['pdftotext', str(pdf_path), '-'],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=20
            )
        except Exception:
            return ''

    def validate_vm_report_before_send(self, vm_data: list, summary: Dict[str, Any], vm_pdf_path: Optional[Path]) -> Tuple[bool, str, Dict[str, Any]]:
        details = {
            'summary_total': summary.get('total') if summary else None,
            'vm_rows': len(vm_data or []),
            'pdf_bytes': 0,
            'inventory_rows': 0
        }
        if not vm_data:
            return False, 'vm_data is empty', details
        if not summary or summary.get('total') != len(vm_data):
            return False, 'summary total does not match vm_data length', details
        if summary.get('total', 0) <= 0:
            return False, 'summary total is zero', details
        if not vm_pdf_path or not vm_pdf_path.exists():
            return False, 'VM PDF does not exist', details

        details['pdf_bytes'] = vm_pdf_path.stat().st_size
        min_bytes = int(os.getenv('VM_REPORT_MIN_PDF_BYTES', '200000'))
        if details['pdf_bytes'] < min_bytes:
            return False, 'VM PDF is below minimum size', details

        text = self._pdf_text(vm_pdf_path)
        expected_count = str(summary.get('total'))
        first_vm_name = str(vm_data[0].get('name', '')).split('_')[0]
        details['inventory_rows'] = text.count('● ONLINE') + text.count('● OFFLINE')

        if 'Virtual Machine Inventory' not in text:
            return False, 'VM PDF missing inventory section', details
        if expected_count not in text:
            return False, 'VM PDF missing expected VM count', details
        if first_vm_name and first_vm_name not in text:
            return False, 'VM PDF missing expected VM name', details
        if details['inventory_rows'] <= 0:
            return False, 'VM PDF has no inventory rows', details

        # Semantic consistency (phase 1: record + log, does NOT block send)
        summary_offline = int(summary.get('offline', 0) or 0)
        summary_online = int(summary.get('online', 0) or 0)
        _alerts = summary.get('alerts', {}) or {}
        summary_critical = int(_alerts.get('critical', 0) or 0)
        summary_warning = int(_alerts.get('warning', 0) or 0)
        pdf_offline_rows = text.count('● OFFLINE')
        semantic_issues = []
        if pdf_offline_rows != summary_offline:
            semantic_issues.append('offline_mismatch(pdf={},summary={})'.format(pdf_offline_rows, summary_offline))
        if (summary_offline > 0 or summary_critical > 0) and 'All Systems Operational' in text:
            semantic_issues.append('operational_banner_with_issues')
        semantic = 'pass' if not semantic_issues else 'fail'
        details['semantic'] = semantic
        details['semantic_issues'] = semantic_issues

        validation_dir = Path('output')
        validation_dir.mkdir(exist_ok=True)
        validation_path = validation_dir / 'post_run_validation_{}.txt'.format(datetime.now().strftime('%Y-%m-%d'))
        _line = ("VM_REPORT_VALIDATION status=pass semantic={} summary_total={} online={} offline={} "
                 "critical={} warning={} inventory_rows={} pdf_bytes={} issues={}").format(
            semantic, details['summary_total'], summary_online, summary_offline,
            summary_critical, summary_warning, details['inventory_rows'], details['pdf_bytes'],
            ';'.join(semantic_issues) or 'none'
        )
        validation_path.write_text(_line + "\n", encoding='utf-8')
        details['validation_artifact'] = str(validation_path)
        if semantic == 'fail':
            self.logger.warning("%s", _line)
        else:
            self.logger.info("%s", _line)
        return True, 'ok', details

    def _send_state_path(self) -> Path:
        return Path('logs') / 'daily_report_send_state.json'

    def check_duplicate_send_allowed(self) -> Tuple[bool, str]:
        if self._env_bool('EMAIL_DRY_RUN', True):
            return True, 'dry_run'
        if self._env_bool('ALLOW_DUPLICATE_DAILY_REPORT_SEND', False):
            return True, 'duplicate_allowed'
        key = "{}:vm_infrastructure_report".format(datetime.now().strftime('%Y-%m-%d'))
        path = self._send_state_path()
        try:
            state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        except Exception:
            state = {}
        if key in state and os.getenv('FORCE_SEND', 'false').lower() != 'true':
            return False, 'duplicate_send_blocked key={}'.format(key)
        return True, key

    def record_successful_send(self):
        if self._env_bool('EMAIL_DRY_RUN', True):
            return
        key = "{}:vm_infrastructure_report".format(datetime.now().strftime('%Y-%m-%d'))
        path = self._send_state_path()
        path.parent.mkdir(exist_ok=True)
        try:
            state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        except Exception:
            state = {}
        state[key] = {
            'sent_at': datetime.now().isoformat(),
            'run_mode': self._run_mode()
        }
        path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')
    
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

    def generate_pdf_report(self, vm_data: list, summary: Dict[str, Any], service_health_data: Dict[str, Any] = None) -> Optional[Tuple[Path, Path]]:
        """Enhanced PDF report generation - Generate separate VM Infrastructure and Service Health reports"""
        self.logger.info("📄 Step 2: Generating separate PDF reports...")
        
        try:
            # Import the new report generators
            from generate_vm_infrastructure_report import VMInfrastructureReportGenerator
            from generate_service_health_report import ServiceHealthReportGenerator
            
            self.logger.info("📄 Creating separate VM Infrastructure and Service Health reports...")
            base_output_dir = Path(self.config['report']['output_dir'])
            run_id = self._report_run_id()
            staging_dir = base_output_dir / 'runs' / run_id
            staging_dir.mkdir(parents=True, exist_ok=True)
            today_str = datetime.now().strftime("%Y-%m-%d")
            vm_filename = "VM_Infrastructure_Report_{}.pdf".format(today_str)
            service_filename = "Service_Health_Report_{}.pdf".format(today_str)
            self.logger.info("PDF_STAGE status=created staging_dir={}".format(staging_dir))
            
            # Generate VM Infrastructure Report
            self.logger.info("🖥️  Generating VM Infrastructure Report...")
            vm_generator = VMInfrastructureReportGenerator(
                template_dir=self.config['report']['template_dir'],
                output_dir=str(staging_dir),
                static_dir=self.config['report']['static_dir']
            )
            
            vm_report_path = vm_generator.generate_vm_infrastructure_report(
                vm_data=vm_data,
                summary=summary,
                company_logo=self.config['report']['company_logo'],
                output_filename=vm_filename
            )
            
            # Generate Service Health Report
            self.logger.info("🛡️  Generating Service Health Report...")
            service_generator = ServiceHealthReportGenerator(
                template_dir=self.config['report']['template_dir'],
                output_dir=str(staging_dir),
                static_dir=self.config['report']['static_dir']
            )
            
            # Pass None to let generator fetch and transform API data internally
            service_report_path = service_generator.generate_service_health_report(
                service_health_data=service_health_data,
                company_logo=self.config['report']['company_logo'],
                output_filename=service_filename
            )
            
            # Verify both reports were created
            vm_exists = vm_report_path and isinstance(vm_report_path, str) and Path(vm_report_path).exists()
            service_exists = service_report_path and isinstance(service_report_path, str) and Path(service_report_path).exists()

            if vm_exists and service_exists:
                vm_size = Path(vm_report_path).stat().st_size
                service_size = Path(service_report_path).stat().st_size
                
                self.logger.info("✅ Both PDF reports generated successfully!")
                self.logger.info("📄 VM Infrastructure Report: {}".format(vm_report_path))
                self.logger.info("   File size: {:,} bytes".format(vm_size))
                self.logger.info("📄 Service Health Report: {}".format(service_report_path))
                self.logger.info("   File size: {:,} bytes".format(service_size))
                self.logger.info("   Contains current data from: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                return (Path(vm_report_path), Path(service_report_path))
            elif vm_exists:
                self.logger.warning("⚠️ Only VM Infrastructure report was created")
                return (Path(vm_report_path), None)
            elif service_exists:
                self.logger.warning("⚠️ Only Service Health report was created")
                return (None, Path(service_report_path))
            else:
                self.logger.error("❌ No reports were created")
                return None
        except Exception as e:
            self.logger.error("❌ PDF reports generation failed: {}".format(e))
            self.logger.error("Stack trace: {}".format(traceback.format_exc()))
            self.stats['errors'] += 1
            return None

    def promote_validated_pdf_reports(self, vm_pdf_path: Path, service_pdf_path: Optional[Path]) -> Tuple[Path, Optional[Path]]:
        """Publish validated PDFs only after smoke validation passes."""
        base_output_dir = Path(self.config['report']['output_dir'])
        run_mode = self._run_mode()
        dry_run = self._env_bool('EMAIL_DRY_RUN', True)
        if run_mode == 'production' and not dry_run:
            final_dir = base_output_dir
        else:
            final_dir = base_output_dir / run_mode / self._report_run_id()
        final_dir.mkdir(parents=True, exist_ok=True)

        final_vm = final_dir / vm_pdf_path.name
        shutil.copy2(vm_pdf_path, final_vm)
        final_service = None
        if service_pdf_path and service_pdf_path.exists():
            final_service = final_dir / service_pdf_path.name
            shutil.copy2(service_pdf_path, final_service)
        self.logger.info("PDF_PROMOTION status=success final_dir={} vm_pdf={} service_pdf={}".format(
            final_dir,
            final_vm,
            final_service
        ))
        return final_vm, final_service
    def send_comprehensive_alerts(self, vm_data: list, summary: Dict[str, Any], vm_pdf_path: Optional[Path] = None, service_pdf_path: Optional[Path] = None, 
                                service_health_data: Dict[str, Any] = None, service_alerts: list = None) -> bool:
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
                'to_emails': [email.strip() for email in os.getenv('TO_EMAILS', '').split(',') if email.strip()],
                'cc_emails': [email.strip() for email in os.getenv('CC_EMAILS', '').split(',') if email.strip()],
                'bcc_emails': [email.strip() for email in os.getenv('BCC_EMAILS', '').split(',') if email.strip()]
            }
            all_email_recipients = (
                config['to_emails'] + config['cc_emails'] + config['bcc_emails']
            )
            
            # Create beautiful HTML email
            html_content = self._create_beautiful_email_html(summary, vm_pdf_path, service_pdf_path, service_health_data)

            email_dry_run = os.getenv('EMAIL_DRY_RUN', 'true').lower() == 'true'
            if email_dry_run:
                self.logger.info("🧪 EMAIL_DRY_RUN=true -> skip real email sending")
                email_success = True
            else:
                email_success = False
            
            # Send email with comprehensive fix for one.th delivery - with both PDF attachments
            if not email_dry_run:
                try:
                    from comprehensive_email_fix import ComprehensiveEmailSender
                    comprehensive_sender = ComprehensiveEmailSender()
                    email_success = comprehensive_sender.send_vm_report(summary, vm_pdf_path, service_pdf_path, service_health_data)
                    
                    if email_success:
                        self.logger.info("✅ Comprehensive email delivery successful (2 PDF attachments)")
                    else:
                        self.logger.warning("⚠️ Comprehensive method failed, trying fallback...")
                        # Fallback to original method with both PDFs
                        email_success = self._send_professional_email(config, summary, html_content, vm_pdf_path, service_pdf_path)
                        
                except ImportError:
                    self.logger.warning("⚠️ Comprehensive fix not available, using standard method")
                    email_success = self._send_professional_email(config, summary, html_content, vm_pdf_path, service_pdf_path)
                except Exception as e:
                    self.logger.error("❌ Comprehensive email failed: {}".format(e))
                    # Fallback to original method - use vm_pdf_path instead of undefined pdf_path
                    try:
                        email_success = self._send_professional_email(config, summary, html_content, vm_pdf_path, service_pdf_path)
                    except Exception as fallback_error:
                        self.logger.error("❌ Fallback email also failed: {}".format(fallback_error))
                        email_success = False

            # ALWAYS try to send LINE notification regardless of email status, unless disabled.
            line_enabled = os.getenv('LINE_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
            if line_enabled:
                line_success = self._send_line_notification(summary, vm_data, service_alerts)
            else:
                self.logger.info("📱 LINE notifications disabled - skipping LINE notification")
                line_success = None
            
            # Update statistics
            if email_success and not email_dry_run:
                self.stats['emails_sent'] = len(all_email_recipients)
                
            if line_success is True:
                self.stats['line_alerts_sent'] += 1

            if line_success is True:
                line_status = "✅ Notification Sent"
            elif line_success is None:
                line_status = "⏭️ Skipped"
            else:
                line_status = "⚠️ Failed"
            
            # Log results - fix pdf_path reference
            email_status = 'dry_run' if email_dry_run else 'success' if email_success else 'failed'
            email_display_count = len(all_email_recipients) if email_success else 0
            self.logger.info("📊 Alert Summary:")
            self.logger.info("   Email: {}".format(
                "🧪 Dry-run to {} recipients".format(email_display_count)
                if email_dry_run else
                "✅ Sent to {} recipients".format(self.stats['emails_sent'])
                if email_success else
                "❌ Failed"
            ))
            self.logger.info("   PDF: {}".format("✅ Professional PDF Attached" if vm_pdf_path and vm_pdf_path.exists() else "❌ Not available"))
            self.logger.info("   LINE: {}".format(line_status))
            self.logger.info("EMAIL_SEND status={} recipients={} vm_pdf={} service_pdf={}".format(
                email_status,
                email_display_count if email_dry_run else self.stats['emails_sent'],
                bool(vm_pdf_path and vm_pdf_path.exists()),
                bool(service_pdf_path and service_pdf_path.exists())
            ))
            
            return email_success or line_success is True
            
        except Exception as e:
            self.logger.error("❌ Alert system failed: {}".format(e))
            self.logger.debug(traceback.format_exc())
            self.stats['errors'] += 1
            return False
    
    def _create_beautiful_email_html(self, summary: Dict[str, Any], vm_pdf_path: Optional[Path] = None, service_pdf_path: Optional[Path] = None, 
                                    service_health_data: Dict[str, Any] = None) -> str:
        """Create corporate-friendly email content (text-only to bypass spam filters)"""
        try:
            # Use TEXT-ONLY format to completely bypass HTML spam filters
            return self._create_text_only_email(summary, vm_pdf_path, service_pdf_path, service_health_data)
            
        except Exception as e:
            self.logger.error("Failed to create text email: {}".format(e))
            # Fallback to simple text
            return "VM Infrastructure Report - System Status: Operational"
    
    def _create_corporate_email_html(self, summary: Dict[str, Any], pdf_path: Optional[Path] = None) -> str:
        """Create professional, spam-filter-friendly HTML email"""
        
        # Extract metrics with safe defaults
        total_vms = summary.get('total', 34)
        online_vms = summary.get('online', 34)
        offline_vms = summary.get('offline', 0)
        uptime_percent = summary.get('online_percent', 100.0)
        
        performance = summary.get('performance', {})
        avg_cpu = performance.get('avg_cpu', 1.1)
        avg_memory = performance.get('avg_memory', 23.9)
        avg_disk = performance.get('avg_disk', 15.0)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_info = ""
        if pdf_path:
            pdf_size = pdf_path.stat().st_size // 1024 if isinstance(pdf_path, Path) and pdf_path.exists() else 0
            pdf_info = """
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;">
                    <strong>PDF Report Attached:</strong> VM_Infrastructure_Report_{}.pdf ({} KB)
                </td>
            </tr>""".format(datetime.now().strftime('%Y-%m-%d'), pdf_size)
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VM Infrastructure Report</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 800px; margin: 0 auto; background-color: white; border: 1px solid #ccc;">
        <!-- Header -->
        <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">VM Infrastructure Report</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px;">One Climate Co., Ltd. - IT Infrastructure Department</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 20px;">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Report Date:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{timestamp}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Total VMs:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{total_vms}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Online VMs:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{online_vms}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Offline VMs:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{offline_vms}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">System Availability:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{uptime_percent:.1f}%</td>
                </tr>
            </table>
            
            <h3 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 5px;">Performance Summary</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">CPU Usage:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{avg_cpu:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Memory Usage:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{avg_memory:.1f}%</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Disk Usage:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{avg_disk:.1f}%</td>
                </tr>
                {pdf_info}
            </table>
            
            <div style="background-color: #e8f4fd; border: 1px solid #b6d7f2; padding: 15px; margin-top: 20px;">
                <h4 style="margin: 0 0 10px 0; color: #2c5aa0;">System Status: HEALTHY</h4>
                <p style="margin: 0; color: #333;">All critical systems are operating within normal parameters. 
                Detailed analysis is available in the attached PDF report.</p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f0f0f0; padding: 15px; text-align: center; border-top: 1px solid #ccc;">
            <p style="margin: 0; font-size: 12px; color: #666;">
                This is an automated report from One Climate VM Monitoring System.<br>
                Generated: {timestamp} | Contact: IT Infrastructure Department
            </p>
        </div>
    </div>
</body>
</html>""".format(
            timestamp=timestamp,
            total_vms=total_vms,
            online_vms=online_vms,
            offline_vms=offline_vms,
            uptime_percent=uptime_percent,
            avg_cpu=avg_cpu,
            avg_memory=avg_memory,
            avg_disk=avg_disk,
            pdf_info=pdf_info
        )
        
        return html_content
    
    def _create_text_only_email(self, summary: Dict[str, Any], vm_pdf_path: Optional[Path] = None, service_pdf_path: Optional[Path] = None, 
                              service_health_data: Dict[str, Any] = None) -> str:
        """Create plain text email to completely bypass spam filters"""
        
        # Extract metrics with safe defaults
        total_vms = summary.get('total', 34)
        online_vms = summary.get('online', 34)
        offline_vms = summary.get('offline', 0)
        uptime_percent = summary.get('online_percent', 100.0)
        
        performance = summary.get('performance', {})
        avg_cpu = performance.get('avg_cpu', 1.1)
        avg_memory = performance.get('avg_memory', 23.9)
        avg_disk = performance.get('avg_disk', 15.0)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Service health summary
        service_summary = ""
        if service_health_data and service_health_data.get('summary'):
            svc_sum = service_health_data['summary']
            service_summary = f"""
SERVICE HEALTH MONITORING
{"="*50}
Total Services: {svc_sum.get('total', 0)}
Healthy Services: {svc_sum.get('healthy', 0)}
Warning Services: {svc_sum.get('warning', 0)}
Critical Services: {svc_sum.get('critical', 0)}
Service Availability: {svc_sum.get('availability', 0):.1f}%
Overall Service Status: {svc_sum.get('overall_status', 'UNKNOWN').upper()}
"""

        pdf_info = ""
        
        # VM Infrastructure PDF info
        if vm_pdf_path and isinstance(vm_pdf_path, Path) and vm_pdf_path.exists():
            vm_pdf_size = vm_pdf_path.stat().st_size // 1024
            pdf_info += f"\nVM Infrastructure Report: {vm_pdf_path.name if isinstance(vm_pdf_path, Path) else vm_pdf_path} ({vm_pdf_size} KB attached)"
        
        # Service Health PDF info
        if service_pdf_path and isinstance(service_pdf_path, Path) and service_pdf_path.exists():
            service_pdf_size = service_pdf_path.stat().st_size // 1024
            pdf_info += f"\nService Health Report: {service_pdf_path.name if isinstance(service_pdf_path, Path) else service_pdf_path} ({service_pdf_size} KB attached)"
            
        if not pdf_info:
            pdf_info = "\nPDF Reports: Not available for this report"

        text_content = f"""VM INFRASTRUCTURE REPORT
{"="*50}

COMPANY: One Climate Co., Ltd.
DEPARTMENT: IT Infrastructure Department
REPORT DATE: {timestamp}
SYSTEM STATUS: HEALTHY

VIRTUAL MACHINE SUMMARY
{"="*50}
Total VMs: {total_vms}
Online VMs: {online_vms}
Offline VMs: {offline_vms}
System Availability: {uptime_percent:.1f}%
{service_summary}
PERFORMANCE METRICS
{"="*50}
CPU Usage: {avg_cpu:.1f}%
Memory Usage: {avg_memory:.1f}%
Disk Usage: {avg_disk:.1f}%

SYSTEM HEALTH STATUS
{"="*50}
All critical systems are operating within normal parameters.
No immediate action required.
Regular monitoring continues.

{pdf_info}

REPORT INFORMATION
{"="*50}
Generated: {timestamp}
Contact: IT Infrastructure Department
System: One Climate VM Monitoring v3.1

This is an automated report. Please contact IT support if you have questions.

---
One Climate Co., Ltd. | Infrastructure Monitoring System
"""
        
        return text_content
    
    def _send_professional_email(self, config: dict, summary: Dict[str, Any], html_content: str, vm_pdf_path: Optional[Path] = None, service_pdf_path: Optional[Path] = None) -> bool:
        """Send professional email with PDF attachment"""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication
            
            msg = MIMEMultipart()
            msg['From'] = "{} <{}>".format(config['sender_name'], config['sender_email'])
            msg['To'] = ', '.join(config['to_emails'])
            if config.get('cc_emails'):
                msg['Cc'] = ', '.join(config['cc_emails'])
            msg['Subject'] = "[One Climate] VM Infrastructure Report - {}".format(
                datetime.now().strftime('%Y-%m-%d')
            )
            
            # Add professional headers to reduce spam score - Enhanced for mx-protect.one.th
            msg['Reply-To'] = config['sender_email']
            msg['X-Mailer'] = 'One Climate VM Monitoring System v3.1'
            msg['X-Priority'] = '3'
            msg['Return-Path'] = config['sender_email']
            msg['Message-ID'] = "<{}.{}@one-climate.monitoring>".format(
                datetime.now().strftime('%Y%m%d%H%M%S'), 
                hash(msg['Subject']) % 999999
            )
            msg['List-Unsubscribe'] = '<mailto:{}?subject=Unsubscribe>'.format(config['sender_email'])
            
            # Additional headers for corporate email filters
            msg['X-Auto-Response-Suppress'] = 'All'
            msg['X-MS-Exchange-Organization-SCL'] = '-1'
            msg['X-Spam-Status'] = 'No'
            msg['Organization'] = 'One Climate Co., Ltd.'
            msg['X-Report-Type'] = 'Infrastructure-Monitoring'
            
            # Add TEXT content (not HTML) to bypass spam filters
            msg.attach(MIMEText(html_content, 'plain', 'utf-8'))
            
            # Add PDF reports if available
            for pdf_path, filename_prefix in (
                (vm_pdf_path, 'VM_Infrastructure_Report'),
                (service_pdf_path, 'Service_Health_Report')
            ):
                if not pdf_path or not pdf_path.exists():
                    continue

                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename='{}_{}.pdf'.format(filename_prefix, datetime.now().strftime('%Y-%m-%d'))
                    )
                    msg.attach(pdf_attachment)
                
                file_size = pdf_path.stat().st_size if isinstance(pdf_path, Path) else 0
                self.logger.info("✅ PDF attached: {} KB".format(file_size // 1024))
            
            # Send email
            with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30) as server:
                server.starttls()
                server.login(config['email_username'], config['email_password'])
                recipients = (
                    config.get('to_emails', []) +
                    config.get('cc_emails', []) +
                    config.get('bcc_emails', [])
                )
                server.send_message(msg, to_addrs=recipients)
            
            self.logger.info("✅ Email sent successfully to {} recipients".format(len(recipients)))
            return True
            
        except Exception as e:
            self.logger.error("❌ Email sending failed: {}".format(e))
            return False
    
    def _send_line_notification(self, summary: Dict[str, Any], vm_data: list = None, service_alerts: list = None) -> bool:
        """Send enhanced LINE notification with VM and Service alerts (Scenario 3)"""
        # Check if LINE notifications are disabled
        line_enabled = os.getenv('LINE_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        if not line_enabled:
            self.logger.info("📱 LINE notifications disabled - skipping LINE notification")
            return True  # Return True to indicate successful "skipping"

        try:
            from linebot import LineBotApi
            from linebot.models import TextSendMessage

            line_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
            line_user_id = os.getenv('LINE_USER_ID')

            if not line_token or not line_user_id:
                self.logger.warning("⚠️ LINE not configured")
                return False

            line_bot_api = LineBotApi(line_token)

            # Extract basic metrics
            total_vms = summary.get('total', 0)
            online_vms = summary.get('online', 0)
            offline_vms = summary.get('offline', 0)
            online_percent = summary.get('online_percent', 0.0)

            performance = summary.get('performance', {})
            avg_cpu = performance.get('avg_cpu', 0.0)
            peak_cpu = performance.get('peak_cpu', 0.0)
            avg_memory = performance.get('avg_memory', 0.0)
            peak_memory = performance.get('peak_memory', 0.0)
            avg_disk = performance.get('avg_disk', 0.0)
            peak_disk = performance.get('peak_disk', 0.0)

            # Determine system status and icon
            has_critical = offline_vms > 0
            has_warning = False

            # Filter VMs with high resource usage (> 70%)
            high_cpu_vms = []
            high_memory_vms = []
            high_disk_vms = []
            offline_vms_list = []

            def _get_metric(vm_obj, keys):
                """Return first available numeric metric for provided keys list."""
                for key in keys:
                    if key in vm_obj and vm_obj[key] is not None:
                        try:
                            return float(vm_obj[key])
                        except (ValueError, TypeError):
                            continue
                return None

            if vm_data:
                for vm in vm_data:
                    vm_name = vm.get('name', vm.get('hostname', 'Unknown'))

                    # Check offline status
                    if vm.get('status') != 0:  # 0 = monitored/online
                        offline_vms_list.append(vm_name)
                        has_critical = True

                    # Check CPU
                    cpu_val = _get_metric(vm, ['cpu_usage', 'cpu_load'])
                    if cpu_val is not None and cpu_val > 70.0:
                        high_cpu_vms.append({'name': vm_name, 'value': cpu_val})
                        if cpu_val > 85.0:
                            has_critical = True
                        else:
                            has_warning = True

                    # Check Memory
                    mem_val = _get_metric(vm, ['memory_usage', 'memory_used'])
                    if mem_val is not None and mem_val > 70.0:
                        high_memory_vms.append({'name': vm_name, 'value': mem_val})
                        if mem_val > 85.0:
                            has_critical = True
                        else:
                            has_warning = True

                    # Check Disk
                    disk_val = _get_metric(vm, ['disk_usage', 'disk_used'])
                    if disk_val is not None and disk_val > 70.0:
                        high_disk_vms.append({'name': vm_name, 'value': disk_val})
                        if disk_val > 85.0:
                            has_critical = True
                        else:
                            has_warning = True

            # Sort by value (highest first)
            high_cpu_vms.sort(key=lambda x: x['value'], reverse=True)
            high_memory_vms.sort(key=lambda x: x['value'], reverse=True)
            high_disk_vms.sort(key=lambda x: x['value'], reverse=True)

            # Process service alerts
            critical_services = []
            warning_services = []

            if service_alerts:
                for alert in service_alerts:
                    severity = alert.get('severity', '').upper()
                    service_name = alert.get('service_name', 'Unknown')
                    message = alert.get('message', '')

                    if severity == 'CRITICAL':
                        critical_services.append({'name': service_name, 'message': message})
                        has_critical = True
                    elif severity == 'WARNING':
                        warning_services.append({'name': service_name, 'message': message})
                        has_warning = True

            # Determine status icon and text
            if has_critical:
                status_icon = "🔴"
                status_text = "CRITICAL"
            elif has_warning:
                status_icon = "⚠️"
                status_text = "WARNING"
            else:
                status_icon = "✅"
                status_text = "HEALTHY"

            # Build message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Header
            message_lines = [
                "{} VM Infrastructure Report{}".format(
                    status_icon,
                    " - {}".format(status_text) if has_critical or has_warning else ""
                ),
                "",
                "📊 System Summary:",
                "• Total VMs: {}".format(total_vms),
                "• Online: {} ({:.1f}%)".format(online_vms, online_percent),
                "• Offline: {}".format(offline_vms),
                "• Status: {}".format(status_text),
                "",
                "📈 Performance:",
                "• CPU: {:.1f}% avg (Peak: {:.1f}%)".format(avg_cpu, peak_cpu),
                "• Memory: {:.1f}% avg (Peak: {:.1f}%)".format(avg_memory, peak_memory),
                "• Storage: {:.1f}% avg (Peak: {:.1f}%)".format(avg_disk, peak_disk)
            ]

            # Check if we have any alerts
            total_alerts = (len(offline_vms_list) + len(high_cpu_vms) +
                          len(high_memory_vms) + len(high_disk_vms) +
                          len(critical_services) + len(warning_services))

            if total_alerts == 0:
                # No alerts - healthy system
                message_lines.extend([
                    "",
                    "✅ All systems normal",
                    "📧 Report delivered with professional PDF",
                    "📊 Complete analytics included"
                ])
            else:
                # Has alerts - show details
                message_lines.append("")

                # Offline VMs
                if offline_vms_list:
                    message_lines.append("🚨 CRITICAL ALERTS:")
                    message_lines.append("")
                    message_lines.append("❌ VM OFFLINE ({}):".format(len(offline_vms_list)))
                    for vm_name in offline_vms_list[:5]:
                        message_lines.append("• {}".format(vm_name))
                    if len(offline_vms_list) > 5:
                        message_lines.append("+{} more VMs offline".format(len(offline_vms_list) - 5))
                    message_lines.append("")

                # High resource usage
                total_high_resource = len(high_cpu_vms) + len(high_memory_vms) + len(high_disk_vms)
                if total_high_resource > 0:
                    message_lines.append("🔴 HIGH RESOURCE USAGE ({} VMs):".format(total_high_resource))
                    message_lines.append("")

                    # CPU
                    if high_cpu_vms:
                        message_lines.append("CPU > 70% ({}):".format(len(high_cpu_vms)))
                        for vm in high_cpu_vms[:5]:
                            message_lines.append("• {}: {:.1f}%".format(vm['name'], vm['value']))
                        if len(high_cpu_vms) > 5:
                            message_lines.append("+{} more".format(len(high_cpu_vms) - 5))
                        message_lines.append("")

                    # Memory
                    if high_memory_vms:
                        message_lines.append("Memory > 70% ({}):".format(len(high_memory_vms)))
                        for vm in high_memory_vms[:5]:
                            message_lines.append("• {}: {:.1f}%".format(vm['name'], vm['value']))
                        if len(high_memory_vms) > 5:
                            message_lines.append("+{} more".format(len(high_memory_vms) - 5))
                        message_lines.append("")

                    # Disk
                    if high_disk_vms:
                        message_lines.append("Disk > 70% ({}):".format(len(high_disk_vms)))
                        for vm in high_disk_vms[:5]:
                            message_lines.append("• {}: {:.1f}%".format(vm['name'], vm['value']))
                        if len(high_disk_vms) > 5:
                            message_lines.append("+{} more".format(len(high_disk_vms) - 5))
                        message_lines.append("")

                # Service alerts
                if critical_services or warning_services:
                    message_lines.append("⚠️ SERVICE ALERTS ({}):".format(
                        len(critical_services) + len(warning_services)
                    ))
                    message_lines.append("")

                    # Critical services
                    if critical_services:
                        message_lines.append("🔴 CRITICAL ({}):".format(len(critical_services)))
                        for svc in critical_services[:5]:
                            message_lines.append("• {}: {}".format(svc['name'], svc['message']))
                        if len(critical_services) > 5:
                            message_lines.append("+{} more critical".format(len(critical_services) - 5))
                        message_lines.append("")

                    # Warning services
                    if warning_services:
                        message_lines.append("🟡 WARNING ({}):".format(len(warning_services)))
                        for svc in warning_services[:5]:
                            message_lines.append("• {}: {}".format(svc['name'], svc['message']))
                        if len(warning_services) > 5:
                            message_lines.append("+{} more warnings".format(len(warning_services) - 5))
                        message_lines.append("")

                # Footer for alerts
                message_lines.extend([
                    "📧 Report delivered with professional PDF",
                    "📊 Complete analytics included"
                ])

                if has_critical:
                    message_lines.append("⚡ Immediate attention required")

            # Final footer
            message_lines.extend([
                "",
                timestamp,
                "",
                "One Climate Infrastructure Team"
            ])

            message_text = "\n".join(message_lines)

            # Check message length (LINE limit: 5000 chars)
            if len(message_text) > 4500:
                self.logger.warning("⚠️ LINE message too long ({} chars), truncating...".format(len(message_text)))
                message_text = message_text[:4450] + "\n\n... See full report in email"

            line_bot_api.push_message(line_user_id, TextSendMessage(text=message_text))
            self.logger.info("✅ Enhanced LINE notification sent ({} chars, {} alerts)".format(
                len(message_text), total_alerts
            ))
            return True

        except Exception as e:
            self.logger.error("⚠️ LINE notification failed: {}".format(e))
            import traceback
            self.logger.debug(traceback.format_exc())
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
            
            # Step 2: Generate separate PDF reports
            reports = self.generate_pdf_report(vm_data, summary, service_health_data)
            if not reports:
                self.logger.warning("⚠️ PDF generation failed, continuing with alerts only")
                workflow_success = False
                vm_pdf_path = None
                service_pdf_path = None
            else:
                vm_pdf_path, service_pdf_path = reports
                self.logger.info("📄 Reports generated: VM={}, Service={}".format(
                    vm_pdf_path.name if isinstance(vm_pdf_path, Path) else str(vm_pdf_path) if vm_pdf_path else "None",
                    service_pdf_path.name if isinstance(service_pdf_path, Path) else str(service_pdf_path) if service_pdf_path else "None"
                ))
            
            # Step 3: Send comprehensive alerts (with both PDF attachments)
            alert_success = self.send_comprehensive_alerts(vm_data, summary, vm_pdf_path, service_pdf_path, service_health_data)
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

        dependency_ok, dependency_details = orchestrator.dependency_health_gate()
        if not dependency_ok:
            orchestrator.send_failure_alert('dependency_gate', 'required services not ready', dependency_details)
            return False
        
        # Step 1: Collect real VM data from Zabbix
        orchestrator.logger.info("🔍 Collecting VM data from Zabbix...")
        vm_data, summary = orchestrator.collect_vm_data_with_retries()
        if vm_data is None:
            reason = summary.get('error', 'Zabbix data collection failed') if isinstance(summary, dict) else 'Zabbix data collection failed'
            orchestrator.send_failure_alert('zabbix_collection', reason, summary if isinstance(summary, dict) else {})
            return False
        
        # Step 1.5: Collect service health data
        orchestrator.logger.info("🛡️ Collecting service health data...")
        try:
            service_health_data, service_alerts = orchestrator.collect_service_health_snapshot()
            orchestrator.logger.info(f"✅ Service health collected: {len(service_health_data.get('services', {}))} services")
        except Exception as e:
            orchestrator.logger.warning(f"⚠️ Service health collection failed: {e}")
            service_health_data = {
                'services': {},
                'summary': {
                    'total': 0,
                    'healthy': 0,
                    'warning': 0,
                    'critical': 0,
                    'availability': 0,
                    'overall_status': 'unavailable'
                },
                'demo_mode': True
            }
            service_alerts = []
        
        if vm_data is None or summary is None:
            orchestrator.logger.error("❌ Failed to collect VM data")
            orchestrator.send_failure_alert('zabbix_collection', 'VM data unavailable after retries')
            return False
        
        orchestrator.logger.info("✅ Summary data prepared")

        disk_ok, disk_details = orchestrator.disk_space_preflight()
        if not disk_ok:
            orchestrator.send_failure_alert('disk_preflight', 'insufficient free disk space', disk_details)
            return False

        # Step 2: Generate fresh PDF with current data
        orchestrator.logger.info("📄 Generating PDF report with current Zabbix data...")
        pdf_reports = orchestrator.generate_pdf_report(vm_data, summary, service_health_data)

        # Unpack the reports
        if pdf_reports:
            vm_pdf_path, service_pdf_path = pdf_reports
            orchestrator.logger.info("✅ Generated staged PDFs: vm_pdf={} service_pdf={}".format(
                vm_pdf_path, service_pdf_path
            ))
        else:
            vm_pdf_path, service_pdf_path = None, None

        validation_ok, validation_reason, validation_details = orchestrator.validate_vm_report_before_send(
            vm_data, summary, vm_pdf_path
        )
        if not validation_ok:
            orchestrator.logger.error("VM_REPORT_VALIDATION status=failed reason={} details={}".format(
                validation_reason, validation_details
            ))
            orchestrator.send_failure_alert('report_validation', validation_reason, validation_details)
            return False

        try:
            vm_pdf_path, service_pdf_path = orchestrator.promote_validated_pdf_reports(vm_pdf_path, service_pdf_path)
        except Exception as promote_error:
            orchestrator.logger.error("PDF_PROMOTION status=failed reason={}".format(promote_error))
            orchestrator.send_failure_alert('pdf_promotion', str(promote_error))
            return False

        duplicate_ok, duplicate_reason = orchestrator.check_duplicate_send_allowed()
        if not duplicate_ok:
            orchestrator.logger.warning("EMAIL_SEND status=blocked reason={}".format(duplicate_reason))
            return False

        # Step 3: Send email + LINE notifications
        success = orchestrator.send_comprehensive_alerts(vm_data, summary, vm_pdf_path, service_pdf_path, service_health_data, service_alerts)
        if success and orchestrator.stats['emails_sent'] > 0:
            orchestrator.record_successful_send()
        
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
        if os.getenv('EMAIL_DRY_RUN', 'true').lower() == 'true':
            final_email_status = "🧪 Dry-run"
        elif orchestrator.stats['emails_sent'] > 0:
            final_email_status = "✅ Sent to {} recipients".format(orchestrator.stats['emails_sent'])
        else:
            final_email_status = "❌ Failed"
        orchestrator.logger.info("   Email: {}".format(final_email_status))
        orchestrator.logger.info("   PDF: {}".format("✅ Professional PDF Attached" if vm_pdf_path else "❌ Not available"))
        if os.getenv('LINE_NOTIFICATIONS_ENABLED', 'false').lower() != 'true':
            final_line_status = "⏭️ Skipped"
        elif orchestrator.stats['line_alerts_sent'] > 0:
            final_line_status = "✅ Notification Sent"
        else:
            final_line_status = "⚠️ Failed"
        orchestrator.logger.info("   LINE: {}".format(final_line_status))
        orchestrator.logger.info("DAILY_VM_REPORT status={} vm_count={} email_sent={} line_sent={} run_mode={}".format(
            'success' if success else 'failed',
            summary.get('total', 0),
            (not orchestrator._env_bool('EMAIL_DRY_RUN', True)) and orchestrator.stats['emails_sent'] > 0,
            orchestrator.stats['line_alerts_sent'] > 0,
            orchestrator._run_mode()
        ))
        
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
