from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError
import os
from datetime import datetime
from passlib.hash import bcrypt
from fastapi.security import HTTPBearer
from typing import List

from dotenv import load_dotenv
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if JWT_SECRET is None:
    raise EnvironmentError("JWT_SECRET is not set in the environment variables")

router = APIRouter()
bearer_scheme = HTTPBearer()

import database
import models
import users.schemas

@router.get("/", response_model=List[users.schemas.UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    token: str = Depends(bearer_scheme),
):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=users.schemas.UserCreateResponse)
def create_user(
    request: users.schemas.UserCreateRequest,
    db: Session = Depends(database.get_db),
):
    existing_user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with the provided email already exists",
        )

    existing_username = db.query(models.User).filter(
        models.User.username == request.username
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with the provided username already exists",
        )

    user = models.User(
        username=request.username,
        email=request.email,
        password_hash=bcrypt.hash(request.password),
        role=request.role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully", "user": user}
    
@router.put("/", response_model=users.schemas.UserUpdateResponse)
def update_user(
    request: users.schemas.UserUpdateRequest,
    db: Session = Depends(database.get_db),
    token: str = Depends(bearer_scheme),
):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(models.User).filter(
        models.User.id == payload.get("user_id"),
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    if request.password:
        user.password_hash = bcrypt.hash(request.password)
    if request.role:
        user.role = request.role
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {"message": "User updated successfully", "user": user}

@router.get("/me", response_model=users.schemas.UserResponse)
def get_me(token: str = Depends(bearer_scheme), db: Session = Depends(database.get_db)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(models.User).filter(
        models.User.id == payload.get("user_id"),
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return user

@router.get("/{user_id}", response_model=users.schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(
        models.User.id == user_id,
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user