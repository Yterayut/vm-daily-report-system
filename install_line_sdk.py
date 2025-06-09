#!/usr/bin/env python3
"""
Install LINE Bot SDK for VM Monitoring System
This script will install the LINE Bot SDK and test the configuration
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def main():
    print("🚀 Installing LINE Bot SDK for VM Monitoring System")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("❌ Python 3.7+ required for LINE Bot SDK")
        return False
    
    # Install LINE Bot SDK
    commands = [
        ("pip3 install line-bot-sdk>=3.5.0", "Installing LINE Bot SDK"),
        ("pip3 install --upgrade line-bot-sdk", "Upgrading LINE Bot SDK to latest version"),
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    if not success:
        print("\n❌ Installation failed. Please check errors above.")
        return False
    
    # Test import
    print("\n🧪 Testing LINE Bot SDK import...")
    try:
        from linebot import LineBotApi
        from linebot.models import TextSendMessage
        print("✅ LINE Bot SDK imported successfully")
    except ImportError as e:
        print(f"❌ LINE Bot SDK import failed: {e}")
        return False
    
    # Check environment configuration
    print("\n🔍 Checking LINE configuration in .env...")
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if "LINE_CHANNEL_ACCESS_TOKEN" in env_content:
            print("✅ LINE_CHANNEL_ACCESS_TOKEN found in .env")
        else:
            print("⚠️ LINE_CHANNEL_ACCESS_TOKEN not found in .env")
        
        if "LINE_USER_ID" in env_content:
            print("✅ LINE_USER_ID found in .env")
        else:
            print("⚠️ LINE_USER_ID not found in .env")
    else:
        print("⚠️ .env file not found")
    
    # Test LINE Bot initialization
    print("\n🧪 Testing LINE Bot initialization...")
    try:
        # Load environment
        from load_env import load_env_file
        load_env_file()
        
        # Test alert system
        from enhanced_alert_system import EnhancedAlertSystem, AlertLevel
        alert_system = EnhancedAlertSystem()
        
        if alert_system.line_bot_api:
            print("✅ LINE Bot API initialized successfully")
            
            # Test sending a message
            print("\n📱 Testing LINE message sending...")
            success = alert_system.send_line_alert(
                "🧪 LINE Bot SDK Installation Test\n✅ Installation completed successfully!",
                AlertLevel.INFO
            )
            
            if success:
                print("✅ Test message sent successfully!")
                print("📱 Check your LINE app for the test message")
            else:
                print("❌ Test message failed to send")
                print("   Please check your LINE configuration")
        else:
            print("❌ LINE Bot API initialization failed")
            print("   Please check your LINE_CHANNEL_ACCESS_TOKEN")
    
    except Exception as e:
        print(f"❌ LINE Bot test failed: {e}")
        print("   This might be due to missing dependencies or configuration issues")
    
    print("\n" + "=" * 60)
    print("🏁 Installation completed!")
    print("\nNext steps:")
    print("1. Verify your LINE_CHANNEL_ACCESS_TOKEN in .env")
    print("2. Verify your LINE_USER_ID in .env")
    print("3. Run: python3 daily_report.py --test-alerts")
    print("4. Run: python3 daily_report.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    main()
