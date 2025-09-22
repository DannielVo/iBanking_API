from sqlalchemy import Column, Integer, String
from .database import Base

class Authentication(Base):
    __tablename__ = "Authentication"

    userId = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
