#!/bin/bash

# ANTAM Bot Update Script
echo "🔄 Updating ANTAM Bot from GitHub..."

cd /opt/antam-bot

# Stop the service
echo "⏹️ Stopping service..."
sudo systemctl stop antam-bot

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
  sudo cp nginx/antam-bot.conf /etc/nginx/sites-available/
  sudo nginx -t && sudo systemctl reload nginx
fi

# Make scripts executable (exclude currently running script)
find . -name "*.sh" -not -name "update.sh" -exec chmod +x {} \;
chmod +x scripts/*.sh 2>/dev/null || true

# Start the service
echo "🚀 Starting service..."
sudo systemctl start antam-bot

# Check status
echo "📊 Service status:"
sudo systemctl status antam-bot --no-pager

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