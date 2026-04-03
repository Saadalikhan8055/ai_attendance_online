# Docker Deployment Quick Start Guide

## Overview
This guide provides quick steps to deploy the AI Attendance System using Docker and Docker Compose.

## Prerequisites

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Git**: For cloning the repository
- **8GB RAM minimum** for smooth operation
- **50GB disk space** recommended

## Quick Start (5 minutes)

### 1. Clone Repository
```bash
git clone <repository-url>
cd ai_attendance_online
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.docker .env

# Edit .env with your settings
# At minimum, change:
# - SECRET_KEY (generate a random string)
# - MAIL_USERNAME and MAIL_PASSWORD
# - DB_PASSWORD and REDIS_PASSWORD
nano .env
```

### 3. Run Docker Compose
```bash
# Make the launcher script executable
chmod +x docker-launch.sh

# Start all services
./docker-launch.sh up
```

That's it! Your application should now be running.

## Access the Application

- **Web Application**: http://localhost (or https://yourdomain.com)
- **PostgreSQL**: localhost:5432 (user: `attendance_user`)
- **Redis**: localhost:6379 (password: from `.env`)

## Default Login

After setup, create an admin user:
```bash
./docker-launch.sh admin
```

Or manually:
```bash
./docker-launch.sh shell
python -c "
from app import app, db
from models import User

with app.app_context():
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('your-password')
    db.session.add(admin)
    db.session.commit()
"
```

## Common Commands

### Start/Stop Services
```bash
# Start all containers
./docker-launch.sh up

# Stop all containers
./docker-launch.sh down

# Restart all containers
./docker-launch.sh restart
```

### View Logs
```bash
# View application logs
./docker-launch.sh logs

# View specific container logs
docker logs attendance_app
docker logs attendance_nginx
docker logs attendance_postgres
```

### Database Operations
```bash
# Run migrations
./docker-launch.sh migrate

# Backup database
./docker-launch.sh backup

# Restore from backup
./docker-launch.sh restore backups/backup_20240101_120000.sql.gz
```

### Maintenance
```bash
# Health check
./docker-launch.sh health

# Open shell in app container
./docker-launch.sh shell

# View running containers
./docker-launch.sh ps

# Clean up (removes containers and volumes)
./docker-launch.sh clean
```

## Architecture

The Docker Compose setup includes:

1. **PostgreSQL**: Database server
2. **Redis**: Cache and session storage
3. **App**: Flask application with Gunicorn
4. **Nginx**: Reverse proxy and load balancer
5. **Celery Worker**: Background task processing
6. **Celery Beat**: Scheduled task execution

```
┌─────────────┐
│   Nginx     │ (Port 80, 443)
└──────┬──────┘
       │
┌──────┴──────────────────────┐
│    Flask App (Gunicorn)     │ (Port 5000)
└──────┬──────────────────────┘
       │
   ┌───┴────────────────┬───────────────┐
   │                    │               │
┌──┴──┐          ┌──────┴──────┐   ┌───┴────┐
│ PostgreSQL     │   Redis     │   │ Celery │
│ (Port 5432)    │ (Port 6379) │   │Worker  │
└───────┘        └─────────────┘   └────────┘
```

## Production Configuration

### 1. Enable HTTPS

Place your SSL certificates in `docker/certs/`:
```bash
mkdir -p docker/certs
cp /path/to/fullchain.pem docker/certs/
cp /path/to/privkey.pem docker/certs/
```

Update `docker/nginx.conf` with your domain name.

### 2. Configure Email

Edit `.env`:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
ADMIN_EMAIL=admin@yourdomain.com
```

For Gmail:
1. Enable 2-factor authentication
2. Generate app-specific password: https://myaccount.google.com/apppasswords
3. Use the app password in `MAIL_PASSWORD`

### 3. Secure Passwords

Generate strong passwords:
```bash
# Generate random secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in .env
SECRET_KEY=<generated-key>
DB_PASSWORD=<new-password>
REDIS_PASSWORD=<new-password>
```

### 4. Configure Firewall

```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
```

## Troubleshooting

### Containers Won't Start

```bash
# Check Docker logs
docker logs attendance_app
docker logs attendance_postgres

# Verify Docker daemon is running
docker ps

# Try rebuilding
./docker-launch.sh build
./docker-launch.sh up
```

### High Memory Usage

```bash
# Reduce Gunicorn workers in docker-compose.yml
# Change: gunicorn --workers 4 to --workers 2

# Check memory usage
docker stats
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
docker-compose exec postgres psql -U attendance_user -d attendance_db -c "SELECT 1"

# Check DATABASE_URL in .env
grep DATABASE_URL .env

# Restart database
docker-compose restart postgres
```

### SSL Certificate Issues

```bash
# Check certificate validity
ls -la docker/certs/

# Update Nginx config with correct domain
# Restart Nginx
docker-compose restart nginx
```

### Performance Issues

```bash
# Enable caching in Redis
# Check .env REDIS_URL is set

# Increase Gunicorn workers if CPU usage is low
# But monitor memory

# Enable gzip compression (already enabled in nginx.conf)
```

## Monitoring & Logs

### Application Logs
```bash
# Real-time application logs
docker logs -f attendance_app

# Last 100 lines
docker logs --tail 100 attendance_app

# With timestamps
docker logs -t attendance_app
```

### Database Logs
```bash
docker logs -f attendance_postgres
```

### Nginx Logs
```bash
docker logs -f attendance_nginx
```

### Celery Logs
```bash
docker logs -f attendance_celery
```

## Backup & Recovery

### Backup Database
```bash
./docker-launch.sh backup
# Creates: backups/backup_YYYYMMDD_HHMMSS.sql.gz
```

### Restore Backup
```bash
./docker-launch.sh restore backups/backup_20240101_120000.sql.gz
```

### Manual Backup
```bash
docker-compose exec postgres pg_dump -U attendance_user attendance_db > backup.sql
```

## Scaling

### Horizontal Scaling

For multiple app instances with load balancing:

```bash
# Scale app service to 3 instances
docker-compose up -d --scale app=3

# Note: You'll need a load balancer in front
```

### Resource Limits

Edit `docker-compose.yml`:
```yaml
app:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 512M
```

## Updates & Maintenance

### Update Application Code
```bash
git pull origin main
./docker-launch.sh build
./docker-launch.sh restart
```

### Update Base Images
```bash
docker-compose pull
./docker-launch.sh build
./docker-launch.sh restart
```

## Clean Deployment

For a fresh installation:

```bash
# Remove existing containers
./docker-launch.sh clean

# Start fresh
./docker-launch.sh up

# Create admin user
./docker-launch.sh admin
```

## Production Checklist

- [ ] Update `.env` with production values
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure email service
- [ ] Setup SSL certificates
- [ ] Configure database password
- [ ] Setup backup strategy
- [ ] Enable firewall
- [ ] Configure monitoring
- [ ] Setup log aggregation (optional)
- [ ] Test health check: `./docker-launch.sh health`
- [ ] Perform load testing
- [ ] Document runbook

## Support

For issues:
1. Check logs: `./docker-launch.sh logs`
2. Run health check: `./docker-launch.sh health`
3. Review `.env` configuration
4. Check Docker/Docker Compose versions
5. See Troubleshooting section above

## Resources

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Documentation](https://docs.docker.com/compose)
- [Flask Documentation](https://flask.palletsprojects.com)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)
- [Nginx Documentation](https://nginx.org/en/docs)

---

**Last Updated:** 2024
**Version:** 1.0.0
