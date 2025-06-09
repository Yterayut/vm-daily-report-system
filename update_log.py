#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Log Update Helper - Simple version for Python 2/3 compatibility
"""

import os
import sys
from datetime import datetime

def update_log_timestamp():
    """Update timestamp in main log file"""
    log_file = "PROJECT_DEVELOPMENT_LOG.md"
    
    if not os.path.exists(log_file):
        print("❌ PROJECT_DEVELOPMENT_LOG.md not found")
        return
    
    try:
        # Read log file
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Find and replace "Last Updated" pattern
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Search for "Last Updated" line
        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            if line.startswith('**Last Updated**:'):
                # Replace this line
                lines[i] = '**Last Updated**: {} [Updated via script]'.format(current_date)
                updated = True
                break
        
        if updated:
            # Write back to file
            with open(log_file, 'w') as f:
                f.write('\n'.join(lines))
            print("✅ Updated timestamp to {}".format(current_date))
        else:
            print("⚠️ 'Last Updated' line not found in file")
            
    except Exception as e:
        print("❌ Error: {}".format(e))

def add_log_entry(change_type, title, description, files_modified=None):
    """Add new entry to log"""
    log_file = "PROJECT_DEVELOPMENT_LOG.md"
    
    if not os.path.exists(log_file):
        print("❌ PROJECT_DEVELOPMENT_LOG.md not found")
        return
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Create new entry
    new_entry = """
### {} - {}: {}
- **Change**: {}
- **Files Modified**: {}
- **Impact**: Enhanced system functionality
""".format(current_date, change_type, title, description, 
           ', '.join(files_modified) if files_modified else 'N/A')
    
    try:
        # Read log file
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Find "Update History" section and add entry
        history_marker = "## 🔄 Update History"
        
        if history_marker in content:
            # Split before and after Update History
            parts = content.split(history_marker)
            before_history = parts[0] + history_marker
            after_history = parts[1] if len(parts) > 1 else ""
            
            # Add new entry after Update History header
            updated_content = before_history + new_entry + after_history
            
            # Write back to file
            with open(log_file, 'w') as f:
                f.write(updated_content)
            
            print("✅ Added log entry: {} - {}".format(change_type, title))
            
            # Update timestamp too
            update_log_timestamp()
            
        else:
            print("⚠️ 'Update History' section not found in file")
            
    except Exception as e:
        print("❌ Error: {}".format(e))

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("📝 Log Update Helper")
        print("=" * 30)
        print("Usage:")
        print("  python update_log.py timestamp                    # Update timestamp")
        print("  python update_log.py add <type> <title> <desc>   # Add entry")
        print("")
        print("Examples:")
        print("  python update_log.py timestamp")
        print("  python update_log.py add 'Bug Fix' 'LINE Alert Fix' 'Fixed LINE notification'")
        return
    
    command = sys.argv[1].lower()
    
    if command == "timestamp":
        update_log_timestamp()
        
    elif command == "add" and len(sys.argv) >= 5:
        change_type = sys.argv[2]
        title = sys.argv[3]
        description = sys.argv[4]
        files_modified = sys.argv[5:] if len(sys.argv) > 5 else []
        
        add_log_entry(change_type, title, description, files_modified)
        
    else:
        print("❌ Invalid command")
        print("Use 'python update_log.py' to see usage")

if __name__ == "__main__":
    main()
