# VM Daily Report System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Status](https://img.shields.io/badge/status-production-green.svg)

**Enhanced VM Daily Report System with Alert Integration** - ระบบตรวจสอบและรายงานประสิทธิภาพ Virtual Machine แบบครอบคลุม พร้อมระบบแจ้งเตือนหลายช่องทาง

## 🎯 Features

- 🖥️ **VM Monitoring**: ตรวจสอบ VM ผ่าน Zabbix API
- 📊 **Performance Charts**: กราฟแสดงประสิทธิภาพ CPU, Memory, Storage
- 📧 **Email Reports**: ส่งรายงาน PDF ทางอีเมลอัตโนมัติ
- 📱 **LINE Alerts**: แจ้งเตือนผ่าน LINE Bot
- 🌐 **Web Dashboard**: หน้าเว็บสำหรับดูข้อมูล Real-time
- 📈 **Storage Analysis**: วิเคราะห์การใช้พื้นที่จัดเก็บข้อมูล
- 🔔 **Multi-level Alerts**: แจ้งเตือนตามระดับความสำคัญ

## 🏗️ Architecture

### Core Components

1. **daily_report.py** - System Orchestrator
2. **fetch_zabbix_data.py** - Zabbix Data Collection  
3. **enhanced_alert_system.py** - Multi-channel Alert System
4. **generate_report.py** - PDF Report Generation

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+
pip install -r requirements.txt
```

### Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Configure your settings:
```bash
# Zabbix Configuration
ZABBIX_URL=http://your-zabbix-server/zabbix/api_jsonrpc.php
ZABBIX_USER=your_username
ZABBIX_PASS=your_password

# Email Configuration
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
TO_EMAILS=recipient@domain.com

# LINE Bot Configuration (Optional)
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_USER_ID=your_line_user_id
```

### Usage

```bash
# Run daily report
python daily_report.py

# Check system status
python main.py status

# Test system
python main.py test
```

## 📊 Sample Output

The system generates:
- **PDF Reports** with performance charts and statistics
- **Email notifications** with attached reports
- **LINE alerts** for critical issues
- **Web dashboard** for real-time monitoring

## 🔧 Configuration Options

### Alert Thresholds
```bash
CPU_WARNING_THRESHOLD=70
CPU_CRITICAL_THRESHOLD=85
MEMORY_WARNING_THRESHOLD=75
MEMORY_CRITICAL_THRESHOLD=90
DISK_WARNING_THRESHOLD=80
DISK_CRITICAL_THRESHOLD=90
```

### Alert Channels
```bash
WARNING_ALERT_CHANNELS=email,line
CRITICAL_ALERT_CHANNELS=email,line
EMERGENCY_ALERT_CHANNELS=email,line
```

## 📁 Project Structure

```
project_vm_daily_report_2/
├── daily_report.py              # Main orchestrator
├── fetch_zabbix_data.py         # Data collection
├── enhanced_alert_system.py     # Alert system
├── generate_report.py           # Report generation
├── load_env.py                  # Configuration loader
├── mobile_api.py                # Dashboard API
├── requirements.txt             # Dependencies
├── templates/                   # Report templates
├── static/                      # Static assets
├── output/                      # Generated reports
└── logs/                        # System logs
```

## 🐛 Known Issues & Solutions

See [PROJECT_DEVELOPMENT_LOG.md](PROJECT_DEVELOPMENT_LOG.md) for detailed development history and solutions.

## 📈 Performance

- Monitors 25+ VMs efficiently
- Generates reports in < 30 seconds
- 99%+ uptime with proper configuration
- Supports email delivery to multiple recipients

## 🔒 Security

- Environment variables for sensitive data
- Secure SMTP with TLS encryption
- API token authentication for LINE Bot
- Configurable SSL verification for Zabbix

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - Initial work - [YourGithub](https://github.com/YourGithub)

## 🙏 Acknowledgments

- Zabbix API for monitoring capabilities
- LINE Bot SDK for mobile notifications
- WeasyPrint for PDF generation
- One Climate team for requirements and testing

---

**🎉 Happy Monitoring!**
