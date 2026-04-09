#!/bin/bash
# Start LLM Debate Web UI in Docker (Production Mode)

set -e

echo "🐳 Starting LLM Debate Web UI in Docker..."
echo ""

# Get the server's IP address
IP=$(hostname -I | awk '{print $1}')

echo "📍 Server Information:"
echo "   Local:   http://localhost:8000"
echo "   Network: http://${IP}:8000"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker first"
    exit 1
fi

# Use production docker-compose if it exists, otherwise use regular
if [ -f "docker-compose.prod.yml" ]; then
    echo "🚀 Using production configuration..."
    docker-compose -f docker-compose.prod.yml up --build -d
else
    echo "🚀 Using development configuration..."
    docker-compose up --build -d
fi

echo ""
echo "✅ Container started!"
echo ""
echo "📱 Access from other devices on your network:"
echo "   http://${IP}:8000"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f llm-debate-web"
echo ""
echo "⏹  Stop container:"
echo "   docker-compose down"
echo ""
