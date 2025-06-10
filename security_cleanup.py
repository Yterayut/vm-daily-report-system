#!/usr/bin/env python3
"""
Security Cleanup Tool - Remove all sensitive data before GitHub upload
เครื่องมือทำความสะอาดข้อมูลส่วนตัวก่อนอัปโหลด GitHub
"""

import os
import re
from pathlib import Path

def scan_and_clean_sensitive_data():
    """สแกนและทำความสะอาดข้อมูลส่วนตัว"""
    
    project_dir = Path(__file__).parent
    
    # รายการข้อมูลส่วนตัวที่ต้องแทนที่
    sensitive_patterns = {
        'noev kftj juiy ermg': '[YOUR_EMAIL_APP_PASSWORD]',
        'njtx qzrw qnyd dylz': '[YOUR_EMAIL_APP_PASSWORD]',
        'U8@1v3z#14': '[YOUR_SERVER_PASSWORD]',
        '192.168.20.10': '[YOUR_SERVER_IP]',
        'one-climate@192.168.20.10': '[YOUR_USER]@[YOUR_SERVER_IP]',
        'yterayut@gmail.com': '[YOUR_EMAIL]@gmail.com',
        'yterayut@inet.co.th': '[YOUR_EMAIL]@[YOUR_DOMAIN].th',
        'Support-oneclimate@one.th': '[SUPPORT_EMAIL]@[YOUR_DOMAIN].th',
        'sKjdOmddbjqyU3MyIkQ/QzU6oiLHBFMWaFFO3W6tqBwiQmiUx1MgIqICOIkiO8MWdp0/0IOIVrnI4oLvNEKj9T+7IdLM29TJyxBld5rZYUzNa2clO7CK3y7j363tc4s5H6bki7ngOagsOXY9UVsFfQdB04t89/1O/w1cDnyilFU=': '[YOUR_LINE_CHANNEL_ACCESS_TOKEN]',
        'U5e06da00701ddd8fade3b7b7b67c7a14': '[YOUR_LINE_USER_ID]',
        'teerayutyeerahem': '[YOUR_USERNAME]',
        'yterayut': '[YOUR_USERNAME]'
    }
    
    # ไฟล์ที่ต้องทำความสะอาด (เฉพาะที่จะอัปโหลด GitHub)
    files_to_clean = [
        'NEW_CHAT_COMPLETE_GUIDE.md',
        'NEW_CHAT_MESSAGE.txt', 
        'NEW_CHAT_QUICK_REFERENCE.md',
        'PROJECT_DEVELOPMENT_LOG.md',
        'pre-commit-security-check.sh',
        'deploy_smart.sh',
        'deploy_password.sh',
        'deploy_quick.sh',
        'deploy_simple.sh',
        'sync_deploy.sh',
        'setup_dev.sh',
        'setup_logrotate_project_vm.sh',
        'start_dashboard.sh',
        'watch_deploy.sh',
        'mobile_dashboard.html',
        'vm_monitoring_manual.html'
    ]
    
    print("🔍 SCANNING FOR SENSITIVE DATA...")
    print("=" * 60)
    
    cleaned_files = []
    
    for file_name in files_to_clean:
        file_path = project_dir / file_name
        if file_path.exists():
            print(f"📄 Processing {file_name}...")
            
            try:
                # อ่านไฟล์
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                found_sensitive = False
                
                # แทนที่ข้อมูลส่วนตัว
                for sensitive, replacement in sensitive_patterns.items():
                    if sensitive in content:
                        content = content.replace(sensitive, replacement)
                        found_sensitive = True
                        print(f"   🔒 Replaced: {sensitive[:20]}...")
                
                # เขียนกลับถ้ามีการเปลี่ยนแปลง
                if found_sensitive:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    cleaned_files.append(file_name)
                    print(f"   ✅ Cleaned: {file_name}")
                else:
                    print(f"   ✅ Clean: {file_name}")
                    
            except Exception as e:
                print(f"   ❌ Error processing {file_name}: {e}")
    
    print(f"\n📊 SUMMARY:")
    print(f"Files cleaned: {len(cleaned_files)}")
    if cleaned_files:
        print("Cleaned files:")
        for file_name in cleaned_files:
            print(f"  - {file_name}")
    
    return cleaned_files

