#!/usr/bin/env python3
"""
Enhanced Alert System for VM Daily Report - WORKING VERSION
Fixed to use LINE Bot SDK v2 (working version)
"""

import os
import ssl
import smtplib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dataclasses import dataclass
from enum import Enum

# LINE Bot imports (v2 - working version)
try:
    from linebot import LineBotApi
    from linebot.models import TextSendMessage, FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, SeparatorComponent
    from linebot.exceptions import LineBotApiError
    LINE_AVAILABLE = True
except ImportError:
    print("⚠️ LINE Bot SDK not available. Install with: pip install line-bot-sdk")
    LINE_AVAILABLE = False

# Load environment variables
try:
    from load_env import load_env_file, get_config_dict
    load_env_file()
    config = get_config_dict()
except ImportError:
    config = {}

# Setup logger - will be configured when logging is properly initialized
logger = None

def get_logger():
    """Get logger instance, creating if needed"""
    global logger
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
    return logger

def log_info(message):
    """Safe logging info"""
    try:
        get_logger().info(message)
    except:
        print("INFO: {}".format(message))

def log_warning(message):
    """Safe logging warning"""
    try:
        get_logger().warning(message)
    except:
        print("WARNING: {}".format(message))

def log_error(message):
    """Safe logging error"""
    try:
        get_logger().error(message)
    except:
        print("ERROR: {}".format(message))

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Available alert channels"""
    EMAIL = "email"
    LINE = "line"
    SLACK = "slack"
    TEAMS = "teams"

@dataclass
class AlertConfig:
    """Alert system configuration"""
    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    sender_email: str = ""
    sender_name: str = "VM Monitoring System"
    to_emails: List[str] = None
    cc_emails: List[str] = None
    bcc_emails: List[str] = None
    
    # LINE settings
    line_channel_access_token: str = ""
    line_user_id: str = ""
    
    # Alert thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 85.0
    memory_warning_threshold: float = 75.0
    memory_critical_threshold: float = 90.0
    disk_warning_threshold: float = 80.0
    disk_critical_threshold: float = 90.0
    
    # Channel preferences
    info_channels: List[AlertChannel] = None
    warning_channels: List[AlertChannel] = None
    critical_channels: List[AlertChannel] = None
    emergency_channels: List[AlertChannel] = None
    
    def __post_init__(self):
        if self.to_emails is None:
            self.to_emails = []
        if self.info_channels is None:
            self.info_channels = [AlertChannel.EMAIL]
        if self.warning_channels is None:
            self.warning_channels = [AlertChannel.EMAIL, AlertChannel.LINE]
        if self.critical_channels is None:
            self.critical_channels = [AlertChannel.EMAIL, AlertChannel.LINE]
        if self.emergency_channels is None:
            self.emergency_channels = [AlertChannel.EMAIL, AlertChannel.LINE]

class EnhancedAlertSystem:
    """Enhanced multi-channel alert system - WORKING VERSION"""
    
    def __init__(self, config: AlertConfig = None):
        self.config = config or self._load_config_from_env()
        self.line_bot_api = None
        self._setup_line_bot()
        
    def _load_config_from_env(self) -> AlertConfig:
        """Load configuration from environment variables"""
        to_emails_str = os.getenv('TO_EMAILS', '')
        to_emails = [email.strip() for email in to_emails_str.split(',') if email.strip()]
        
        cc_emails_str = os.getenv('CC_EMAILS', '')
        cc_emails = [email.strip() for email in cc_emails_str.split(',') if email.strip()]
        
        bcc_emails_str = os.getenv('BCC_EMAILS', '')
        bcc_emails = [email.strip() for email in bcc_emails_str.split(',') if email.strip()]
        
        return AlertConfig(
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            email_username=os.getenv('EMAIL_USERNAME', ''),
            email_password=os.getenv('EMAIL_PASSWORD', ''),
            sender_email=os.getenv('SENDER_EMAIL', ''),
            sender_name=os.getenv('SENDER_NAME', 'VM Monitoring System'),
            to_emails=to_emails,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            line_channel_access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN', ''),
            line_user_id=os.getenv('LINE_USER_ID', ''),
            cpu_warning_threshold=float(os.getenv('CPU_WARNING_THRESHOLD', '70')),
            cpu_critical_threshold=float(os.getenv('CPU_CRITICAL_THRESHOLD', '85')),
            memory_warning_threshold=float(os.getenv('MEMORY_WARNING_THRESHOLD', '75')),
            memory_critical_threshold=float(os.getenv('MEMORY_CRITICAL_THRESHOLD', '90')),
            disk_warning_threshold=float(os.getenv('DISK_WARNING_THRESHOLD', '80')),
            disk_critical_threshold=float(os.getenv('DISK_CRITICAL_THRESHOLD', '90'))
        )
    
    def _setup_line_bot(self):
        """Initialize LINE Bot API"""
        if not LINE_AVAILABLE:
            log_warning("LINE Bot SDK not available")
            return
            
        if self.config.line_channel_access_token:
            try:
                self.line_bot_api = LineBotApi(self.config.line_channel_access_token)
                log_info("✅ LINE Bot API initialized successfully")
            except Exception as e:
                log_error("❌ Failed to initialize LINE Bot API: {}".format(e))
                self.line_bot_api = None
        else:
            log_warning("⚠️ LINE_CHANNEL_ACCESS_TOKEN not configured")
    
    def analyze_vm_alerts(self, vm_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze VM data and generate alerts including power state changes"""
        alerts = {
            'critical': [],
            'warning': [],
            'offline': [],
            'healthy': [],
            'power_changes': []  # New: Power state change alerts
        }
        
        for vm in vm_data:
            vm_name = vm.get('name', 'Unknown VM')
            is_online = vm.get('is_online', False)
            
            if not is_online:
                alerts['offline'].append({
                    'vm': vm_name,
                    'message': "{} is OFFLINE".format(vm_name),
                    'level': AlertLevel.CRITICAL
                })
                continue
            
            # Check CPU
            cpu = vm.get('cpu_load', 0)
            if cpu >= self.config.cpu_critical_threshold:
                alerts['critical'].append({
                    'vm': vm_name,
                    'metric': 'CPU',
                    'value': cpu,
                    'threshold': self.config.cpu_critical_threshold,
                    'message': "{}: CPU {:.1f}% (Critical)".format(vm_name, cpu),
                    'level': AlertLevel.CRITICAL
                })
            elif cpu >= self.config.cpu_warning_threshold:
                alerts['warning'].append({
                    'vm': vm_name,
                    'metric': 'CPU',
                    'value': cpu,
                    'threshold': self.config.cpu_warning_threshold,
                    'message': "{}: CPU {:.1f}% (Warning)".format(vm_name, cpu),
                    'level': AlertLevel.WARNING
                })
            
            # Check Memory
            memory = vm.get('memory_used', 0)
            if memory >= self.config.memory_critical_threshold:
                alerts['critical'].append({
                    'vm': vm_name,
                    'metric': 'Memory',
                    'value': memory,
                    'threshold': self.config.memory_critical_threshold,
                    'message': "{}: Memory {:.1f}% (Critical)".format(vm_name, memory),
                    'level': AlertLevel.CRITICAL
                })
            elif memory >= self.config.memory_warning_threshold:
                alerts['warning'].append({
                    'vm': vm_name,
                    'metric': 'Memory',
                    'value': memory,
                    'threshold': self.config.memory_warning_threshold,
                    'message': "{}: Memory {:.1f}% (Warning)".format(vm_name, memory),
                    'level': AlertLevel.WARNING
                })
            
            # Check Disk
            disk = vm.get('disk_used', 0)
            if disk >= self.config.disk_critical_threshold:
                alerts['critical'].append({
                    'vm': vm_name,
                    'metric': 'Disk',
                    'value': disk,
                    'threshold': self.config.disk_critical_threshold,
                    'message': "{}: Disk {:.1f}% (Critical)".format(vm_name, disk),
                    'level': AlertLevel.CRITICAL
                })
            elif disk >= self.config.disk_warning_threshold:
                alerts['warning'].append({
                    'vm': vm_name,
                    'metric': 'Disk',
                    'value': disk,
                    'threshold': self.config.disk_warning_threshold,
                    'message': "{}: Disk {:.1f}% (Warning)".format(vm_name, disk),
                    'level': AlertLevel.WARNING
                })
            
            # If no alerts, mark as healthy
            if not any([
                cpu >= self.config.cpu_warning_threshold,
                memory >= self.config.memory_warning_threshold,
                disk >= self.config.disk_warning_threshold
            ]):
                alerts['healthy'].append(vm_name)
        
        # Check for power state changes in any VM
        power_changes = self._extract_power_changes(vm_data)
        if power_changes:
            alerts['power_changes'] = power_changes
        
        return alerts
    
    def _extract_power_changes(self, vm_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract power state changes from VM data"""
        power_change_alerts = []
        
        for vm in vm_data:
            power_changes = vm.get('power_changes')
            if not power_changes or not power_changes.get('has_changes', False):
                continue
            
            # Process power change alerts
            alerts = power_changes.get('alerts', [])
            for alert in alerts:
                power_change_alerts.append({
                    'type': alert.get('type', 'unknown'),
                    'level': alert.get('level', 'INFO'),
                    'title': alert.get('title', 'Power State Change'),
                    'message': alert.get('message', ''),
                    'icon': alert.get('icon', '🔄'),
                    'details': alert.get('details', {}),
                    'timestamp': alert.get('timestamp', ''),
                    'vm_name': alert.get('details', {}).get('vm_name', 'Unknown'),
                    'hostname': alert.get('details', {}).get('hostname', 'Unknown'),
                    'ip': alert.get('details', {}).get('ip', 'N/A')
                })
        
        return power_change_alerts
    
    def send_power_change_alerts(self, power_changes: List[Dict[str, Any]]) -> bool:
        """Send power state change alerts via LINE and Email"""
        if not power_changes:
            return True
        
        # Limit power change alerts to avoid rate limiting
        max_alerts = 5  # Limit to 5 alerts to avoid LINE rate limits
        limited_changes = power_changes[:max_alerts]
        
        success_count = 0
        total_alerts = len(limited_changes)
        
        if len(power_changes) > max_alerts:
            log_info("🔄 Limiting power change alerts to {} out of {} to avoid rate limits".format(max_alerts, len(power_changes)))
        
        for change in limited_changes:
            # Send LINE notification for each change
            line_message = self._format_power_change_line_message(change)
            if self.send_line_alert(line_message, AlertLevel.INFO):
                success_count += 1
        
        log_info("🔄 Sent {}/{} power change alerts (limited from {})".format(success_count, total_alerts, len(power_changes)))
        return success_count == total_alerts
    
    def _format_power_change_line_message(self, change: Dict[str, Any]) -> str:
        """Format power change for LINE message"""
        icon = change.get('icon', '🔄')
        title = change.get('title', 'Power State Change')
        vm_name = change.get('vm_name', 'Unknown')
        hostname = change.get('hostname', 'Unknown')
        ip = change.get('ip', 'N/A')
        change_type = change.get('type', 'unknown')
        
        message = f"""{icon} {title}
        
🖥️ VM: {vm_name}
🏷️ Host: {hostname}
🌐 IP: {ip}
⚡ Event: {change_type.replace('_', ' ').title()}"""
        
        # Add specific details based on change type
        details = change.get('details', {})
        if change_type == 'recovery' and 'downtime_duration' in details:
            message += f"\n⏱️ Downtime: {details['downtime_duration']}"
        elif change_type == 'power_off' and 'last_seen' in details:
            message += f"\n⏰ Last Seen: {details['last_seen']}"
        
        return message
    
    def send_line_alert(self, message: str, alert_level: AlertLevel = AlertLevel.INFO) -> bool:
        """Send alert to LINE OA with enhanced formatting"""
        if not self.line_bot_api or not self.config.line_user_id:
            log_warning("⚠️ LINE Bot not configured")
            return False
        
        try:
            # Create enhanced LINE message with emoji and formatting
            emoji_map = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.CRITICAL: "🚨",
                AlertLevel.EMERGENCY: "🔥"
            }
            
            emoji = emoji_map.get(alert_level, "📢")
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            formatted_message = f"""{emoji} VM Infrastructure Alert

🕒 Time: {current_time}
🖥️ System: One Climate Infrastructure
📊 Level: {alert_level.value.upper()}

{message}

---
VM Monitoring System"""
            
            # Send text message
            self.line_bot_api.push_message(
                self.config.line_user_id,
                TextSendMessage(text=formatted_message)
            )
            
            log_info("✅ LINE alert sent successfully ({})".format(alert_level.value))
            return True
            
        except LineBotApiError as e:
            log_error("❌ LINE Bot API error: {}".format(e))
            return False
        except Exception as e:
            log_error("❌ Failed to send LINE alert: {}".format(e))
            return False
    
    def send_email_alert(self, subject: str, body: str, alert_level: AlertLevel = AlertLevel.INFO, 
                        pdf_path: str = None) -> bool:
        """Send email alert with enhanced formatting"""
        try:
            if not self.config.to_emails and not self.config.cc_emails and not self.config.bcc_emails:
                log_warning("⚠️ No email recipients configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = "{} <{}>".format(self.config.sender_name, self.config.sender_email)
            
            # Set TO recipients
            if self.config.to_emails:
                msg['To'] = ', '.join(self.config.to_emails)
            
            # Set CC recipients
            if self.config.cc_emails:
                msg['Cc'] = ', '.join(self.config.cc_emails)
            
            msg['Subject'] = subject
            
            # Add anti-spam headers
            msg['Reply-To'] = self.config.sender_email
            msg['Message-ID'] = "<{}.{}@one-climate.monitoring>".format(datetime.now().strftime('%Y%m%d%H%M%S'), hash(subject))
            msg['X-Mailer'] = 'One Climate VM Monitoring System v2.0'
            msg['List-Unsubscribe'] = '<mailto:{}?subject=Unsubscribe>'.format(self.config.sender_email)
            
            # Add priority based on alert level
            if alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
                msg['Importance'] = 'High'
            else:
                msg['X-Priority'] = '3'
                msg['X-MSMail-Priority'] = 'Normal'
                msg['Importance'] = 'Normal'
            
            # Add body
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Add PDF attachment if provided
            if pdf_path and Path(pdf_path).exists():
                try:
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    attachment = MIMEApplication(pdf_data, 'pdf')
                    attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=Path(pdf_path).name
                    )
                    msg.attach(attachment)
                    log_info("📎 PDF attached: {}".format(Path(pdf_path).name))
                except Exception as e:
                    log_warning("⚠️ Failed to attach PDF: {}".format(e))
            
            # Send email with proper Gmail SMTP configuration
            try:
                # Prepare all recipients for sending
                all_recipients = []
                if self.config.to_emails:
                    all_recipients.extend(self.config.to_emails)
                if self.config.cc_emails:
                    all_recipients.extend(self.config.cc_emails)
                if self.config.bcc_emails:
                    all_recipients.extend(self.config.bcc_emails)
                
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=30) as server:
                    # Enable TLS encryption
                    server.starttls()
                    server.login(self.config.email_username, self.config.email_password)
                    # Send to all recipients (TO, CC, BCC)
                    server.sendmail(self.config.sender_email, all_recipients, msg.as_string())
                
                log_info("✅ Email alert sent successfully ({}) to {} recipients".format(alert_level.value, len(all_recipients)))
                return True
                
            except Exception as e:
                log_warning("⚠️ Email sending failed: {}".format(e))
                return False
            
        except Exception as e:
            log_warning("⚠️ Email system error: {}".format(e))
            return False
    
    def send_comprehensive_alert(self, vm_data: List[Dict[str, Any]], summary: Dict[str, Any], 
                                pdf_path: str = None) -> Dict[str, bool]:
        """Send comprehensive alerts through all configured channels"""
        results = {
            'email': False,
            'line_text': False
        }
        
        try:
            # Analyze alerts
            alerts = self.analyze_vm_alerts(vm_data)
            
            # Determine overall alert level
            if alerts['offline'] or alerts['critical']:
                overall_level = AlertLevel.CRITICAL
            elif alerts['warning']:
                overall_level = AlertLevel.WARNING
            else:
                overall_level = AlertLevel.INFO
            
            # Create comprehensive alert message
            alert_message = self._create_alert_message(alerts, summary)
            
            # Determine which channels to use based on alert level
            channels = self._get_channels_for_level(overall_level)
            
            # Send alerts through appropriate channels - SKIP EMAIL HERE
            # (Email will be sent later in the ALWAYS section to avoid duplication)
            
            # ALWAYS send LINE notification for daily reports (ignore channel restrictions)
            if self.line_bot_api:
                if overall_level == AlertLevel.INFO:
                    # For healthy systems, send summary
                    summary_message = f"""✅ Daily VM Infrastructure Report

🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ One Climate Infrastructure

=== STATUS: HEALTHY ===
✅ Total VMs: {summary.get('total', 0)}
✅ Online: {summary.get('online', 0)} ({summary.get('online_percent', 0):.1f}%)
✅ All systems running normally

📊 Performance:
💻 CPU: {summary.get('performance', {}).get('avg_cpu', 0):.1f}%
🧠 Memory: {summary.get('performance', {}).get('avg_memory', 0):.1f}%
💽 Storage: {summary.get('performance', {}).get('avg_disk', 0):.1f}%

---
VM Monitoring System"""
                    
                    results['line_text'] = self.send_line_alert(summary_message, AlertLevel.INFO)
                else:
                    # Send alert message for problems
                    results['line_text'] = self.send_line_alert(alert_message, overall_level)
            
            # ALWAYS try to send email 
            if self.config.to_emails:
                subject = self._create_email_subject(summary, overall_level)
                
                # Use the same format as alert_message for email body
                email_body = alert_message
                
                results['email'] = self.send_email_alert(
                    subject=subject,
                    body=email_body,
                    alert_level=overall_level,
                    pdf_path=pdf_path
                )
            else:
                log_warning("📧 No email recipients configured")
                results['email'] = False
            
            # Log results
            successful_channels = [channel for channel, success in results.items() if success]
            failed_channels = [channel for channel, success in results.items() if not success]
            
            if successful_channels:
                log_info("✅ Alerts sent via: {}".format(', '.join(successful_channels)))
            if failed_channels:
                log_warning("⚠️ Failed to send alerts via: {}".format(', '.join(failed_channels)))
            
            return results
            
        except Exception as e:
            log_error("❌ Failed to send comprehensive alert: {}".format(e))
            return results
    
    def _get_channels_for_level(self, alert_level: AlertLevel) -> List[AlertChannel]:
        """Get appropriate channels for alert level"""
        if alert_level == AlertLevel.EMERGENCY:
            return self.config.emergency_channels
        elif alert_level == AlertLevel.CRITICAL:
            return self.config.critical_channels
        elif alert_level == AlertLevel.WARNING:
            return self.config.warning_channels
        else:
            return self.config.info_channels
    
    def _create_alert_message(self, alerts: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """Create comprehensive alert message"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"""VM Infrastructure Alert Report
Generated: {current_time}

=== SYSTEM OVERVIEW ===
Total VMs: {summary.get('total', 0)}
Online: {summary.get('online', 0)} ({summary.get('online_percent', 0):.1f}%)
Offline: {summary.get('offline', 0)} ({summary.get('offline_percent', 0):.1f}%)
System Status: {summary.get('system_status', 'unknown').upper()}

=== ALERT SUMMARY ===
🚨 Critical: {len(alerts['critical'])}
⚠️ Warning: {len(alerts['warning'])}
🔴 Offline: {len(alerts['offline'])}
✅ Healthy: {len(alerts['healthy'])}

"""
        
        # Add offline VMs
        if alerts['offline']:
            message += "=== OFFLINE SYSTEMS ===\n"
            for alert in alerts['offline']:
                message += "🔴 {}\n".format(alert['message'])
            message += "\n"
        
        # Add critical alerts
        if alerts['critical']:
            message += "=== CRITICAL ALERTS ===\n"
            for alert in alerts['critical']:
                message += "🚨 {}\n".format(alert['message'])
            message += "\n"
        
        # Add warning alerts
        if alerts['warning']:
            message += "=== WARNING ALERTS ===\n"
            for alert in alerts['warning'][:5]:  # Limit to first 5
                message += "⚠️ {}\n".format(alert['message'])
            if len(alerts['warning']) > 5:
                message += "... and {} more warnings\n".format(len(alerts['warning']) - 5)
            message += "\n"
        
        # Add performance summary
        if summary.get('performance'):
            perf = summary['performance']
            message += f"""=== PERFORMANCE OVERVIEW ===
💻 Average CPU: {perf.get('avg_cpu', 0):.1f}%
🧠 Average Memory: {perf.get('avg_memory', 0):.1f}%
💽 Average Disk: {perf.get('avg_disk', 0):.1f}%

"""
        
        message += "---\nVM Monitoring System\nOne Climate Infrastructure"
        
        return message
    
    def _create_email_subject(self, summary: Dict[str, Any], alert_level: AlertLevel) -> str:
        """Create email subject based on summary and alert level"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        base_subject = "VM Infrastructure Alert - {}".format(current_date)
        
        total_vms = summary.get('total', 0)
        offline_vms = summary.get('offline', 0)
        # Get alert counts from analyze_vm_alerts result or summary
        if 'alerts' in summary:
            critical_alerts = summary['alerts'].get('critical', 0)
            warning_alerts = summary['alerts'].get('warning', 0)
        else:
            critical_alerts = 0
            warning_alerts = 0
        
        if alert_level == AlertLevel.CRITICAL:
            if offline_vms > 0:
                return "{} 🚨 {} VMs OFFLINE".format(base_subject, offline_vms)
            elif critical_alerts > 0:
                return "{} 🚨 {} CRITICAL ALERTS".format(base_subject, critical_alerts)
        elif alert_level == AlertLevel.WARNING:
            return "{} ⚠️ {} Warnings".format(base_subject, warning_alerts)
        else:
            return "{} ✅ All Systems Normal".format(base_subject)
        
        return base_subject

# Integration function for existing codebase
def send_enhanced_alerts(vm_data: List[Dict[str, Any]], summary: Dict[str, Any], 
                        pdf_path: str = None) -> bool:
    """Enhanced alert function that integrates with existing VM report system"""
    try:
        alert_system = EnhancedAlertSystem()
        results = alert_system.send_comprehensive_alert(vm_data, summary, pdf_path)
        return any(results.values())
    except Exception as e:
        log_error("❌ Enhanced alerts failed: {}".format(e))
        return False

# Backward compatibility function
def send_email(summary: Dict[str, Any], pdf_path: str = None) -> bool:
    """Backward compatible function"""
    vm_data = []
    return send_enhanced_alerts(vm_data, summary, pdf_path)

if __name__ == "__main__":
    print("🧪 Testing Enhanced Alert System...")
    
    # Test LINE connectivity
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        system = EnhancedAlertSystem()
        if system.line_bot_api:
            success = system.send_line_alert(
                "🧪 Enhanced Alert System Test\n✅ LINE integration working!",
                AlertLevel.INFO
            )
            print("LINE test: {}".format('✅ Success' if success else '❌ Failed'))
        else:
            print("❌ LINE not configured")
    except Exception as e:
        print("❌ Test failed: {}".format(e))
