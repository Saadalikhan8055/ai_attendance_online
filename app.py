import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response, jsonify, g
from models import get_engine, get_session, Student, Attendance, User, ClassSection
from recognition import register_student, recognize_and_mark, load_known_encodings
from email_utils import init_email, send_contact_email, send_contact_confirmation
import cv2
import datetime
import pandas as pd
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")
engine = get_engine()

# Initialize Email
init_email(app)

# --- Per-Request Database Session Management ---
@app.before_request
def before_request_func():
    # Open a fresh database session for each request
    g.session = get_session(engine)

@app.teardown_request
def teardown_request_func(exception=None):
    # Commit changes if no error, then close the session
    if 'session' in g:
        if exception:
            g.session.rollback()
        else:
            g.session.commit()
        g.session.close()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# Simple User class for Flask-Login
class UserLogin(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    u = g.session.query(User).filter_by(id=int(user_id)).first()
    if u:
        return UserLogin(u.id, u.username, u.password)
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        u = g.session.query(User).filter_by(username=username, password=password).first()
        if u:
            user_obj = UserLogin(u.id, u.username, u.password)
            login_user(user_obj)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/register_student", methods=["GET","POST"])
@login_required
def register_student_route():
    if request.method == "POST":
        name = request.form.get("name")
        student_id = request.form.get("student_id")
        file = request.files.get("photo")
        if not file:
            flash("Please upload a photo", "warning")
            return redirect(request.url)
        save_path = os.path.join("static", "uploads")
        os.makedirs(save_path, exist_ok=True)
        filepath = os.path.join(save_path, file.filename)
        file.save(filepath)
        try:
            register_student(filepath, name, student_id, session=g.session)
            flash("Student registered successfully", "success")
        except Exception as e:
            g.session.rollback()
            flash(str(e), "danger")
    return render_template("register.html")

def gen_frames():
    """Video streaming generator function."""
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
    camera.release()

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
@app.route("/capture_single_frame", methods=["POST"])
@login_required
def capture_single_frame():
    camera = cv2.VideoCapture(0)
    success, frame = camera.read()
    camera.release()
    
    if not success:
        return jsonify({"message": "Error: Could not capture frame."}), 500
    
    try:
        matches_info = recognize_and_mark(frame, session=g.session)
        if matches_info:
            return jsonify({"message": f"Captured successfully!"}), 200
        else:
            return jsonify({"message": "No face recognized."}), 200
    except Exception as e:
        g.session.rollback()
        return jsonify({"message": f"Error during recognition: {str(e)}"}), 500

@app.route("/start_capture")
@login_required
def start_capture():
    return render_template('capture.html')

@app.route('/get_attendance_log')
@login_required
def get_attendance_log():
    one_minute_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
    records = g.session.query(Attendance).filter(Attendance.timestamp >= one_minute_ago).order_by(Attendance.timestamp.desc()).all()
    
    log = []
    for r in records:
        if r.timestamp:
            # Format timestamp as HH:MM:SS
            time_str = r.timestamp.strftime('%H:%M:%S')
        else:
            time_str = 'N/A'
        
        log.append({
            'name': r.student.name if r.student else 'Unknown',
            'student_id': r.student_id if r.student_id else 'N/A',
            'timestamp': time_str
        })
    return jsonify(log)

@app.route("/delete_attendance/<int:record_id>", methods=["POST"])
@login_required
def delete_attendance(record_id):
    if current_user.username != "admin":
        flash("You do not have permission to delete records.", "danger")
        return redirect(url_for("dashboard"))

    record = g.session.query(Attendance).filter_by(id=record_id).first()
    if record:
        g.session.delete(record)
        flash("Attendance record deleted successfully.", "success")
    else:
        flash("Record not found.", "danger")
    return redirect(url_for("dashboard"))

@app.route("/delete_student/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    if current_user.username != "admin":
        flash("You do not have permission to delete students.", "danger")
        return redirect(url_for("dashboard"))

    student = g.session.query(Student).filter_by(id=student_id).first()
    if student:
        g.session.delete(student)
        flash("Student deleted successfully. All associated attendance records have also been deleted.", "success")
    else:
        flash("Student not found.", "danger")
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    attendance_records = g.session.query(Attendance).all()
    student_records = g.session.query(Student).all()
    
    rows_attendance = []
    for r in attendance_records:
        rows_attendance.append({
            "id": r.id,
            "name": r.student.name,
            "student_id": r.student.student_id,
            "timestamp": r.timestamp
        })

    rows_students = []
    for s in student_records:
        rows_students.append({
            "id": s.id,
            "name": s.name,
            "student_id": s.student_id
        })
        
    return render_template("dashboard.html", attendance_records=rows_attendance, student_records=rows_students)

@app.route("/export_csv")
@login_required
def export_csv():
    records = g.session.query(Attendance).all()
    df = pd.DataFrame([{"name": r.student.name, "student_id": r.student.student_id, "timestamp": r.timestamp} for r in records])
    out_path = "attendance_export.csv"
    df.to_csv(out_path, index=False)
    return send_file(out_path, as_attachment=True)

# --- Analytics Route ---
@app.route("/analytics")
@login_required
def analytics():
    """Display attendance analytics and insights"""
    total_students = g.session.query(Student).count()
    total_records = g.session.query(Attendance).count()
    
    # Get today's date
    today = datetime.date.today()
    
    # Count present today
    present_today = g.session.query(Attendance).filter(
        Attendance.timestamp.like(f"{today}%")
    ).count()
    
    # Count absent (students not in today's attendance)
    absent_today = total_students - present_today
    
    # Calculate average attendance
    if total_students > 0:
        avg_attendance = round((present_today / total_students) * 100, 1)
    else:
        avg_attendance = 0
    
    # Count at-risk students (less than 75% attendance)
    at_risk_count = 0
    for student in g.session.query(Student).all():
        attendance_count = g.session.query(Attendance).filter_by(student_id=student.id).count()
        if attendance_count > 0:
            percentage = (attendance_count / (attendance_count + 1)) * 100
            if percentage < 75:
                at_risk_count += 1
    
    return render_template("analytics.html", 
                         total_students=total_students,
                         avg_attendance=avg_attendance,
                         at_risk_count=at_risk_count,
                         total_records=total_records)

# --- Student Directory Route ---
@app.route("/student_directory")
@login_required
def student_directory():
    """Display student directory with attendance profiles"""
    students = g.session.query(Student).all()
    return render_template("student_directory.html", students=students)

# --- Class Management Routes ---
@app.route("/class_management")
@login_required
def class_management():
    """Manage classroom sections and classes"""
    classes = g.session.query(ClassSection).all()
    return render_template("class_management.html", classes=classes)

@app.route("/api/classes", methods=['GET'])
@login_required
def get_classes():
    """Get all classes as JSON"""
    classes = g.session.query(ClassSection).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'instructor': c.instructor,
        'room': c.room,
        'schedule': c.schedule,
        'capacity': c.capacity,
        'color': c.color
    } for c in classes])

