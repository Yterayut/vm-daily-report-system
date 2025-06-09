#!/usr/bin/env python3
"""
Clean Daily Report - Minimal logging version
Run with clean output for production use
"""

import sys
import os

# Set clean logging - suppress debug messages
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.getLogger('weasyprint').setLevel(logging.ERROR)
logging.getLogger('pyzabbix.api').setLevel(logging.WARNING)

# Import after setting log levels
from daily_report import main

if __name__ == "__main__":
    # Clean environment for production
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    print("🚀 VM Daily Report - Production Mode")
    print("=" * 50)
    
    # Run with minimal output
    result = main()
    
    if result == 0:
        print("✅ Daily report completed successfully!")
    else:
        print("❌ Daily report completed with errors!")
    
    sys.exit(result)
