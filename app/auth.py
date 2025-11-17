from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Default to HS256 if not set
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Hash password
def hash_password(password: str) -> str:
    # Convert plain password to hashed password
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Check if plain password matches hashed password
    return pwd_context.verify(plain_password, hashed_password)

# Create JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Generate JWT token with expiration
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta  # ← Fixed
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)  # ← Fixed
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user from token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Extract user from JWT token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

# Check if user is SuperAdmin
def require_superadmin(current_user: models.User = Depends(get_current_user)):
    # Dependency to ensure user is SuperAdmin
    if current_user.role.role_name != "SuperAdmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin can perform this action"
        )
    return current_user