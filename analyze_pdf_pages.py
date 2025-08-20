#!/usr/bin/env python3
"""
Analyze PDF page structure to verify empty pages are removed
"""

import PyPDF2
import os
from pathlib import Path

def analyze_pdf_structure(pdf_path):
    """Analyze PDF page structure"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"📄 Analyzing: {Path(pdf_path).name}")
            print(f"   Total Pages: {len(pdf_reader.pages)}")
            print(f"   File Size: {os.path.getsize(pdf_path):,} bytes ({os.path.getsize(pdf_path)/1024:.0f} KB)")
            
            # Analyze each page content length as indicator
            for i, page in enumerate(pdf_reader.pages, 1):
                try:
                    text = page.extract_text()
                    content_length = len(text.strip()) if text else 0
                    
                    # Estimate page content
                    if content_length < 50:
                        status = "❌ LIKELY EMPTY"
                    elif content_length < 200:
                        status = "⚠️  MINIMAL CONTENT"
                    else:
                        status = "✅ GOOD CONTENT"
                    
                    print(f"   Page {i}: {content_length:4d} chars - {status}")
                    
                    # Show sample content for debugging
                    if i <= 3 and text:
                        sample = text.replace('\n', ' ').strip()[:100]
                        print(f"           Sample: {sample}...")
                        
                except Exception as e:
                    print(f"   Page {i}: Error reading - {e}")
            
            print()
            return len(pdf_reader.pages)
            
    except Exception as e:
        print(f"❌ Error analyzing {pdf_path}: {e}")
        return 0

def main():
    """Compare PDF structures"""
    print("🔍 PDF Page Structure Analysis")
    print("=" * 50)
    
    output_dir = Path("output")
    
    # Check latest reports
    latest_files = [
        "test_no_empty_pages.pdf",
        "vm_infrastructure_report_2025-07-16.pdf"
    ]
    
    total_pages = {}
    
    for filename in latest_files:
        filepath = output_dir / filename
        if filepath.exists():
            pages = analyze_pdf_structure(filepath)
            total_pages[filename] = pages
        else:
            print(f"⚠️  File not found: {filename}")
    
    # Summary
    print("📊 SUMMARY:")
    print("-" * 30)
    for filename, pages in total_pages.items():
        print(f"   {filename}: {pages} pages")
    
    # Expected structure
    print("\n🎯 EXPECTED STRUCTURE (4 pages):")
    print("   Page 1: Cover Page")
    print("   Page 2: Executive Summary + Service Health")
    print("   Page 3: VM Inventory Table")
    print("   Page 4: Recommendations")
    print("\n❌ PREVIOUS ISSUES (had 10 pages):")
    print("   - Empty pages after Summary")
    print("   - Empty pages before VM Inventory")
    print("   - Unnecessary page breaks")

if __name__ == "__main__":
    main()
