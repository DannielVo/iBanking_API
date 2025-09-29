from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import pyodbc
from passlib.context import CryptContext
from fastapi import Depends, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

# ===== Cấu hình JWT =====
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Authentication Service")
security = HTTPBearer()

# Cho phép origin từ React
origins = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",   # phòng khi anh mở bằng IP thay vì localhost
    # có thể thêm domain production sau này, ví dụ:
    # "https://mybankingapp.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # danh sách origin được phép
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE...
    allow_headers=["*"],          # cho phép mọi header
)

# OAuth2PasswordBearer sẽ làm Swagger UI hiện nút Authorize
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ================== Logging Config ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================== Global Exception Handler ==================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error. Please try again later."})

# ================== DB Connection ==================
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-PV9Q0OQ\SQLEXPRESS;"
        "DATABASE=AuthenticationDB;"
        "Trusted_Connection=yes;"
    )

# ================== Password Hash ==================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ===== Tạo token =====
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ===== Giải mã và xác thực token =====
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

# ================== Models ==================
class LoginRequest(BaseModel):
    username: str
    password: str

class HashRequest(BaseModel):
    password: str

# ================== Endpoints ==================

@app.post("/auth/hash")
def generate_hash(data: HashRequest):
    try:
        hashed = hash_password(data.password)
        logging.info("Password hashed successfully")
        return {"password": data.password, "hash": hashed}
    except Exception as e:
        logging.error(f"Error generating hash: {e}")
        raise HTTPException(status_code=500, detail="Error generating hash")
    
@app.post("/auth/login")
def login(data: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT userId, customer_id, password_hash FROM authentication WHERE username = ?", (data.username,))
        row = cur.fetchone()
        if not row:
            logging.warning(f"Login failed for non-existent user {data.username}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user_id, customer_id, password_hash = row
        if not verify_password(data.password, password_hash):
            logging.warning(f"Login failed for user {data.username} due to wrong password")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        access_token = create_access_token(data={"sub": data.username})
        return {"access_token": access_token, "token_type": "bearer", "customerId": customer_id}
    finally:
        conn.close()

@app.get("/secure-data")
def get_secure_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)  # Giải mã token
    return {"message": "This is protected data", "user": payload.get("sub")}


# ================== Run ==================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
