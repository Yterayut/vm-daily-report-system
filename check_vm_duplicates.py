#!/usr/bin/env python3
"""
Check all VMs from Zabbix for duplicate naming patterns
"""

from fetch_zabbix_data import EnhancedZabbixClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Create Zabbix client using correct initialization
    client = EnhancedZabbixClient()
    
    # Connect to Zabbix
    if not client.connect():
        print("❌ Failed to connect to Zabbix")
        return

    print('🔍 Connecting to Zabbix and fetching all hosts...')
    print('=' * 80)

    try:
        # Get all hosts with detailed info
        hosts = client.zapi.host.get(
            output=['hostid', 'name', 'host', 'status', 'available'],
            selectInterfaces=['ip', 'dns', 'port'],
            selectGroups=['name'],
            filter={'status': 0}  # Only enabled hosts
        )
        
        print(f'📊 Found {len(hosts)} enabled hosts in Zabbix')
        print('=' * 80)
        
        # Track duplicates and patterns
        duplicates = []
        name_counts = {}
        host_counts = {}
        
        for i, host in enumerate(hosts, 1):
            hostid = host.get('hostid', 'N/A')
            name = host.get('name', 'N/A')
            hostname = host.get('host', 'N/A')
            status = host.get('status', 'N/A')
            available = host.get('available', 'N/A')
            
            # Get IP address
            interfaces = host.get('interfaces', [])
            ip = interfaces[0].get('ip', 'N/A') if interfaces else 'N/A'
            
            # Count occurrences
            name_counts[name] = name_counts.get(name, 0) + 1
            host_counts[hostname] = host_counts.get(hostname, 0) + 1
            
            # Check if name and hostname are different
            if name != hostname:
                duplicates.append({
                    'hostid': hostid,
                    'name': name,
                    'hostname': hostname,
                    'ip': ip
                })
            
            print(f'{i:2d}. Host ID: {hostid}')
            print(f'    📛 Name: {name}')
            print(f'    🏠 Host: {hostname}')
            print(f'    🌐 IP: {ip}')
            print(f'    📊 Status: {status} | Available: {available}')
            
            # Check for specific patterns that cause duplicates
            if 'PRD_One-Climate' in name or 'ONE-CLIMATE-PRD' in hostname:
                print(f'    ⚠️  DUPLICATE PATTERN DETECTED')
            
            print('-' * 40)
        
        print('\n' + '=' * 80)
        print('🔍 DUPLICATE ANALYSIS SUMMARY')
        print('=' * 80)
        
        # Show hosts with different name vs hostname
        if duplicates:
            print(f'⚠️ Found {len(duplicates)} hosts with different name/hostname:')
            for dup in duplicates:
                print(f'\n🔄 Host ID: {dup["hostid"]} | IP: {dup["ip"]}')
                print(f'   📛 Name: {dup["name"]}')
                print(f'   🏠 Host: {dup["hostname"]}')
                
                # Check for specific duplicate pattern
                if ('PRD_One-Climate' in dup["name"] and 'ONE-CLIMATE-PRD' in dup["hostname"]):
                    print(f'   🚨 THIS IS THE REPORTED DUPLICATE ISSUE!')
        else:
            print('✅ All hosts have identical name and hostname fields')
        
        # Show actual duplicates in each field
        print(f'\n📊 DUPLICATE NAMES (same name field):')
        name_dups = {k: v for k, v in name_counts.items() if v > 1}
        if name_dups:
            for name, count in name_dups.items():
                print(f'   {count}x: {name}')
        else:
            print('   ✅ No duplicate names found')
        
        print(f'\n📊 DUPLICATE HOSTNAMES (same host field):')
        host_dups = {k: v for k, v in host_counts.items() if v > 1}
        if host_dups:
            for hostname, count in host_dups.items():
                print(f'   {count}x: {hostname}')
        else:
            print('   ✅ No duplicate hostnames found')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()