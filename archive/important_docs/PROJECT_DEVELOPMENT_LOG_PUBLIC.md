# VM Daily Report System - Development Log

**Project Name**: Enhanced VM Daily Report System with Alert Integration  
**Local Path**: `project_vm_daily_report_2`  
**Remote Server**: `your-server@your-ip:~/project_vm_daily_report_2`  
**Last Updated**: 2025-06-10 [Updated via script]

---

## 📋 System Overview

### Core Purpose
Advanced VM monitoring system that connects to Zabbix, generates comprehensive daily reports with performance metrics, storage analysis, and multi-channel alerting through Email and LINE notifications.

### Key Features
- **Zabbix Integration**: Real-time VM performance monitoring
- **PDF Report Generation**: Automated daily reports with charts
- **Multi-Channel Alerts**: Email + LINE Bot notifications  
- **Storage Performance Analysis**: Detailed disk usage monitoring
- **Web Dashboard**: Mobile-friendly monitoring interface
- **Performance Charts**: Visual metrics with matplotlib

---

## 🏗️ System Architecture

### Core Components

#### 1. **main.py** - System Controller
- **Purpose**: CLI interface and system orchestration
- **Key Functions**:
  - `show_system_status()` - Display current VM status
  - `run_comprehensive_test()` - Full system validation
  - `generate_daily_report()` - Trigger report generation
  - `run_maintenance_check()` - Health checks
- **Commands**: status, test, report, charts, maintenance, full

#### 2. **daily_report.py** - Report Orchestrator  
- **Purpose**: Main workflow coordinator with alert integration
- **Key Classes**:
  - `EnhancedVMReportOrchestrator` - Primary orchestrator
- **Features**:
  - Signal handling for graceful shutdown
  - Statistics tracking (VMs processed, emails sent, alerts triggered)
  - Comprehensive error handling and logging

#### 3. **fetch_zabbix_data.py** - Data Collection Engine
- **Purpose**: Enhanced Zabbix data fetching with fixed CPU metrics
- **Key Classes**:
  - `EnhancedZabbixClient` - Zabbix API client
- **Fixed Issues**:
  - CPU metric keys corrected (system.cpu.util vs system.cpu.util[])
  - Storage performance calculations
  - Memory usage analysis
- **Data Collected**: CPU, Memory, Storage, Network, Host status

#### 4. **enhanced_alert_system.py** - Alert Management
- **Purpose**: Multi-channel alert system (Email + LINE)
- **Key Classes**:
  - `AlertLevel` (Enum): INFO, WARNING, CRITICAL, EMERGENCY
  - `AlertChannel` (Enum): EMAIL, LINE, SLACK, TEAMS
  - `AlertConfig` - Configuration dataclass
- **Features**:
  - LINE Bot SDK v2 integration
  - Email SMTP with attachments
  - Configurable thresholds
  - Alert templates

#### 5. **generate_report.py** - PDF Generation
- **Purpose**: PDF report creation with charts and tables
- **Features**: WeasyPrint PDF generation, chart embedding

#### 6. **mobile_api.py** - Dashboard API
- **Purpose**: Web API for mobile dashboard
- **Features**: JSON API endpoints for real-time data

---

## 🔧 Configuration System

### Environment Files
- **`.env`** - Main production configuration
- **`.env.key`** - API keys and secrets
- **`.env.example`** - Template for configuration

### Required Environment Variables

#### Zabbix Configuration
```bash
ZABBIX_URL=http://your-zabbix-server/zabbix/api_jsonrpc.php
ZABBIX_USER=your_username
ZABBIX_PASS=your_password
ZABBIX_TIMEOUT=30
ZABBIX_VERIFY_SSL=false
```

