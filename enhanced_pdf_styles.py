#!/usr/bin/env python3
"""
Enhanced PDF Styles - One Climate Style Matching
Based on provided PDF sample with exact styling replication
"""

def get_enhanced_a4_css():
    """Professional A4-optimized CSS matching One Climate style exactly"""
    return """
    @page {
        size: A4 portrait;
        margin: 15mm 12mm 15mm 12mm;
        @top-right {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 9px;
            color: #666;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin-top: 5mm;
        }
        @bottom-center {
            content: "Generated: One Climate VM Infrastructure Report";
            font-size: 9px;
            color: #666;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    }

    @page:first {
        margin: 0;
        @top-right { content: none; }
        @bottom-center { content: none; }
    }

    /* Professional Typography - Matching Sample */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Segoe UI', 'Arial', 'Helvetica Neue', sans-serif;
        line-height: 1.5;
        color: #2c3e50;
        font-size: 10pt;
        font-weight: 400;
        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
    }

    .page {
        width: 100%;
        min-height: 100vh;
        page-break-inside: avoid;
    }

    .page-break {
        page-break-before: always;
    }

    /* Enhanced Cover Page - Exact Match */
    .cover-page {
        height: 297mm;
        width: 210mm;
        margin: 0;
        padding: 0;
        background: linear-gradient(135deg, 
            #2E5BBA 0%, 
            #4A90E2 25%, 
            #3498DB 50%, 
            #2ECC71 75%, 
            #27AE60 100%);
        color: white;
        display: flex;
        flex-direction: column;
        position: relative;
        overflow: hidden;
        page-break-after: always;
        box-sizing: border-box;
    }

    .cover-page::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 15% 15%, rgba(255,255,255,0.08) 0%, transparent 35%),
            radial-gradient(circle at 85% 85%, rgba(255,255,255,0.05) 0%, transparent 35%);
    }

    .cover-header {
        padding: 40px 50px 20px 50px;
        position: relative;
        z-index: 3;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }

    .cover-logo {
        width: 200px;
        height: auto;
        max-height: 60px;
    }

    .cover-badge {
        background: rgba(255,255,255,0.2);
        color: white;
        padding: 8px 20px;
        border-radius: 20px;
        font-size: 11pt;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .cover-content {
        flex-grow: 1;
        padding: 20px 50px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        z-index: 3;
        text-align: left;
    }

    .cover-title {
        font-size: 48pt;
        font-weight: 300;
        line-height: 1.1;
        margin-bottom: 15px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    .cover-title h1 {
        margin: 0;
        padding: 0;
        font-size: inherit;
        font-weight: inherit;
    }

    .cover-title .highlight {
        font-weight: 700;
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5) !important;
        background: rgba(255,255,255,0.1);
        padding: 5px 15px;
        border-radius: 8px;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255,255,255,0.2);
    }

    .cover-subtitle {
        font-size: 15pt;
        font-weight: 300;
        margin-bottom: 10px;
        line-height: 1.4;
        opacity: 0.95;
    }

    .subtitle-features {
        font-size: 13pt;
        opacity: 0.85;
        font-weight: 400;
        margin-bottom: 30px;
    }

    .cover-date {
        font-size: 16pt;
        font-weight: 500;
        margin-bottom: 40px;
        background: rgba(255,255,255,0.15);
        padding: 12px 25px;
        border-radius: 25px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        display: inline-block;
        max-width: 250px;
    }

    .cover-stats {
        margin-top: 20px;
    }

    .cover-section {
        background: rgba(255,255,255,0.12);
        padding: 15px 25px;
        border-radius: 12px;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 15px;
    }

    .section-title {
        font-size: 11pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        opacity: 0.9;
    }

    .section-stats {
        font-size: 13pt;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .stat-item {
        color: white;
    }

    .stat-divider {
        opacity: 0.7;
        font-weight: 300;
    }

    .cover-footer {
        padding: 25px 50px;
        position: relative;
        z-index: 3;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        background: rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }

    .footer-left {
        text-align: left;
    }

    .department {
        font-size: 13pt;
        font-weight: 600;
        margin-bottom: 5px;
    }

    .company {
        font-size: 11pt;
        opacity: 0.9;
    }

    .footer-right {
        text-align: right;
    }

    .confidential {
        background: rgba(255,255,255,0.2);
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 9pt;
        font-weight: 600;
        letter-spacing: 0.5px;
        border: 1px solid rgba(255,255,255,0.3);
    }

    /* Enhanced Summary Page - Exact Match */
    .summary-page {
        padding: 25px 20px;
        background: #fafbfc;
        min-height: calc(100vh - 50px);
    }

    .page-header {
        margin-bottom: 25px;
        border-bottom: 3px solid #2ECC71;
        padding-bottom: 12px;
    }

    .page-header h2 {
        font-size: 22pt;
        font-weight: 600;
        color: #2c3e50;
        margin: 0;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 20px;
        margin-bottom: 25px;
    }

    .summary-section {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
    }

    .summary-section h3 {
        font-size: 15pt;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 15px;
        border-bottom: 2px solid #2ECC71;
        padding-bottom: 8px;
    }

    /* Metrics Grid - Exact Match */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 12px;
    }

    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 15px 12px;
        text-align: center;
        border: 2px solid #ecf0f1;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .metric-card.healthy {
        border-color: #27ae60;
        background: linear-gradient(135deg, #f8fff9 0%, #e8f8f0 100%);
    }

    .metric-card.warning {
        border-color: #f39c12;
        background: linear-gradient(135deg, #fffdf8 0%, #fff3e0 100%);
    }

    .metric-card.critical {
        border-color: #e74c3c;
        background: linear-gradient(135deg, #fffafa 0%, #ffe8e8 100%);
    }

    .metric-value {
        font-size: 20pt;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 6px;
        line-height: 1;
    }

    .metric-label {
        font-size: 8pt;
        font-weight: 600;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        line-height: 1.1;
        margin-bottom: 4px;
    }

    .metric-percentage {
        font-size: 11pt;
        font-weight: 500;
        color: #5d6d7e;
    }

    /* Performance Grid - Exact Match */
    .performance-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-top: 12px;
    }

    .perf-card {
        background: white;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        border: 2px solid #ecf0f1;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .perf-icon {
        font-size: 24pt;
        margin-bottom: 8px;
    }

    .perf-title {
        font-size: 10pt;
        font-weight: 600;
        color: #34495e;
        margin-bottom: 6px;
        line-height: 1.2;
    }

    .perf-value {
        font-size: 18pt;
        font-weight: 700;
        color: #3498db;
        margin-bottom: 6px;
    }

    .perf-detail {
        font-size: 8pt;
        color: #7f8c8d;
        line-height: 1.2;
    }

    /* Status Summary - Exact Match */
    .status-summary {
        background: linear-gradient(135deg, #e8f6f3 0%, #d5edda 100%);
        border: 2px solid #27ae60;
        border-radius: 8px;
        padding: 15px;
        margin-top: 20px;
        font-size: 11pt;
        font-weight: 500;
        color: #27ae60;
        text-align: center;
        box-shadow: 0 2px 6px rgba(39, 174, 96, 0.1);
    }

    /* VM Details Page - Exact Match */
    .details-page {
        padding: 15px;
        background: #fafbfc;
    }

    .details-header {
        margin-bottom: 20px;
        border-bottom: 3px solid #2ECC71;
        padding-bottom: 12px;
    }

    .details-header h2 {
        font-size: 18pt;
        font-weight: 600;
        color: #2c3e50;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* VM Table - Exact Match */
    .vm-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }

    .vm-table th {
        background: linear-gradient(135deg, #2ECC71 0%, #3498DB 100%);
        color: white;
        padding: 10px 6px;
        text-align: left;
        font-size: 8pt;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #27ae60;
    }

    .vm-table td {
        padding: 8px 6px;
        font-size: 7.5pt;
        border-bottom: 1px solid #ecf0f1;
        color: #2c3e50;
        vertical-align: middle;
    }

    .vm-table tr:nth-child(even) {
        background: #f8f9fa;
    }

    .vm-table tr:hover {
        background: #e3f2fd;
    }

    .status-online {
        color: #27ae60 !important;
        font-weight: 600;
    }

    .status-offline {
        color: #e74c3c !important;
        font-weight: 600;
    }

    .health-score {
        font-weight: 600;
        color: #27ae60 !important;
    }

    /* Key Recommendations - Exact Match */
    .recommendations-page {
        padding: 20px;
        background: #fafbfc;
    }

    .recommendations-box {
        background: linear-gradient(135deg, #f0f9ff 0%, #e8f4fd 100%);
        border: 2px solid #2ECC71;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }

    .recommendations-title {
        font-size: 16pt;
        font-weight: 600;
        color: #2ECC71;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .recommendations-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 25px;
    }

    .recommendation-section h4 {
        font-size: 12pt;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 10px;
    }

    .recommendation-section ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .recommendation-section li {
        font-size: 10pt;
        color: #34495e;
        margin-bottom: 6px;
        padding-left: 15px;
        position: relative;
    }

    .recommendation-section li::before {
        content: "•";
        color: #2ECC71;
        font-weight: bold;
        position: absolute;
        left: 0;
    }

    /* Footer Info */
    .report-footer {
        text-align: center;
        padding: 15px;
        font-size: 9pt;
        color: #7f8c8d;
        border-top: 1px solid #ecf0f1;
        margin-top: 20px;
    }

    /* Responsive Design for A4 */
    @media print {
        .page {
            margin: 0;
            padding: 0;
            box-shadow: none;
        }
        
        .metrics-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }
        
        .performance-grid {
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
    }

    /* Service Health Report Styles */
    .service-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid #e8ecf0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }

    .service-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }

    .service-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        border-bottom: 1px solid #e9ecef;
        padding-bottom: 6px;
        background: #f8f9fa;
        padding: 6px 10px;
        border-radius: 4px;
        border: 1px solid #dee2e6;
        flex-wrap: nowrap;
        overflow: hidden;
    }

    .service-header h3 {
        font-size: 10.5pt;
        color: #495057;
        margin: 0;
        font-weight: 600;
        flex: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-right: 8px;
    }

    .status-badge {
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 6pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1px;
        border: 1px solid transparent;
        display: inline-block;
        text-align: center;
        min-width: 18px;
        height: 14px;
        line-height: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        flex-shrink: 0;
        margin-left: 4px;
    }

    .status-ok {
        background: #28a745;
        color: white;
        border-color: #1e7e34;
        font-size: 5.5pt;
        font-weight: 700;
    }

    .status-warning {
        background: #f39c12;
        color: white;
    }

    .status-critical {
        background: #e74c3c;
        color: white;
    }

    .service-metrics {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-bottom: 10px;
        background: #f8f9fa;
        padding: 10px;
        border-radius: 6px;
    }

    .metric-item {
        text-align: center;
    }

    .metric-label {
        font-size: 7pt;
        color: #7f8c8d;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 10pt;
        color: #2c3e50;
        font-weight: 600;
        display: block;
    }

    .service-endpoints {
        margin-top: 8px;
    }
    }

    .endpoints-title {
        font-size: 8pt;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .endpoints-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 4px;
        align-items: start;
    }

    .endpoint-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 3px 5px;
        background: #f8f9fa;
        border-radius: 3px;
        border-left: 2px solid #27ae60;
        font-size: 7pt;
        min-height: 16px;
        margin-bottom: 2px;
        overflow: hidden;
    }

    .endpoint-item span:first-child {
        flex: 1;
        margin-right: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .endpoint-ok {
        background: #28a745;
        color: white;
        padding: 1px 3px;
        border-radius: 3px;
        font-size: 5pt;
        font-weight: 700;
        text-transform: uppercase;
        min-width: 16px;
        text-align: center;
        display: inline-block;
        height: 12px;
        line-height: 10px;
        flex-shrink: 0;
    }

    .demo-note {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 12px;
        margin-top: 20px;
        text-align: center;
    }

    .demo-note span {
        font-size: 9pt;
        color: #856404;
        font-weight: 600;
    }
    """
