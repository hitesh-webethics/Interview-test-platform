from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app import models, schemas
from app.database import get_db
from app.auth import (
    verify_password, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Login endpoint
@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):

    # Find user by email
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()

    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content = {
                "status" : 401,
                "error" : "User not found"
            }
        )

    # Verify password
    if not verify_password(user_credentials.password, user.password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content = {
                "status" : 401,
                "error" : "Invalid credentials"
            }
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}