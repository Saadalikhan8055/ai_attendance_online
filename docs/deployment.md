# AI Attendance System - Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the AI Attendance System to a production environment.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Server Setup](#server-setup)
3. [Database Configuration](#database-configuration)
4. [Application Deployment](#application-deployment)
5. [Security Hardening](#security-hardening)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

- [ ] Server provisioned (Ubuntu 20.04 LTS or CentOS 8+ recommended)
- [ ] Python 3.8+ installed
- [ ] PostgreSQL/MySQL installed (if not using SQLite)
- [ ] SSL certificate obtained (Let's Encrypt recommended)
- [ ] Domain name configured
- [ ] Email service setup (Gmail App Password or SendGrid)
- [ ] Backup strategy planned
- [ ] Monitoring solution configured
- [ ] VCS (Git) repository cloned

---

## Server Setup

### 1. System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- OS: Ubuntu 20.04 LTS or equivalent

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- Load balancer for high availability

### 2. Install Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3.8 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    supervisor \
    fail2ban \
    certbot \
    python3-certbot-nginx

# Install system dependencies for facial recognition
sudo apt install -y \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    cmake
```

### 3. Create Application User

```bash
# Create dedicated user for the app
sudo useradd -m -s /bin/bash attendance-app
sudo usermod -aG www-data attendance-app

# Set directory permissions
sudo mkdir -p /var/www/attendance
sudo chown -R attendance-app:www-data /var/www/attendance
sudo chmod 755 /var/www/attendance
```

---

## Database Configuration

### PostgreSQL Setup (Recommended for Production)

```bash
# Connect to PostgreSQL as root
sudo -u postgres psql

# Create database and user
CREATE DATABASE attendance_db;
CREATE USER attendance_user WITH PASSWORD 'strong_password_here';
ALTER ROLE attendance_user SET client_encoding TO 'utf8';
ALTER ROLE attendance_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE attendance_user SET default_transaction_deferrable TO on;
ALTER ROLE attendance_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;
\q
```

### Database Connection Pool (Optional but Recommended)

```bash
# Install PgBouncer for connection pooling
sudo apt install -y pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
# Add connection pooling settings for high-traffic scenarios
```

### Backup Strategy

```bash
# Create backup directory
sudo mkdir -p /var/backups/attendance
sudo chown attendance-app:www-data /var/backups/attendance

# Add cron job for daily backups
# sudo crontab -e (as attendance-app user)
# 0 2 * * * pg_dump attendance_db | gzip > /var/backups/attendance/backup_$(date +\%Y\%m\%d).sql.gz
```

---

## Application Deployment

### 1. Clone Repository

```bash
cd /var/www/attendance
sudo -u attendance-app git clone <your-repo-url> .
```

### 2. Setup Python Virtual Environment

```bash
cd /var/www/attendance
sudo -u attendance-app python3 -m venv venv
sudo -u attendance-app source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
cd /var/www/attendance
sudo -u attendance-app venv/bin/pip install --upgrade pip
sudo -u attendance-app venv/bin/pip install -r requirements.txt gunicorn gevent
```

### 4. Configure Environment Variables

```bash
# Copy example env file
sudo -u attendance-app cp .env.example .env

# Edit .env with production values
sudo -u attendance-app nano .env
```

**Important .env values for production:**
```
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=postgresql://attendance_user:password@localhost:5432/attendance_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SECRET_KEY=generate-a-random-secret-key
```

### 5. Initialize Database

```bash
cd /var/www/attendance
source venv/bin/activate

# Run database migrations
python db_init.py

# Create admin user
python -c "
from app import app, db
from models import User
with app.app_context():
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('strong_password')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created')
"
```

---

## Security Hardening

### 1. SSL/TLS Certificate Setup

```bash
# Using Let's Encrypt (recommended for free SSL)
sudo certbot certonly --standalone -d yourdomain.com

# Or with Nginx plugin
sudo certbot certonly --nginx -d yourdomain.com
```

### 2. Nginx Configuration

Create `/etc/nginx/sites-available/attendance`:

```nginx
upstream attendance_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    gzip_min_length 1000;

    # Proxy settings
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Location configurations
    location / {
        proxy_pass http://attendance_app;
    }

    location /static/ {
        alias /var/www/attendance/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Prevent access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ ~$ {
        deny all;
    }

    # Logging
    access_log /var/log/nginx/attendance_access.log;
    error_log /var/log/nginx/attendance_error.log;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Gunicorn Configuration

Create `/var/www/attendance/gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
log_level = "info"
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(q)s" "%(D)s"'
```

### 4. Supervisor Configuration

Create `/etc/supervisor/conf.d/attendance.conf`:

```ini
[program:attendance]
command=/var/www/attendance/venv/bin/gunicorn --config /var/www/attendance/gunicorn_config.py app:app
directory=/var/www/attendance
user=attendance-app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/attendance/gunicorn.log
environment=PATH="/var/www/attendance/venv/bin",FLASK_ENV="production"

[program:attendance-worker]
command=/var/www/attendance/venv/bin/celery -A app.celery worker --loglevel=info
directory=/var/www/attendance
user=attendance-app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/attendance/celery.log
```

Start supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 5. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 5000  # Gunicorn
```

### 6. Fail2Ban Configuration

Create `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-limit-req]
enabled = true
```

Restart Fail2Ban:
```bash
sudo systemctl restart fail2ban
```

---

## Monitoring & Maintenance

### 1. Application Monitoring

```bash
# Install monitoring tools
pip install prometheus-client psutil

# Add to app.py for metrics
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('app_requests_total', 'Total requests')
request_duration = Histogram('app_request_duration_seconds', 'Request duration')
```

### 2. Log Monitoring

```bash
# View application logs
sudo tail -f /var/log/attendance/gunicorn.log

# View system logs
sudo journalctl -u nginx -f
sudo journalctl -u supervisor -f

# Centralized logging (optional)
# Install and configure ELK stack or Datadog
```

### 3. Regular Maintenance Tasks

**Daily:**
- Monitor application logs
- Check system resources (CPU, RAM, Disk)

**Weekly:**
- Review access logs
- Backup database
- Check SSL certificate validity

**Monthly:**
- Update system packages
- Review security logs
- Audit user access
- Performance optimization review

```bash
# Auto-backup script (add to crontab)
#!/bin/bash
BACKUP_DIR="/var/backups/attendance"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump attendance_db | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

### 4. Performance Optimization

```python
# Enable caching in app.py
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

# Cache frequently accessed pages
@app.route('/dashboard')
@cache.cached(timeout=300)
def dashboard():
    # Your code
    pass
```

---

## Troubleshooting

### Common Issues

#### Application won't start
```bash
# Check Gunicorn logs
sudo tail -f /var/log/attendance/gunicorn.log

# Verify environment variables
source /var/www/attendance/venv/bin/activate
env | grep FLASK

# Test application directly
cd /var/www/attendance
python app.py
```

#### Database connection errors
```bash
# Test PostgreSQL connection
psql -h localhost -U attendance_user -d attendance_db

# Check database URL in .env
grep DATABASE_URL /var/www/attendance/.env

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### SSL certificate issues
```bash
# Check certificate validity
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --dry-run

# Check Nginx SSL configuration
sudo nginx -t
```

#### High memory usage
```bash
# Reduce Gunicorn workers
# Edit gunicorn_config.py and reduce worker count

# Monitor memory usage
free -h
ps aux | grep gunicorn
```

#### Performance issues
```bash
# Enable slow query logging (PostgreSQL)
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

# Monitor active connections
psql -c "SELECT * FROM pg_stat_activity;"
```

---

## Deployment Checklist

- [ ] Server provisioned and hardened
- [ ] Database configured and backed up
- [ ] Application cloned and dependencies installed
- [ ] Environment variables configured
- [ ] SSL certificate installed
- [ ] Nginx configured
- [ ] Gunicorn running
- [ ] Supervisor configured
- [ ] Firewall configured
- [ ] Fail2Ban configured
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] DNS records updated
- [ ] Testing completed
- [ ] Monitoring enabled

---

## Support & Troubleshooting

For issues or questions:
1. Check application logs: `/var/log/attendance/`
2. Review server logs: `sudo journalctl -xe`
3. Test connectivity: `curl -I https://yourdomain.com`
4. Contact system administrator

---

## Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Nginx Documentation: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/
- Supervisor Documentation: http://supervisord.org/

---

**Last Updated:** 2024
**Version:** 1.0.0
