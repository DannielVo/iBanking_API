# auth.py
from datetime import timezone, datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette import status
from database import SessionLocal
from models import Authentication
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
import redis

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# --- CONFIG ---
SECRET_KEY = "058b552005ae4ed8a18808b455a6d832ca62d851c8ee6625079bab8af69ca9d6"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Note: tokenUrl should be the absolute path where the token is obtained
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Redis để quản lý token blacklist (DB index 1 dành cho blacklist)
redis_client = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)


# ---------------------- MODELS ----------------------
class CreateUserRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


# ---------------------- DB DEPENDENCY ----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


# ---------------------- CREATE USER ----------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    """
    Create a new user (Authentication table).
    """
    try:
        hashed_pw = bcrypt_context.hash(create_user_request.password)
        new_user = Authentication(
            username=create_user_request.username,
            hashed_password=hashed_pw,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.userid, "username": new_user.username}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )


# ---------------------- LOGIN ----------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    """
    Exchange username/password for a JWT access token.
    Token lifetime = 20 minutes by default.
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user."
        )
    token = create_access_token(user.username, user.userid, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}


# ---------------------- LOGOUT ----------------------
@router.post("/logout")
async def logout(request: Request, token: Annotated[str, Depends(oauth2_bearer)]):
    """
    Logout: put current token into Redis blacklist with TTL = remaining lifetime.
    """
    try:
        # Decode without verifying expiry to get exp (but jose will still verify by default).
        # We'll use jwt.decode which validates exp; if expired it will raise ExpiredSignatureError.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(status_code=400, detail="Invalid token (no exp)")

        now_ts = int(datetime.now(timezone.utc).timestamp())
        ttl = int(exp) - now_ts
        if ttl <= 0:
            # token already expired; no need to blacklist but respond success
            return {"message": "Token already expired"}

        # Store token in blacklist with TTL (seconds)
        redis_client.setex(f"blacklist:{token}", ttl, "true")

        return {"message": "Logout successful"}
    except ExpiredSignatureError:
        # token already expired
        return {"message": "Token already expired"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ---------------------- HELPER FUNCTIONS ----------------------
def authenticate_user(username: str, password: str, db: Session):
    """
    Authenticate against Authentication table.
    Returns the user object or False.
    """
    user = db.query(Authentication).filter(Authentication.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    """
    Create JWT and set 'exp' as integer timestamp (seconds since epoch).
    """
    now_ts = int(datetime.now(timezone.utc).timestamp())
    exp_ts = now_ts + int(expires_delta.total_seconds())
    payload = {
        "sub": username,
        "id": user_id,
        "iat": now_ts,
        "exp": exp_ts
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """
    Dependency to get current user from token.
    Checks blacklist first, then verifies token and returns a dict with username and id.
    """
    # Check blacklist
    if redis_client.get(f"blacklist:{token}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user."
            )
        return {"username": username, "id": user_id}
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
