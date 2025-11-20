from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import hash_password, get_current_user, require_superadmin

router = APIRouter(prefix="/users", tags=["Users"])

# Create User - Only SuperAdmin can create users
@router.post("/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_superadmin)  # Must be SuperAdmin
):

    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Create user with hashed password
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password,  # Store hashed password
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Get all Users - Any authenticated user can view
@router.get("/", response_model=list[schemas.UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Must be logged in
):
    # Get all users (requires authentication)
    return db.query(models.User).all()

# Get User by ID - Any authenticated user can view
@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Must be logged in
):
    # Get single user by ID (requires authentication)
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Update User - Can only update yourself
@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int, 
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Must be logged in
):
    # Check if user is updating themselves
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    if user.name is not None:
        db_user.name = user.name
    
    if user.email is not None:
        db_user.email = user.email
    
    if user.password is not None:
        db_user.password = hash_password(user.password)  # Hash new password
    
    if user.role_id is not None:
        db_user.role_id = user.role_id
    
    db.commit()
    db.refresh(db_user)
    return db_user

# Delete User - Only SuperAdmin can delete Admin users
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_superadmin)  # Must be SuperAdmin
):

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if target user is Admin
    if db_user.role.role_name != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SuperAdmin can only delete Admin users"
        )
    
    db.delete(db_user)
    db.commit()
    
    return {"message": "User deleted successfully"}