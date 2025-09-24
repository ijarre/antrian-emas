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

# Update nginx configuration if it exists
if [ -f "nginx/antam-bot.conf" ]; then
  echo "🌐 Updating Nginx configuration..."
   cp nginx/antam-bot.conf /etc/nginx/sites-available/
   nginx -t &&  systemctl reload nginx
fi

# Make scripts executable
chmod +x *.sh scripts/*.sh

# Start the service
echo "🚀 Starting service..."
systemctl start antam-bot

# Check status
echo "📊 Service status:"
systemctl status antam-bot --no-pager

# Wait for service to start
sleep 3

# Test endpoint
echo "🧪 Testing endpoint..."
if curl -f -s http://localhost >/dev/null; then
    echo "✅ HTTP endpoint is responding"
else
    echo "⚠️ HTTP endpoint test failed, check logs"
fi

echo ""
echo "✅ Update complete!"
echo "🔗 Access: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')"