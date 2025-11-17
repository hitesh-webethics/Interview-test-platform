from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import require_superadmin, get_current_user

router = APIRouter(prefix="/roles", tags=["Roles"])

# Create Role - Only SuperAdmin
@router.post("/", response_model=schemas.RoleResponse)
def create_role(
    role: schemas.RoleCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_superadmin)  # Must be SuperAdmin
):
    # Create new role (SuperAdmin only)
    db_role = models.Role(role_name=role.role_name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

# Get all roles - Any authenticated user
@router.get("/", response_model=list[schemas.RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Must be logged in
):
    # Get all roles (requires authentication)
    return db.query(models.Role).all()

# Get Role by ID - Any authenticated user
@router.get("/{role_id}", response_model=schemas.RoleResponse)
def get_role(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Must be logged in
):
    # Get role by ID (requires authentication)
    db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

# Update Role - Only SuperAdmin
@router.put("/{role_id}", response_model=schemas.RoleResponse)
def update_role(
    role_id: int, 
    role: schemas.RoleCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_superadmin)  # Must be SuperAdmin
):
    # Update role (SuperAdmin only)
    db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    db_role.role_name = role.role_name
    db.commit()
    db.refresh(db_role)
    return db_role

# Delete Role - Only SuperAdmin
@router.delete("/{role_id}")
def delete_role(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_superadmin)  # Must be SuperAdmin
):
    # Delete role (SuperAdmin only)
    db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    db.delete(db_role)
    db.commit()
    
    check_role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if check_role:
        raise HTTPException(status_code=500, detail="Role not deleted due to dependency or DB issue")
    
    return {"message": "Role deleted successfully"}