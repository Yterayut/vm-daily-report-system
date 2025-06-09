#!/usr/bin/env python3
from load_env import load_env_file, setup_logging
from fetch_zabbix_data import fetch_vm_data, calculate_enhanced_summary, generate_enhanced_charts  
from generate_report import EnhancedReportGenerator
from send_email_simple import send_email

def main():
    load_env_file()
    
    # Get real Zabbix data
    vm_data = fetch_vm_data()
    summary = calculate_enhanced_summary(vm_data)
    
    # Generate charts and PDF
    generate_enhanced_charts(vm_data, summary, 'static')
    generator = EnhancedReportGenerator()
    pdf_path = generator.generate_comprehensive_report(vm_data, summary)
    
    # Send email with real data
    success = send_email(summary, pdf_path)
    print(f"{'✅ SUCCESS' if success else '❌ FAILED'}: Real Zabbix data sent!")

if __name__ == "__main__":
    main()