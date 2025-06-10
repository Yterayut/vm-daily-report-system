#!/usr/bin/env python3
'''
Cron-Safe Environment Loader
ป้องกันปัญหาการใช้ไฟล์ .env ผิด
'''

import os
from pathlib import Path

def load_cron_safe_env():
    """โหลด environment ที่ปลอดภัยสำหรับ cron"""
    
    # บังคับใช้ absolute path
    script_dir = Path(__file__).parent.absolute()
    main_env_file = script_dir / '.env'
    
    print(f"🔒 Cron-Safe: Loading from {main_env_file}")
    
    if not main_env_file.exists():
        print(f"❌ Main .env file not found: {main_env_file}")
        return False
    
    try:
        with open(main_env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        
        print(f"✅ Loaded environment from: {main_env_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading environment: {e}")
        return False

if __name__ == "__main__":
    load_cron_safe_env()
