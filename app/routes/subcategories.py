from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
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
    current_user: models.User = Depends(require_admin)
):
    # Check if category exists
    category = db.query(models.Category).filter(
        models.Category.id == subcategory.category_id
    ).first()

    if not category:
        return JSONResponse(
            status_code=404,
            content = {
                "status" : 404,
                "error" : "Category not found"
            }
        )

    # Check if subcategory with same name exists under the same category
    existing_subcategory = db.query(models.Subcategory).filter(
        models.Subcategory.name == subcategory.name,
        models.Subcategory.category_id == subcategory.category_id
    ).first()

    if existing_subcategory:
        return JSONResponse(
            status_code=400,
            content = {
                "status" : 400,
                "error" : "Subcategory with this name already exists under this category"
            }
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
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Subcategory not found"
        })

    # Count questions in this specific subcategory
    question_count = db.query(models.Question).filter(
        models.Question.sub_category_id == subcategory_id
    ).count()

    # Add question_count to response
    subcategory_dict = {
        "id": db_subcategory.id,
        "category_id": db_subcategory.category_id,
        "name": db_subcategory.name,
        "created_at": db_subcategory.created_at.isoformat(),
        "question_count": question_count
    }

    return JSONResponse(status_code=200, content=subcategory_dict)

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
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Subcategory not found"
        })

    return db_subcategory


# Update subcategory - Any authenticated user can update
@router.put("/{subcategory_id}", response_model=schemas.SubcategoryResponse)
def update_subcategory(
    subcategory_id: int,
    subcategory: schemas.SubcategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    db_subcategory = db.query(models.Subcategory).filter(
        models.Subcategory.id == subcategory_id
    ).first()

    if not db_subcategory:
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Subcategory not found"
        })

    # Update name if provided
    if subcategory.name is not None:
        # Check if new name already exists under the same category
        existing = db.query(models.Subcategory).filter(
            models.Subcategory.name == subcategory.name,
            models.Subcategory.category_id == db_subcategory.category_id,
            models.Subcategory.id != subcategory_id
        ).first()

        if existing:
            return JSONResponse(
                status_code=400,
                content = {
                    "status" : 400,
                    "error" : "Subcategory with this name already exists under this category"
                }
            )

        db_subcategory.name = subcategory.name

    # Update category_id if provided
    if subcategory.category_id is not None:
        # Check if new category exists
        category = db.query(models.Category).filter(
            models.Category.id == subcategory.category_id
        ).first()

        if not category:
            return JSONResponse(status_code=404, content = {
                "status" : 404,
                "error" : "Category not found"
            })

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
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Subcategory not found"
        })

    db.delete(db_subcategory)
    db.commit()

    return {"message": "Subcategory deleted successfully"}