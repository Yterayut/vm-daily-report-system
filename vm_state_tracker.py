#!/usr/bin/env python3
"""
VM State Tracker - Power On/Off Detection System
Tracks VM power state changes and generates alerts
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class VMStateTracker:
    """Track VM power state changes and detect power on/off events"""
    
    def __init__(self, state_file: str = "vm_states.json"):
        """Initialize state tracker"""
        self.state_file = Path(state_file)
        self.previous_states = self._load_previous_states()
        
    def _load_previous_states(self) -> Dict[str, Any]:
        """Load previous VM states from file"""
        if not self.state_file.exists():
            return {}
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_current_states(self, states: Dict[str, Any]):
        """Save current VM states to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(states, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save VM states: {e}")
    
    def detect_power_changes(self, current_vm_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect power state changes between current and previous states
        Returns: {
            'powered_on': [list of VMs that powered on],
            'powered_off': [list of VMs that powered off],
            'recovered': [list of VMs that came back online],
            'new_vms': [list of newly discovered VMs]
        }
        """
        changes = {
            'powered_on': [],
            'powered_off': [],
            'recovered': [],
            'new_vms': []
        }
        
        # Create current states dict
        current_states = {}
        timestamp = datetime.now().isoformat()
        
        for vm in current_vm_data:
            host_id = vm.get('hostid', vm.get('name', 'unknown'))
            current_states[host_id] = {
                'name': vm.get('name', 'Unknown'),
                'hostname': vm.get('hostname', vm.get('host', 'unknown')),
                'ip': vm.get('ip', 'N/A'),
                'is_online': vm.get('is_online', False),
                'available': vm.get('available', 0),
                'status': vm.get('status', 1),
                'timestamp': timestamp,
                'alert_status': vm.get('alert_status', 'unknown'),
                'cpu_load': vm.get('cpu_load', 0),
                'memory_used': vm.get('memory_used', 0),
                'disk_used': vm.get('disk_used', 0)
            }
        
        # Compare with previous states
        for host_id, current_state in current_states.items():
            previous_state = self.previous_states.get(host_id)
            
            if previous_state is None:
                # New VM discovered
                if current_state['is_online']:
                    changes['new_vms'].append({
                        'host_id': host_id,
                        'name': current_state['name'],
                        'hostname': current_state['hostname'],
                        'ip': current_state['ip'],
                        'timestamp': timestamp,
                        'event': 'new_vm_online'
                    })
                continue
            
            # Check for power state changes
            was_online = previous_state.get('is_online', False)
            is_online = current_state['is_online']
            
            if not was_online and is_online:
                # VM powered on or recovered
                time_diff = self._calculate_time_diff(previous_state.get('timestamp'))
                event_type = 'recovered' if time_diff and time_diff > timedelta(hours=1) else 'powered_on'
                
                change_data = {
                    'host_id': host_id,
                    'name': current_state['name'],
                    'hostname': current_state['hostname'],
                    'ip': current_state['ip'],
                    'timestamp': timestamp,
                    'downtime_duration': str(time_diff) if time_diff else 'Unknown',
                    'event': event_type
                }
                
                if event_type == 'recovered':
                    changes['recovered'].append(change_data)
                else:
                    changes['powered_on'].append(change_data)
                    
            elif was_online and not is_online:
                # VM powered off
                changes['powered_off'].append({
                    'host_id': host_id,
                    'name': current_state['name'],
                    'hostname': current_state['hostname'],
                    'ip': current_state['ip'],
                    'timestamp': timestamp,
                    'last_seen': previous_state.get('timestamp', 'Unknown'),
                    'event': 'powered_off'
                })
        
        # Check for VMs that disappeared (were in previous but not in current)
        for host_id, previous_state in self.previous_states.items():
            if host_id not in current_states and previous_state.get('is_online', False):
                changes['powered_off'].append({
                    'host_id': host_id,
                    'name': previous_state['name'],
                    'hostname': previous_state['hostname'],
                    'ip': previous_state.get('ip', 'N/A'),
                    'timestamp': timestamp,
                    'last_seen': previous_state.get('timestamp', 'Unknown'),
                    'event': 'vm_disappeared'
                })
        
        # Save current states for next comparison
        self._save_current_states(current_states)
        
        return changes
    
    def _calculate_time_diff(self, previous_timestamp: Optional[str]) -> Optional[timedelta]:
        """Calculate time difference from previous timestamp"""
        if not previous_timestamp:
            return None
        
        try:
            previous_time = datetime.fromisoformat(previous_timestamp.replace('Z', '+00:00'))
            current_time = datetime.now()
            return current_time - previous_time
        except (ValueError, TypeError):
            return None
    
    def generate_power_change_alerts(self, changes: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate alerts for power state changes"""
        alerts = []
        
        # Power on alerts
        for vm in changes['powered_on']:
            alerts.append({
                'level': 'INFO',
                'type': 'power_on',
                'title': f"VM Powered On: {vm['name']}",
                'message': f"Virtual machine {vm['name']} ({vm['hostname']}) has powered on",
                'details': {
                    'vm_name': vm['name'],
                    'hostname': vm['hostname'],
                    'ip': vm['ip'],
                    'timestamp': vm['timestamp'],
                    'event': vm['event']
                },
                'icon': '🟢',
                'timestamp': vm['timestamp']
            })
        
        # Power off alerts
        for vm in changes['powered_off']:
            alerts.append({
                'level': 'WARNING',
                'type': 'power_off',
                'title': f"VM Powered Off: {vm['name']}",
                'message': f"Virtual machine {vm['name']} ({vm['hostname']}) has powered off or become unavailable",
                'details': {
                    'vm_name': vm['name'],
                    'hostname': vm['hostname'],
                    'ip': vm['ip'],
                    'timestamp': vm['timestamp'],
                    'last_seen': vm['last_seen'],
                    'event': vm['event']
                },
                'icon': '🔴',
                'timestamp': vm['timestamp']
            })
        
        # Recovery alerts
        for vm in changes['recovered']:
            alerts.append({
                'level': 'INFO',
                'type': 'recovery',
                'title': f"VM Recovered: {vm['name']}",
                'message': f"Virtual machine {vm['name']} ({vm['hostname']}) has recovered after {vm['downtime_duration']}",
                'details': {
                    'vm_name': vm['name'],
                    'hostname': vm['hostname'],
                    'ip': vm['ip'],
                    'timestamp': vm['timestamp'],
                    'downtime_duration': vm['downtime_duration'],
                    'event': vm['event']
                },
                'icon': '🟡',
                'timestamp': vm['timestamp']
            })
        
        # New VM alerts
        for vm in changes['new_vms']:
            alerts.append({
                'level': 'INFO',
                'type': 'new_vm',
                'title': f"New VM Discovered: {vm['name']}",
                'message': f"New virtual machine {vm['name']} ({vm['hostname']}) has been discovered and is online",
                'details': {
                    'vm_name': vm['name'],
                    'hostname': vm['hostname'],
                    'ip': vm['ip'],
                    'timestamp': vm['timestamp'],
                    'event': vm['event']
                },
                'icon': '✨',
                'timestamp': vm['timestamp']
            })
        
        return alerts
    
    def get_summary_stats(self, changes: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Get summary statistics for power changes"""
        return {
            'total_changes': sum(len(changes[key]) for key in changes),
            'powered_on_count': len(changes['powered_on']),
            'powered_off_count': len(changes['powered_off']),
            'recovered_count': len(changes['recovered']),
            'new_vms_count': len(changes['new_vms']),
            'has_changes': any(len(changes[key]) > 0 for key in changes),
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup_old_states(self, days_to_keep: int = 7):
        """Clean up old state records"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        cleaned_states = {}
        for host_id, state in self.previous_states.items():
            timestamp_str = state.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if timestamp > cutoff_time:
                        cleaned_states[host_id] = state
                except (ValueError, TypeError):
                    # Keep states with invalid timestamps for safety
                    cleaned_states[host_id] = state
            else:
                # Keep states without timestamps for safety
                cleaned_states[host_id] = state
        
        self.previous_states = cleaned_states
        self._save_current_states(cleaned_states)


def test_vm_state_tracker():
    """Test the VM state tracker with sample data"""
    print("🧪 Testing VM State Tracker...")
    
    # Sample VM data
    sample_vms = [
        {
            'hostid': '10001',
            'name': 'web-server-01',
            'hostname': 'web01',
            'ip': '10.0.1.10',
            'is_online': True,
            'available': 1,
            'status': 0,
            'alert_status': 'ok'
        },
        {
            'hostid': '10002',
            'name': 'database-server',
            'hostname': 'db01',
            'ip': '10.0.1.20',
            'is_online': False,
            'available': 0,
            'status': 0,
            'alert_status': 'critical'
        }
    ]
    
    tracker = VMStateTracker("test_vm_states.json")
    
    # First run - establish baseline
    print("First run (establishing baseline)...")
    changes = tracker.detect_power_changes(sample_vms)
    alerts = tracker.generate_power_change_alerts(changes)
    print(f"Changes detected: {tracker.get_summary_stats(changes)}")
    
    # Second run - simulate power change
    print("\nSecond run (simulating database recovery)...")
    sample_vms[1]['is_online'] = True
    sample_vms[1]['available'] = 1
    
    changes = tracker.detect_power_changes(sample_vms)
    alerts = tracker.generate_power_change_alerts(changes)
    stats = tracker.get_summary_stats(changes)
    
    print(f"Changes detected: {stats}")
    print(f"Alerts generated: {len(alerts)}")
    
    for alert in alerts:
        print(f"  {alert['icon']} {alert['level']}: {alert['title']}")
    
    # Cleanup test file
    test_file = Path("test_vm_states.json")
    if test_file.exists():
        test_file.unlink()
    
    print("✅ Test completed!")


if __name__ == "__main__":
    test_vm_state_tracker()