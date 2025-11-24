from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
import json

router = APIRouter(prefix="/tests", tags=["Tests"])


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
    
    # Validate subcategry
    if sub_category_id is not None:
        subcategory = db.query(models.Subcategory).filter(
            models.Subcategory.id == sub_category_id
        ).first()
        
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        
        # Check subcategory belongs to the specified category
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

