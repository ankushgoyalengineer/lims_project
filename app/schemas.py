# app/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Any, Dict
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

    model_config = ConfigDict(from_attributes=True)

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshIn(BaseModel):
    refresh_token: str
    device_id: Optional[str] = None

# --- Samples ---
class SampleBase(BaseModel):
    barcode: str
    sample_type: Optional[str] = None
    metadata: Optional[Any] = None

class SampleCreate(BaseModel):
    barcode: str
    sample_type: Optional[str] = None
    project_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class SampleOut(BaseModel):
    id: int
    barcode: str
    sample_type: Optional[str]
    project_id: Optional[int]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Projects ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    owner_email: Optional[str] = None

class ProjectOut(ProjectBase):
    id: int
    owner_email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: Optional[str] = None
    revoked: bool
    created_at: datetime
    expires_at: Optional[datetime] = None