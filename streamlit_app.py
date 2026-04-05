import datetime as dt
import os
import tempfile
from contextlib import contextmanager

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from models import Attendance, Base, ClassSection, Student, User, get_engine, get_session
from recognition import recognize_and_mark, register_student


st.set_page_config(
    page_title="AI Attendance Online",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .hero {
            padding: 1.5rem 1.75rem;
            border-radius: 24px;
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #0284c7 100%);
            color: white;
            box-shadow: 0 24px 48px rgba(15, 23, 42, 0.18);
            margin-bottom: 1.25rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.2rem;
        }
        .hero p {
            margin: 0.4rem 0 0;
            opacity: 0.9;
            font-size: 1rem;
        }
        .section-card {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            background: rgba(255, 255, 255, 0.72);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        }
        .small-muted {
            color: #64748b;
            font-size: 0.92rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_app_engine():
    return get_engine()


engine = get_app_engine()


@contextmanager
def session_scope():
    session = get_session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_database():
    Base.metadata.create_all(engine)
    with session_scope() as session:
        admin = session.query(User).filter_by(username="admin").first()
        if admin is None:
            session.add(User(username="admin", password="admin123"))


def init_state():
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("is_admin", False)


def login_form():
    st.sidebar.header("Sign in")
    with st.sidebar.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        with session_scope() as session:
            user = session.query(User).filter_by(username=username, password=password).first()

        if user:
            st.session_state.authenticated = True
            st.session_state.username = user.username
            st.session_state.is_admin = user.username == "admin"
            st.rerun()

        st.sidebar.error("Invalid credentials.")


def logout_button():
    if st.sidebar.button("Sign out"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.rerun()


def show_public_intro():
    st.markdown(
        """
        <div class="hero">
            <h1>AI Attendance Online</h1>
            <p>Streamlit deployment for student registration, face recognition, attendance tracking, and reports.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("Use the default admin account after first launch: admin / admin123")
    st.markdown(
        """
        <div class="section-card">
            <div class="small-muted">Deployment note</div>
            <p style="margin-bottom: 0;">This Streamlit entry point is separate from the Flask app in app.py. Deploy streamlit_app.py to Streamlit Community Cloud or any Streamlit host that supports OpenCV and face_recognition.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def image_to_frame(image_file):
    image = Image.open(image_file).convert("RGB")
    rgb_frame = np.array(image)
    return cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)


def save_uploaded_file(uploaded_file):
    suffix = ".jpg"
    if getattr(uploaded_file, "name", None):
        _, ext = os.path.splitext(uploaded_file.name)
        if ext:
            suffix = ext

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp_file.write(uploaded_file.getbuffer())
        temp_file.flush()
        return temp_file.name
    finally:
        temp_file.close()


def today_window():
    today = dt.date.today()
    start = dt.datetime.combine(today, dt.time.min)
    end = dt.datetime.combine(today, dt.time.max)
    return start, end


def dashboard_page():
    with session_scope() as session:
        total_students = session.query(Student).count()
        total_attendance = session.query(Attendance).count()
        total_classes = session.query(ClassSection).count()
        start, end = today_window()
        present_today = session.query(Attendance).filter(Attendance.timestamp >= start, Attendance.timestamp <= end).count()
        recent_records = session.query(Attendance).order_by(Attendance.timestamp.desc()).limit(10).all()

    attendance_rate = round((present_today / total_students) * 100, 1) if total_students else 0.0
    absent_today = max(total_students - present_today, 0)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", total_students)
    c2.metric("Attendance records", total_attendance)
    c3.metric("Classes", total_classes)
    c4.metric("Today %", f"{attendance_rate}%")
    st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Today's overview")
        st.write(f"Present today: {present_today}")
        st.write(f"Absent today: {absent_today}")
        st.write(f"Logged in as: {st.session_state.username}")

    with right:
        st.subheader("Recent attendance")
        recent_df = pd.DataFrame(
            [
                {
                    "student": record.student.name if record.student else "Unknown",
                    "student_id": record.student.student_id if record.student else "N/A",
                    "timestamp": record.timestamp,
                }
                for record in recent_records
            ]
        )
        st.dataframe(recent_df, use_container_width=True, hide_index=True)


def register_student_page():
    st.subheader("Register a student")
    st.caption("Upload a clear face photo or capture one with the webcam. The image is used for encoding and is not stored permanently.")

    with st.form("register_student_form"):
        name = st.text_input("Student name")
        student_id = st.text_input("Student ID")
        camera_photo = st.camera_input("Webcam capture")
        uploaded_photo = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Register student")

    if submitted:
        image_source = camera_photo or uploaded_photo
        if not name or not student_id or image_source is None:
            st.error("Provide a name, student ID, and photo.")
            return

        temp_path = save_uploaded_file(image_source)
        try:
            with session_scope() as session:
                register_student(temp_path, name, student_id, session=session)
            st.success("Student registered successfully.")
        except Exception as exc:
            st.error(f"Registration failed: {exc}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def capture_attendance_page():
    st.subheader("Mark attendance")
    st.caption("Capture a frame with the webcam or upload a still image for recognition.")

    camera_image = st.camera_input("Webcam capture")
    uploaded_frame = st.file_uploader("Or upload a photo", type=["jpg", "jpeg", "png"], key="attendance_upload")
    image_source = camera_image or uploaded_frame

    if st.button("Run recognition", type="primary"):
        if image_source is None:
            st.error("Capture or upload an image first.")
            return

        try:
            frame = image_to_frame(image_source)
            with session_scope() as session:
                matches = recognize_and_mark(frame, session=session)

            matched_students = [entry["matched"]["name"] for entry in matches if entry.get("matched")]
            if matched_students:
                st.success(f"Attendance marked for: {', '.join(matched_students)}")
            else:
                st.info("No face was recognized in the image.")
        except Exception as exc:
            st.error(f"Recognition failed: {exc}")


def students_page():
    st.subheader("Student directory")
    with session_scope() as session:
        students = session.query(Student).order_by(Student.name.asc()).all()

    student_rows = [
        {"id": student.id, "name": student.name, "student_id": student.student_id}
        for student in students
    ]
    st.dataframe(pd.DataFrame(student_rows), use_container_width=True, hide_index=True)

    if st.session_state.is_admin and students:
        st.markdown("### Admin actions")
        student_choices = {f"{student.name} ({student.student_id})": student.id for student in students}
        selected_label = st.selectbox("Select a student to delete", options=list(student_choices.keys()))
        if st.button("Delete student", type="secondary"):
            with session_scope() as session:
                student = session.query(Student).filter_by(id=student_choices[selected_label]).first()
                if student:
                    session.delete(student)
            st.success("Student deleted.")
            st.rerun()


def attendance_records_page():
    st.subheader("Attendance records")
    with session_scope() as session:
        records = session.query(Attendance).order_by(Attendance.timestamp.desc()).all()

    rows = [
        {
            "student": record.student.name if record.student else "Unknown",
            "student_id": record.student.student_id if record.student else "N/A",
            "timestamp": record.timestamp,
        }
        for record in records
    ]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="attendance_export.csv",
        mime="text/csv",
    )


def classes_page():
    st.subheader("Class management")

    with st.form("create_class_form"):
        name = st.text_input("Class name")
        instructor = st.text_input("Instructor")
        room = st.text_input("Room")
        schedule = st.text_input("Schedule")
        capacity = st.number_input("Capacity", min_value=1, value=40, step=1)
        color = st.selectbox("Color", options=["blue", "green", "purple"], index=0)
        submitted = st.form_submit_button("Create class")

    if submitted:
        if not all([name, instructor, room, schedule]):
            st.error("Fill in all class fields.")
        else:
            with session_scope() as session:
                session.add(
                    ClassSection(
                        name=name,
                        instructor=instructor,
                        room=room,
                        schedule=schedule,
                        capacity=int(capacity),
                        color=color,
                    )
                )
            st.success("Class created.")
            st.rerun()

    with session_scope() as session:
        classes = session.query(ClassSection).order_by(ClassSection.created_at.desc()).all()

    class_rows = [
        {
            "id": item.id,
            "name": item.name,
            "instructor": item.instructor,
            "room": item.room,
            "schedule": item.schedule,
            "capacity": item.capacity,
            "color": item.color,
        }
        for item in classes
    ]
    st.dataframe(pd.DataFrame(class_rows), use_container_width=True, hide_index=True)


def reports_page():
    st.subheader("Reports")
    with session_scope() as session:
        total_students = session.query(Student).count()
        total_records = session.query(Attendance).count()
        start, end = today_window()
        present_today = session.query(Attendance).filter(Attendance.timestamp >= start, Attendance.timestamp <= end).count()

    absent_today = max(total_students - present_today, 0)
    attendance_rate = round((present_today / total_students) * 100, 1) if total_students else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total students", total_students)
    c2.metric("Present today", present_today)
    c3.metric("Attendance rate", f"{attendance_rate}%")

    report_df = pd.DataFrame(
        [
            {"metric": "Total students", "value": total_students},
            {"metric": "Present today", "value": present_today},
            {"metric": "Absent today", "value": absent_today},
            {"metric": "Total attendance records", "value": total_records},
        ]
    )
    st.dataframe(report_df, use_container_width=True, hide_index=True)


def main():
    initialize_database()
    init_state()

    show_public_intro()
    login_form()

    if not st.session_state.authenticated:
        st.stop()

    st.sidebar.success(f"Signed in as {st.session_state.username}")
    logout_button()

    page = st.sidebar.radio(
        "Navigate",
        [
            "Dashboard",
            "Register Student",
            "Capture Attendance",
            "Student Directory",
            "Attendance Records",
            "Class Management",
            "Reports",
        ],
    )

    if page == "Dashboard":
        dashboard_page()
    elif page == "Register Student":
        register_student_page()
    elif page == "Capture Attendance":
        capture_attendance_page()
    elif page == "Student Directory":
        students_page()
    elif page == "Attendance Records":
        attendance_records_page()
    elif page == "Class Management":
        classes_page()
    elif page == "Reports":
        reports_page()


if __name__ == "__main__":
    main()