#!/usr/bin/env python3
"""
Patent Miner Analytics Dashboard - Streamlit UI
Display patent discovery results with interactive analytics and insights
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Patent Miner Analytics",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


class PatentAnalyzer:
    """Load and analyze patent discovery data."""
    
    def __init__(self, vault_dir: str = "./patent_intelligence_vault/"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.patents: List[Dict[str, Any]] = []
        self.load_latest_discoveries()
    
    def load_latest_discoveries(self) -> bool:
        """Load the most recent patent discoveries file."""
        discovery_files = sorted(
            self.vault_dir.glob("patent_discoveries_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not discovery_files:
            st.warning("No patent discoveries found. Run the discovery first!")
            return False
        
        try:
            with open(discovery_files[0], 'r', encoding='utf-8') as f:
                self.patents = json.load(f)
            st.sidebar.success(f"✓ Loaded {len(self.patents)} patents")
            st.sidebar.caption(f"File: {discovery_files[0].name}")
            return True
        except Exception as e:
            st.error(f"Error loading discoveries: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate analytics statistics."""
        if not self.patents:
            return {}
        
        df = pd.DataFrame(self.patents)
        
        return {
            "total_patents": len(df),
            "date_range": f"{df['filing_date'].min()} to {df['filing_date'].max()}",
            "assignee_types": df['assignee_type'].value_counts().to_dict(),
            "patent_types": df['patent_type'].value_counts().to_dict() if 'patent_type' in df else {},
        }
    
    def get_patents_by_date(self) -> pd.DataFrame:
        """Get patent filing dates for timeline visualization."""
        df = pd.DataFrame(self.patents)
        df['filing_date'] = pd.to_datetime(df['filing_date'])
        df['year'] = df['filing_date'].dt.year
        return df.groupby('year').size().reset_index(name='count')
    
    def get_assignee_distribution(self) -> pd.DataFrame:
        """Get distribution of patents by assignee."""
        df = pd.DataFrame(self.patents)
        assignee_map = {'4': 'Unknown', '5': 'Other', '14': 'Individual', '15': 'Company'}
        df['assignee_label'] = df['assignee_type'].map(assignee_map).fillna('Other')
        return df['assignee_label'].value_counts().reset_index()
    
    def get_top_patents(self, n: int = 10) -> pd.DataFrame:
        """Get top patents (first n records)."""
        df = pd.DataFrame(self.patents[:n])
        return df[['patent_number', 'title', 'filing_date', 'patent_date', 'assignee_type']]
    
    def calculate_opportunity_score(self, patent: Dict[str, Any]) -> float:
        """Calculate opportunity score (1-10 scale)."""
        score = 0.0
        
        # Filing date recency factor (older = more expired)
        from datetime import datetime as dt
        filing_year = int(patent['filing_date'][:4])
        age = 2026 - filing_year
        recency_score = min(10, age / 5)  # Max 10 if 50+ years old
        score += recency_score * 0.3
        
        # Title complexity indicator
        title_length = len(patent['title'])
        complexity_score = min(10, title_length / 20)
        score += complexity_score * 0.2
        
        # Abstract length indicator (more detailed = higher potential)
        abstract_length = len(patent.get('abstract', ''))
        detail_score = min(10, abstract_length / 500)
        score += detail_score * 0.3
        
        # Patent type factor
        if patent.get('patent_type') == 'utility':
            score += 2  # Utility patents typically more valuable
        
        # Baseline
        score += 2
        
        return min(10, score)
    
    def get_enriched_patents(self) -> List[Dict[str, Any]]:
        """Add opportunity scores to patents."""
        enriched = []
        for patent in self.patents:
            patent_copy = patent.copy()
            patent_copy['opportunity_score'] = self.calculate_opportunity_score(patent)
            enriched.append(patent_copy)
        
        # Sort by opportunity score
        return sorted(enriched, key=lambda x: x['opportunity_score'], reverse=True)


@st.cache_resource
def get_analyzer() -> PatentAnalyzer:
    """Cache the analyzer to avoid reloading on every interaction."""
    return PatentAnalyzer()


def render_header():
    """Render dashboard header."""
    col1, col2, col3 = st.columns([2, 3, 1])
    
    with col1:
        st.title("🔬 Patent Miner Analytics")
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()


def render_overview_metrics(stats: Dict[str, Any]):
    """Render key overview metrics."""
    st.subheader("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patents", f"{stats['total_patents']:,}")
    
    with col2:
        st.metric("Filing Years", stats['date_range'])
    
    with col3:
        assignee_count = len(stats['assignee_types'])
        st.metric("Assignee Types", assignee_count)
    
    with col4:
        patent_type_count = len(stats['patent_types'])
        st.metric("Patent Types", patent_type_count)


