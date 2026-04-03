# AI Attendance Online

AI Attendance Online is a Flask-based attendance management system that uses face recognition to register students, capture attendance from a webcam, and provide dashboards for analytics, reports, class management, and administration.

## Features

- Face-based student registration with photo upload
- Live webcam attendance capture and automatic recognition
- Attendance dashboard with student and record listings
- Attendance analytics and daily reports
- CSV export of attendance records
- Student directory and class management pages
- Admin panel for managing users and students
- Public pages for features, documentation, FAQ, and contact
- PostgreSQL support in production and SQLite fallback for local development

## Tech Stack

- Python 3.11
- Flask
- SQLAlchemy
- Flask-Login
- OpenCV
- face_recognition
- pandas
- Flask-Mail
- Gunicorn

## Project Structure

- `app.py` - main Flask application and routes
- `models.py` - database models and engine/session setup
- `recognition.py` - face encoding, registration, and attendance matching
- `email_utils.py` - contact form email helpers
- `db_init.py` - database initialization and default admin creation
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, and uploaded files
- `docker/` - Docker and Nginx configuration

## Prerequisites

- Python 3.11.7 or compatible Python 3.11 environment
- A webcam for attendance capture
- PostgreSQL for production, or SQLite for local development
- Optional: email credentials if you want contact form notifications

## Local Setup

1. Clone the repository.

2. Create and activate a virtual environment.

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Configure environment variables.

```bash
set FLASK_SECRET=your-secret-key
set FLASK_ENV=development
```

If you want to use PostgreSQL locally, also set `DATABASE_URL`.

5. Initialize the database.

```bash
python db_init.py
```

This creates the tables and adds a default admin user if one does not already exist.

6. Start the application.

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Default Admin Account

The database initializer creates a default admin user:

- Username: `admin`
- Password: `admin123`

Change this password immediately after first login.

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string; if not set, the app uses SQLite
- `FLASK_SECRET` - Flask session secret key
- `FLASK_ENV` - set to `production` for deployment
- `MAIL_SERVER` - SMTP host for contact form emails
- `MAIL_PORT` - SMTP port
- `MAIL_USERNAME` - SMTP username
- `MAIL_PASSWORD` - SMTP password
- `ADMIN_EMAIL` - destination for contact form messages
- `PORT` - runtime port used by the app host

## Usage

1. Log in with the admin account or a created user.
2. Register a student by uploading a photo with a clear face.
3. Start capture from the dashboard and use the webcam to mark attendance.
4. Review attendance records, analytics, reports, and the student directory.
5. Manage classes and system users from the admin section.

## Deployment

The repository includes deployment guidance for Render in [DEPLOYMENT.md](DEPLOYMENT.md). The app is configured to run with Gunicorn in production.

For a typical Render deployment:

```bash
gunicorn app:app
```

## Notes

- Face recognition is CPU-intensive and works better on paid instances than on free-tier hosts.
- Uploaded images are stored locally by default, so consider persistent object storage for production.
- If you are using the Docker setup, review the files in `docker/` and `docker-compose.yml` for the full multi-service stack.

## Troubleshooting

- If the app fails to start, confirm that dependencies are installed and `DATABASE_URL` or SQLite access is available.
- If face detection fails, make sure the uploaded image contains a single clear face.
- If attendance is not being marked, verify that the webcam is accessible and not already in use by another application.

## License

No license file is currently included in this repository.
