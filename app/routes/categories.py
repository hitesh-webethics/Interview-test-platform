from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/categories", tags=["Categories"])

# Create Category - Any authenticated user can create
@router.post("/", response_model=schemas.CategoryResponse)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Trim whitespace
    category_name = category.name.strip()
    
    # Case-insensitive uniqueness check
    existing_category = db.query(models.Category).filter(
        func.lower(models.Category.name) == func.lower(category_name)
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists."
        )
    
    # Create category
    db_category = models.Category(
        name=category.name,
        description=category.description,
        user_id=current_user.id
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Get all categories - Any authenticated user
@router.get("/", response_model=list[schemas.CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Category).all()

# Get single category by ID - Any authenticated user
@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return db_category

# Update category - Admin can update any, others can update their own
@router.put("/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if user is Admin or category creator
    if current_user.role.role_name != "Admin" and db_category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own categories"
        )
    
    # Update only provided fields
    if category.name is not None:
        # Check if new name already exists
        existing = db.query(models.Category).filter(
            models.Category.name == category.name,
            models.Category.id != category_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Category with this name already exists"
            )
        
        db_category.name = category.name
    
    if category.description is not None:
        db_category.description = category.description
    
    db.commit()
    db.refresh(db_category)
    return db_category

# Delete category - Only Admin can delete
@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(db_category)
    db.commit()
    
    return {"message": "Category deleted successfully"}