def add_to_gitignore():
    """เพิ่มไฟล์ที่มีข้อมูลส่วนตัวใน .gitignore"""
    
    sensitive_files = [
        # ไฟล์ที่มีข้อมูลส่วนตัว - ต้องไม่อัปโหลด
        '.env',
        '.env.key', 
        '.env.yterayut',
        '.env.yterayut.disabled',
        '.env.yterayut.backup.*',
        'cron.log*',
        'alerts.log*',
        '.last_resource_alert.json',
        'vm_report.log',
        'system_analysis_results.json',
        
        # ไฟล์ที่มีข้อมูลเซิร์ฟเวอร์จริง
        'deploy_password.sh',
        'deploy_quick.sh', 
        'deploy_simple.sh',
        'deploy_smart.sh',
        'sync_deploy.sh',
        'setup_dev.sh',
        'setup_logrotate_project_vm.sh',
        'start_dashboard.sh',
        'watch_deploy.sh',
        
        # ไฟล์เอกสารที่มีข้อมูลส่วนตัว
        'NEW_CHAT_COMPLETE_GUIDE.md',
        'NEW_CHAT_MESSAGE.txt',
        'NEW_CHAT_QUICK_REFERENCE.md', 
        'PROJECT_DEVELOPMENT_LOG.md',
        'QUICK_START_MESSAGE.txt',
        
        # ไฟล์ test และ debug ที่อาจมีข้อมูลจริง
        'diagnose_email_config.py',
        'fix_email_config.py',
        'comprehensive_system_analysis.py',
        'final_email_configuration.py',
        'final_system_status.py',
        'logo_fix_summary.py',
        'production_status_check.py',
        
        # Tool files ที่มีข้อมูลส่วนตัว
        'security_incident_response.py',
        'clean_git_history.sh',
        'check_alerts_only.py',
        'check_critical_alerts.py',
        'check_line_friendship.py',
        'daily_summary.py',
        'install.py',
        
        # Dashboard และ manual files
        'mobile_dashboard.html',
        'vm_monitoring_manual.html',
        'dashboard-settings.html',
        'VM_Monitoring_Mobile_Dashboard.html',
        
        # Backup และ temp files  
        '*.save',
        '*.success',
        '*.success2',
        '*.01062025',
        'load_env copy.py',
        'main.py.disabled',
        'mobile_api.py.save',
        'generate_report.py.save',
        'generate_report.py.success*',
        'fetch_zabbix_data.py.save',
        'fetch_zabbix_data.py.01062025',
        'daily_report.py.save',
        'daily_report.py.success',
        'apiVersion:.save'
    ]
    
    gitignore_path = Path(__file__).parent / '.gitignore'
    
    # อ่าน .gitignore ปัจจุบัน
    current_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            current_content = f.read()
    
    # เพิ่มไฟล์ที่ยังไม่มี
    new_entries = []
    for file_pattern in sensitive_files:
        if file_pattern not in current_content:
            new_entries.append(file_pattern)
    
    if new_entries:
        with open(gitignore_path, 'a') as f:
            f.write(f"\n# Additional sensitive files - Added by security cleanup\n")
            for entry in new_entries:
                f.write(f"{entry}\n")
        
        print(f"✅ Added {len(new_entries)} entries to .gitignore")
    else:
        print("✅ .gitignore already up to date")

if __name__ == "__main__":
    print("🔒 SECURITY CLEANUP TOOL")
    print("=" * 60)
    
    # ทำความสะอาดข้อมูลส่วนตัว
    cleaned_files = scan_and_clean_sensitive_data()
    
    # อัปเดต .gitignore  
    add_to_gitignore()
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Review cleaned files to ensure they're safe")
    print("2. Test the application still works")
    print("3. Commit only safe files to GitHub")
    print("4. Never commit actual .env files")
    
    print(f"\n⚠️ REMINDER:")
    print("The following contain real secrets and should NEVER be committed:")
    print("- .env files")
    print("- Files with server passwords")
    print("- Files with email passwords") 
    print("- Files with LINE tokens")
