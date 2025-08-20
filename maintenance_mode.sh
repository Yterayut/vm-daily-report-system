#!/bin/bash
# Maintenance Mode Control for Enhanced VM Critical Alerts
# Usage: ./maintenance_mode.sh [enable|disable|status]

MAINTENANCE_FILE="logs/maintenance_mode"

case "$1" in
    enable)
        echo "$(date): Maintenance mode enabled" > "$MAINTENANCE_FILE"
        echo "✅ Maintenance mode ENABLED - VM critical alerts will be suppressed"
        ;;
    disable)
        if [ -f "$MAINTENANCE_FILE" ]; then
            rm "$MAINTENANCE_FILE"
            echo "✅ Maintenance mode DISABLED - VM critical alerts will resume"
        else
            echo "ℹ️ Maintenance mode was not enabled"
        fi
        ;;
    status)
        if [ -f "$MAINTENANCE_FILE" ]; then
            echo "🔧 Maintenance mode is ENABLED"
            echo "Enabled: $(cat $MAINTENANCE_FILE)"
        else
            echo "✅ Maintenance mode is DISABLED"
        fi
        ;;
    *)
        echo "Usage: $0 [enable|disable|status]"
        echo ""
        echo "Commands:"
        echo "  enable  - Enable maintenance mode (suppress alerts)"
        echo "  disable - Disable maintenance mode (resume alerts)"
        echo "  status  - Check maintenance mode status"
        ;;
esac