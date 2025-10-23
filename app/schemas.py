# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime

# --- Users ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    class Config:
        orm_mode = True

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Samples ---
class SampleBase(BaseModel):
    barcode: str
    sample_type: Optional[str] = None
    metadata: Optional[Any] = None

class SampleCreate(SampleBase):
    pass

class SampleOut(SampleBase):
    id: int
    project_id: Optional[int] = None
    created_at: datetime
    class Config:
        orm_mode = True
