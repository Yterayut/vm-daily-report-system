#!/usr/bin/env python3
"""
Quick Fix - Replace send_email.py with simple version
"""

import os
import shutil
from pathlib import Path

def backup_and_replace():
    """Backup current send_email.py and replace with simple version"""
    
    current_dir = Path('.')
    
    # Backup current send_email.py
    current_send_email = current_dir / 'send_email.py'
    backup_send_email = current_dir / 'send_email.py.enhanced_backup'
    
    if current_send_email.exists():
        shutil.copy2(current_send_email, backup_send_email)
        print(f"✅ Backed up current send_email.py to {backup_send_email}")
    
    # Replace with simple version
    simple_version = current_dir / 'send_email_simple.py'
    
    if simple_version.exists():
        shutil.copy2(simple_version, current_send_email)
        print(f"✅ Replaced send_email.py with simple working version")
    else:
        print("❌ send_email_simple.py not found")
        return False
    
    return True

def main():
    print("🔧 Updating VM Daily Report System to use Simple Email")
    print("=" * 60)
    
    if backup_and_replace():
        print("\n✅ System updated successfully!")
        print("\nNow you can run:")
        print("  python3 daily_report.py --test")
        print("\nAnd the emails should be delivered! 📧")
        
        print("\nWhat changed:")
        print("• Removed complex HTML templates")
        print("• Removed professional headers")  
        print("• Uses simple plain text format")
        print("• Same format as working test emails")
        
        print("\nTo restore enhanced version later:")
        print("  mv send_email.py.enhanced_backup send_email.py")
    else:
        print("\n❌ Update failed!")

if __name__ == "__main__":
    main()
