#!/bin/bash

# ANTAM Bot Dashboard Startup Script
echo "Starting ANTAM Bot Dashboard..."

# Change to app directory
cd /opt/antam-bot

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_ENV=production
export PYTHONPATH=/opt/antam-bot

# Create necessary directories
mkdir -p logs screenshots

# Start the application with gunicorn
exec gunicorn --bind 0.0.0.0:5005 --workers 1 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 50 --preload --access-logfile logs/access.log --error-logfile logs/error.log bot_dashboard:app