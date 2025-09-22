#!/bin/bash

# ANTAM Bot Deployment Script for Ubuntu/Debian
echo "🤖 ANTAM Bot Dashboard Deployment Script"
echo "========================================"

# Check if GitHub repo URL is provided
if [ -z "$1" ]; then
    echo "❌ Please provide your GitHub repository URL"
    echo "Usage: ./deploy.sh https://github.com/yourusername/your-repo.git"
    exit 1
fi

REPO_URL="$1"

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Git, Python and required packages
echo "🐍 Installing Git, Python and dependencies..."
apt install -y git python3 python3-pip python3-venv wget curl unzip

# Install Chrome and ChromeDriver
echo "🌐 Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Install ChromeDriver
echo "🚗 Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | awk -F. '{print $1}')
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -N "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin/
rm chromedriver_linux64.zip

# Install Xvfb for headless Chrome
echo "🖥️ Installing Xvfb for headless display..."
apt install -y xvfb

# Set timezone to WIB (Western Indonesia Time)
echo "🕐 Setting timezone to WIB (Asia/Jakarta)..."
timedatectl set-timezone Asia/Jakarta

# Clone repository
echo "📥 Cloning repository from GitHub..."
if [ -d "/opt/antam-bot" ]; then
    rm -rf /opt/antam-bot
fi
git clone "$REPO_URL" /opt/antam-bot
cd /opt/antam-bot

# Run setup script
echo "🚀 Running application setup..."
chmod +x setup_app.sh
./setup_app.sh

echo ""
echo "✅ Deployment complete!"
echo "🔗 Access your dashboard at: http://$(curl -s ifconfig.me):5005"