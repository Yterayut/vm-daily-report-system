#!/usr/bin/env python3
"""
Service Health Real-time Monitor
ตรวจสอบสถานะ Services ทุก 2 นาที และแจ้งเตือนเมื่อ service ล่ม/กลับมา
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
LOG_FILE = Path(__file__).parent / "logs" / "service_health_monitor.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)

# State file for service status tracking
SERVICE_STATE_FILE = Path(__file__).parent / "logs" / "service_states.json"

sys.path.insert(0, str(Path(__file__).parent))

try:
    from service_health_checker import ServiceHealthMonitor
    from enhanced_alert_system import EnhancedAlertSystem, AlertLevel
    from load_env import load_env_file

    load_env_file()

    class ServiceStateTracker:
        def __init__(self):
            self.previous_states = self.load_previous_states()

        def load_previous_states(self):
            """Load previous service states"""
            if SERVICE_STATE_FILE.exists():
                try:
                    with open(SERVICE_STATE_FILE, "r") as f:
                        return json.load(f)
                except:
                    return {}
            return {}

        def save_states(self, current_states):
            """Save current service states"""
            try:
                with open(SERVICE_STATE_FILE, "w") as f:
                    json.dump(current_states, f, indent=2)
            except Exception as e:
                logging.error(f"Failed to save service states: {e}")

        def detect_changes(self, current_data):
            """Detect service status changes (down/recovery)"""
            current_states = {}
            changes = []

            for service_id, service_data in current_data["services"].items():
                service_name = service_data["name"]
                current_health = service_data["health_level"]
                error_type = service_data.get("error_type")
                error_message = service_data.get("error")
                current_states[service_id] = {
                    "name": service_name,
                    "health_level": current_health,
                    "last_check": datetime.now().isoformat()
                }

                previous_health = self.previous_states.get(service_id, {}).get("health_level", "unknown")

                # Detect status changes
                if previous_health != "unknown" and previous_health != current_health:
                    if current_health == "critical" and previous_health in ["healthy", "warning"]:
                        # Service went down
                        changes.append({
                            "type": "service_down",
                            "service_name": service_name,
                            "service_id": service_id,
                            "previous": previous_health,
                            "current": current_health,
                            "message": f"🔴 SERVICE DOWN: {service_name}",
                            "details": f"Status changed: {previous_health} → {current_health}",
                            "level": AlertLevel.CRITICAL
                        })
                    elif current_health == "unreachable":
                        changes.append({
                            "type": "service_unreachable",
                            "service_name": service_name,
                            "service_id": service_id,
                            "previous": previous_health,
                            "current": current_health,
                            "message": f"📡 SERVICE UNREACHABLE: {service_name}",
                            "details": f"Monitoring path issue: {error_type or 'connection_error'} ({error_message or 'no details'})",
                            "level": AlertLevel.WARNING
                        })
                    elif current_health in ["healthy", "warning"] and previous_health == "critical":
                        # Service recovered
                        changes.append({
                            "type": "service_recovery",
                            "service_name": service_name,
                            "service_id": service_id,
                            "previous": previous_health,
                            "current": current_health,
                            "message": f"✅ SERVICE RECOVERED: {service_name}",
                            "details": f"Status recovered: {previous_health} → {current_health}",
                            "level": AlertLevel.INFO
                        })
                    elif current_health in ["healthy", "warning"] and previous_health == "unreachable":
                        changes.append({
                            "type": "service_reachable",
                            "service_name": service_name,
                            "service_id": service_id,
                            "previous": previous_health,
                            "current": current_health,
                            "message": f"✅ SERVICE REACHABLE: {service_name}",
                            "details": f"Monitoring path recovered: {previous_health} → {current_health}",
                            "level": AlertLevel.INFO
                        })
                elif previous_health == "unknown" and current_health == "critical":
                    # New service detected as critical (first run)
                    changes.append({
                        "type": "service_critical",
                        "service_name": service_name,
                        "service_id": service_id,
                        "previous": previous_health,
                        "current": current_health,
                        "message": f"🔴 SERVICE CRITICAL: {service_name}",
                        "details": f"Service detected in critical state",
                        "level": AlertLevel.CRITICAL
                    })
                elif previous_health == "unknown" and current_health == "unreachable":
                    changes.append({
                        "type": "service_unreachable",
                        "service_name": service_name,
                        "service_id": service_id,
                        "previous": previous_health,
                        "current": current_health,
                        "message": f"📡 SERVICE UNREACHABLE: {service_name}",
                        "details": f"Monitoring path issue: {error_type or 'connection_error'} ({error_message or 'no details'})",
                        "level": AlertLevel.WARNING
                    })

            # Update states
            self.previous_states = current_states
            self.save_states(current_states)

            return changes

    class ServiceHealthAlertManager:
        def __init__(self, dry_run=False):
            self.service_monitor = ServiceHealthMonitor()
            self.service_monitor.demo_mode = False
            self.state_tracker = ServiceStateTracker()
            self.alert_system = EnhancedAlertSystem()
            self.dry_run = dry_run

        def send_service_alert(self, change_data):
            """Send dual alert (LINE + Email) for service status change"""
            try:
                message = change_data["message"]
                details = change_data["details"]
                service_name = change_data["service_name"]
                alert_level = change_data["level"]

                # Create detailed message
                full_message = f"{message}\n{details}\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                if self.dry_run:
                    logging.info(f"Dry-run mode: alert suppressed for {change_data['type']} - {service_name}")
                    return True

                # Send LINE alert
                line_result = self.alert_system.send_line_alert(full_message, alert_level)

                # Send Email alert
                subject = f"🔧 Service Alert - {service_name} | One Climate Co., Ltd."
                email_result = self.alert_system.send_email_alert(subject, full_message, alert_level)

                logging.info(f"Service alert sent - LINE: {line_result}, Email: {email_result}")
                logging.info(f"Alert: {change_data['type']} for {service_name}")

                return line_result and email_result

            except Exception as e:
                logging.error(f"Failed to send service alert: {e}")
                return False

        def run_service_monitoring(self):
            """Main service monitoring function"""
            try:
                logging.info("Starting service health monitoring check")

                # Get current service health data
                current_data = self.service_monitor.check_all_services()

                if not current_data or "services" not in current_data:
                    logging.warning("No service data received")
                    return

                # Detect status changes
                changes = self.state_tracker.detect_changes(current_data)

                # Process and send alerts for changes
                if changes:
                    logging.info(f"Detected {len(changes)} service status changes")

                    for change in changes:
                        # Send alert for critical changes (down/recovery/critical)
                        if change["type"] in ["service_down", "service_recovery", "service_critical"]:
                            self.send_service_alert(change)
                            time.sleep(1)  # Small delay between alerts
                        else:
                            logging.warning(f"Monitoring issue ({change['type']}): {change['service_name']} - {change['details']}")
                else:
                    logging.info("No service status changes detected")

                # Log current summary
                healthy_count = sum(1 for s in current_data["services"].values() if s["health_level"] == "healthy")
                warning_count = sum(1 for s in current_data["services"].values() if s["health_level"] == "warning")
                critical_count = sum(1 for s in current_data["services"].values() if s["health_level"] == "critical")
                unreachable_count = sum(1 for s in current_data["services"].values() if s["health_level"] == "unreachable")
                total_count = len(current_data["services"])

                logging.info(
                    f"Service Health Summary: {healthy_count} healthy, {warning_count} warning, "
                    f"{critical_count} critical, {unreachable_count} unreachable (Total: {total_count})"
                )

            except Exception as e:
                logging.error(f"Service monitoring error: {e}")
                import traceback
                traceback.print_exc()

    def main():
        """Main entry point"""
        parser = argparse.ArgumentParser(description="Service Health Real-time Monitor")
        parser.add_argument("--dry-run", action="store_true", help="Run checks without sending LINE/Email alerts")
        parser.add_argument("--test", action="store_true", help="Alias of --dry-run for compatibility")
        args = parser.parse_args()

        dry_run = args.dry_run or args.test
        print(f"🔧 Service Health Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if dry_run:
            print("Checking service status changes... (dry-run, alerts disabled)")
        else:
            print("Checking service status changes...")

        alert_manager = ServiceHealthAlertManager(dry_run=dry_run)
        alert_manager.run_service_monitoring()

        print("✅ Service monitoring check completed")

    if __name__ == "__main__":
        main()

except ImportError as e:
    logging.error(f"Import error: {e}")
    print(f"❌ Missing dependencies: {e}")
    sys.exit(1)
except Exception as e:
    logging.error(f"Unexpected error: {e}")
    print(f"❌ Error: {e}")
    sys.exit(1)
