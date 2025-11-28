from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
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
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Category not found"
        })

    # Validate subcategory if provided
    if question.sub_category_id is not None:
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == question.sub_category_id
        ).first()
        if not subcategory:
            return JSONResponse(status_code=404, content = {
                "status" : 404,
                "error" : "Subcategory not found"
            })

        # Ensure subcategory belongs to the specified category
        if subcategory.category_id != question.category_id:
            return JSONResponse(
                status_code=400,
                content = {
                    "status" : 400,
                    "error" : "Subcategory does not belong to the specified category"
                }
            )

    # Validate correct_option is one of the option keys
    if question.correct_option not in question.options:
        return JSONResponse(
            status_code=400,
            content = {
                "status" : 400,
                "error" : f"correct option '{question.correct_option}' must be one of the option keys"
            }
        )

    # Validate correct_option is a single character
    if len(question.correct_option) != 1:
        return JSONResponse(
            status_code=400,
            content = {
                "status" : 400,
                "error" : "correct option must be a single character (e.g., 'a', 'b', 'c', 'd')"
            }
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


# Get all questions with optional filters - Any authenticated user
@router.get("/", response_model=list[schemas.QuestionResponse])
def get_questions(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    sub_category_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
    difficulty: Optional[schemas.DifficultyEnum] = Query(None, description="Filter by difficulty: Easy, Medium, or Hard"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Start with base query
    query = db.query(models.Question)

    # Apply category filter if provided
    if category_id is not None:
        # Validate category exists
        category = db.query(models.Category).filter(
            models.Category.id == category_id
        ).first()
        if not category:
            return JSONResponse(status_code=404, content = {
                "status" : 404,
                "error" : "Category not found"
            })
        
        query = query.filter(models.Question.category_id == category_id)

    # Apply subcategory filter if provided
    if sub_category_id is not None:
        # Validate subcategory exists
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == sub_category_id
        ).first()
        if not subcategory:
            return JSONResponse(status_code=404, content = {
                "status" : 404,
                "error" : "Subcategory not found"
            })

        # If category_id is also provided, ensure subcategory belongs to it
        if category_id is not None and subcategory.category_id != category_id:
            return JSONResponse(
                status_code=400,
                content = {
                    "status" : 400,
                    "error" : "Subcategory does not belong to the specified category"
                })
        
        query = query.filter(models.Question.sub_category_id == sub_category_id)

    # Apply difficulty filter if provided
    if difficulty is not None:
        query = query.filter(models.Question.difficulty == difficulty.value)

    # Execute query
    questions = query.all()

    # Convert options from JSON string to dict for each question
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
    # Get a specific question by ID

    db_question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()

    if not db_question:
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Question not found"
        })

    # Convert options from JSON string to dict
    db_question.options = json.loads(db_question.options)

    return db_question


# Update question - Admin or creator can update
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
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Question not found"
        })

    # Check authorization: Admin or creator
    if current_user.role.role_name != "Admin" and db_question.user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content = {
                "status" : 403,
                "error" : "You can only update your own questions"
            }
        )

    # Update category_id if provided
    if question.category_id is not None:
        category = db.query(models.Category).filter(
            models.Category.id == question.category_id
        ).first()
        if not category:
            return JSONResponse(status_code=404, content = {
                "status" : 404,
                "error" : "Category not found"
            })
        db_question.category_id = question.category_id

    # Update sub_category_id if provided
    if question.sub_category_id is not None:
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == question.sub_category_id
        ).first()
        if not subcategory:
            return JSONResponse(status_code=404, content = {
                "status" : 404,
                "error" : "Subcategory not found"
            })

        # Ensure subcategory belongs to the category
        if subcategory.category_id != db_question.category_id:
            return JSONResponse(
                status_code=400,
                content = {
                    "status" : 400,
                    "error" : "Subcategory does not belong to the question's category"
                }
            )
        db_question.sub_category_id = question.sub_category_id

    # Update question_text if provided
    if question.question_text is not None:
        db_question.question_text = question.question_text

    # Update options if provided
    if question.options is not None:
        # Validate correct_option still exists in new options if correct_option not being updated
        if question.correct_option is None and db_question.correct_option not in question.options:
            return JSONResponse(
                status_code=400,
                content = {
                    "status" : 400,
                    "error" : f"Current correct option '{db_question.correct_option}' must exist in new options"
                })
        db_question.options = json.dumps(question.options)

    # Update correct_option if provided
    if question.correct_option is not None:
        # Validate it exists in options
        current_options = json.loads(db_question.options)
        if question.correct_option not in current_options:
            return JSONResponse(
                status_code=400,
                content = {
                    "status" : 400,
                    "error" : "correct option must be one of the option keys"
                })

        # Validate single character
        if len(question.correct_option) != 1:
            return JSONResponse(
                status_code=400,
                content = {
                    "status" : 400,
                    "error" : "correct option must be a single character"
                })

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
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Question not found"
        })

    db.delete(db_question)
    db.commit()

    return {"message": "Question deleted successfully"}