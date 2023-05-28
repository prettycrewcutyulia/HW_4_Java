from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
from models import User, Order, Dish
from orders.schemas import (
    OrderCreateRequest,
    OrderCreateResponse,
    OrderErrorResponse,
    OrderStatusUpdateRequest,
    OrderStatusUpdateResponse,
    OrderStatusUpdateErrorResponse,
    OrderResponce,
    OrderListResponse,
)

import jwt
from dotenv import load_dotenv
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from fastapi.security import HTTPBearer
import os

router = APIRouter()

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if JWT_SECRET is None:
    raise EnvironmentError("JWT_SECRET is not set in the environment variables")

security = HTTPBearer()

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

    user = db.query(User).get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return user


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    for dish_item in order_data.dishes:
        dish = db.query(Dish).filter(Dish.id == dish_item.dish_id).first()
        if not dish or dish.quantity == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dish with id {dish_item.dish_id} is not available",
            )
        if dish.quantity < dish_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {dish.quantity} {dish.name} available",
            )
        dish.quantity -= dish_item.quantity

    order = Order(
        user_id=current_user.id,
        special_requests=order_data.special_requests,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    return {"order_id": order.id}

@router.put("/{order_id}/status", response_model=OrderStatusUpdateResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check if the current user has the "manager" or "chef" role
    if current_user.role not in ["manager", "chef"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update the order status",
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    order.status = status_data.status
    db.commit()
    return {"message": "Order status updated"}


@router.get("/{order_id}", response_model=OrderResponce)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.get("", response_model=OrderListResponse)
def get_all_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check if the current user has the "manager" or "chef" role
    if current_user.role not in ["manager", "chef"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to get the list of all orders",
        )

    orders = db.query(Order).all()
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found",
        )
    return {"orders": orders}

@router.delete("/{order_id}", response_model=OrderResponce)
def delete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check if the current user has the "manager" role
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete orders",
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    db.delete(order)
    db.commit()
    return order
