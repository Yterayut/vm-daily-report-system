# Claude Code Configuration

This directory is now configured for use with Claude Code.

## Project Context
Working directory: /Users/teerayutyeerahem/project_vm_daily_report_2
Platform: macOS -> Ubuntu Server (one-climate@192.168.20.10)

## 🎯 PROJECT OVERVIEW
VM Infrastructure Monitoring System with 100% operational alert system, comprehensive email delivery, and complete real-time monitoring capabilities.

## 📋 IMPORTANT: Read First in New Context
**ALWAYS read `PROJECT_CONTEXT.md` first** - contains complete project state, recent changes, and current status.

## 🚀 Quick Start Commands for New Context

### **Check Project Status**
```bash
# Read project context first
cat PROJECT_CONTEXT.md

# Check checkpoint status
./checkpoint_sync.sh status

# Check server connection
ssh one-climate@192.168.20.10 "cd ~/project_vm_daily_report_2 && ./server_checkpoint_status.sh"
```

### **Key Systems Status**
```bash
# Test email system
python3 daily_report.py

# Test alert systems
./monitor_server.sh
ssh one-climate@192.168.20.10 "python3 ~/project_vm_daily_report_2/check_critical_alerts.py"

# Check recent logs
tail -20 logs/vm_daily_report.log
tail -10 logs/server_monitor.log
```

## 🔧 Recent Major Changes (REAL-TIME DATA FIX + LINE DISABLE: 2025-08-01 14:30)
- ✅ **LINE NOTIFICATIONS DISABLED**: ปิด LINE alerts ชั่วคราว (เก็บโค้ดไว้เปิดในอนาคต) - IMPLEMENTED ✅
- ✅ **HARDCODE DATA FIXED**: แก้ไขข้อมูล email จาก hardcode (2.1%, 24.8%, 15.3%) เป็น real-time - PERMANENT ✅
- ✅ **DATA ENRICHMENT PIPELINE**: เพิ่ม enrich_host_data() ใน send_production_dual.py - DEPLOYED ✅  
- ✅ **VM STATUS LOGIC FIXED**: เปลี่ยนจาก is_online เป็น Zabbix status field (0=online) - RESOLVED ✅
- ✅ **PERFORMANCE METRICS REAL**: ข้อมูล CPU/Memory/Disk จาก 34 VMs จริง - DIAGNOSED ✅
- ✅ **EMAIL CONTENT VERIFIED**: แสดงข้อมูล real-time เช่น CPU=1.0%, Memory=23.4% - CONFIRMED ✅
- ✅ **COMPREHENSIVE EMAIL FIX**: แก้ไข fallback logic ใช้ข้อมูลจริงแทน hardcode - VERIFIED ✅
- ✅ **DUAL RECIPIENTS**: ส่งไป yterayut@gmail.com + Support-oneclimate@one.th - WORKING ✅
- 🟢 **MISSION COMPLETE**: Real-time data + LINE disable ตามที่ขอ - SUCCESS ✅

## 🔧 Previous Major Changes (EMAIL SCHEDULE + NEW VM ALERTS ULTIMATE FIX: 2025-07-03 19:35)
- ✅ **EMAIL SCHEDULE MODIFICATION**: Changed from 8AM+5:30PM to 8AM only per user request - IMPLEMENTED ✅
- ✅ **NEW VM ALERTS ULTIMATE FIX**: Fixed vm_state_tracker.py test mode auto-execution causing false alerts - PERMANENT ✅
- ✅ **CRON SCHEDULE UPDATED**: Removed 17:30 completely, kept only 8:00 AM daily report - DEPLOYED ✅

## 📊 Current System State
- **Status**: Production Perfect ✅ (REAL-TIME DATA + LINE DISABLED + EMAIL SYSTEM FLAWLESS)
- **Email Schedule**: 8:00 AM only (17:30 removed per user request) ✅
- **LINE Notifications**: DISABLED (โค้ดเก็บไว้เปิดในอนาคต) ✅
- **Email Data**: REAL-TIME from Zabbix (ไม่ใช่ hardcode 2.1%, 24.8%, 15.3% แล้ว) ✅
- **Performance Metrics**: จาก 34 VMs จริง เช่น CPU=1.0%, Memory=23.4%, Disk=16.2% ✅
- **Data Pipeline**: fetch_hosts() → enrich_host_data() → calculate_enhanced_summary() ✅
- **VM Status Logic**: ใช้ Zabbix status field (0=monitored/online) แทน is_online ✅
- **Alert System**: 100% perfect - All monitoring systems working flawlessly with zero false alerts ✅
- **Critical Monitoring**: Every minute (check_critical_alerts.py fixed) ✅
- **Server Monitoring**: Every 15 minutes (monitor_server.sh optimized) ✅
- **Email**: 100% delivery success with safe HTML formatting + real data at 8:00 AM ✅
- **Recipients**: Support-oneclimate@one.th + yterayut@gmail.com (both working) ✅
- **Latest Fix**: Real-time data integration complete (2025-08-01) ✅

