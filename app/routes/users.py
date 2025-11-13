from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix = "/users", tags = ["Users"])

# Create User
@router.post("/", response_model = schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(
        name = user.name,
        email = user.email,
        password = user.password,
        role_id = user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Get all Users
@router.get("/", response_model = list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

# Get User by ID
@router.get("/{user_id}", response_model = schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code = 404, detail = "User not found")
    return db_user

# Update User
@router.put("/{user_id}", response_model = schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if user.name is not None:
        db_user.name = user.name

    if user.email is not None:
        db_user.email = user.email

    if user.password is not None:
        db_user.password = user.password

    if user.role_id is not None:
        db_user.role_id = user.role_id

    db_user.name = user.name
    db_user.email = user.email
    db_user.role_id = user.role_id
    db.commit()
    db.refresh(db_user)
    return db_user

# Delete User
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    db.delete(db_user)
    db.commit()
    
    return {"message": "User Deleted Successfully"}