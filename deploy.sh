#!/bin/bash

# ANTAM Bot Deployment Script for Ubuntu/Debian
echo "🤖 ANTAM Bot Dashboard Deployment Script"
echo "========================================"

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python and required packages
echo "🐍 Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv wget curl unzip

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

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/antam-bot
cd /opt/antam-bot

# You'll need to upload your files here
echo "📤 Please upload your application files to /opt/antam-bot/"
echo "Files needed:"
echo "  - bot_dashboard.py"
echo "  - antam_bot.py"
echo "  - requirements.txt"
echo "  - start.sh"
echo "  - antam-bot.service"
echo "  - templates/ directory"
echo ""
echo "Then run: bash /opt/antam-bot/setup_app.sh"