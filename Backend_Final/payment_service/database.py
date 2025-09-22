from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Lấy URL từ biến môi trường hoặc fallback mặc định
DATABASE_URL = os.getenv(
    "AUTH_DATABASE_URL",
    "mssql+pyodbc://@localhost\\MSSQLSERVER01/Payment_Service?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

)

engine = create_engine(DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
