import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.core.permissions import UserRole

class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    email: EmailStr
    role: UserRole = UserRole.OFFICER
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(min_length=8, description="Minimum 8 characters")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
