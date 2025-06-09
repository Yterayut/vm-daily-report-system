#!/usr/bin/env python3
"""
Ultimate Clean Daily Report - No Verbose Output
"""

import os
import sys
import warnings

# Silence everything before importing
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Redirect stderr to null to suppress weasyprint warnings
import contextlib
from io import StringIO

def silence_external_warnings():
    """Silence external library warnings"""
    import logging
    
    # Set all external loggers to CRITICAL
    external_loggers = [
        'weasyprint', 'weasyprint.html', 'weasyprint.css', 'weasyprint.css.targets',
        'weasyprint.css.style_for', 'weasyprint.css.get_all_computed_styles',
        'fontTools', 'fontTools.subset', 'fontTools.ttLib', 'fontTools.ttLib.ttFont',
        'fontTools.subset.timer', 'pyzabbix.api'
    ]
    
    for logger_name in external_loggers:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)

def main():
    """Run clean daily report"""
    print("🚀 VM Daily Report - Ultra Clean Mode")
    print("=" * 45)
    
    try:
        # Setup clean environment
        silence_external_warnings()
        
        # Import and run daily report with suppressed output
        from daily_report import EnhancedVMReportOrchestrator
        
        print("🔧 Initializing system...")
        orchestrator = EnhancedVMReportOrchestrator()
        
        # Capture verbose output during initialization
        f = StringIO()
        with contextlib.redirect_stderr(f):
            if not orchestrator.initialize():
                print("❌ System initialization failed")
                return 1
        
        print("✅ System ready")
        print("📊 Running daily workflow...")
        
        # Run workflow with suppressed output
        with contextlib.redirect_stderr(f):
            success = orchestrator.run_complete_workflow()
        
        if success:
            print("✅ Daily report completed successfully!")
            print("📧 Email sent with PDF attachment")
            print("📱 LINE notification sent")
            return 0
        else:
            print("❌ Workflow failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
