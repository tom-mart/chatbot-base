#!/bin/bash

# Deployment script for Chatbot (lifepal.app)

set -e

echo "🚀 Starting Chatbot deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with required variables"
    exit 1
fi

# Stop old lifepal stack if running
echo "📦 Stopping old lifepal stack..."
cd ../lifepal
sudo docker-compose down || true
cd ../lifepal.app

# Build and start new chatbot stack
echo "🔨 Building chatbot images..."
sudo docker-compose build --no-cache

echo "🚀 Starting chatbot services..."
sudo docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo "📊 Service status:"
sudo docker-compose ps

echo "✅ Deployment complete!"
echo ""
echo "Access your application at:"
echo "  - HTTP:  http://localhost:8082"
echo "  - HTTPS: https://localhost:8443"
echo ""
echo "Useful commands:"
echo "  - View logs: sudo docker-compose logs -f"
echo "  - Stop: sudo docker-compose down"
echo "  - Restart: sudo docker-compose restart"
