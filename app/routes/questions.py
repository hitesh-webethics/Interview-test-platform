from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, require_admin
import json

router = APIRouter(prefix="/questions", tags=["Questions"])


# Create Question - Any authenticated user can create
@router.post("/", response_model=schemas.QuestionResponse)
def create_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate category exists
    category = db.query(models.Category).filter(
        models.Category.id == question.category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Validate subcategory if provided
    if question.sub_category_id is not None:
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == question.sub_category_id
        ).first()
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        
        # Ensure subcategory belongs to the specified category
        if subcategory.category_id != question.category_id:
            raise HTTPException(
                status_code=400,
                detail="Subcategory does not belong to the specified category"
            )
    
    # Validate correct_option is one of the option keys
    if question.correct_option not in question.options:
        raise HTTPException(
            status_code=400,
            detail=f"correct_option '{question.correct_option}' must be one of the option keys"
        )
    
    # Validate correct_option is a single character
    if len(question.correct_option) != 1:
        raise HTTPException(
            status_code=400,
            detail="correct_option must be a single character (e.g., 'a', 'b', 'c', 'd')"
        )
    
    # Convert options dict to JSON string for storage
    options_json = json.dumps(question.options)
    
    # Create question
    db_question = models.Question(
        category_id=question.category_id,
        sub_category_id=question.sub_category_id,
        question_text=question.question_text,
        options=options_json,
        correct_option=question.correct_option,
        difficulty=question.difficulty.value,
        user_id=current_user.id
    )
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    # Convert options back to dict for response
    db_question.options = json.loads(db_question.options)
    
    return db_question


# Get all questions - Any authenticated user
@router.get("/", response_model=list[schemas.QuestionResponse])
def get_questions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    questions = db.query(models.Question).all()
    
    # Convert options from JSON string to dict for each question
    for question in questions:
        question.options = json.loads(question.options)
    
    return questions


# Get questions by category - Any authenticated user
@router.get("/category/{category_id}", response_model=list[schemas.QuestionResponse])
def get_questions_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if category exists
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get all questions for this category
    questions = db.query(models.Question).filter(
        models.Question.category_id == category_id
    ).all()
    
    # Convert options from JSON string to dict
    for question in questions:
        question.options = json.loads(question.options)
    
    return questions


# Get questions by subcategory - Any authenticated user
@router.get("/subcategory/{subcategory_id}", response_model=list[schemas.QuestionResponse])
def get_questions_by_subcategory(
    subcategory_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if subcategory exists
    subcategory = db.query(models.Subcategory).filter(
        models.Subcategory.id == subcategory_id
    ).first()
    
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    # Get all questions for this subcategory
    questions = db.query(models.Question).filter(
        models.Question.sub_category_id == subcategory_id
    ).all()
    
    # Convert options from JSON string to dict
    for question in questions:
        question.options = json.loads(question.options)
    
    return questions


# Get questions by difficulty - Any authenticated user
@router.get("/difficulty/{difficulty}", response_model=list[schemas.QuestionResponse])
def get_questions_by_difficulty(
    difficulty: schemas.DifficultyEnum,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    questions = db.query(models.Question).filter(
        models.Question.difficulty == difficulty.value
    ).all()
    
    # Convert options from JSON string to dict
    for question in questions:
        question.options = json.loads(question.options)
    
    return questions


# Get single question by ID - Any authenticated user
@router.get("/{question_id}", response_model=schemas.QuestionResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Convert options from JSON string to dict
    db_question.options = json.loads(db_question.options)
    
    return db_question


# Update question - Any authenticated user can update
@router.put("/{question_id}", response_model=schemas.QuestionResponse)
def update_question(
    question_id: int,
    question: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Update category_id if provided
    if question.category_id is not None:
        category = db.query(models.Category).filter(
            models.Category.id == question.category_id
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        db_question.category_id = question.category_id
    
    # Update sub_category_id if provided
    if question.sub_category_id is not None:
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == question.sub_category_id
        ).first()
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        
        # Ensure subcategory belongs to the category
        if subcategory.category_id != db_question.category_id:
            raise HTTPException(
                status_code=400,
                detail="Subcategory does not belong to the question's category"
            )
        db_question.sub_category_id = question.sub_category_id
    
    # Update question_text if provided
    if question.question_text is not None:
        db_question.question_text = question.question_text
    
    # Update options if provided
    if question.options is not None:
        db_question.options = json.dumps(question.options)
    
    # Update correct_option if provided
    if question.correct_option is not None:
        # Validate it exists in options
        current_options = json.loads(db_question.options)
        if question.correct_option not in current_options:
            raise HTTPException(
                status_code=400,
                detail="correct_option must be one of the option keys"
            )
        db_question.correct_option = question.correct_option
    
    # Update difficulty if provided
    if question.difficulty is not None:
        db_question.difficulty = question.difficulty.value
    
    db.commit()
    db.refresh(db_question)
    
    # Convert options back to dict for response
    db_question.options = json.loads(db_question.options)
    
    return db_question


# Delete question - Only Admin can delete
@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    db_question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()
    
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(db_question)
    db.commit()
    
    return {"message": "Question deleted successfully"}