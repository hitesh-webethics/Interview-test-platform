from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, require_superadmin

router = APIRouter(prefix="/categories", tags=["Categories"])

# Create Category - SuperAdmin and Admin can create
@router.post("/", response_model=schemas.CategoryResponse)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    # Check if user is SuperAdmin or Admin
    if current_user.role.role_name not in ["SuperAdmin", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin and Admin can create categories"
        )
    
    # Check if category name already exists
    existing_category = db.query(models.Category).filter(
        models.Category.name == category.name
    ).first()
    
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists"
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
    # Get category by ID (requires authentication)
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return db_category


# Update category - SuperAdmin and Admin can update
@router.put("/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Check if user is SuperAdmin or Admin
    if current_user.role.role_name not in ["SuperAdmin", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin and Admin can update categories"
        )
    
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
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


# Delete category - SuperAdmin and Admin can delete
@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Check if user is SuperAdmin or Admin
    if current_user.role.role_name not in ["SuperAdmin", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin and Admin can delete categories"
        )
    
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(db_category)
    db.commit()
    
    return {"message": "Category deleted successfully"}