from .database import engine, Base
from .models import Authentication

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Auth DB tables created")

if __name__ == "__main__":
    init_db()
