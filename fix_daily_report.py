#!/usr/bin/env python3
"""Fix daily_report.py AlertLevel issues"""

with open('daily_report.py', 'r') as f:
    content = f.read()

# Fix import
old_import = "from enhanced_alert_system import EnhancedAlertSystem, send_enhanced_alerts  # NEW IMPORT"
new_import = "from enhanced_alert_system import EnhancedAlertSystem, send_enhanced_alerts, AlertLevel  # NEW IMPORT"
content = content.replace(old_import, new_import)

# Fix AlertLevel references
content = content.replace("orchestrator.alert_system.AlertLevel.INFO", "AlertLevel.INFO")
content = content.replace("orchestrator.alert_system.AlertLevel.WARNING", "AlertLevel.WARNING") 
content = content.replace("orchestrator.alert_system.AlertLevel.CRITICAL", "AlertLevel.CRITICAL")

# Write back
with open('daily_report.py', 'w') as f:
    f.write(content)

print("✅ Fixed daily_report.py")
