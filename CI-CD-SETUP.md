# CI/CD Setup Guide

This guide walks you through setting up automated deployment with GitHub Actions for the ANTAM Bot Dashboard.

## Overview

The CI/CD pipeline automatically:
- ✅ **Tests** code on every push (syntax validation)
- 🚀 **Deploys** to VPS when you push to `main` branch
- 📦 **Creates backups** before deployment
- 🔄 **Rolls back** automatically if deployment fails
- 🧪 **Validates** deployment with health checks

## 🚀 Quick Setup (3 Steps)

### Step 1: Initial VPS Deployment

Since you've already deployed using the existing scripts, skip this step!

If you need to deploy fresh on a new VPS:
```bash
# On your VPS (as root)
curl -O https://raw.githubusercontent.com/yourusername/your-repo/main/deploy.sh
chmod +x deploy.sh
sudo ./deploy.sh https://github.com/yourusername/your-repo.git
```

### Step 2: Setup GitHub Actions User

Create a dedicated user for GitHub Actions deployments:

```bash
# On your VPS (as root)
cd /opt/antam-bot
sudo ./scripts/setup_vps_user.sh YOUR_GITHUB_USERNAME
```

This will output SSH keys - **copy them for step 3**.

### Step 3: Add GitHub Secrets

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**

Add these 3 secrets:

| Secret Name | Value |
|-------------|-------|
| `VPS_HOST` | Your VPS IP address |
| `VPS_USER` | `deploy` (from setup script) |
| `VPS_SSH_KEY` | The private key from setup script |

## ✅ That's It!

Now every time you push to main:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

GitHub Actions will automatically:
1. Test your code
2. Deploy to VPS
3. Restart services
4. Validate deployment
5. Notify you of results

## 📊 Monitoring

**View deployment logs:**
- GitHub: Go to Actions tab in your repo
- VPS: `journalctl -u antam-bot -f`

**Manual deployment trigger:**
- GitHub repo → Actions → "Deploy ANTAM Bot to VPS" → "Run workflow"

## 🔧 Advanced Configuration

### Custom Branch Deployment

Edit `.github/workflows/deploy.yml` to deploy from different branch:
```yaml
on:
  push:
    branches: [ production ]  # Change from 'main' to 'production'
```

### Environment Variables

Add environment-specific secrets in GitHub:
```yaml
env:
  FLASK_SECRET_KEY: ${{ secrets.FLASK_SECRET_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Slack Notifications

Add Slack webhook for deployment notifications:
```yaml
- name: Slack notification
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🛠️ Troubleshooting

**Deployment fails:**
1. Check GitHub Actions logs
2. SSH to VPS: `ssh deploy@your-vps-ip`
3. Check service status: `sudo systemctl status antam-bot`
4. View application logs: `tail -f /opt/antam-bot/logs/error.log`

**Permission issues:**
```bash
# On VPS, fix ownership
sudo chown -R deploy:deploy /opt/antam-bot
```

**Rollback manually:**
```bash
# On VPS
cd /opt/antam-bot
sudo systemctl stop antam-bot
sudo rm -rf /opt/antam-bot
sudo mv /opt/antam-bot-backup /opt/antam-bot
sudo systemctl start antam-bot
```

## 📁 File Structure

```
├── .github/workflows/
│   └── deploy.yml          # GitHub Actions workflow
├── scripts/
│   ├── setup_vps_user.sh   # VPS user setup for CI/CD
│   └── initial_deploy.sh   # First-time deployment script
└── CI-CD-SETUP.md         # This guide
```

## 🔐 Security Notes

- The `deploy` user has minimal sudo permissions (only for service management)
- SSH keys are unique per repository
- Private keys are encrypted in GitHub secrets
- Automatic rollback prevents broken deployments
- Backup created before each deployment