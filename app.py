import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response, jsonify, g
from models import get_engine, get_session, Student, Attendance, User
from recognition import register_student, recognize_and_mark, load_known_encodings
import cv2
import datetime
import pandas as pd
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")
engine = get_engine()

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
    records = g.session.query(Attendance).filter(Attendance.timestamp >= one_minute_ago).all()
    
    log = []
    for r in records:
        log.append({
            'name': r.student.name,
            'timestamp': r.timestamp.strftime('%H:%M:%S')
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
