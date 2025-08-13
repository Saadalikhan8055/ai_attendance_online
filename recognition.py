import face_recognition
import numpy as np
import cv2
from models import get_engine, get_session, Student, Attendance
import ast

def encoding_to_str(enc):
    return ",".join(map(str, enc.tolist()))

def str_to_encoding(s):
    return np.array(list(map(float, s.split(","))))

def register_student(image_path, name, student_id, session=None):
    # load image and compute encoding
    image = face_recognition.load_image_file(image_path)
    encs = face_recognition.face_encodings(image)
    if len(encs) == 0:
        raise ValueError("No face found in the image.")
    encoding = encs[0]
    enc_str = encoding_to_str(encoding)

    # save to DB
    student = Student(name=name, student_id=student_id, encoding=enc_str)
    session.add(student)
    return student

def load_known_encodings(session):
    students = session.query(Student).all()
    encodings = []
    meta = []
    for s in students:
        enc = str_to_encoding(s.encoding)
        encodings.append(enc)
        meta.append({"id": s.id, "name": s.name, "student_id": s.student_id})
    return encodings, meta

def recognize_and_mark(frame, session, tolerance=0.6):
    # input: BGR OpenCV frame
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)

    known_encodings, known_meta = load_known_encodings(session)
    matches_info = []

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=tolerance)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding) if known_encodings else []
        best_match_index = None
        if len(face_distances) > 0:
            best_match_index = int(np.argmin(face_distances))
        matched_student = None
        if best_match_index is not None and matches and matches[best_match_index]:
            meta = known_meta[best_match_index]
            # mark attendance
            student = session.query(Student).filter_by(id=meta["id"]).first()
            from models import Attendance
            a = Attendance(student=student)
            session.add(a)
            matched_student = meta
        matches_info.append({"location": face_location, "matched": matched_student})
    return matches_info