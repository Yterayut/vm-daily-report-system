#!/bin/bash
# VM Server Monitor - รันจาก Mac เพื่อ monitor server
# ตรวจสอบ server และส่งแจ้งเตือนหากมีปัญหา

SERVER="192.168.20.10"
SERVER_USER="one-climate"
SERVER_PASS="U8@1v3z#14"
LOG_FILE="$HOME/project_vm_daily_report_2/logs/server_monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# สร้าง logs directory
mkdir -p "$(dirname "$LOG_FILE")"

# ฟังก์ชัน log
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# ตรวจสอบการเชื่อมต่อ server
check_server_connection() {
    # Try ping with shorter timeout and retry mechanism
    local attempts=0
    local max_attempts=2
    
    while [ $attempts -lt $max_attempts ]; do
        if ping -c 2 -W 3000 "$SERVER" >/dev/null 2>&1; then
            log_message "✅ Server $SERVER is reachable (attempt $((attempts + 1)))"
            return 0
        fi
        attempts=$((attempts + 1))
        [ $attempts -lt $max_attempts ] && sleep 2
    done
    
    log_message "❌ Server $SERVER is unreachable after $max_attempts attempts"
    return 1
}

# ตรวจสอบ SSH connection
check_ssh_connection() {
    # Try SSH with key authentication (faster and more reliable)
    local attempts=0
    local max_attempts=2
    
    while [ $attempts -lt $max_attempts ]; do
        if ssh -o ConnectTimeout=8 -o ServerAliveInterval=5 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" "echo 'SSH OK'" >/dev/null 2>&1; then
            log_message "✅ SSH connection OK (attempt $((attempts + 1)))"
            return 0
        fi
        attempts=$((attempts + 1))
        [ $attempts -lt $max_attempts ] && sleep 2
    done
    
    log_message "❌ SSH connection failed after $max_attempts attempts"
    return 1
}

# ตรวจสอบ cron service บน server
check_remote_cron() {
    local result=$(ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" "systemctl is-active cron 2>/dev/null")
    if [ "$result" = "active" ]; then
        log_message "✅ Remote cron service is active"
        return 0
    else
        log_message "❌ Remote cron service is not active: $result"
        return 1
    fi
}

# ตรวจสอบ last report generation
check_last_report() {
    local last_report=$(ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" "ls -t ~/project_vm_daily_report_2/output/*.pdf 2>/dev/null | head -1")
    if [ -n "$last_report" ]; then
        local report_date=$(echo "$last_report" | grep -o '2025-[0-9-]*')
        log_message "✅ Last report: $report_date"
        
        # ตรวจสอบว่าเป็นวันนี้หรือไม่
        local today=$(date '+%Y-%m-%d')
        if [[ "$last_report" == *"$today"* ]]; then
            log_message "✅ Today's report exists"
            return 0
        else
            log_message "⚠️ No report for today ($today)"
            return 1
        fi
    else
        log_message "❌ No reports found"
        return 1
    fi
}

# ตรวจสอบ disk space และ inodes
check_server_resources() {
    local disk_usage=$(ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" "df -h / | tail -1 | awk '{print \$5}' | sed 's/%//'")
    
    # คำนวณ inode usage อย่างถูกต้อง
    local inode_info=$(ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" "df -i / | tail -1")
    local inode_total=$(echo "$inode_info" | awk '{print $2}')
    local inode_used=$(echo "$inode_info" | awk '{print $3}')
    local inode_free=$(echo "$inode_info" | awk '{print $4}')
    
    # คำนวณ percentage จริง
    local inode_usage_real=$(echo "scale=1; $inode_used * 100 / $inode_total" | bc 2>/dev/null || echo "0")
    local inode_usage_int=$(echo "$inode_usage_real" | cut -d. -f1)
    
    log_message "📊 Server resources: Disk ${disk_usage}%, Inodes ${inode_usage_real}% (${inode_free} free)"
    
    if [ "$disk_usage" -gt 90 ] || [ "$inode_usage_int" -gt 99 ]; then
        log_message "⚠️ Server resources critical"
        return 1
    else
        log_message "✅ Server resources OK"
        return 0
    fi
}

# ส่งการแจ้งเตือน
send_notification() {
    local message="$1"
    log_message "🚨 ALERT: $message"
    
    # อาจเพิ่ม email notification ในอนาคต
    echo "Alert: $message" | mail -s "VM Server Monitor Alert" "yterayut@gmail.com" 2>/dev/null || true
}

# รีสตาร์ท cron service บน server
restart_remote_cron() {
    log_message "🔄 Attempting to restart remote cron service..."
    # Use SSH key authentication with sudo (requires passwordless sudo for cron service)
    local result=$(ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER" "sudo systemctl restart cron 2>&1")
    sleep 3
    
    if check_remote_cron; then
        log_message "✅ Remote cron service restarted successfully"
        return 0
    else
        log_message "❌ Failed to restart remote cron service"
        return 1
    fi
}

# Main execution
main() {
    log_message "🔍 Server Monitor Check Started"
    
    local issues=0
    
    # ตรวจสอบการเชื่อมต่อ
    if ! check_server_connection; then
        issues=$((issues + 1))
        send_notification "Server connection failed"
    else
        # ตรวจสอบ SSH
        if ! check_ssh_connection; then
            issues=$((issues + 1))
            send_notification "SSH connection failed"
        else
            # ตรวจสอบ cron service
            if ! check_remote_cron; then
                issues=$((issues + 1))
                restart_remote_cron || send_notification "Failed to restart cron service"
            fi
            
            # ตรวจสอบ resources
            if ! check_server_resources; then
                issues=$((issues + 1))
                send_notification "Server resources critical"
            fi
            
            # ตรวจสอบ reports (เฉพาะช่วงเวลาที่ควรมี)
            local hour=$(date '+%H')
            if [ "$hour" -gt 8 ] && [ "$hour" -lt 23 ]; then
                if ! check_last_report; then
                    issues=$((issues + 1))
                fi
            fi
        fi
    fi
    
    if [ "$issues" -eq 0 ]; then
        log_message "✅ All checks passed"
    else
        log_message "⚠️ Found $issues issues"
    fi
    
    log_message "🏁 Server Monitor Check Completed"
    
    # Keep log file manageable
    tail -200 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
}

# Execute main function
main "$@"