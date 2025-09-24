# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the ANTAM Bot Dashboard - a Flask web application that schedules and monitors automated bots for ANTAM queue registration. The application uses Selenium WebDriver to automate form filling on ANTAM websites.

### Core Architecture

**Main Application (`bot_dashboard.py`)**:
- Flask web server with SQLite database backend
- `BotController` class manages bot scheduling, execution, and monitoring
- Background scheduler checks for scheduled tasks every 30 seconds
- Uses WIB timezone (Asia/Jakarta)
- Serves on port 5005

**Bot Logic (`antam_bot.py`)**:
- `ANTAMQueueBot` class handles Selenium automation
- Chrome WebDriver with headless option for server deployment
- Randomized user agents and delays to avoid detection
- Screenshot capture for debugging

**Database Schema**:
- `sites` table: ANTAM websites configuration
- `schedules` table: Bot scheduling with timezone support
- `bot_runs` table: Execution history and status tracking
- `user_settings` table: User configuration storage

**File Structure**:
```
├── bot_dashboard.py      # Main Flask application
├── antam_bot.py         # Selenium bot automation
├── templates/           # HTML templates (dashboard, settings, etc.)
├── nginx/              # Nginx reverse proxy configuration
│   └── antam-bot.conf  # Nginx site configuration
├── scripts/            # CI/CD and deployment scripts
│   └── setup_vps_user.sh    # GitHub Actions user setup
├── .github/workflows/  # GitHub Actions CI/CD pipeline
│   └── deploy.yml      # Automated deployment workflow
├── logs/               # Application logs
├── screenshots/        # Debug screenshots from bot runs
├── bot_control.db      # SQLite database
└── deployment scripts (deploy.sh, setup_app.sh, start.sh)
```

## Development Commands

**Local Development**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python bot_dashboard.py

# Access dashboard
http://localhost:5005
```

**Production Deployment**:
```bash
# Full deployment (Ubuntu/Debian)
./deploy.sh https://github.com/yourusername/your-repo.git

# Manual setup after code upload
./setup_app.sh

# Start/stop services
systemctl start antam-bot
systemctl stop antam-bot
systemctl restart antam-bot
systemctl status nginx

# View logs
journalctl -u antam-bot -f
tail -f /var/log/nginx/antam-bot.*.log
```

**Database Management**:
The SQLite database is automatically initialized on first run. Manual database operations can be done through the Flask application or direct SQLite commands.

## Key Components

**Authentication**: Basic HTTP auth for screenshot access 

**Scheduling**: Cron-like scheduling with timezone support, one-time execution flags

**Bot Management**: Track running bots, cancel mid-execution, status monitoring

**Screenshot Debug**: Captures screenshots during bot execution for troubleshooting

**Nginx Reverse Proxy**: Production deployment includes nginx configuration with:
- SSL/HTTPS support (configurable)
- Rate limiting and security headers
- Static file serving optimization
- Access via port 80/443 instead of direct port 5005

**Dependencies**:
- Flask 2.3.3
- Selenium 4.15.0
- Gunicorn for production
- Nginx for reverse proxy
- Chrome/ChromeDriver for automation
- Xvfb for headless display on servers

## Security Notes

- Change Flask secret key in production
- Screenshots may contain sensitive form data
- Consider changing default admin credentials (admin/admin)
- Database file permissions should be restricted in production
- Nginx provides additional security layer with rate limiting and headers
- For HTTPS, uncomment SSL configuration in `nginx/antam-bot.conf` and add certificates

## Access Points

**Production (with Nginx)**:
- Main dashboard: `http://YOUR_SERVER_IP` (port 80)
- Screenshots: `http://YOUR_SERVER_IP/debug/screenshots`
- Direct Flask access: `http://YOUR_SERVER_IP:5005` (for debugging)

**Local Development**:
- Dashboard: `http://localhost:5005`

## CI/CD Pipeline

**Automated Deployment**: GitHub Actions workflow triggers on every push to `main` branch
- Tests code syntax before deployment
- Deploys to VPS with automatic rollback on failure
- Health checks validate successful deployment

**Setup CI/CD** (for already deployed VPS):
```bash
# Setup GitHub Actions user on existing VPS
sudo ./scripts/setup_vps_user.sh YOUR_GITHUB_USERNAME

# Add GitHub secrets: VPS_HOST, VPS_USER, VPS_SSH_KEY
# Future deployments: git push origin main
```

**Monitoring**:
- GitHub Actions logs in repository Actions tab
- VPS logs: `journalctl -u antam-bot -f`
- Manual trigger: GitHub Actions → "Deploy ANTAM Bot to VPS" → "Run workflow"

See `CI-CD-SETUP.md` for detailed setup instructions.