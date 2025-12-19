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
    current_user: models.User = Depends(require_admin)
):
    # Validate question_text is not empty
    if not question.question_text or not question.question_text.strip():
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": "question_text is a required field and cannot be empty"
            }
        )

    # Validate options is not empty
    if not question.options or len(question.options) == 0:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": "options is a required field and cannot be empty"
            }
        )

    # Validate each option value is not empty
    for key, value in question.options.items():
        if not value or not value.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": f"Option '{key}' cannot be empty"
                }
            )

    # Validate correct_option is not empty
    if not question.correct_option or not question.correct_option.strip():
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": "correct_option is a required field and cannot be empty"
            }
        )

    # Validate category exists
    category = db.query(models.Category).filter(
        models.Category.id == question.category_id
    ).first()
    if not category:
        return JSONResponse(status_code=404, content={
            "status": 404,
            "error": "Category not found"
        })

    # Validate subcategory if provided
    # Subcategory removed - merged into Category
    # if question.sub_category_id is not None:
        # ... validation logic removed ...

    # Validate correct_option is one of the option keys
    if question.correct_option not in question.options:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": f"correct_option '{question.correct_option}' must be one of the option keys"
            }
        )

    # Validate correct_option is a single character
    if len(question.correct_option) != 1:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": "correct_option must be a single character (e.g., 'a', 'b', 'c', 'd')"
            }
        )

    # Convert options dict to JSON string for storage
    options_json = json.dumps(question.options)

    # Create question
    db_question = models.Question(
        category_id=question.category_id,
        # sub_category_id removed
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
@router.get("/", response_model=schemas.QuestionPaginatedResponse)
@router.get("/", response_model=schemas.QuestionPaginatedResponse)
def get_questions(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    # sub_category_id argument removed
    difficulty: Optional[schemas.DifficultyEnum] = Query(None, description="Filter by difficulty: Easy, Medium, or Hard"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
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

        query = query.filter(models.Question.category_id == category_id)

    # Subcategory filter removed

    # Apply difficulty filter if provided
    if difficulty is not None:
        query = query.filter(models.Question.difficulty == difficulty.value)

    # Get total count before pagination
    total = query.count()

    # Calculate skip value
    skip = (page - 1) * per_page

    # Execute query with pagination
    questions = query.offset(skip).limit(per_page).all()

    # Build response with category and subcategory names
    result = []
    for question in questions:
        # Get category name
        category = db.query(models.Category).filter(
            models.Category.id == question.category_id
        ).first()
        category_name = category.name if category else "Unknown"

        # Get subcategory name (if exists)
        # subcategory_name removed

        # Convert options from JSON string to dict
        options_dict = json.loads(question.options)

        # Build response dict
        question_dict = {
            "id": question.id,
            "category_id": question.category_id,
            # "sub_category_id": question.sub_category_id,
            "category_name": category_name,  # ← NEW
            # "subcategory_name": subcategory_name,  # ← NEW
            "question_text": question.question_text,
            "options": options_dict,
            "correct_option": question.correct_option,
            "difficulty": question.difficulty,
            "user_id": question.user_id,
            "created_at": question.created_at.isoformat()
        }
        result.append(question_dict)

    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": per_page
    }


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


    # Get category and subcategory names
    # Get category name
    category = db.query(models.Category).filter(
        models.Category.id == db_question.category_id
    ).first()
    category_name = category.name if category else "Unknown"

    # Get subcategory name (if exists)
    # subcategory_name removed

    # Convert options from JSON string to dict
    options_dict = json.loads(db_question.options)

    # Build response dict
    question_dict = {
        "id": db_question.id,
        "category_id": db_question.category_id,
        # "sub_category_id": db_question.sub_category_id,
        "category_name": category_name,  # ← NEW
        # "subcategory_name": subcategory_name,  # ← NEW
        "question_text": db_question.question_text,
        "options": options_dict,
        "correct_option": db_question.correct_option,
        "difficulty": db_question.difficulty,
        "user_id": db_question.user_id,
        "created_at": db_question.created_at.isoformat()
    }

    return question_dict

# Update question - Admin or creator can update
@router.put("/{question_id}", response_model=schemas.QuestionResponse)
def update_question(
    question_id: int,
    question: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)  # ✅ Only Admin can update questions
):
    db_question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()

    if not db_question:
        return JSONResponse(status_code=404, content={
            "status": 404,
            "error": "Question not found"
        })

    # Validate question_text if provided
    if question.question_text is not None:
        if not question.question_text.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "'question_text' cannot be empty"
                }
            )
        db_question.question_text = question.question_text

    # Validate options if provided
    if question.options is not None:
        if len(question.options) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "'options' cannot be empty"
                }
            )

        # Validate each option value is not empty
        for key, value in question.options.items():
            if not value or not value.strip():
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": 400,
                        "error": f"Option '{key}' cannot be empty"
                    }
                )

        # Validate correct_option still exists in new options if correct_option not being updated
        if question.correct_option is None and db_question.correct_option not in question.options:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": f"Current correct_option '{db_question.correct_option}' must exist in new options"
                }
            )
        db_question.options = json.dumps(question.options)

    # Validate correct_option if provided
    if question.correct_option is not None:
        if not question.correct_option.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "'correct_option' cannot be empty"
                }
            )

        # Validate single character
        if len(question.correct_option) != 1:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "correct_option must be a single character"
                }
            )

        # Validate it exists in options
        current_options = json.loads(db_question.options)
        if question.correct_option not in current_options:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "correct_option must be one of the option keys"
                }
            )

        db_question.correct_option = question.correct_option

    # Update category_id if provided
    if question.category_id is not None:
        category = db.query(models.Category).filter(
            models.Category.id == question.category_id
        ).first()
        if not category:
            return JSONResponse(status_code=404, content={
                "status": 404,
                "error": "Category not found"
            })
        db_question.category_id = question.category_id

    # Update sub_category_id if provided
    # sub_category_id removed

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