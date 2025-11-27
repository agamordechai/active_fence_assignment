#!/bin/bash
# Complete reset and restart script

echo "🧹 Cleaning up old containers..."
docker-compose down -v 2>/dev/null
docker rm -f reddit-api reddit-scraper 2>/dev/null

echo ""
echo "🔨 Rebuilding containers..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "📊 Checking statistics..."
curl -s http://localhost:8000/statistics | python3 -m json.tool 2>/dev/null || echo "API not ready yet"

echo ""
echo "✅ Done! Services are running."
echo ""
echo "📝 To see auto-import in action:"
echo "   docker-compose logs -f reddit-scraper"
echo "   (Look for: [AUTO-IMPORT] and ✅ DATABASE IMPORT COMPLETED!)"
echo ""
echo "🌐 Access:"
echo "   - http://localhost:8000/docs"
echo "   - http://localhost:8000/statistics"
echo ""
echo "📋 View logs:"
echo "   - API: docker-compose logs -f api"
echo "   - Scraper: docker-compose logs -f reddit-scraper"

