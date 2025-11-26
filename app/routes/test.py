from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
import json
import uuid

router = APIRouter(prefix="/tests", tags=["Tests"])


def generate_test_code() -> str:
    # Generate a unique test code using UUID
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


# Get questions for test creation
@router.get("/questions", response_model=list[schemas.QuestionResponse])
def get_test_questions(
    category_id: int = Query(..., description="Category ID (required)"),
    difficulty: schemas.DifficultyEnum = Query(..., description="Difficulty level: Easy, Medium, or Hard"),
    sub_category_id: Optional[int] = Query(None, description="Subcategory ID (optional)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Get questions for test creation based on category, subcategory (optional), and difficulty
    
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


# Create Test
@router.post("/create", response_model=schemas.TestResponse)
def create_test(
    test_data: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Create a new test with selected questions
    
    # **category_id**: Required - Category for the test
    # **sub_category_id**: Optional - Subcategory for the test
    # **difficulty**: Required - Difficulty level (Easy, Medium, Hard)
    # **selected_question_ids**: Required - List of question IDs to include in test
    
    # Returns test_id, unique test_code, and question_count
    
    # Validate selected_question_ids is not empty
    if not test_data.selected_question_ids:
        raise HTTPException(
            status_code=400,
            detail="selected_question_ids cannot be empty"
        )
    
    # Validate category exists
    category = db.query(models.Category).filter(
        models.Category.id == test_data.category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Validate subcategory if provided
    if test_data.sub_category_id is not None:
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == test_data.sub_category_id
        ).first()
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        
        # Ensure subcategory belongs to the category
        if subcategory.category_id != test_data.category_id:
            raise HTTPException(
                status_code=400,
                detail="Subcategory does not belong to the specified category"
            )
    
    # Validate all questions exist and match the criteria
    questions = db.query(models.Question).filter(
        models.Question.id.in_(test_data.selected_question_ids)
    ).all()
    
    # Check if all question IDs were found
    found_question_ids = {q.id for q in questions}
    missing_ids = set(test_data.selected_question_ids) - found_question_ids
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Questions not found: {list(missing_ids)}"
        )
    
    # Validate each question belongs to the correct category, subcategory, and difficulty
    for question in questions:
        # Check category
        if question.category_id != test_data.category_id:
            raise HTTPException(
                status_code=400,
                detail=f"Question {question.id} does not belong to category {test_data.category_id}"
            )
        
        # Check subcategory
        if test_data.sub_category_id is not None:
            if question.sub_category_id != test_data.sub_category_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Question {question.id} does not belong to subcategory {test_data.sub_category_id}"
                )
        else:
            # If no subcategory specified, ensure question also has no subcategory
            if question.sub_category_id is not None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Question {question.id} belongs to a subcategory but test has no subcategory"
                )
        
        # Check difficulty
        if question.difficulty not in [d.value for d in test_data.difficulty]:
            raise HTTPException(
                status_code=400,
                detail=f"Question {question.id} has difficulty '{question.difficulty}' but test requires '{test_data.difficulty.value}'"
            )
    
    # Generate unique test code using UUID
    test_code = generate_test_code()
    
    # Ensure test code is unique (extremely rare collision with UUID, but safety check)
    while db.query(models.Test).filter(models.Test.test_code == test_code).first():
        test_code = generate_test_code()
    
    # Convert question IDs to JSON string for storage
    question_ids_json = json.dumps(test_data.selected_question_ids)
    
    difficulty_json = json.dumps([d.value for d in test_data.difficulty])

    # Create test
    db_test = models.Test(
        test_code=test_code,
        category_id=test_data.category_id,
        sub_category_id=test_data.sub_category_id,
        difficulty = difficulty_json,
        question_ids=question_ids_json,
        user_id=current_user.id,
        is_active=False
    )
    
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    
    # Return response
    return schemas.TestResponse(
        test_id=db_test.id,
        test_code=db_test.test_code,
        question_count=len(test_data.selected_question_ids)
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
    
    # Convert question_ids from JSON to list for each test
    result = []
    for test in tests:
        test_dict = {
            "id": test.id,
            "test_code": test.test_code,
            "category_id": test.category_id,
            "sub_category_id": test.sub_category_id,
            "difficulty": test.difficulty,
            "question_ids": json.loads(test.question_ids),
            "user_id": test.user_id,
            "created_at": test.created_at,
            "is_active": test.is_active
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
    
    # Convert question_ids from JSON to list
    return schemas.TestDetailResponse(
        id=db_test.id,
        test_code=db_test.test_code,
        category_id=db_test.category_id,
        sub_category_id=db_test.sub_category_id,
        difficulty=db_test.difficulty,
        question_ids=json.loads(db_test.question_ids),
        user_id=db_test.user_id,
        created_at=db_test.created_at,
        is_active=db_test.is_active
    )