from sqlalchemy import Column, Integer, String, DateTime, create_engine, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import os

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    student_id = Column(String, unique=True, nullable=False)
    encoding = Column(String, nullable=False)  # store encoding as comma-separated string

    attendances = relationship("Attendance", back_populates="student")

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="attendances")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)  # store hashed password in production

class ClassSection(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    instructor = Column(String, nullable=False)
    room = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    color = Column(String, default="blue")  # blue, green, purple
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def get_engine(db_path=None):
    if db_path:
        # Use provided path (for custom scenarios)
        return create_engine(db_path, connect_args={"check_same_thread": False})
    
    # Check if DATABASE_URL is set (Render provides this)
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Production: Use PostgreSQL
        # Fix the protocol if needed (Render uses postgres://, but SQLAlchemy needs postgresql://)
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return create_engine(database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
    else:
        # Development: Use SQLite
        return create_engine("sqlite:///attendance.db", connect_args={"check_same_thread": False})

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
