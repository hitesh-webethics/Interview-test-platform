from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, require_creator_or_admin
import json
import uuid

router = APIRouter(prefix="/tests", tags=["Tests"])


def generate_test_code() -> str:
    # Generate a unique test code using UUID
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


# Get questions for test creation (unchanged - still useful for fetching questions)
@router.get("/questions", response_model=list[schemas.QuestionResponse])
def get_test_questions(
    category_id: int = Query(..., description="Category ID (required)"),
    difficulty: schemas.DifficultyEnum = Query(..., description="Difficulty level: Easy, Medium, or Hard"),
    sub_category_id: Optional[int] = Query(None, description="Subcategory ID (optional)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Get questions for test creation based on category, subcategory (optional), and difficulty
    
    # **category_id**: Required - The category to fetch questions from
    # **difficulty**: Required - Easy, Medium, or Hard
    # **sub_category_id**: Optional - If provided, fetches from specific subcategory, otherwise from entire category
    
    # Returns all matching questions
    
    # Validate category exists
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Build base query
    query = db.query(models.Question).filter(
        models.Question.category_id == category_id,
        models.Question.difficulty == difficulty.value
    )
    
    # If subcategory is provided, validate and filter by it
    if sub_category_id is not None:
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == sub_category_id
        ).first()
        
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        
        # Ensure subcategory belongs to the specified category
        if subcategory.category_id != category_id:
            raise HTTPException(
                status_code=400,
                detail="Subcategory does not belong to the specified category"
            )
        
        # Filter by subcategory
        query = query.filter(models.Question.sub_category_id == sub_category_id)
    else:
        # If no subcategory specified, get questions directly under category (no subcategory)
        query = query.filter(models.Question.sub_category_id == None)
    
    # Execute query
    questions = query.all()
    
    # Convert options from JSON string to dict for each question
    for question in questions:
        question.options = json.loads(question.options)
    
    return questions


# Create Test - NEW IMPLEMENTATION
@router.post("/create", response_model=schemas.TestResponse)
def create_test(
    test_data: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_creator_or_admin)
):

    # Create a new test with complete question data
    
    # **questions**: Required - List of complete question objects with all details
    
    # The complete question data is stored in the test, so even if questions are deleted later,
    # the test preserves all question information for results and analytics.
    
    # Returns test_id, unique test_code, and question_count
    
    # Validate questions list is not empty
    if not test_data.questions:
        raise HTTPException(
            status_code=400,
            detail="questions list cannot be empty"
        )
    
    # Basic validation: ensure all required fields are present
    for idx, question in enumerate(test_data.questions):
        # Validate answer is not empty
        if not question.answer or not question.answer.strip():
            raise HTTPException(
                status_code=400,
                detail=f"Question at index {idx} has empty answer"
            )
        
        # Validate options is not empty
        if not question.options:
            raise HTTPException(
                status_code=400,
                detail=f"Question at index {idx} has empty options"
            )
        
        # Validate question text is not empty
        if not question.question or not question.question.strip():
            raise HTTPException(
                status_code=400,
                detail=f"Question at index {idx} has empty question text"
            )
        
        # Validate answer exists in options
        if question.answer.upper() not in [key.upper() for key in question.options.keys()]:
            raise HTTPException(
                status_code=400,
                detail=f"Question at index {idx}: answer '{question.answer}' is not in options"
            )
    
    # Generate unique test code using UUID
    test_code = generate_test_code()
    
    # Ensure test code is unique
    while db.query(models.Test).filter(models.Test.test_code == test_code).first():
        test_code = generate_test_code()
    
    # Convert questions data to JSON string for storage
    questions_data_list = []
    for question in test_data.questions:
        question_dict = {
            "question_id": question.question_id,
            "answer": question.answer,
            "options": question.options,
            "category": {
                "id": question.category.id,
                "name": question.category.name,
                "subcategory": question.category.subcategory
            },
            "question": question.question,
            "difficulty": question.difficulty,
            "user_id": question.user_id
        }
        questions_data_list.append(question_dict)
    
    questions_json = json.dumps(questions_data_list)
    
    # Create test
    db_test = models.Test(
        test_code=test_code,
        questions_data=questions_json,
        user_id=current_user.id
    )
    
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    
    # Return response
    return schemas.TestResponse(
        test_id=db_test.id,
        test_code=db_test.test_code,
        question_count=len(test_data.questions)
    )


# Get all tests created by current user
@router.get("/my-tests", response_model=list[schemas.TestDetailResponse])
def get_my_tests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get all tests created by the current user
    
    tests = db.query(models.Test).filter(
        models.Test.user_id == current_user.id
    ).all()
    
    # Convert questions_data from JSON to list for each test
    result = []
    for test in tests:
        questions_data = json.loads(test.questions_data)
        
        # Convert back to TestQuestionData objects
        questions_list = []
        for q in questions_data:
            question_obj = schemas.TestQuestionData(
                question_id=q["question_id"],
                answer=q["answer"],
                options=q["options"],
                category=schemas.QuestionCategory(**q["category"]),
                question=q["question"],
                difficulty=q["difficulty"],
                user_id=q["user_id"]
            )
            questions_list.append(question_obj)
        
        test_dict = {
            "id": test.id,
            "test_code": test.test_code,
            "questions_data": questions_list,
            "user_id": test.user_id,
            "created_at": test.created_at
        }
        result.append(schemas.TestDetailResponse(**test_dict))
    
    return result


# Get test by test_code
@router.get("/{test_code}", response_model=schemas.TestDetailResponse)
def get_test_by_code(
    test_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get test details by test code
    
    db_test = db.query(models.Test).filter(
        models.Test.test_code == test_code
    ).first()
    
    if not db_test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Convert questions_data from JSON to list
    questions_data = json.loads(db_test.questions_data)
    
    # Convert back to TestQuestionData objects
    questions_list = []
    for q in questions_data:
        question_obj = schemas.TestQuestionData(
            question_id=q["question_id"],
            answer=q["answer"],
            options=q["options"],
            category=schemas.QuestionCategory(**q["category"]),
            question=q["question"],
            difficulty=q["difficulty"],
            user_id=q["user_id"]
        )
        questions_list.append(question_obj)
    
    return schemas.TestDetailResponse(
        id=db_test.id,
        test_code=db_test.test_code,
        questions_data=questions_list,
        user_id=db_test.user_id,
        created_at=db_test.created_at
    )