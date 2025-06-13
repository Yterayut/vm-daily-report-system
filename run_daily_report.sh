#!/bin/bash
# VM Daily Report Cron Job Script
# Automatically runs daily email report at 8:00 AM

# Change to project directory
cd "/Users/teerayutyeerahem/project_vm_daily_report_2"

# Set environment variables (if needed)
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the daily report
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 daily_report.py --simple >> logs/cron_daily_report.log 2>&1

# Log completion
echo "$(date): Daily report cron job completed" >> logs/cron_daily_report.log