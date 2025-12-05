#!/bin/bash
# Start Company Validation API Server

echo "=================================="
echo "Company Validation API Server"
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Create .env file with required API keys"
    echo ""
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start server
echo "🚀 Starting server on http://localhost:8003"
echo "📚 API Docs: http://localhost:8003/docs"
echo "💚 Health Check: http://localhost:8003/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python api_server.py
