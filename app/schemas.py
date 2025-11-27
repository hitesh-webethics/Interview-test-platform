from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List
import json
from enum import Enum

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
        from_attributes = True

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
        from_attributes = True


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

# Subcategory Schemas
class SubcategoryBase(BaseModel):
    name: str
    category_id: int

class SubcategoryCreate(SubcategoryBase):
    pass

class SubcategoryUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None

class SubcategoryResponse(SubcategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Difficulty Enum
class DifficultyEnum(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


# Question Schemas
class QuestionBase(BaseModel):
    category_id: int
    sub_category_id: Optional[int] = None  # Optional - if None, question is directly under category
    question_text: str
    options: Dict[str, str]  # Example: {"a": "Option A", "b": "Option B", "c": "Option C", "d": "Option D"}
    correct_option: str  # Single character: 'a', 'b', 'c', or 'd'
    difficulty: DifficultyEnum


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    category_id: Optional[int] = None
    sub_category_id: Optional[int] = None
    question_text: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_option: Optional[str] = None
    difficulty: Optional[DifficultyEnum] = None


class QuestionResponse(BaseModel):
    id: int
    category_id: int
    sub_category_id: Optional[int]
    question_text: str
    options: Dict[str, str]  # Will be converted from JSON string
    correct_option: str
    difficulty: str
    user_id: int
    created_at: datetime
    

class QuestionCategory(BaseModel):
    id: int
    name: str
    subcategory: Optional[str] = None
    
    class Config:
        from_attributes = True


# Test Schemas
class TestQuestionData(BaseModel):
    question_id: int
    answer: str
    options: Dict[str, str]  # e.g., {"A": "Option A", "B": "Option B", ...}
    category: QuestionCategory
    question: str
    difficulty: str  # "Easy", "Medium", "Hard"
    user_id: int


# Test Create Schema
class TestCreate(BaseModel):
    questions: List[TestQuestionData]


# Test Response Schema
class TestResponse(BaseModel):
    test_id: int
    test_code: str
    question_count: int
    
    class Config:
        from_attributes = True


# Test Detail Response Schema
class TestDetailResponse(BaseModel):
    id: int
    test_code: str
    questions_data: List[TestQuestionData]  # Returns the complete question array
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
