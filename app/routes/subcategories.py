from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/subcategories", tags=["Subcategories"])


# Create Subcategory - Any authenticated user can create
@router.post("/", response_model=schemas.SubcategoryResponse)
def create_subcategory(
    subcategory: schemas.SubcategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if category exists
    category = db.query(models.Category).filter(
        models.Category.id == subcategory.category_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    
    # Check if subcategory with same name exists under the same category
    existing_subcategory = db.query(models.Subcategory).filter(
        models.Subcategory.name == subcategory.name,
        models.Subcategory.category_id == subcategory.category_id
    ).first()
    
    if existing_subcategory:
        raise HTTPException(
            status_code=400,
            detail="Subcategory with this name already exists under this category"
        )
    
    # Create subcategory
    db_subcategory = models.Subcategory(
        name=subcategory.name,
        category_id=subcategory.category_id
    )
    
    db.add(db_subcategory)
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory


# Get all subcategories - Any authenticated user
@router.get("/", response_model=list[schemas.SubcategoryResponse])
def get_subcategories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Subcategory).all()


# Get subcategories by category_id - Any authenticated user
@router.get("/category/{category_id}", response_model=list[schemas.SubcategoryResponse])
def get_subcategories_by_category(
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
    
    # Get all subcategories for this category
    subcategories = db.query(models.Subcategory).filter(
        models.Subcategory.category_id == category_id
    ).all()
    
    return subcategories


# Get single subcategory by ID - Any authenticated user
@router.get("/{subcategory_id}", response_model=schemas.SubcategoryResponse)
def get_subcategory(
    subcategory_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_subcategory = db.query(models.Subcategory).filter(
        models.Subcategory.id == subcategory_id
    ).first()
    
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    return db_subcategory


# Update subcategory - Any authenticated user can update
@router.put("/{subcategory_id}", response_model=schemas.SubcategoryResponse)
def update_subcategory(
    subcategory_id: int,
    subcategory: schemas.SubcategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_subcategory = db.query(models.Subcategory).filter(
        models.Subcategory.id == subcategory_id
    ).first()
    
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    # Update name if provided
    if subcategory.name is not None:
        # Check if new name already exists under the same category
        existing = db.query(models.Subcategory).filter(
            models.Subcategory.name == subcategory.name,
            models.Subcategory.category_id == db_subcategory.category_id,
            models.Subcategory.id != subcategory_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Subcategory with this name already exists under this category"
            )
        
        db_subcategory.name = subcategory.name
    
    # Update category_id if provided
    if subcategory.category_id is not None:
        # Check if new category exists
        category = db.query(models.Category).filter(
            models.Category.id == subcategory.category_id
        ).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        db_subcategory.category_id = subcategory.category_id
    
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory


# Delete subcategory - Only Admin can delete
@router.delete("/{subcategory_id}")
def delete_subcategory(
    subcategory_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    db_subcategory = db.query(models.Subcategory).filter(
        models.Subcategory.id == subcategory_id
    ).first()
    
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    db.delete(db_subcategory)
    db.commit()
    
    return {"message": "Subcategory deleted successfully"}