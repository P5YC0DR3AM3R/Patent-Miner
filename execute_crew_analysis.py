#!/usr/bin/env python3
"""
Standalone Crew.AI Analysis Runner for Patent Intelligence
Executes comprehensive analysis with LLM-enhanced insights
"""

if __name__ == "__main__":
    import sys
    import os
    os.chdir("/Volumes/Elements/Patent Miner")
    sys.path.insert(0, "/Volumes/Elements/Patent Miner")
    
    # Import and run
    from run_expired_patent_analysis import run_comprehensive_analysis
    
    print("\n" + "="*80)
    print("COMPREHENSIVE PATENT ANALYSIS WITH CREW.AI")
    print("="*80 + "\n")
    
    try:
        result = run_comprehensive_analysis(enable_crew=True)
        print(f"\n✅ Analysis Complete!")
        print(f"   Status: {result.get('status')}")
        print(f"   Markdown Report: {result.get('markdown_report')}")
        print(f"   JSON Export: {result.get('json_export')}")
        print(f"   CSV Export: {result.get('csv_export')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
