from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import get_db
from models import Dish, User
from dishes.schemas import (
    DishCreateRequest,
    DishUpdateRequest,
    DishInfoResponse,
    DishListResponse,
    DishErrorResponse,
)
import requests
from requests.exceptions import RequestException
import jwt
from dotenv import load_dotenv
import os

router = APIRouter()

AUTH_SERVICE_HOST = os.getenv("AUTH_SERVICE_HOST")

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if JWT_SECRET is None:
    raise EnvironmentError("JWT_SECRET is not set in the environment variables")

security = HTTPBearer()

def get_user_by_id(user_id: int) -> User:
    try:
        url = f"http://{AUTH_SERVICE_HOST}:8000/users/{user_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            user_data = response.json()
            user = User(**user_data)
            return user
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch user data",
            )
    except RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)):
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

    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return user

@router.get("/menu", response_model=DishListResponse)
def get_menu(db: Session = Depends(get_db)):
    dishes = db.query(Dish).filter(Dish.quantity > 0).all()
    return {"dishes": dishes}

@router.post("", response_model=DishInfoResponse, status_code=status.HTTP_201_CREATED)
def create_dish(
    dish_data: DishCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can create dishes",
        )

    existing_dish = db.query(Dish).filter(Dish.name == dish_data.name).first()
    if existing_dish:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dish with this name already exists",
        )

    dish = Dish(**dish_data.dict())
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish

@router.put("/{dish_id}", response_model=DishInfoResponse)
def update_dish(
    dish_id: int,
    dish_data: DishUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can update dishes",
        )

    dish = db.query(Dish).get(dish_id)
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found",
        )

    for field, value in dish_data.dict(exclude_unset=True).items():
        setattr(dish, field, value)
    db.commit()
    db.refresh(dish)
    return dish

@router.get("", response_model=DishListResponse)
def get_all_dishes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can get all dishes"
        )

    dishes = db.query(Dish).all()
    return {"dishes": dishes}

@router.get("/{dish_id}", response_model=DishInfoResponse)
def get_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can get a dish",
        )

    dish = db.query(Dish).get(dish_id)
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found",
        )

    return dish

@router.delete("/{dish_id}", response_model=DishErrorResponse)
def delete_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can delete dishes",
        )

    dish = db.query(Dish).get(dish_id)
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found",
        )
    db.delete(dish)
    db.commit()
    return {"error": "Dish deleted"}
