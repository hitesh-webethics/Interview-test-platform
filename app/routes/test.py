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


















# # Alternative endpoint: Get questions from multiple sources for test
# @router.get("/questions/batch", response_model=dict)
# def get_batch_test_questions(
#     category_ids: str = Query(..., description="Comma-separated category IDs (e.g., '1,2,3')"),
#     difficulty: schemas.DifficultyEnum = Query(..., description="Difficulty level: Easy, Medium, or Hard"),
#     questions_per_category: int = Query(5, description="Number of questions per category (default: 5)"),
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
    
#     # Get questions from multiple categories for test creation
#     # Parse category IDs
#     try:
#         category_id_list = [int(id.strip()) for id in category_ids.split(',')]
#     except ValueError:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid category_ids format. Use comma-separated integers (e.g., '1,2,3')"
#         )
    
#     result = {
#         "difficulty": difficulty.value,
#         "questions_per_category": questions_per_category,
#         "categories": []
#     }
    
#     # Fetch questions for each category
#     for category_id in category_id_list:
#         # Validate category exists
#         category = db.query(models.Category).filter(
#             models.Category.id == category_id
#         ).first()
        
#         if not category:
#             continue  # Skip invalid categories
        
#         # Get questions for this category
#         questions = db.query(models.Question).filter(
#             models.Question.category_id == category_id,
#             models.Question.difficulty == difficulty.value
#         ).limit(questions_per_category).all()
        
#         # Convert options from JSON
#         for question in questions:
#             question.options = json.loads(question.options)
        
#         # Add to result
#         result["categories"].append({
#             "category_id": category_id,
#             "category_name": category.name,
#             "questions_fetched": len(questions),
#             "questions": questions
#         })
    
#     return result