from pydantic import BaseModel, Field, conint, constr
from decimal import Decimal
from typing import Optional

class DishCreateRequest(BaseModel):
    name: constr(max_length=100)
    description: constr(max_length=255) = ""
    price: Decimal = Field(..., ge=0)
    quantity: conint(ge=0)


class DishUpdateRequest(BaseModel):
    name: constr(max_length=100)
    description: constr(max_length=255) = ""
    price: Decimal = Field(..., ge=0)
    quantity: conint(ge=0)


class DishInfoResponse(BaseModel):
    id: int
    name: str
    description: str
    price: Decimal
    quantity: int

    class Config:
        orm_mode = True


class DishListResponse(BaseModel):
    dishes: list[DishInfoResponse]


class DishErrorResponse(BaseModel):
    error: str
