#!/usr/bin/env python3
"""
VM Daily Report - Clean Production Version
No verbose logging from weasyprint or fontTools
"""

import os
import sys
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Setup clean logging before importing anything
def setup_clean_logging():
    # Suppress external libraries
    logging.getLogger('weasyprint').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.subset').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.ttLib').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.ttLib.ttFont').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.subset.timer').setLevel(logging.CRITICAL)
    
    # Setup main logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# Setup clean logging first
setup_clean_logging()

# Now import the daily report system
from daily_report import main

if __name__ == "__main__":
    print("🚀 VM Daily Report - Clean Production Mode")
    print("=" * 50)
    
    # Run the main daily report
    exit_code = main()
    
    if exit_code == 0:
        print("✅ Daily report completed successfully!")
    else:
        print("❌ Daily report failed!")
    
    sys.exit(exit_code)
