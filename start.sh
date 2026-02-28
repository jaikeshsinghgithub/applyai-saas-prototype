#!/bin/bash
# ApplyAI — Start Script (Mac/Linux)
# ====================================

echo ""
echo "🤖 ApplyAI SaaS — Starting..."
echo "======================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install from https://python.org"
    exit 1
fi

# Install backend dependencies
echo "📦 Installing backend packages..."
cd backend
pip3 install -r requirements.txt -q

# Start backend in background
echo "🚀 Starting backend API on http://localhost:8000 ..."
python3 main.py &
BACKEND_PID=$!

cd ..

# Wait a moment for backend to start
sleep 2

# Open frontend
echo "🌐 Opening frontend..."
if command -v xdg-open &> /dev/null; then
    xdg-open frontend/index.html
elif command -v open &> /dev/null; then
    open frontend/index.html
else
    echo "Please open: frontend/index.html in your browser"
fi

echo ""
echo "======================================"
echo "✅ ApplyAI is running!"
echo "📊 Dashboard:  Open frontend/index.html"
echo "⚡ API Docs:   http://localhost:8000/docs"
echo "🔌 Extension:  Load extension/ folder in Chrome"
echo "======================================"
echo ""
echo "Press Ctrl+C to stop..."
wait $BACKEND_PID
