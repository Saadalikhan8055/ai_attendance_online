# VPS Deployment Guide

This repository runs on a VPS with Docker and Docker Compose.

## What this setup includes

- Flask app served by Gunicorn inside a Docker container.
- PostgreSQL in a separate container.
- Port `80` exposed on the app container.
- Persistent storage for uploaded images and logs.

## Prerequisites

- A VPS with at least 2 GB RAM. 4 GB RAM is safer for this app.
- Docker installed on the VPS.
- Docker Compose available on the VPS.

## Step by step

1. SSH into your VPS.
2. Install Docker and Docker Compose if they are not already installed.
3. Copy this repository to the server.
4. Create a `.env` file in the project root with at least:

```env
FLASK_SECRET=your-long-random-secret
SECRET_KEY=your-long-random-secret
DB_PASSWORD=your-db-password
MAIL_USERNAME=
MAIL_PASSWORD=
ADMIN_EMAIL=
```

5. Start the stack:

```bash
docker compose -f docker-compose.vps.yml up -d --build
```

6. Check the logs if needed:

```bash
docker compose -f docker-compose.vps.yml logs -f app
```

7. Open the VPS public IP in your browser on port `80`.

## Notes

- The database is initialized automatically when the app container starts.
- Uploaded files are stored in `static/uploads` on the VPS host.
- If you change the code, rerun the `docker compose ... up -d --build` command.
