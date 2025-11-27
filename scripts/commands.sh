#!/bin/bash
# Quick command reference for common tasks

echo "📋 Reddit Hate Speech Detection - Quick Commands"
echo "=================================================="
echo ""

echo "🔍 VIEW LOGS (containers already running):"
echo "  docker-compose logs -f api              # Follow API logs"
echo "  docker-compose logs -f reddit-scraper   # Follow scraper logs"
echo "  docker-compose logs -f                  # Follow all logs"
echo "  docker-compose logs --tail=100 api      # Last 100 lines"
echo ""
echo "  💡 TIP: Auto-import messages always show (using print, not logger)"
echo "         Look for: [AUTO-IMPORT] and ✅ DATABASE IMPORT COMPLETED!"
echo ""

echo "🎚️  CHANGE LOG LEVEL:"
echo "  1. Edit .env and change LOG_LEVEL:"
echo "     WARNING = minimal (default)"
echo "     INFO    = show pipeline steps"
echo "     DEBUG   = very verbose"
echo "  2. docker-compose restart"
echo ""

echo "🎯 CHANGE SUBREDDITS:"
echo "  1. Edit .env and change TARGET_SUBREDDITS:"
echo "     TARGET_SUBREDDITS=news,worldnews,politics,AskReddit"
echo "  2. docker-compose restart reddit-scraper"
echo ""

echo "📊 CHECK STATUS:"
echo "  curl http://localhost:8000/statistics   # Check database stats"
echo "  curl http://localhost:8000/health       # Check API health"
echo "  docker-compose ps                       # Check containers"
echo ""

echo "🔄 CONTROL:"
echo "  docker-compose up -d                    # Start (background)"
echo "  docker-compose up                       # Start (foreground, see logs)"
echo "  docker-compose stop                     # Stop"
echo "  docker-compose restart                  # Restart"
echo "  docker-compose down                     # Stop and remove"
echo ""

echo "🛠️  TROUBLESHOOT:"
echo "  ./restart.sh                            # Complete reset"
echo "  python3 manual_import.py                # Manual data import"
echo "  docker-compose logs api | grep error    # Find errors"
echo ""

echo "📚 DOCS:"
echo "  http://localhost:8000/docs              # API documentation"
echo "  README.md                               # Project documentation"

