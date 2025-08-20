#!/bin/bash
# Server Cleanup Script - ทำความสะอาด server จาก Mac

SERVER="192.168.20.10"
SERVER_USER="one-climate"
SERVER_PASS="U8@1v3z#14"
LOG_FILE="$HOME/project_vm_daily_report_2/logs/server_cleanup.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# สร้าง logs directory
mkdir -p "$(dirname "$LOG_FILE")"

# ฟังก์ชัน log
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# ทำความสะอาด Python cache files
cleanup_python_cache() {
    log_message "🧹 Cleaning Python cache files..."
    sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" \
        "find /usr -name '*.pyc' -delete 2>/dev/null || true && find /usr -name '*.pyo' -delete 2>/dev/null || true && find /usr -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"
    log_message "✅ Python cache cleaned"
}

# ทำความสะอาด Docker
cleanup_docker() {
    log_message "🧹 Cleaning Docker system..."
    sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" \
        "echo '$SERVER_PASS' | sudo -S docker system prune -f 2>/dev/null || true"
    log_message "✅ Docker system cleaned"
}

# ทำความสะอาด APT cache
cleanup_apt() {
    log_message "🧹 Cleaning APT cache..."
    sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" \
        "echo '$SERVER_PASS' | sudo -S apt-get clean 2>/dev/null || true"
    log_message "✅ APT cache cleaned"
}

# ทำความสะอาด logs เก่า
cleanup_logs() {
    log_message "🧹 Cleaning old log files..."
    sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" \
        "echo '$SERVER_PASS' | sudo -S find /var/log -name '*.log.*' -mtime +7 -delete 2>/dev/null || true && echo '$SERVER_PASS' | sudo -S find /var/log -name '*.gz' -mtime +14 -delete 2>/dev/null || true"
    log_message "✅ Old logs cleaned"
}

# ทำความสะอาด temporary files
cleanup_temp() {
    log_message "🧹 Cleaning temporary files..."
    sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" \
        "echo '$SERVER_PASS' | sudo -S find /var/tmp -type f -mtime +7 -delete 2>/dev/null || true && find /tmp -type f -mtime +1 -delete 2>/dev/null || true"
    log_message "✅ Temporary files cleaned"
}

# ทำความสะอาด systemd journal
cleanup_journal() {
    log_message "🧹 Cleaning systemd journal..."
    sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" \
        "echo '$SERVER_PASS' | sudo -S journalctl --vacuum-time=7d 2>/dev/null || true"
    log_message "✅ Systemd journal cleaned"
}

# ตรวจสอบ inodes ก่อนและหลัง
check_inodes() {
    local inode_info=$(sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" "df -i / | tail -1")
    local inode_total=$(echo "$inode_info" | awk '{print $2}')
    local inode_used=$(echo "$inode_info" | awk '{print $3}')
    local inode_free=$(echo "$inode_info" | awk '{print $4}')
    local inode_usage=$(echo "scale=1; $inode_used * 100 / $inode_total" | bc 2>/dev/null || echo "0")
    
    log_message "📊 Inodes: ${inode_usage}% used (${inode_free} free)"
}

# Main execution
main() {
    log_message "🚀 Server Cleanup Started"
    
    # ตรวจสอบการเชื่อมต่อ
    if ! ping -c 3 -W 5000 "$SERVER" >/dev/null 2>&1; then
        log_message "❌ Server unreachable"
        return 1
    fi
    
    log_message "📊 Before cleanup:"
    check_inodes
    
    # ทำความสะอาด
    cleanup_python_cache
    cleanup_docker
    cleanup_apt
    cleanup_logs
    cleanup_temp
    cleanup_journal
    
    log_message "📊 After cleanup:"
    check_inodes
    
    log_message "✅ Server Cleanup Completed"
    
    # Keep log file manageable
    tail -100 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
}

# Execute main function
main "$@"