def render_visualizations(analyzer: PatentAnalyzer):
    """Render data visualizations."""
    st.subheader("📈 Patent Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Timeline chart
        timeline_df = analyzer.get_patents_by_date()
        fig_timeline = px.bar(
            timeline_df,
            x='year',
            y='count',
            title='Patents by Filing Year',
            labels={'year': 'Year', 'count': 'Number of Patents'},
            color='count',
            color_continuous_scale='Blues'
        )
        fig_timeline.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col2:
        # Assignee distribution
        assignee_df = analyzer.get_assignee_distribution()
        fig_assignee = px.pie(
            assignee_df,
            values=assignee_df.iloc[:, 1],
            names=assignee_df['assignee_label'],
            title='Patents by Assignee Type',
            hole=0.3
        )
        fig_assignee.update_layout(height=350)
        st.plotly_chart(fig_assignee, use_container_width=True)


def render_top_opportunities(analyzer: PatentAnalyzer):
    """Render top patent opportunities."""
    st.subheader("🏆 Top Patent Opportunities")
    
    # Get enriched patents
    enriched = analyzer.get_enriched_patents()
    
    # Slider for number of patents to display
    num_display = st.slider("Display top N patents:", 5, min(50, len(enriched)), 10)
    
    # Create displayable dataframe
    display_data = []
    for patent in enriched[:num_display]:
        display_data.append({
            "Score": f"{patent['opportunity_score']:.1f}/10",
            "Patent #": patent['patent_number'],
            "Title": patent['title'][:60] + "..." if len(patent['title']) > 60 else patent['title'],
            "Filed": patent['filing_date'][:4],
            "Type": patent.get('patent_type', 'N/A'),
        })
    
    df_display = pd.DataFrame(display_data)
    st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_detailed_view(analyzer: PatentAnalyzer):
    """Render detailed patent information."""
    st.subheader("🔍 Patent Details")
    
    # Get enriched patents
    enriched = analyzer.get_enriched_patents()
    
    if not enriched:
        st.info("No patents loaded.")
        return
    
    # Patent selector
    patent_options = {
        f"{p['patent_number']} - {p['title'][:50]}...": idx
        for idx, p in enumerate(enriched[:20])
    }
    
    selected_label = st.selectbox(
        "Select a patent to view details:",
        list(patent_options.keys())
    )
    
    if selected_label:
        patent_idx = patent_options[selected_label]
        patent = enriched[patent_idx]
        
        # Display detailed information
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("Opportunity Score", f"{patent['opportunity_score']:.1f}/10")
            st.metric("Patent Number", patent['patent_number'])
            st.metric("Filing Year", patent['filing_date'][:4])
            st.metric("Issue Year", patent.get('patent_date', 'N/A')[:4])
            st.metric("Type", patent.get('patent_type', 'N/A'))
        
        with col2:
            st.write("**Title**")
            st.write(patent['title'])
            
            st.write("**Abstract**")
            st.write(patent.get('abstract', 'No abstract available')[:500] + "...")
            
            st.write("**Link**")
            link = patent.get('link', '')
            if link:
                st.markdown(f"[View on Google Patents]({link})")


def render_filters():
    """Render filter sidebar options."""
    st.sidebar.header("⚙️ Filters & Options")
    
    view_type = st.sidebar.radio(
        "Select View:",
        ["Overview", "Opportunities", "Details", "Data Export"]
    )
    
    return view_type


def render_data_export(analyzer: PatentAnalyzer):
    """Render data export options."""
    st.subheader("📥 Data Export")
    
    enriched = analyzer.get_enriched_patents()
    
    if not enriched:
        st.info("No data to export.")
        return
    
    # Export to CSV
    csv_data = pd.DataFrame(enriched)
    csv_buffer = csv_data.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Download as CSV",
        data=csv_buffer,
        file_name=f"patents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # Export to JSON
    json_data = json.dumps(enriched, indent=2, default=str)
    st.download_button(
        label="Download as JSON",
        data=json_data,
        file_name=f"patents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
    
    # Show preview
    st.write(f"**Total records:** {len(enriched)}")
    st.dataframe(
        pd.DataFrame(enriched)[['patent_number', 'title', 'filing_date', 'opportunity_score']],
        use_container_width=True
    )


def main():
    """Main app logic."""
    render_header()
    
    # Load analyzer
    analyzer = get_analyzer()
    
    if not analyzer.patents:
        st.error("No patent data available. Please run the discovery pipeline first.")
        st.stop()
    
    # Get statistics
    stats = analyzer.get_statistics()
    
    # Render sidebar filters
    view = render_filters()
    
    # Render selected view
    if view == "Overview":
        render_overview_metrics(stats)
        st.divider()
        render_visualizations(analyzer)
    
    elif view == "Opportunities":
        render_top_opportunities(analyzer)
    
    elif view == "Details":
        render_detailed_view(analyzer)
    
    elif view == "Data Export":
        render_data_export(analyzer)
    
    # Footer with info
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("Patent Miner v2.0 - Enterprise Discovery System")
    with col2:
        st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    with col3:
        st.caption("🔗 [PatentsView API](https://www.patentsview.org/)")


if __name__ == "__main__":
    main()
