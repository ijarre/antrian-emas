#!/bin/bash

# ANTAM Bot Update Script
echo "🔄 Updating ANTAM Bot from GitHub..."

cd /opt/antam-bot

# Stop the service
echo "⏹️ Stopping service..."
systemctl stop antam-bot

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Update dependencies
echo "📦 Updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
chmod +x *.sh

# Start the service
echo "🚀 Starting service..."
systemctl start antam-bot

# Check status
echo "📊 Service status:"
systemctl status antam-bot --no-pager

echo ""
echo "✅ Update complete!"
echo "🔗 Access: http://$(curl -s ifconfig.me):5005"