from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import hash_password, get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["Users"])

# CREATE USER - Public (No authentication required)
@router.post("/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    # Public endpoint for user registration.
    # No authentication required - anyone can create an account.

    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        return JSONResponse(status_code=400, content={
            "status": 400,
            "error": "Email already registered"
        })

    # Hash password
    hashed_password = hash_password(user.password)

    # Create user with hashed password
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# GET ALL USERS - Admin Only
@router.get("/", response_model=list[schemas.UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)  # Only Admin can view all users
):
    # Get all users in the system.
    # Only accessible by Admin.
    return db.query(models.User).all()


# GET USER BY ID - Self or Admin
@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get a specific user by ID.
    # Users can view their own profile, Admins can view anyone.
    # Check permission: must be self or admin
    if current_user.role.role_name != "Admin" and current_user.id != user_id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": 403,
                "error": "You can only view your own profile"
            })

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return JSONResponse(status_code=404, content={
            "status": 404,
            "error": "User not found"
        })
    return db_user


# UPDATE USER - Self or Admin (with restrictions)
@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int, 
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Update user information.
    # Users can update their own profile (except role_id)
    # Admins can update anyone's profile (including role_id)

    # Check if user is Admin or updating themselves
    if current_user.role.role_name != "Admin" and current_user.id != user_id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": 403,
                "error": "You can only update your own profile"
            }
        )

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return JSONResponse(status_code=404, content={
            "status": 404,
            "error": "User not found"
        })

    # Update only provided fields
    if user.name is not None:
        db_user.name = user.name

    if user.email is not None:
        # Check if email is already taken by another user
        existing = db.query(models.User).filter(
            models.User.email == user.email,
            models.User.id != user_id
        ).first()
        if existing:
            return JSONResponse(status_code=400, content={
                "status": 400,
                "error": "Email already in use"
            })
        db_user.email = user.email

    if user.password is not None:
        db_user.password = hash_password(user.password)

    # CRITICAL: Only Admin can change role_id
    if user.role_id is not None:
        if current_user.role.role_name != "Admin":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": 403,
                    "error": "Only Admin can change user roles"
                }
            )
        db_user.role_id = user.role_id

    db.commit()
    db.refresh(db_user)
    return db_user


# DELETE USER - Self or Admin (with restrictions)
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Delete a user.
    # Users can delete their own account
    # Admins can delete any non-Admin user
    # Admins can only delete their own Admin account (not other Admins)
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return JSONResponse(status_code=404, content={
            "status": 404,
            "error": "User not found"
        })
    
    # Check if target user is Admin
    if db_user.role.role_name == "Admin":
        # Only the admin themselves can delete their own account
        if current_user.id != user_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": 403,
                    "error": "Admins can only delete their own account"
                }
            )
    else:
        # For non-admin users, only Admin can delete or users can delete themselves
        if current_user.role.role_name != "Admin" and current_user.id != user_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": 403,
                    "error": "You don't have permission to delete this user"
                }
            )

    db.delete(db_user)
    db.commit()
    
    return {"message": "User deleted successfully"}