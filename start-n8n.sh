#!/bin/bash

# Start n8n locally with Docker

set -e

echo "🚀 Starting n8n locally..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Copy .env.example to .env and fill in your API keys:"
    echo "   cp .env.example .env"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "🐳 Please start Docker Desktop and try again."
    exit 1
fi

# Start n8n
echo "🐳 Starting n8n container..."
docker-compose up -d

echo ""
echo "✅ n8n is running!"
echo ""
echo "🌐 Access n8n at: http://localhost:5678"
echo "👤 Username: admin"
echo "🔑 Password: (check your .env file)"
echo ""
echo "📊 View logs: docker-compose logs -f n8n"
echo "🛑 Stop n8n: docker-compose down"
echo ""
