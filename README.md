
# AI Attendance System - Online Web Application

A complete, intelligent attendance management system powered by AI face recognition. This web application automates the student attendance marking process using real-time facial recognition technology via webcam.

## 🎯 Project Overview

This is a **Flask-based web application** that leverages artificial intelligence to:
- **Automatically identify students** using their facial features
- **Mark attendance in real-time** without manual intervention
- **Manage student profiles** with photo uploads
- **Track and export attendance records** for reporting
- **Provide secure access** with user authentication

## ✨ Key Features

### 1. **User Authentication**
   - Secure login system with username and password
   - Role-based access control (Admin functionality)
   - Session management with Flask-Login
   - Default admin account (username: `admin`, password: `admin123`)

### 2. **Student Management**
   - Register new students with their photo
   - Store facial encodings in secure database
   - View all registered students
   - Delete student profiles (Admin only)
   - Automatic cascade deletion of related attendance records

### 3. **Real-Time Face Recognition**
   - Live video stream capture from webcam
   - Advanced facial recognition using `face_recognition` library
   - Automatic identification and attendance marking
   - Configurable tolerance level for matching accuracy
   - Real-time display of captured faces and matches

### 4. **Attendance Dashboard**
   - View all attendance records with student details
   - See timestamps for each attendance entry
   - Filter and manage records
   - Delete incorrect attendance entries (Admin only)
   - Real-time attendance log updates

### 5. **Data Export**
   - Export all attendance records to CSV format
   - Download Attendance logs for external analytics
   - Includes student name, ID, and timestamp

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Flask, Flask-Login |
| **Database** | SQLite, SQLAlchemy ORM |
| **Face Recognition** | face_recognition, OpenCV (cv2) |
| **Frontend** | Bootstrap 5, HTML/Jinja2 Templates |
| **Data Processing** | Pandas |
| **Server** | Gunicorn (for production) |
| **Environment** | Python-dotenv |

## 📂 Project Structure

```
ai_attendance_online/
├── app.py                    # Main Flask application with all routes
├── models.py                 # SQLAlchemy database models (Student, Attendance, User)
├── recognition.py            # Face recognition logic and encoding functions
├── db_init.py               # Database initialization script
├── check_ids.py             # Utility to check existing student IDs
├── requirements.txt         # Python dependencies
├── attendance_export.csv    # Exported attendance records
├── templates/               # HTML templates
│   ├── base.html           # Base template with navigation
│   ├── index.html          # Home page
│   ├── login.html          # Login form
│   ├── register.html       # Student registration form
│   ├── capture.html        # Face capture/attendance marking interface
│   └── dashboard.html      # Attendance records dashboard
├── static/                  # Static files
│   ├── css/
│   │   └── style.css       # Custom CSS styles
│   └── uploads/            # Uploaded student photos
└── .env (optional)         # Environment variables
```

## 📋 File Descriptions

| File | Purpose |
|------|---------|
| **app.py** | Main Flask application with all web routes (login, student registration, capture, dashboard, export) |
| **models.py** | Database schema with SQLAlchemy ORM (Student, Attendance, User models) |
| **recognition.py** | Core face recognition algorithms (encoding, matching, attendance marking) |
| **db_init.py** | Initialize database and create default admin user |
| **check_ids.py** | Utility script to list all registered student IDs |
| **requirements.txt** | All Python package dependencies |

## 📦 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Webcam (for face capture)
- Modern web browser (Chrome, Firefox, Edge, etc.)

### Step 1: Clone/Download the Repository
```bash
cd ai_attendance_online-main
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Initialize the Database
```bash
python db_init.py
```
This creates the SQLite database and initializes the admin user.

### Step 4: Run the Application
```bash
python app.py
```
The application will start on `http://localhost:5000`

## 🚀 Usage Guide

### Initial Setup
1. **Access the application** at `http://localhost:5000`
2. **Login** with default credentials:
   - Username: `admin`
   - Password: `admin123`
3. **Change admin password** (recommended for security)

### Registering Students

1. Navigate to **"Register Student"** from the navigation menu
2. Enter the student's details:
   - **Name**: Full name of the student
   - **Student ID**: Unique identifier (roll number, ID, etc.)
   - **Photo**: Upload a clear photo of the student's face
3. Click **"Register"** to save
4. The system will extract and store the facial encoding

### Marking Attendance

1. Go to **"Start Capture"** page
2. Allow webcam access when prompted
3. Position the student's face in front of the camera
4. Click **"Capture Frame"** to:
   - Detect the face in the frame
   - Compare against registered students
   - Automatically mark attendance if matched
5. View real-time log of marked attendance below the video feed

### Viewing Dashboard

1. Click **"Dashboard"** in the navigation
2. View two sections:
   - **Attendance Records**: All marked attendance entries with timestamps
   - **Student Records**: List of all registered students
3. **Export Data**: Click "Export to CSV" for analyses

