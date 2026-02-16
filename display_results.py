#!/usr/bin/env python3
"""
Load and display comprehensive patent analysis results
"""

import json
from pathlib import Path
from datetime import datetime

# Configuration
output_dir = Path('./patent_intelligence_vault/')
checkpoint_file = output_dir / 'checkpoint_analysis_20260212_182702_final.json'

# Load checkpoint data
print("="*100)
print("📊 PATENT MINER ANALYSIS RESULTS - 2026")
print("="*100)

if checkpoint_file.exists():
    with open(checkpoint_file, 'r', encoding='utf-8') as f:
        analyzed_patents = json.load(f)
    
    print(f"\n✓ Loaded {len(analyzed_patents)} analyzed patents\n")
    
    # Sort by opportunity score
    sorted_patents = sorted(analyzed_patents, key=lambda x: x.get('opportunity_score', 0), reverse=True)
    
    # Display results
    print("\n" + "="*100)
    print("🏆 TOP PATENT OPPORTUNITIES (Ranked by Opportunity Score)")
    print("="*100 + "\n")
    
    for i, patent in enumerate(sorted_patents, 1):
        print(f"#{i} | SCORE: {patent.get('opportunity_score', 0)}/20")
        print(f"   Patent Number: {patent.get('patent_number', 'Unknown')}")
        print(f"   Title: {patent.get('title', 'Unknown')}")
        print(f"   Category: {patent.get('category', 'Unknown')}")
        print(f"   ---")
        print(f"   Viability: {patent.get('viability', 0)}/10 | Complexity: {patent.get('complexity', 0)}/10")
        print(f"   Market: {patent.get('market_summary', 'N/A')}")
        print(f"   Target Customers: {patent.get('target_customers', 'N/A')}")
        print(f"   Key Features: {', '.join(patent.get('key_features', []))}")
        print(f"   🔗 {patent.get('link', 'No link')}")
        print()
    
    # Summary statistics
    print("\n" + "="*100)
    print("📈 SUMMARY STATISTICS")
    print("="*100)
    
    categories = {}
    total_viability = 0
    total_complexity = 0
    total_score = 0
    
    for patent in analyzed_patents:
        cat = patent.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
        total_viability += patent.get('viability', 0)
        total_complexity += patent.get('complexity', 0)
        total_score += patent.get('opportunity_score', 0)
    
    print(f"Total Patents Analyzed: {len(analyzed_patents)}")
    print(f"Average Viability Score: {total_viability/len(analyzed_patents):.1f}/10")
    print(f"Average Complexity Score: {total_complexity/len(analyzed_patents):.1f}/10")
    print(f"Average Opportunity Score: {total_score/len(analyzed_patents):.1f}/20")
    print(f"\nCategories Found:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {cat}: {count} patent(s)")
    
    # Recommendations
    print("\n" + "="*100)
    print("💡 RECOMMENDATIONS FOR COMMERCIALIZATION")
    print("="*100)
    
    top_3 = sorted_patents[:3]
    for i, patent in enumerate(top_3, 1):
        print(f"\n{i}. {patent.get('title', 'Unknown')}")
        print(f"   Why: Score {patent.get('opportunity_score', 0)}/20 - {patent.get('category', 'Unknown')} opportunity")
        print(f"   Next Steps:")
        print(f"     → Verify patent status on USPTO PAIR")
        print(f"     → Conduct Freedom-to-Operate (FTO) search")
        print(f"     → Research competitor products in market")
        print(f"     → Get manufacturing quotes from 3+ suppliers")
        print(f"     → Survey 50-100 potential customers")
    
    # Export summary
    summary = {
        "analysis_date": datetime.now().isoformat(),
        "total_patents": len(analyzed_patents),
        "avg_viability": total_viability/len(analyzed_patents),
        "avg_complexity": total_complexity/len(analyzed_patents),
        "avg_opportunity_score": total_score/len(analyzed_patents),
        "categories": categories,
        "top_3_opportunities": [
            {
                "rank": i+1,
                "patent_number": p.get('patent_number'),
                "title": p.get('title'),
                "score": p.get('opportunity_score'),
                "category": p.get('category')
            }
            for i, p in enumerate(top_3)
        ]
    }
    
    summary_file = output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Summary saved to: {summary_file.name}")
    print("\n" + "="*100)
    print("✅ PIPELINE COMPLETE - Ready for commercialization analysis!")
    print("="*100)

else:
    print(f"❌ Checkpoint file not found: {checkpoint_file}")
    print(f"Files in directory: {list(output_dir.glob('*.json'))}")
