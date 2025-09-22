from passlib.context import CryptContext
from sqlalchemy.orm import Session
from auth_service.database import SessionLocal, engine, Base
from auth_service.models import Authentication

# Dùng bcrypt để hash password
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_users():
    Base.metadata.create_all(bind=engine)  # Đảm bảo bảng đã được tạo
    db: Session = SessionLocal()

    users = [
        {"username": "student01", "password": "123456"},
        {"username": "student02", "password": "abcdef"},
        {"username": "admin01", "password": "admin123"},
    ]

    for u in users:
        # Kiểm tra user đã tồn tại chưa
        existing = db.query(Authentication).filter(Authentication.username == u["username"]).first()
        if not existing:
            hashed_pw = bcrypt_context.hash(u["password"])
            new_user = Authentication(username=u["username"], password_hash=hashed_pw)
            db.add(new_user)
            print(f"Inserted user: {u['username']} with password: {u['password']}")

    db.commit()
    db.close()

if __name__ == "__main__":
    init_users()
