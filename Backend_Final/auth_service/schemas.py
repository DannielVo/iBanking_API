from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str
