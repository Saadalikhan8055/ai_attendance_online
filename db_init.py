from models import Base, get_engine, get_session, User
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import inspect
import os

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    session = get_session(engine)
    # create admin user if not exists
    if not session.query(User).filter_by(username="admin").first():
        admin = User(username="admin", password="admin123")  # change password later
        session.add(admin)
        session.commit()
    print("DB initialized")

if __name__ == "__main__":
    init_db()
