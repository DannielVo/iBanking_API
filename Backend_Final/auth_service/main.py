import uvicorn
from fastapi import FastAPI
from .auth_router import router as auth_router

app = FastAPI(title="Auth Service")
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("auth_service.main:app", host="0.0.0.0", port=8002, reload=True)
