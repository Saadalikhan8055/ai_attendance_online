from models import get_session, Student, get_engine
from sqlalchemy.orm.exc import NoResultFound

def check_students():
    engine = get_engine()
    session = get_session(engine)
    print("Fetching all existing student IDs...")
    try:
        students = session.query(Student.student_id).all()
        if students:
            print("The following student IDs are already in use:")
            for s_id in students:
                print(s_id[0])
        else:
            print("No students found in the database.")
    except NoResultFound:
        print("No students found in the database.")
    finally:
        session.close()

if __name__ == "__main__":
    check_students()