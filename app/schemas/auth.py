from typing import Optional
from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = "inspector"  # inspector | supervisor | admin
    region: Optional[str] = None
    supervisor_id: Optional[int] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    email: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    region: Optional[str] = None
    supervisor_id: Optional[int] = None
    is_active: bool = True

    class Config:
        from_attributes = True
