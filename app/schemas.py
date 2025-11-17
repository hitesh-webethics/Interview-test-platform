from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Login Schema
class UserLogin(BaseModel):
    email: str
    password: str

# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str

# Token Data
class TokenData(BaseModel):
    user_id: Optional[int] = None


# Role Schemas
class RoleBase(BaseModel):
    role_name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int

    class Config:
        orm_mode = True

# User Schemas
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str
    role_id: int

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    role_id: int | None = None

class UserResponse(UserBase):
    id: int
    role: RoleResponse
    created_at: datetime

    class Config:
        orm_mode = True


# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
