from .database import engine, Base
from .models import OTP

def init_db():
    Base.metadata.create_all(bind=engine)
    print("OTP DB tables created")

if __name__ == "__main__":
    init_db()
