from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, Dict, List
import json
from enum import Enum

# Login Schema
class UserLogin(BaseModel):
    email: str = Field(..., min_length=1, description="User email address")
    password: str = Field(..., min_length=1, description="User password")

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
    role_name: str = Field(..., min_length=1, description="Role name cannot be empty")

class RoleResponse(RoleBase):
    id: int

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    role_id: int = Field(..., description="Role ID (required)")

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
    question_count: Optional[int] = 0

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
    question_count: Optional[int] = 0

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


# CANDIDATE & RESPONSE SCHEMAS (SIMPLIFIED)

# Individual Answer Item
class AnswerItem(BaseModel):
    questionId: str
    selected: str


# Candidate Submission
class CandidateCreate(BaseModel):
    testId: str
    name: str
    email: EmailStr
    timeTaken: int
    answers: List[AnswerItem]


# Basic Candidate Response
class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    test_id: int
    time_taken: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Question Breakdown for Results
class QuestionBreakdown(BaseModel):
    question_id: str
    question_text: str
    selected_option: str
    correct_option: str
    is_correct: bool
    options: Dict[str, str]
    difficulty: str
    category_name: str
    subcategory_name: Optional[str] = None


# Candidate Detail with Score
class CandidateDetailResponse(BaseModel):
    id: int
    name: str
    email: str
    test_id: int
    test_code: str
    time_taken: int
    time_taken_formatted: str
    total_questions: int
    correct_answers: int
    score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# Full Result Response
class CandidateResultResponse(BaseModel):
    candidate: CandidateDetailResponse
    responses: List[QuestionBreakdown]


# Dashboard List Item
class CandidateListItem(BaseModel):
    id: int
    name: str
    email: str
    test_code: str
    score: str
    score_percentage: int
    time_taken_formatted: str
    created_at: datetime