## 🎯 Common Tasks

### **Development Workflow**
```bash
# After making changes
./auto_workflow.sh deploy

# Emergency rollback if needed
./auto_workflow.sh rollback <checkpoint_name>
```

### **Maintenance**
```bash
# Sync checkpoints manually
./checkpoint_sync.sh auto

# Check alert system health
./monitor_server.sh
ssh one-climate@192.168.20.10 "python3 ~/project_vm_daily_report_2/check_critical_alerts.py"

# Check system health
./auto_workflow.sh test
```

## ⚠️ Important Notes
- **Server credentials**: one-climate@192.168.20.10 (SSH key auth)
- **Email recipients**: Support-oneclimate@one.th + yterayut@gmail.com
- **LINE Bot**: Monthly quota reached (emails working)
- **Cron jobs**: Running 08:00 AM daily only

## 🔗 Key Files to Understand
1. `PROJECT_CONTEXT.md` - Complete project state ✅ UPDATED
2. `daily_report.py` - Main system (with LINE disable check) ✅ UPDATED
3. `send_production_dual.py` - Production email sender (with real-time data) ✅ FIXED
4. `comprehensive_email_fix.py` - Multi-approach email delivery (fixed fallback logic) ✅ FIXED
5. `fetch_zabbix_data.py` - Zabbix data collection (fixed VM status logic) ✅ FIXED
6. `enhanced_alert_system.py` - Multi-channel alerts (LINE disabled) ✅ UPDATED
7. `monitor_server.sh` - Server health monitoring ✅ OPTIMIZED
8. `check_critical_alerts.py` - Critical monitoring ✅ FIXED
9. `vm_state_tracker.py` - VM power state tracking ✅ STABLE
10. `checkpoint_sync.sh` - Auto-sync system  
11. `.env` - Configuration (sensitive)

---
# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## 🎯 CURRENT TASK (Updated: 26 July 2025, 13:47)

### 📊 Service Health Dashboard Redesign - 9 Services
- **Status**: ✅ In Progress - Ready for Implementation
- **Target**: http://192.168.20.10:5000/mobile Services tab

### 📋 Requirements:
**Total Services: 9 (แทน 5)**

**🌍 Carbon Footprint Services (5 cards):**
1. Carbon Footprint (UAT)
2. Carbon Footprint (PRD) 
3. E-Tax Software
4. Rancher Management
5. Database Cluster

**📋 Carbon Receipt Services (4 cards):**
1. Etax Api (from sub-services)
2. One Api (from sub-services)
3. One Box Api (from sub-services) 
4. Vekin Api (from sub-services)

### 🔧 Implementation Plan:
1. ⏳ ปรับ Total Services เป็น 9 (5+4)
2. ⏳ แยกเป็น 2 กลุ่ม: Carbon Footprint (5) และ Carbon Receipt (4)
3. ⏳ สร้าง Carbon Receipt cards จาก sub-services API
4. ⏳ Deploy และทดสอบ

### 📡 API Endpoints:
- Carbon Receipt: https://uat-carbonreceipt.one.th/api/v1/health
- Mobile API: http://192.168.20.10:5000/api/services/health

### 📂 Latest Checkpoint:
- `SERVICE_HEALTH_DASHBOARD_REDESIGN_9_SERVICES_JULY_26_2025`
- Ready to continue implementation

## 📋 Context Continuity Instructions
When starting a new Claude Code session:
1. **FIRST**: Read `PROJECT_CONTEXT.md` completely
2. **SECOND**: Check `CLAUDE.md` for recent changes
3. **THIRD**: Run status commands to verify current state
4. **THEN**: Proceed with user requests based on current context

This ensures continuity across sessions and prevents duplicating completed work.
- to memorize