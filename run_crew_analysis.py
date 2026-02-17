#!/usr/bin/env python3
"""Quick script to run crew.ai analysis."""

import sys
import subprocess

try:
    from run_expired_patent_analysis import run_comprehensive_analysis
    
    print("=" * 80)
    print("RUNNING COMPREHENSIVE ANALYSIS WITH CREW.AI")
    print("=" * 80)
    
    result = run_comprehensive_analysis(enable_crew=True)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"Status: {result['status']}")
    print(f"Markdown Report: {result.get('markdown_report', 'N/A')}")
    print(f"JSON Export: {result.get('json_export', 'N/A')}")
    print(f"CSV Export: {result.get('csv_export', 'N/A')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
