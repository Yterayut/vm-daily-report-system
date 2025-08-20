#!/bin/bash
# Start Mac Dashboard Script

PROJECT_DIR="/Users/teerayutyeerahem/project_vm_daily_report_2"
DASHBOARD_PID_FILE="$PROJECT_DIR/dashboard.pid"
LOG_FILE="$PROJECT_DIR/logs/dashboard.log"

# สร้าง logs directory
mkdir -p "$PROJECT_DIR/logs"

# ฟังก์ชันสำหรับหยุด dashboard
stop_dashboard() {
    if [ -f "$DASHBOARD_PID_FILE" ]; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "🛑 Stopping dashboard (PID: $PID)..."
            kill "$PID"
            rm -f "$DASHBOARD_PID_FILE"
            echo "✅ Dashboard stopped"
        else
            echo "⚠️ Dashboard not running"
            rm -f "$DASHBOARD_PID_FILE"
        fi
    else
        echo "⚠️ No dashboard PID file found"
    fi
}

# ฟังก์ชันสำหรับเริ่ม dashboard
start_dashboard() {
    if [ -f "$DASHBOARD_PID_FILE" ]; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️ Dashboard already running (PID: $PID)"
            echo "🌐 URL: http://localhost:5001"
            return
        else
            rm -f "$DASHBOARD_PID_FILE"
        fi
    fi
    
    echo "🚀 Starting Mac Dashboard..."
    echo "📊 VM Monitoring Dashboard"
    echo "🌐 URL: http://localhost:5001"
    echo "📱 Mobile responsive design"
    echo ""
    
    cd "$PROJECT_DIR"
    
    # ตรวจสอบ Python และ dependencies
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found"
        exit 1
    fi
    
    # ติดตั้ง Flask หากไม่มี
    python3 -c "import flask" 2>/dev/null || {
        echo "📦 Installing Flask..."
        pip3 install flask flask-cors
    }
    
    # เริ่ม dashboard
    python3 mac_dashboard.py > "$LOG_FILE" 2>&1 &
    DASHBOARD_PID=$!
    
    echo "$DASHBOARD_PID" > "$DASHBOARD_PID_FILE"
    echo "✅ Dashboard started (PID: $DASHBOARD_PID)"
    echo "📋 Log file: $LOG_FILE"
    
    # รอให้ service เริ่มต้น
    sleep 2
    
    # ตรวจสอบว่า service ทำงาน
    if ps -p "$DASHBOARD_PID" > /dev/null 2>&1; then
        echo "🎉 Dashboard is running successfully!"
        echo ""
        echo "🌐 Open in browser: http://localhost:5001"
        echo "📱 Or try: http://$(hostname -I | awk '{print $1}'):5001"
        echo ""
        echo "Commands:"
        echo "  ./start_mac_dashboard.sh stop    - Stop dashboard"
        echo "  ./start_mac_dashboard.sh restart - Restart dashboard"
        echo "  ./start_mac_dashboard.sh status  - Check status"
        
        # เปิด browser ถ้าเป็น Mac
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sleep 1
            open "http://localhost:5001" 2>/dev/null || true
        fi
        
    else
        echo "❌ Failed to start dashboard"
        rm -f "$DASHBOARD_PID_FILE"
        echo "📋 Check log: $LOG_FILE"
        exit 1
    fi
}

# ฟังก์ชันสำหรับตรวจสอบสถานะ
check_status() {
    if [ -f "$DASHBOARD_PID_FILE" ]; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Dashboard is running (PID: $PID)"
            echo "🌐 URL: http://localhost:5001"
            echo "📋 Log: $LOG_FILE"
        else
            echo "❌ Dashboard not running (stale PID file)"
            rm -f "$DASHBOARD_PID_FILE"
        fi
    else
        echo "❌ Dashboard not running"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_dashboard
        ;;
    stop)
        stop_dashboard
        ;;
    restart)
        stop_dashboard
        sleep 1
        start_dashboard
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "  start   - Start dashboard (default)"
        echo "  stop    - Stop dashboard"
        echo "  restart - Restart dashboard"
        echo "  status  - Check dashboard status"
        exit 1
        ;;
esac