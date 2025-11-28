from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/roles", tags=["Roles"])

# Create Role - Only Admin can create
@router.post("/", response_model=schemas.RoleResponse)
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    # Check if role already exists
    existing_role = db.query(models.Role).filter(
        models.Role.role_name == role.role_name
    ).first()

    if existing_role:
        return JSONResponse(
            status_code=400,
            content = {
                "status" : 400,
                "error" : "Role with this name already exists"
            }
        )

    # Create new role (Admin only)
    db_role = models.Role(role_name=role.role_name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

# Get all roles - Any authenticated user
@router.get("/", response_model=list[schemas.RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Role).all()

# Get Role by ID - Any authenticated user
@router.get("/{role_id}", response_model=schemas.RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not db_role:
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Role not found"
        })
    return db_role

# Delete Role
@router.delete("/{role_id}")
def delete_role(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)  # Must be Admin
):
    # Delete role (Admin only)
    db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not db_role:
        return JSONResponse(status_code=404, content = {
            "status" : 404,
            "error" : "Role not found"
        })

    db.delete(db_role)
    db.commit()

    check_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if check_role:
        return JSONResponse(status_code=500, content = {
            "status" : 500,
            "error" : "Role not deleted due to dependency or DB issue"
        })

    return {"message": "Role deleted successfully"}