@app.route("/api/classes", methods=['POST'])
@login_required
def create_class():
    """Create a new class"""
    data = request.get_json()
    try:
        new_class = ClassSection(
            name=data.get('name'),
            instructor=data.get('instructor'),
            room=data.get('room'),
            schedule=data.get('schedule'),
            capacity=int(data.get('capacity', 40)),
            color=data.get('color', 'blue')
        )
        g.session.add(new_class)
        g.session.commit()
        return jsonify({'success': True, 'id': new_class.id, 'message': 'Class created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route("/api/classes/<int:class_id>", methods=['GET'])
@login_required
def get_class(class_id):
    """Get a specific class"""
    cls = g.session.query(ClassSection).filter_by(id=class_id).first()
    if cls:
        return jsonify({
            'id': cls.id,
            'name': cls.name,
            'instructor': cls.instructor,
            'room': cls.room,
            'schedule': cls.schedule,
            'capacity': cls.capacity,
            'color': cls.color
        })
    return jsonify({'error': 'Class not found'}), 404

@app.route("/api/classes/<int:class_id>", methods=['PUT'])
@login_required
def update_class(class_id):
    """Update a class"""
    cls = g.session.query(ClassSection).filter_by(id=class_id).first()
    if not cls:
        return jsonify({'error': 'Class not found'}), 404
    
    data = request.get_json()
    try:
        cls.name = data.get('name', cls.name)
        cls.instructor = data.get('instructor', cls.instructor)
        cls.room = data.get('room', cls.room)
        cls.schedule = data.get('schedule', cls.schedule)
        cls.capacity = int(data.get('capacity', cls.capacity))
        cls.color = data.get('color', cls.color)
        g.session.commit()
        return jsonify({'success': True, 'message': 'Class updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route("/api/classes/<int:class_id>", methods=['DELETE'])
@login_required
def delete_class(class_id):
    """Delete a class"""
    cls = g.session.query(ClassSection).filter_by(id=class_id).first()
    if not cls:
        return jsonify({'error': 'Class not found'}), 404
    
    try:
        g.session.delete(cls)
        g.session.commit()
        return jsonify({'success': True, 'message': 'Class deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# --- Reports Route ---
@app.route("/reports")
@login_required
def reports():
    """Generate attendance reports"""
    total_students = g.session.query(Student).count()
    today = datetime.date.today()
    
    present_today = g.session.query(Attendance).filter(
        Attendance.timestamp.like(f"{today}%")
    ).count()
    
    absent_today = total_students - present_today
    
    if total_students > 0:
        percentage = round((present_today / total_students) * 100, 1)
    else:
        percentage = 0
    
    return render_template("reports.html",
                         total_students=total_students,
                         present_today=present_today,
                         absent_today=absent_today,
                         attendance_percentage=percentage)

# --- API: Get Daily Attendance Stats ---
@app.route("/api/daily_stats")
@login_required
def get_daily_stats():
    """API endpoint for daily statistics"""
    today = datetime.date.today()
    total = g.session.query(Student).count()
    present = g.session.query(Attendance).filter(
        Attendance.timestamp.like(f"{today}%")
    ).count()
    
    return jsonify({
        "total": total,
        "present": present,
        "absent": total - present,
        "percentage": round((present / total * 100), 1) if total > 0 else 0
    })

# --- Public Pages (No Login Required) ---
@app.route("/features")
def features():
    """Display features page"""
    return render_template("features.html")

@app.route("/documentation")
def documentation():
    """Display documentation page"""
    return render_template("documentation.html")

@app.route("/faq")
def faq():
    """Display FAQ page"""
    return render_template("faq.html")

@app.route("/contact_us")
def contact_us():
    """Display contact us page"""
    return render_template("contact_us.html")

@app.route("/send_contact_message", methods=['POST'])
def send_contact_message():
    """Handle contact form submissions"""
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    organization = request.form.get('organization', '')
    message = request.form.get('message')
    
    # Send emails
    admin_email_sent = send_contact_email(name, email, subject, organization, message)
    user_email_sent = send_contact_confirmation(name, email)
    
    if admin_email_sent and user_email_sent:
        flash(f"Thank you {name}! We received your message. Confirmation sent to {email}.", "success")
    elif admin_email_sent:
        flash(f"Thank you {name}! We received your message (confirmation email pending).", "success")
    else:
        flash(f"Thank you {name}! Your message was received. Please note email notifications are not configured.", "warning")
    
    return redirect(url_for('contact_us'))

# --- Admin Panel Routes ---
@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin_panel():
    """Admin panel dashboard"""
    # Check if user is admin
    if current_user.username != "admin":
        flash("Unauthorized access. Admin rights required.", "danger")
        return redirect(url_for('dashboard'))
    
    stats = {
        'total_students': g.session.query(Student).count(),
        'total_attendance': g.session.query(Attendance).count(),
        'total_users': g.session.query(User).count(),
    }
    
    return render_template("admin/dashboard.html", stats=stats)

@app.route("/admin/students", methods=['GET', 'POST'])
@login_required
def admin_students():
    """Manage students"""
    if current_user.username != "admin":
        flash("Unauthorized access. Admin rights required.", "danger")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        student_id = request.form.get('student_id')
        
        if action == 'delete':
            student = g.session.query(Student).filter_by(id=student_id).first()
            if student:
                g.session.delete(student)
                g.session.commit()
                flash(f"Student {student.name} deleted successfully.", "success")
    
    students = g.session.query(Student).all()
    return render_template("admin/students.html", students=students)

@app.route("/admin/users", methods=['GET', 'POST'])
@login_required
def admin_users():
    """Manage system users"""
    if current_user.username != "admin":
        flash("Unauthorized access. Admin rights required.", "danger")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if action == 'add':
            new_user = User(username=username, password=password)
            g.session.add(new_user)
            g.session.commit()
            flash(f"User {username} created successfully.", "success")
        elif action == 'delete':
            user = g.session.query(User).filter_by(username=username).first()
            if user and user.username != "admin":
                g.session.delete(user)
                g.session.commit()
                flash(f"User {username} deleted successfully.", "success")
    
    users = g.session.query(User).all()
    return render_template("admin/users.html", users=users)

@app.route("/admin/settings")
@login_required
def admin_settings():
    """System settings"""
    if current_user.username != "admin":
        flash("Unauthorized access. Admin rights required.", "danger")
        return redirect(url_for('dashboard'))
    
    return render_template("admin/settings.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
