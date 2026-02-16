#!/bin/bash
# Launch the Patent Miner Streamlit Dashboard
# Usage: ./run_dashboard.sh

echo "🔬 Patent Miner Analytics Dashboard"
echo "=================================="
echo ""
echo "Checking requirements..."

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✓ Starting dashboard..."
echo "📊 Opening at http://localhost:8501/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py