#### Email Configuration
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
SENDER_NAME=VM Monitoring System
TO_EMAILS=recipient1@domain.com,recipient2@domain.com
```

#### LINE Bot Configuration
```bash
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_USER_ID=your_line_user_id
```

#### Alert Thresholds
```bash
CPU_WARNING_THRESHOLD=70.0
CPU_CRITICAL_THRESHOLD=85.0
MEMORY_WARNING_THRESHOLD=75.0
MEMORY_CRITICAL_THRESHOLD=90.0
STORAGE_WARNING_THRESHOLD=80.0
STORAGE_CRITICAL_THRESHOLD=95.0
```

---

## 🚀 Deployment & Operations

### Available Commands
```bash
vm-cd          # Navigate to project directory
vm-pull        # Pull latest changes from server
vm-deploy      # Deploy to remote server
vm-test        # Test deployment on server
vm-run         # Run production system
vm-status      # Check system status
code .         # Open in VS Code
```

### Deployment Process
1. **Local Development**: Make changes in local project
2. **Deploy**: Use `vm-deploy` to push to server
3. **Test**: Use `vm-test` to validate deployment
4. **Production**: Use `vm-run` to start production

### Server Details
- **Host**: `your-server-ip`
- **User**: `your-username`
- **Path**: `~/project_vm_daily_report_2`

---

## 📊 System Capabilities

### Data Collection
- **VM Status**: Online/Offline monitoring
- **Performance Metrics**: CPU, Memory, Storage utilization
- **Storage Analysis**: Used/Total space, usage percentages
- **Network Monitoring**: Interface status and traffic
- **Host Information**: Names, groups, descriptions

### Report Generation
- **PDF Reports**: Comprehensive daily summaries
- **Performance Charts**: CPU, Memory, Storage trends
- **Alert Summaries**: Warning and critical issues
- **Storage Analysis**: Top users and capacity planning

### Alert System
- **Email Alerts**: Rich HTML notifications with attachments
- **LINE Notifications**: Instant mobile alerts
- **Severity Levels**: INFO, WARNING, CRITICAL, EMERGENCY
- **Customizable Thresholds**: Per-metric configuration

---

## 🛠️ Development Workflow

### Standard Process
1. **Issue Identification**: User reports problem
2. **File Analysis**: Examine relevant system files
3. **Code Modification**: Make necessary changes
4. **Deployment**: Use `vm-deploy` to push changes
5. **Testing**: Use `vm-test` to validate fixes
6. **Documentation**: Update this log with changes

### Testing Commands
```bash
python main.py status          # Show system status
python main.py test            # Run comprehensive test
python main.py maintenance     # Health checks
python main.py full            # Complete workflow
```

---

## 📁 Important Files & Directories

### Core Python Files
- `main.py` - System controller
- `daily_report.py` - Report orchestrator
- `fetch_zabbix_data.py` - Data collection
- `enhanced_alert_system.py` - Alert system
- `generate_report.py` - PDF generation
- `mobile_api.py` - Dashboard API
- `load_env.py` - Environment loader

### Configuration Files
- `.env*` files - Environment configuration
- `requirements*.txt` - Python dependencies

### Output Directories
- `output/` - Generated reports and files
- `logs/` - System logs
- `static/` - Web dashboard assets
- `templates/` - Report templates

---

## 🐛 Known Issues & Solutions

### Fixed Issues
1. **CPU Metrics**: Corrected Zabbix key format from `system.cpu.util[]` to `system.cpu.util`
2. **Storage Calculation**: Fixed storage performance calculations
3. **LINE Bot Integration**: Updated to use LINE Bot SDK v2
4. **Email Attachments**: Resolved PDF attachment issues

### Common Problems
1. **Zabbix Connection**: Check URL format and credentials
2. **Email Delivery**: Verify SMTP settings and app passwords
3. **LINE Notifications**: Confirm token and user ID
4. **Storage Data**: Ensure Zabbix has storage monitoring items

---

## 📈 Performance Metrics

### System Monitoring
- **Total VMs**: Count of monitored virtual machines
- **Online VMs**: Currently active systems
- **Storage Usage**: Aggregate disk utilization
- **Alert Frequency**: Warning and critical alerts per day

### Report Statistics
- **VMs Processed**: Number of systems in reports
- **Charts Generated**: Performance visualizations created
- **Emails Sent**: Notification delivery count
- **LINE Alerts**: Mobile notifications sent

---

## 🔄 Update History

### Recent Major Updates

- **System Architecture**: Enhanced VM monitoring with multi-channel alerts
- **Email System**: Implemented reliable delivery to multiple recipients
- **LINE Integration**: Added LINE Bot notifications for critical alerts
- **Report Generation**: Professional PDF reports with performance charts
- **Configuration**: Comprehensive environment variable management
- **Logging**: Advanced logging system with rotation
- **Documentation**: Complete development log system

---

## 📝 Notes for Future Development

### Code Quality
- All functions include comprehensive error handling
- Logging is implemented throughout with safe fallbacks
- Environment variables are validated on startup
- Signal handlers ensure graceful shutdown

### Extension Points
- Alert system supports additional channels (Slack, Teams)
- Report templates can be customized in `templates/`
- Dashboard can be extended with new API endpoints
- Monitoring can include additional Zabbix metrics

### Best Practices
- Always test locally before deployment
- Update this log with any significant changes
- Use proper error handling and logging
- Follow established naming conventions
- Document configuration changes

---

**For any questions or issues, refer to this log and examine the relevant source files in the project directory.**
