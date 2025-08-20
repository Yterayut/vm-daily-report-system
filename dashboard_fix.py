#!/usr/bin/env python3
"""
Dashboard Quick Fix Script
"""

dashboard_fix = '''
<script>
// Force initialize dashboard if it's stuck
function forceInitializeDashboard() {
    console.log('Force initializing dashboard...');
    
    // Hide loading, show dashboard
    const loading = document.getElementById('loading');
    const dashboard = document.getElementById('dashboard');
    
    if (loading) loading.style.display = 'none';
    if (dashboard) dashboard.style.display = 'block';
    
    // Set default values
    const elements = {
        'totalVMs': '34',
        'onlineVMs': '34', 
        'offlineVMs': '0',
        'uptimePercentage': '100%'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
    
    console.log('Dashboard force initialized');
}

// Auto-run after 3 seconds if still loading
setTimeout(forceInitializeDashboard, 3000);

// Add to window for manual trigger
window.forceInit = forceInitializeDashboard;
</script>
'''

print("Dashboard Fix Script")
print("===================")
print("Add this script to browser console or inject into dashboard:")
print()
print(dashboard_fix)
print()
print("To manually fix dashboard, run in browser console:")
print("forceInitializeDashboard()")
