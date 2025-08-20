#!/usr/bin/env python3
"""
Create Current VM Baseline for vm_states.json
Fetch current VM states from Zabbix and create proper baseline
"""

import json
from datetime import datetime
from fetch_zabbix_data import EnhancedZabbixClient

def create_current_baseline():
    """Create vm_states.json with current online VM states"""
    print("🔄 Creating Current VM Baseline...")
    print("=" * 50)
    
    # Initialize Zabbix client
    client = EnhancedZabbixClient()
    
    try:
        # Connect to Zabbix
        print("🔌 Connecting to Zabbix...")
        if not client.connect():
            print("❌ Failed to connect to Zabbix")
            return False
        
        # Fetch current VM data
        print("📡 Fetching current VM data from Zabbix...")
        hosts = client.fetch_hosts()
        
        if not hosts:
            print("❌ Failed to fetch VM data")
            return False
        
        # Enrich host data with metrics
        print("📊 Enriching VM data with metrics...")
        hosts = client.enrich_host_data(hosts)
        print(f"✅ Found {len(hosts)} VMs")
        
        # Create new baseline with current states
        current_states = {}
        timestamp = datetime.now().isoformat()
        
        for vm in hosts:
            host_id = vm.get('hostid', vm.get('name', 'unknown'))
            
            # Determine current online status
            is_online = vm.get('is_online', False)
            if vm.get('available') == 1:
                is_online = True
            
            current_states[host_id] = {
                'name': vm.get('name', 'Unknown'),
                'hostname': vm.get('hostname', vm.get('host', 'unknown')),
                'ip': vm.get('ip', 'N/A'),
                'is_online': is_online,
                'available': vm.get('available', 0),
                'status': vm.get('status', 1),
                'timestamp': timestamp,
                'alert_status': vm.get('alert_status', 'unknown'),
                'cpu_load': vm.get('cpu_load', 0),
                'memory_used': vm.get('memory_used', 0),
                'disk_used': vm.get('disk_used', 0)
            }
            
            print(f"  ✅ {vm.get('name', 'Unknown')} -> online: {is_online}")
        
        # Save to vm_states.json
        output_file = "logs/vm_states_current_baseline.json"
        with open(output_file, 'w') as f:
            json.dump(current_states, f, indent=2)
        
        # Show statistics
        online_count = sum(1 for vm in current_states.values() if vm['is_online'])
        total_count = len(current_states)
        
        print(f"\n📊 Baseline Created:")
        print(f"  Total VMs: {total_count}")
        print(f"  Online: {online_count}")
        print(f"  Offline: {total_count - online_count}")
        print(f"  File: {output_file}")
        print(f"  Size: {len(json.dumps(current_states, indent=2))} bytes")
        
        # Show problematic VMs status
        problematic_vms = ['10084', '10665', '10666', '10667', '10668']
        print(f"\n🔍 Problematic VMs Status:")
        for vm_id in problematic_vms:
            if vm_id in current_states:
                vm = current_states[vm_id]
                print(f"  {vm['name']}: online={vm['is_online']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating baseline: {e}")
        return False

if __name__ == "__main__":
    success = create_current_baseline()
    if success:
        print("\n✅ Current baseline created successfully!")
        print("📝 Next steps:")
        print("  1. Replace logs/vm_states.json with current baseline")
        print("  2. Deploy to server")
        print("  3. Test alert system")
    else:
        print("\n❌ Failed to create baseline")