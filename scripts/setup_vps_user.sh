#!/bin/bash

# VPS User Setup Script for GitHub Actions CI/CD
# Run this script on your VPS to prepare it for GitHub Actions deployment

set -e

echo "🔧 Setting up VPS for GitHub Actions CI/CD..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ This script must be run as root"
  echo "Usage: sudo ./setup_vps_user.sh [github_username]"
  exit 1
fi

# Get GitHub username
GITHUB_USER=${1:-}
if [ -z "$GITHUB_USER" ]; then
  echo "❌ Please provide your GitHub username"
  echo "Usage: sudo ./setup_vps_user.sh [github_username]"
  exit 1
fi

# Create deployment user
DEPLOY_USER="deploy"
echo "👤 Creating deployment user: $DEPLOY_USER"

# Create user if doesn't exist
if ! id "$DEPLOY_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$DEPLOY_USER"
  echo "✅ User $DEPLOY_USER created"
else
  echo "ℹ️  User $DEPLOY_USER already exists"
fi

# Add user to sudo group
usermod -aG sudo "$DEPLOY_USER"
echo "✅ Added $DEPLOY_USER to sudo group"

# Create SSH directory
mkdir -p /home/$DEPLOY_USER/.ssh
chown $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh
chmod 700 /home/$DEPLOY_USER/.ssh

# Setup sudo without password for deployment tasks
echo "🔑 Configuring sudo permissions..."
cat << EOF > /etc/sudoers.d/$DEPLOY_USER
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart antam-bot
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl stop antam-bot
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl start antam-bot
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl status antam-bot
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl stop nginx
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl start nginx
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl status nginx
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/sbin/nginx -t
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/cp /opt/antam-bot/nginx/antam-bot.conf /etc/nginx/sites-available/*
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/cp -r /opt/antam-bot /opt/antam-bot-backup
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/rm -rf /opt/antam-bot-backup
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/rm -rf /opt/antam-bot
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/mv /opt/antam-bot-backup /opt/antam-bot
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u antam-bot -n 20 --no-pager
$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u nginx -n 20 --no-pager
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/chmod +x /opt/antam-bot/update.sh
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
EOF

echo "✅ Sudo permissions configured"

# Set ownership of app directory
if [ -d "/opt/antam-bot" ]; then
  chown -R $DEPLOY_USER:$DEPLOY_USER /opt/antam-bot
  echo "✅ Set ownership of /opt/antam-bot to $DEPLOY_USER"
fi

# Generate SSH key pair
SSH_KEY_PATH="/home/$DEPLOY_USER/.ssh/id_ed25519"
if [ ! -f "$SSH_KEY_PATH" ]; then
  echo "🔑 Generating SSH key pair..."
  sudo -u $DEPLOY_USER ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "github-actions@$GITHUB_USER"
  echo "✅ SSH key pair generated"
else
  echo "ℹ️  SSH key pair already exists"
fi

# Display public key for GitHub
echo ""
echo "📋 IMPORTANT: Add this PUBLIC KEY to your GitHub repository secrets:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat $SSH_KEY_PATH.pub
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Display private key for GitHub secrets
echo "🔐 IMPORTANT: Add this PRIVATE KEY to GitHub secrets as 'VPS_SSH_KEY':"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat $SSH_KEY_PATH
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Display next steps
echo "📝 NEXT STEPS:"
echo ""
echo "1. Add these GitHub repository secrets:"
echo "   - VPS_HOST: $(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')"
echo "   - VPS_USER: $DEPLOY_USER"
echo "   - VPS_SSH_KEY: (the private key shown above)"
echo ""
echo "2. To add secrets to GitHub:"
echo "   → Go to your repo → Settings → Secrets and variables → Actions"
echo "   → Click 'New repository secret' for each one"
echo ""
echo "3. Push your code to trigger the first deployment:"
echo "   git add ."
echo "   git commit -m \"Add CI/CD pipeline\""
echo "   git push origin main"
echo ""
echo "✅ VPS setup complete! GitHub Actions will now be able to deploy automatically."