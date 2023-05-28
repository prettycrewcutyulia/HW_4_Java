from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from typing import List

from dotenv import load_dotenv
import os

from database import get_db
from models import User
from sessions.schemas import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionInfoResponse,
)

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if JWT_SECRET is None:
    raise EnvironmentError("JWT_SECRET is not set in the environment variables")

bearer_scheme = HTTPBearer()

router = APIRouter()

@router.post("/", response_model=SessionCreateResponse)
def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not bcrypt.verify(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    expires_at = datetime.utcnow() + timedelta(minutes=30)
    payload = {
        "user_id": user.id,
        "expires_at": expires_at.isoformat(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"access_token": token}


@router.get("/", response_model=SessionInfoResponse)
def get_session(token: str = Depends(bearer_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided.",
        )
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

    return payload
