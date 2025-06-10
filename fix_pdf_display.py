#!/usr/bin/env python3
"""
PDF Display Fix for WeasyPrint Compatibility
แก้ไขปัญหาการแสดงผล PDF ใน browser
"""

import os
from pathlib import Path
from generate_report import EnhancedReportGenerator

def fix_pdf_display_issues():
    """แก้ไขปัญหาการแสดงผล PDF"""
    
    # ปรับปรุง CSS สำหรับ WeasyPrint
    improved_css = """
    /* PDF-Optimized CSS for WeasyPrint */
    @page {
        size: A4;
        margin: 1.5cm;
        @top-center {
            content: "VM Infrastructure Report";
        }
        @bottom-center {
            content: "Page " counter(page) " of " counter(pages);
        }
    }
    
    /* Base Styles */
    body { 
        font-family: 'DejaVu Sans', 'Arial Unicode MS', sans-serif; 
        font-size: 9pt; 
        line-height: 1.4; 
        color: #333;
    }
    
    /* Table Improvements */
    .vm-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 8pt;
    }
    
    .vm-table th {
        background: linear-gradient(135deg, #27ae60, #2ecc71);
        color: white;
        padding: 8px 4px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #27ae60;
        font-size: 8pt;
    }
    
    .vm-table td {
        padding: 6px 4px;
        border: 1px solid #bdc3c7;
        text-align: center;
        vertical-align: middle;
    }
    
    .vm-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    /* Status Badges - Simple Text Only */
    .status-online {
        background: #27ae60;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 7pt;
        font-weight: bold;
        display: inline-block;
    }
    
    .status-offline {
        background: #e74c3c;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 7pt;
        font-weight: bold;
        display: inline-block;
    }
    
    /* Health Indicators - Simple Circles */
    .health-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
        vertical-align: middle;
    }
    
    .health-excellent { background: #27ae60; }
    .health-good { background: #f39c12; }
    .health-poor { background: #e74c3c; }
    
    /* Metric Values */
    .metric-normal { color: #27ae60; font-weight: bold; }
    .metric-medium { color: #f39c12; font-weight: bold; }
    .metric-high { color: #e74c3c; font-weight: bold; }
    
    /* Headers */
    .page-title {
        color: #27ae60;
        font-size: 18pt;
        margin: 0 0 20px 0;
        text-align: center;
        border-bottom: 2px solid #27ae60;
        padding-bottom: 10px;
    }
    
    .section-title {
        color: #2c3e50;
        font-size: 12pt;
        margin: 20px 0 10px 0;
        padding: 8px 0;
        border-left: 4px solid #27ae60;
        padding-left: 10px;
    }
    
    /* Page breaks */
    .page-break { page-break-before: always; }
    
    /* Text utilities */
    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .font-bold { font-weight: bold; }
    """
    
    return improved_css

def create_pdf_friendly_template():
    """สร้าง template ที่เหมาะสำหรับ PDF"""
    
    template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VM Infrastructure Report</title>
    <style>
    {css_content}
    </style>
</head>
<body>
    <div class="page-break"></div>
    <div class="details-page">
        <h1 class="page-title">Virtual Machine Inventory</h1>
        
        <h2 class="section-title">📋 Complete System Inventory</h2>
        
        <table class="vm-table">
            <thead>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 25%;">VM Name</th>
                    <th style="width: 15%;">IP Address</th>
                    <th style="width: 10%;">CPU %</th>
                    <th style="width: 10%;">Memory %</th>
                    <th style="width: 10%;">Disk %</th>
                    <th style="width: 10%;">Health</th>
                    <th style="width: 15%;">Status</th>
                </tr>
            </thead>
            <tbody>
                {% for vm in vm_data %}
                <tr>
                    <td class="text-center">{{ loop.index }}</td>
                    <td class="font-bold">
                        {% if vm.name|length > 25 %}
                            {{ vm.name[:25] }}...
                        {% else %}
                            {{ vm.name }}
                        {% endif %}
                    </td>
                    <td>{{ vm.ip or vm.hostname or 'N/A' }}</td>
                    <td class="text-center">
                        {% set cpu_class = 'metric-high' if vm.cpu_load > 80 else 'metric-medium' if vm.cpu_load > 60 else 'metric-normal' %}
                        <span class="metric-value {{ cpu_class }}">{{ vm.cpu_load|round(1) }}%</span>
                    </td>
                    <td class="text-center">
                        {% set mem_class = 'metric-high' if vm.memory_used > 85 else 'metric-medium' if vm.memory_used > 70 else 'metric-normal' %}
                        <span class="metric-value {{ mem_class }}">{{ vm.memory_used|round(1) }}%</span>
                    </td>
                    <td class="text-center">
                        {% set disk_class = 'metric-high' if vm.disk_used > 85 else 'metric-medium' if vm.disk_used > 70 else 'metric-normal' %}
                        <span class="metric-value {{ disk_class }}">{{ vm.disk_used|round(1) }}%</span>
                    </td>
                    <td class="text-center">
                        <!-- แก้ไข Health Indicator ไม่ใช้ emoji -->
                        {% set health_class = 'health-excellent' if vm.health_score >= 90 else 'health-good' if vm.health_score >= 70 else 'health-poor' %}
                        <span class="health-indicator {{ health_class }}"></span>{{ vm.health_score or 0 }}
                    </td>
                    <td class="text-center">
                        <!-- แก้ไข Status ไม่ใช้ emoji -->
                        {% if vm.is_online %}
                            <span class="status-online">ONLINE</span>
                        {% else %}
                            <span class="status-offline">OFFLINE</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
    """
    
    return template

if __name__ == "__main__":
    print("🔧 PDF Display Fix Tool")
    print("This script helps fix PDF display issues in browsers")
    
    css = fix_pdf_display_issues()
    template = create_pdf_friendly_template()
    
    print("✅ Improved CSS and template created")
    print("📋 Key improvements:")
    print("   - Removed emoji icons")
    print("   - Simplified status badges")
    print("   - Better color indicators")
    print("   - WeasyPrint optimized CSS")
