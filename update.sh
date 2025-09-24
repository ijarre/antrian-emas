#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"; NC="\033[0m"

log() { echo -e "$GREEN$1$NC"; }
warn() { echo -e "$YELLOW$1$NC" >&2; }
err() { echo -e "$RED$1$NC" >&2; }

require_sudo() {
  if ! sudo -n true 2>/dev/null; then
    warn "⚠️  Sudo password prompt would block non‑interactive run. Configure passwordless sudo for required commands.";
  fi
}

trap 'err "❌ Update failed (line $LINENO). Check logs."' ERR

# ANTAM Bot Update Script
echo "🔄 Updating ANTAM Bot from GitHub..."
require_sudo

cd /opt/antam-bot

# Stop the service
echo "⏹️ Stopping service..."
if ! sudo systemctl stop antam-bot 2>/dev/null; then
  warn "Service stop failed or not running; continuing"
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Update dependencies
echo "📦 Updating dependencies..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt --no-deps >/dev/null || pip install -r requirements.txt

# Update nginx configuration if it exists
if [ -f "nginx/antam-bot.conf" ]; then
  echo "🌐 Updating Nginx configuration..."
  require_sudo
  TMP_BACKUP="/etc/nginx/sites-available/antam-bot.conf.bak.$(date +%s)"
  if [ -f /etc/nginx/sites-available/antam-bot.conf ]; then
    sudo cp /etc/nginx/sites-available/antam-bot.conf "$TMP_BACKUP"
  fi
  sudo cp nginx/antam-bot.conf /etc/nginx/sites-available/antam-bot.conf
  # Ensure enabled symlink exists
  if [ ! -e /etc/nginx/sites-enabled/antam-bot.conf ]; then
    sudo ln -s /etc/nginx/sites-available/antam-bot.conf /etc/nginx/sites-enabled/antam-bot.conf
  fi
  if sudo nginx -t; then
    sudo systemctl reload nginx
    log "✅ Nginx reloaded"
  else
    err "Nginx config test failed; restoring previous version"
    if [ -f "$TMP_BACKUP" ]; then
      sudo cp "$TMP_BACKUP" /etc/nginx/sites-available/antam-bot.conf
      sudo nginx -t && sudo systemctl reload nginx || err "Restore also failed; manual intervention required"
    fi
  fi
fi

# Make scripts executable (exclude currently running script)
find . -name "*.sh" -not -name "update.sh" -exec chmod +x {} \;
chmod +x scripts/*.sh 2>/dev/null || true

# Start the service
echo "🚀 Starting service..."
sudo systemctl start antam-bot || err "Service failed to start"

# Check status
echo "📊 Service status:"
sudo systemctl status antam-bot --no-pager | sed -e 's/\x1b\[[0-9;]*m//g' | head -n 15

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