#!/usr/bin/env python3
"""
Simple Fix: Update vm_states.json to set all VMs as online
Based on current vm_states.json, update all VMs to online status
"""

import json
from datetime import datetime

def fix_vm_baseline():
    """Update existing vm_states.json to set all VMs as online"""
    print("🔧 Fixing VM Baseline - Setting All VMs to Online")
    print("=" * 60)
    
    input_file = "logs/vm_states_full.json"
    output_file = "logs/vm_states_fixed.json"
    
    try:
        # Load current vm_states.json
        with open(input_file, 'r') as f:
            states = json.load(f)
        
        print(f"📂 Loaded {len(states)} VMs from {input_file}")
        
        # Update all VMs to online status
        current_timestamp = datetime.now().isoformat()
        online_count = 0
        
        for vm_id, vm_data in states.items():
            # Set VM as online
            vm_data['is_online'] = True
            vm_data['available'] = 1
            vm_data['status'] = 0
            vm_data['timestamp'] = current_timestamp
            vm_data['alert_status'] = 'ok'
            
            online_count += 1
            print(f"  ✅ {vm_data['name']} -> ONLINE")
        
        # Save fixed baseline
        with open(output_file, 'w') as f:
            json.dump(states, f, indent=2)
        
        print(f"\n📊 Baseline Fixed:")
        print(f"  Total VMs: {len(states)}")
        print(f"  Set to Online: {online_count}")
        print(f"  File: {output_file}")
        print(f"  Size: {len(json.dumps(states, indent=2))} bytes")
        
        # Show problematic VMs status
        problematic_vms = ['10084', '10665', '10666', '10667', '10668']
        print(f"\n🔍 Fixed Problematic VMs:")
        for vm_id in problematic_vms:
            if vm_id in states:
                vm = states[vm_id]
                print(f"  {vm['name']}: online={vm['is_online']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing baseline: {e}")
        return False

if __name__ == "__main__":
    success = fix_vm_baseline()
    if success:
        print("\n✅ VM baseline fixed successfully!")
        print("📝 Next steps:")
        print("  1. cp logs/vm_states_fixed.json logs/vm_states.json")
        print("  2. Deploy to server") 
        print("  3. Test alert system")
    else:
        print("\n❌ Failed to fix baseline")