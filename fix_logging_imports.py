#!/usr/bin/env python3
"""
Fix logging imports in all Python files
"""

import os
import re
from pathlib import Path

def fix_logging_in_file(file_path):
    """Fix logging import issues in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip files that already have safe logging
        if 'safe_log_info' in content or 'get_logger()' in content:
            print(f"✅ {file_path.name} - Already fixed")
            return True
            
        # Skip files that don't use logging
        if 'import logging' not in content and 'logging.' not in content:
            print(f"⚪ {file_path.name} - No logging usage")
            return True
        
        print(f"🔧 Fixing {file_path.name}...")
        
        # Remove standalone import logging
        content = re.sub(r'^import logging\n', '', content, flags=re.MULTILINE)
        
        # Replace logger = logging.getLogger(__name__) with safe version
        safe_logger_setup = '''
# Safe logger setup
logger = None

def get_logger():
    """Get logger instance safely"""
    global logger
    if logger is None:
        try:
            import logging
            logger = logging.getLogger(__name__)
        except:
            logger = None
    return logger

def safe_log_info(message):
    """Safe logging info"""
    try:
        log = get_logger()
        if log:
            log.info(message)
        else:
            print(f"INFO: {message}")
    except:
        print(f"INFO: {message}")

def safe_log_error(message):
    """Safe logging error"""
    try:
        log = get_logger()
        if log:
            log.error(message)
        else:
            print(f"ERROR: {message}")
    except:
        print(f"ERROR: {message}")

def safe_log_warning(message):
    """Safe logging warning"""
    try:
        log = get_logger()
        if log:
            log.warning(message)
        else:
            print(f"WARNING: {message}")
    except:
        print(f"WARNING: {message}")
'''
        
        # Replace logger declaration
        content = re.sub(r'logger = logging\.getLogger\(__name__\)', safe_logger_setup, content)
        
        # Replace logging usage
        content = re.sub(r'logger\.info\(', 'safe_log_info(', content)
        content = re.sub(r'logger\.error\(', 'safe_log_error(', content)
        content = re.sub(r'logger\.warning\(', 'safe_log_warning(', content)
        content = re.sub(r'logging\.warning\(', 'safe_log_warning(', content)
        content = re.sub(r'logging\.error\(', 'safe_log_error(', content)
        content = re.sub(r'logging\.info\(', 'safe_log_info(', content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {file_path.name} - Fixed")
        return True
        
    except Exception as e:
        print(f"❌ {file_path.name} - Error: {e}")
        return False

def main():
    """Fix all Python files"""
    project_dir = Path(__file__).parent
    
    print("🚀 Fixing logging imports in all Python files...")
    print("=" * 50)
    
    # Find all Python files
    python_files = list(project_dir.glob("*.py"))
    
    # Skip this script itself
    python_files = [f for f in python_files if f.name != 'fix_logging_imports.py']
    
    fixed_count = 0
    total_count = len(python_files)
    
    for py_file in python_files:
        if fix_logging_in_file(py_file):
            fixed_count += 1
    
    print("=" * 50)
    print(f"🎯 Results: {fixed_count}/{total_count} files processed")
    
    if fixed_count == total_count:
        print("✅ All files fixed successfully!")
    else:
        print("⚠️ Some files had issues")

if __name__ == "__main__":
    main()
