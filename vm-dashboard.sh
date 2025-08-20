#!/bin/bash
# VM Dashboard Quick Commands

PROJECT_DIR="/Users/teerayutyeerahem/project_vm_daily_report_2"

case "${1:-help}" in
    start)
        echo "🚀 Starting VM Dashboard..."
        cd "$PROJECT_DIR" && ./start_mac_dashboard.sh start
        ;;
    stop)
        echo "🛑 Stopping VM Dashboard..."
        cd "$PROJECT_DIR" && ./start_mac_dashboard.sh stop
        ;;
    restart)
        echo "🔄 Restarting VM Dashboard..."
        cd "$PROJECT_DIR" && ./start_mac_dashboard.sh restart
        ;;
    status)
        cd "$PROJECT_DIR" && ./start_mac_dashboard.sh status
        ;;
    open)
        echo "🌐 Opening Dashboard in browser..."
        open "http://localhost:5001" 2>/dev/null || echo "Please open: http://localhost:5001"
        ;;
    logs)
        echo "📋 Dashboard logs:"
        tail -f "$PROJECT_DIR/logs/dashboard.log"
        ;;
    *)
        echo "📊 VM Dashboard Commands:"
        echo ""
        echo "  vm-dashboard start   - Start dashboard"
        echo "  vm-dashboard stop    - Stop dashboard"
        echo "  vm-dashboard restart - Restart dashboard"
        echo "  vm-dashboard status  - Check status"
        echo "  vm-dashboard open    - Open in browser"
        echo "  vm-dashboard logs    - Show logs"
        echo ""
        echo "🌐 Dashboard URL: http://localhost:5001"
        ;;
esac