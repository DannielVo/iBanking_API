from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schemas, models, database
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth", tags=["auth"])
db_dependency = Annotated[Session, Depends(database.get_db)]

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = Depends  # nếu cần JWT auth


@router.post("/token")
def login(form_data: schemas.LoginRequest, db: db_dependency):
    user = db.query(models.Authentication).filter(models.Authentication.username == form_data.username).first()
    if not user or not bcrypt_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.username, user.userId)
    return {"access_token": token, "token_type": "bearer"}


def create_access_token(username: str, user_id: int, expires_delta: timedelta = timedelta(minutes=20)):
    now_ts = int(datetime.now(timezone.utc).timestamp())
    exp_ts = now_ts + int(expires_delta.total_seconds())
    payload = {"sub": username, "id": user_id, "iat": now_ts, "exp": exp_ts}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
