from .database import engine, Base
from .models import Payment

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Payment DB tables created")

if __name__ == "__main__":
    init_db()
