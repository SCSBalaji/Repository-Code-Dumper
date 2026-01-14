# Deployment Guide

This guide covers deploying the Repository Code Dumper application to a VPS (Virtual Private Server) with domain/subdomain configuration and SSL setup.

## Table of Contents

- [Prerequisites](#prerequisites)
- [VPS Setup](#vps-setup)
- [Domain/Subdomain Configuration](#domainsubdomain-configuration)
- [Application Deployment](#application-deployment)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Nginx Reverse Proxy](#nginx-reverse-proxy)
- [Security Hardening](#security-hardening)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, you'll need:

1. **VPS Provider Account**: DigitalOcean, AWS, Linode, Vultr, etc.
2. **Domain Name**: Purchased from a domain registrar (Namecheap, GoDaddy, Cloudflare, etc.)
3. **SSH Key**: For secure server access
4. **Basic Linux Knowledge**: Command line familiarity

### Recommended VPS Specifications

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2 GB |
| Storage | 20 GB | 40 GB |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

## VPS Setup

### Step 1: Create VPS Instance

Using DigitalOcean as an example:

1. Log in to your DigitalOcean account
2. Click "Create" → "Droplets"
3. Choose Ubuntu 22.04 LTS
4. Select a plan (Basic, $6/month is fine for starting)
5. Choose a datacenter region close to your users
6. Add your SSH key
7. Create Droplet

### Step 2: Connect to Your VPS

```bash
# Connect via SSH
ssh root@YOUR_SERVER_IP

# Or if using a non-root user
ssh username@YOUR_SERVER_IP
```

### Step 3: Initial Server Setup

```bash
# Update system packages
apt update && apt upgrade -y

# Set timezone
timedatectl set-timezone America/New_York  # Change to your timezone

# Create a non-root user (recommended)
adduser deploy
usermod -aG sudo deploy

# Copy SSH keys to new user
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Logout and reconnect as deploy user
exit
ssh deploy@YOUR_SERVER_IP
```

### Step 4: Install Docker

```bash
# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Step 5: Configure Firewall

```bash
# Install UFW if not present
sudo apt install -y ufw

# Allow SSH
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Domain/Subdomain Configuration

### Step 1: Choose Your Domain Structure

Options:
- **Main domain**: `codedumper.example.com`
- **Subdomain**: `dump.example.com`

### Step 2: Configure DNS Records

Log in to your domain registrar and add DNS records:

#### For Subdomain (e.g., dump.example.com)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | dump | YOUR_SERVER_IP | 300 |

#### For Root Domain

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 300 |
| A | www | YOUR_SERVER_IP | 300 |

### Step 3: Verify DNS Propagation

```bash
# Check if DNS is propagated
dig dump.example.com +short

# Or use online tool: https://dnschecker.org
```

DNS propagation can take 5 minutes to 48 hours (usually under 30 minutes).

## Application Deployment

### Step 1: Clone the Repository

```bash
# Create app directory
sudo mkdir -p /opt/repo-dumper
sudo chown $USER:$USER /opt/repo-dumper

# Clone repository
cd /opt/repo-dumper
git clone https://github.com/yourusername/Repository-Code-Dumper.git .

# Or upload your files via SCP
scp -r ./Repository-Code-Dumper/* deploy@YOUR_SERVER_IP:/opt/repo-dumper/
```

### Step 2: Configure Environment (Optional)

Create environment file if needed:

```bash
# Create .env file
cat > .env << 'EOF'
OUTPUT_DIR=/app/outputs
PYTHONUNBUFFERED=1
EOF
```

### Step 3: Build and Start Containers

```bash
cd /opt/repo-dumper

# Build and start
docker compose up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Step 4: Verify Deployment

```bash
# Test backend health
curl http://localhost:8000/health

# Test frontend (should return HTML)
curl http://localhost
```

## SSL/TLS Configuration

We'll use Certbot to get free SSL certificates from Let's Encrypt.

### Step 1: Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Step 2: Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Create site configuration
sudo nano /etc/nginx/sites-available/repo-dumper
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name dump.example.com;  # Replace with your domain

    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Step 3: Enable Site and Get SSL Certificate

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/repo-dumper /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d dump.example.com
```

Follow the prompts:
1. Enter your email address
2. Agree to terms
3. Choose whether to redirect HTTP to HTTPS (recommended: yes)

### Step 4: Verify SSL

```bash
# Test HTTPS
curl https://dump.example.com/health
```

Visit `https://dump.example.com` in your browser and check for the padlock icon.

### Step 5: Auto-Renewal

Certbot sets up auto-renewal automatically. Verify:

```bash
# Test renewal
sudo certbot renew --dry-run

# Check timer
sudo systemctl status certbot.timer
```

## Alternative: Docker with Built-in SSL (Using Traefik)

For a more integrated Docker solution, you can use Traefik as a reverse proxy.

### Create docker-compose.prod.yml

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - web

  backend:
    build: ./backend
    container_name: repo-dumper-backend
    environment:
      - OUTPUT_DIR=/app/outputs
    volumes:
      - output_files:/app/outputs
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`dump.example.com`) && PathPrefix(`/process-repo`, `/download`, `/health`)"
      - "traefik.http.routers.backend.entrypoints=websecure"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
    networks:
      - web
    restart: always

  frontend:
    build:
      context: ./frontend
      args:
        - REACT_APP_API_URL=
    container_name: repo-dumper-frontend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`dump.example.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
    networks:
      - web
    depends_on:
      - backend
    restart: always

volumes:
  output_files:

networks:
  web:
    external: true
```

### Deploy with Traefik

```bash
# Create network
docker network create web

# Update docker-compose.prod.yml with your domain
# Then deploy
docker compose -f docker-compose.prod.yml up -d
```

## Security Hardening

### Disable Root SSH Login

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PermitRootLogin no
PasswordAuthentication no
```

```bash
sudo systemctl restart sshd
```

### Install Fail2ban

```bash
sudo apt install -y fail2ban

# Create local config
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Enable Automatic Security Updates

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Monitoring and Maintenance

### Set Up Log Rotation

Docker logs are automatically rotated with Docker's log driver. For system logs:

```bash
# Check logrotate
cat /etc/logrotate.d/docker
```

### Create Backup Script

```bash
# Create backup script
cat > /opt/repo-dumper/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup output files
docker compose exec -T backend tar czf - /app/outputs > $BACKUP_DIR/outputs_$DATE.tar.gz

# Keep only last 7 backups
ls -t $BACKUP_DIR/outputs_*.tar.gz | tail -n +8 | xargs -r rm

echo "Backup completed: $BACKUP_DIR/outputs_$DATE.tar.gz"
EOF

chmod +x /opt/repo-dumper/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/repo-dumper/backup.sh") | crontab -
```

### Health Check Script

```bash
cat > /opt/repo-dumper/healthcheck.sh << 'EOF'
#!/bin/bash

# Check if containers are running
if ! docker compose ps | grep -q "Up"; then
    echo "Containers not running. Restarting..."
    docker compose up -d
fi

# Check backend health
if ! curl -sf http://localhost:8000/health > /dev/null; then
    echo "Backend unhealthy. Restarting..."
    docker compose restart backend
fi
EOF

chmod +x /opt/repo-dumper/healthcheck.sh

# Add to crontab (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/repo-dumper/healthcheck.sh") | crontab -
```

### Update Application

```bash
cd /opt/repo-dumper

# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose up --build -d
```

## Troubleshooting

### Container Issues

```bash
# Check container logs
docker compose logs backend
docker compose logs frontend

# Restart containers
docker compose restart

# Rebuild from scratch
docker compose down
docker compose up --build -d
```

### SSL Issues

```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check Nginx config
sudo nginx -t
```

### DNS Issues

```bash
# Check DNS resolution
dig dump.example.com

# Check from outside
curl -I https://dump.example.com
```

### Firewall Issues

```bash
# Check UFW status
sudo ufw status verbose

# Check open ports
sudo ss -tulpn
```

### Performance Issues

```bash
# Check system resources
htop

# Check Docker stats
docker stats

# Check disk usage
df -h
```

## Quick Reference

### Common Commands

| Task | Command |
|------|---------|
| Start application | `docker compose up -d` |
| Stop application | `docker compose down` |
| View logs | `docker compose logs -f` |
| Restart | `docker compose restart` |
| Update | `git pull && docker compose up --build -d` |
| SSL renew | `sudo certbot renew` |
| Check health | `curl http://localhost:8000/health` |

### Important Paths

| Path | Description |
|------|-------------|
| `/opt/repo-dumper` | Application directory |
| `/etc/nginx/sites-available` | Nginx configs |
| `/etc/letsencrypt` | SSL certificates |
| `/var/log/nginx` | Nginx logs |

### Ports

| Port | Service |
|------|---------|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |
| 8000 | Backend API (internal) |
