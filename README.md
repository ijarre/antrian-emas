# ANTAM Bot Dashboard

A Flask web application to schedule and monitor ANTAM queue registration bots.

## Features

- 🤖 **Automated Bot Scheduling**: Schedule bots to run at specific times
- 📊 **Dashboard Monitoring**: Real-time view of bot runs and status
- ⏹️ **Cancel Running Bots**: Stop bots mid-execution if needed
- 📸 **Screenshot Viewer**: Debug bot behavior with captured screenshots
- 🔄 **One-time Runs**: Bots auto-disable after completion
- 🛡️ **Simple Security**: Basic auth for sensitive areas

## Quick Deploy on DigitalOcean

1. **Create a DigitalOcean droplet** (Ubuntu 20.04+)

2. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/your-repo.git
   git push -u origin main
   ```

3. **Deploy with one command**:
   ```bash
   ssh root@YOUR_DROPLET_IP
   curl -O https://raw.githubusercontent.com/yourusername/your-repo/main/deploy.sh
   chmod +x deploy.sh
   ./deploy.sh https://github.com/yourusername/your-repo.git
   ```

4. **Access your app**:
   - Dashboard: `http://YOUR_DROPLET_IP:5005`
   - Screenshots: `http://YOUR_DROPLET_IP:5005/debug/screenshots` (admin/admin)

## Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   python bot_dashboard.py
   ```

3. **Access locally**: `http://localhost:5005`

## File Structure

```
├── bot_dashboard.py      # Main Flask application
├── antam_bot.py         # Bot logic for form filling
├── requirements.txt     # Python dependencies
├── templates/           # HTML templates
│   ├── dashboard.html
│   ├── add_task.html
│   ├── schedules.html
│   ├── settings.html
│   └── screenshots.html
├── deploy.sh           # Deployment script
├── setup_app.sh        # App setup script
├── start.sh            # Production startup script
└── antam-bot.service   # Systemd service file
```

## Management Commands

Once deployed, use these commands on your server:

```bash
# Check service status
systemctl status antam-bot

# View logs
journalctl -u antam-bot -f

# Restart service
systemctl restart antam-bot

# Stop service
systemctl stop antam-bot

# Update from GitHub
cd /opt/antam-bot
git pull
systemctl restart antam-bot
```

## Configuration

- **User settings**: Configure in the Settings page
- **Screenshots**: Protected by basic auth (admin/admin)
- **Database**: SQLite stored in `bot_control.db`
- **Logs**: Stored in `logs/` directory

## Security Notes

- Change the Flask secret key in production
- Screenshots contain form data - handle with care
- Consider changing default admin credentials
- Run behind a reverse proxy (nginx) for production use

## Troubleshooting

- **Bot not running**: Check Chrome/ChromeDriver installation
- **Service not starting**: Check logs with `journalctl -u antam-bot -f`
- **Screenshots not working**: Ensure Xvfb is running
- **Database issues**: Check file permissions in `/opt/antam-bot`