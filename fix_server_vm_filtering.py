#!/usr/bin/env python3
"""
Fix VM filtering on production server
This script will update fetch_zabbix_data.py to exclude Carbon-Footprint-API from VM count
"""

import re
import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create backup of original file"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def check_current_filtering(content):
    """Check if filtering code already exists"""
    return 'service_endpoints_to_exclude' in content and 'Carbon-Footprint-API' in content

def apply_vm_filtering_fix(filepath):
    """Apply VM filtering fix to fetch_zabbix_data.py"""
    
    print(f"🔧 Applying VM filtering fix to: {filepath}")
    
    # Read current file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Check if filtering already exists
    if check_current_filtering(content):
        print("✅ VM filtering code already exists!")
        return True
    
    print("❌ VM filtering not found. Adding filtering code...")
    
    # Create backup first
    backup_path = backup_file(filepath)
    
    # Pattern to find the fetch_hosts method
    # Look for the specific pattern in the fetch_hosts method
    pattern = r'(\s+)(vm_hosts = \[\]\s+for host in hosts:)'
    
    if not re.search(pattern, content):
        # Alternative pattern if the above doesn't match
        pattern = r'(\s+)(vm_hosts = \[\]\s+for host in hosts:)'
        if not re.search(pattern, content):
            # Try a more flexible approach
            fetch_hosts_start = content.find('def fetch_hosts(self)')
            if fetch_hosts_start == -1:
                print("❌ Could not find fetch_hosts method!")
                return False
            
            # Find where we process hosts
            hosts_loop = content.find('for host in hosts:', fetch_hosts_start)
            if hosts_loop == -1:
                print("❌ Could not find hosts processing loop!")
                return False
            
            # Find the vm_hosts = [] line before the loop
            vm_hosts_line = content.rfind('vm_hosts = []', fetch_hosts_start, hosts_loop)
            if vm_hosts_line == -1:
                print("❌ Could not find vm_hosts initialization!")
                return False
            
            # Insert filtering code right after vm_hosts = []
            line_end = content.find('\n', vm_hosts_line)
            if line_end == -1:
                print("❌ Could not find line ending!")
                return False
            
            # Get indentation from the vm_hosts line
            line_start = content.rfind('\n', 0, vm_hosts_line) + 1
            indent = content[line_start:vm_hosts_line].replace('vm_hosts = []', '')
            
            # Create the filtering code with proper indentation
            filtering_code = f'''
{indent}# FILTER OUT SERVICE ENDPOINTS (not actual VMs)
{indent}service_endpoints_to_exclude = [
{indent}    'Carbon-Footprint-API',
{indent}    'carbon-footprint-api',
{indent}    'Carbon-Footprint-Endpoint', 
{indent}    'carbon-footprint-endpoint',
{indent}    'Service-Monitor',
{indent}    'service-monitor'
{indent}]
{indent}
{indent}excluded_count = 0
{indent}
{indent}for host in hosts:
{indent}    host_name = host.get('name', '')
{indent}    host_hostname = host.get('host', '')
{indent}    
{indent}    # CHECK IF THIS IS A SERVICE ENDPOINT (not a VM)
{indent}    is_service_endpoint = False
{indent}    for service_name in service_endpoints_to_exclude:
{indent}        if (service_name.lower() in host_name.lower() or 
{indent}            service_name.lower() in host_hostname.lower()):
{indent}            is_service_endpoint = True
{indent}            safe_log_info("🚫 EXCLUDING service endpoint: {{}} (not a VM)".format(host_name))
{indent}            excluded_count += 1
{indent}            break
{indent}    
{indent}    # Skip service endpoints - only include actual VMs
{indent}    if is_service_endpoint:
{indent}        continue
{indent}'''
            
            # Insert the filtering code
            new_content = content[:line_end] + filtering_code + content[hosts_loop:]
            
            # Update the logging message
            log_pattern = r'safe_log_info\("📊 Fetched \{\} hosts from Zabbix"\.format\(len\(vm_hosts\)\)\)'
            log_replacement = '''safe_log_info("📊 Fetched {} actual VMs from Zabbix (excluded {} service endpoints)".format(len(vm_hosts), excluded_count))
            safe_log_info("✅ VM Infrastructure Count: {} (Service endpoints filtered out)".format(len(vm_hosts)))'''
            
            new_content = re.sub(log_pattern, log_replacement, new_content)
            
            # Write the updated content
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("✅ VM filtering code applied successfully!")
                return True
            except Exception as e:
                print(f"❌ Error writing file: {e}")
                # Restore backup
                shutil.copy2(backup_path, filepath)
                print(f"🔄 Restored backup from: {backup_path}")
                return False
    
    print("❌ Could not apply filtering fix!")
    return False

def test_vm_count():
    """Test the VM count after applying fix"""
    try:
        from fetch_zabbix_data import fetch_vm_data
        hosts = fetch_vm_data()
        count = len(hosts)
        print(f"🧪 Test result: {count} VMs found")
        
        if count == 34:
            print("✅ SUCCESS! VM count is correct (34)")
        elif count == 35:
            print("❌ FAILED! Still showing 35 VMs - filtering not working")
        else:
            print(f"⚠️ Unexpected VM count: {count}")
        
        return count
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

def main():
    print("🚀 VM Filtering Fix Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('fetch_zabbix_data.py'):
        print("❌ fetch_zabbix_data.py not found!")
        print("Please run this script from the project directory")
        return False
    
    # Apply the fix
    success = apply_vm_filtering_fix('fetch_zabbix_data.py')
    
    if success:
        print("\n🧪 Testing VM count...")
        test_vm_count()
        
        print("\n✅ Fix completed!")
        print("Please restart the dashboard service:")
        print("  sudo systemctl restart vm-dashboard")
    else:
        print("\n❌ Fix failed!")
    
    return success

if __name__ == "__main__":
    main()
