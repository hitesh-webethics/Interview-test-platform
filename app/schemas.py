from pydantic import BaseModel
from datetime import datetime

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
