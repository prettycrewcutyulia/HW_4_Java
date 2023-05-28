from pydantic import BaseModel, Field, conlist, constr
from decimal import Decimal
from enum import Enum
from datetime import datetime
from typing import Optional


class DishItem(BaseModel):
    dish_id: int
    quantity: int

class OrderStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class OrderCreateRequest(BaseModel):
    dishes: conlist(DishItem, min_items=1)
    special_requests: constr(max_length=255) = ""

class OrderCreateResponse(BaseModel):
    order_id: int


class OrderErrorResponse(BaseModel):
    error: str

from pydantic import BaseModel
from enum import Enum

class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus

class OrderStatusUpdateResponse(BaseModel):
    message: str

class OrderStatusUpdateErrorResponse(BaseModel):
    error: str

class OrderResponce(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    special_requests: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class OrderListResponse(BaseModel):
    orders: list[OrderResponce]