### Admin Operations

As an admin user, you have additional capabilities:
- **Delete Attendance Records**: Remove incorrect entries
- **Delete Students**: Remove students and their all attendance data
- Access full management dashboard

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root:
```
FLASK_SECRET=your_secret_key_here
PORT=5000
DATABASE_URL=sqlite:///attendance.db
```

### Adjusting Face Recognition Tolerance

In `recognition.py`, modify the tolerance value in `recognize_and_mark()`:
```python
def recognize_and_mark(frame, session, tolerance=0.6):
    # Lower tolerance = stricter matching (0.4-0.5)
    # Higher tolerance = more lenient matching (0.6-0.7)
```

## 📊 Database Schema

### Student Table
- `id`: Primary key
- `name`: Student's full name
- `student_id`: Unique student identifier
- `encoding`: Stored facial encoding (as comma-separated values)

### Attendance Table
- `id`: Primary key
- `student_id`: Foreign key linking to Student
- `timestamp`: Date and time of attendance marking

### User Table
- `id`: Primary key
- `username`: Login username
- `password`: Login password

## 🌐 Deployment Options

### Deploy to Render (Recommended)

1. **Prepare code for deployment:**
   - Ensure `requirements.txt` has all dependencies
   - Create `Procfile` with: `web: gunicorn app:app`

2. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

3. **On Render dashboard:**
   - Click **"New Web Service"**
   - Connect your GitHub repository
   - Set **Build command**: `pip install -r requirements.txt`
   - Set **Start command**: `gunicorn app:app`
   - Add **Environment variables**:
     - `PYTHON_VERSION=3.9`
     - `FLASK_SECRET=your_secret_key`

4. Deploy and access your app URL

### Deploy to Netlify

Netlify is primarily for static frontend. For this Flask app with AI processing, use serverless alternatives:
- **Vercel** (with Flask integration)
- **AWS Lambda** (serverless)
- **Google Cloud Run**

### Deploy to Other Platforms

- **Heroku**: Use `Procfile` and deploy via Git
- **AWS EC2**: Run directly on server instance
- **DigitalOcean App Platform**: Connect GitHub repo
- **Self-hosted VPS**: Deploy with Docker/systemd

## ⚠️ Security Recommendations (Before Deployment)

1. **Change Admin Password**: Update default admin credentials immediately
2. **Use Environment Variables**: Store sensitive data in `.env`:
   ```
   FLASK_SECRET=generate_strong_random_key
   DATABASE_URL=your_database_url
   ```
3. **Enable HTTPS**: Ensure SSL/TLS certificates on deployed site
4. **Validate File Uploads**: Restrict file types and sizes for photo uploads
5. **Hash Passwords**: Implement bcrypt for password hashing (not plain text)
6. **Database Security**: 
   - Use PostgreSQL instead of SQLite for production
   - Set strong database credentials
7. **Rate Limiting**: Prevent brute force attacks on login
8. **CORS Protection**: Implement proper CORS headers
9. **Input Validation**: Sanitize all user inputs
10. **API Protection**: Add request throttling

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Webcam not detected** | Check browser permissions, restart browser, try different browser |
| **Faces not recognized** | Ensure good lighting, clear photo during registration, increase tolerance |
| **"Module not found" errors** | Run `pip install -r requirements.txt` again |
| **Database errors** | Delete `attendance.db` and run `python db_init.py` |
| **Port 5000 already in use** | Change port: `set PORT=5001` then `python app.py` |
| **Login fails** | Verify database initialized: run `python db_init.py` |

## 📸 How It Works

1. **Student Registration**
   - Upload a clear photo of the student's face
   - System extracts facial encoding using `face_recognition` library
   - Encoding stored in database for future matching

2. **Attendance Capture**
   - Webcam captures live video stream
   - System detects faces in each frame
   - Compares detected faces against database of registered students
   - Marks attendance automatically when match found

3. **Data Management**
   - All attendance records stored with timestamp
   - Records can be viewed, filtered, and exported
   - Admin can manage records and delete entries as needed

## 🔮 Future Enhancement Ideas

- 📱 Mobile app integration with QR code scanning
- 📧 Email/SMS notifications for absent students
- 📈 Advanced analytics dashboards with charts
- 🔗 Integration with LMS/ERP systems
- 👥 Multi-camera support for large halls
- ⏰ Automated reports generation
- 🌐 Multi-language support
- 🔒 Two-factor authentication

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs and issues
- Submit pull requests with improvements
- Suggest new features
- Improve documentation

## 📜 License

This project is open source and free to use and modify.

## ❓ Support & Issues

If you encounter any issues:
1. Check the Troubleshooting section above
2. Verify all dependencies are installed
3. Ensure database is initialized
4. Check browser console for errors (F12)
5. Open an issue on the repository

---

**Ready to Deploy?** Choose your hosting platform and follow the deployment steps above!

**Good luck with your attendance system! 🚀**
