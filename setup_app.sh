#!/bin/bash

# Application Setup Script (run after uploading files)
echo "🚀 Setting up ANTAM Bot application..."

cd /opt/antam-bot

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
echo "🔧 Setting up permissions..."
chmod +x start.sh
chmod +x /opt/antam-bot/setup_app.sh

# Create directories
mkdir -p logs screenshots

# Setup systemd service
echo "⚙️ Setting up systemd service..."
cp antam-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable antam-bot

# Start Xvfb (virtual display for Chrome)
echo "🖥️ Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
echo $! > /tmp/xvfb.pid

# Start the service
echo "🚀 Starting ANTAM Bot service..."
systemctl start antam-bot

# Check status
echo "📊 Service status:"
systemctl status antam-bot --no-pager

# Show useful information
echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Access your dashboard at: http://YOUR_DROPLET_IP:5005"
echo "🔐 Screenshots access: http://YOUR_DROPLET_IP:5005/debug/screenshots (admin/admin)"
echo ""
echo "📝 Useful commands:"
echo "  - Check service status: systemctl status antam-bot"
echo "  - View logs: journalctl -u antam-bot -f"
echo "  - Restart service: systemctl restart antam-bot"
echo "  - Stop service: systemctl stop antam-bot"
echo ""
echo "📂 Application files are in: /opt/antam-bot"
echo "📋 Logs are in: /opt/antam-bot/logs/"