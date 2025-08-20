#!/bin/bash
# Log Cleanup Script - ทำความสะอาด logs เก่า

PROJECT_DIR="/Users/teerayutyeerahem/project_vm_daily_report_2"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# สร้าง logs directory หากไม่มี
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] 🧹 Starting log cleanup..."

# ทำความสะอาด Mac logs
find "$LOG_DIR" -name "*.log" -size +10M -exec truncate -s 1M {} \;
find "$LOG_DIR" -name "*.log.*" -mtime +7 -delete
find "$PROJECT_DIR" -name "*.log.tmp" -mtime +1 -delete

# ทำความสะอาด output เก่า
find "$PROJECT_DIR/output" -name "*.pdf" -mtime +30 -delete 2>/dev/null || true

echo "[$TIMESTAMP] ✅ Log cleanup completed"