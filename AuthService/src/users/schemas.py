from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        regex='^[a-zA-Z0-9_]*$',
        description='Username (3-20 characters, alphanumeric)'
    )
    email: EmailStr


class UserCreateRequest(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=20,
        regex='^[a-zA-Z0-9_]*$',
        description='Password (8-20 characters, alphanumeric)'
    )
    role: str = Field(
        'customer',
        description='Role must be either customer, chef, or manager',
        enum=['customer', 'chef', 'manager']
    )


class UserUpdateRequest(UserBase):
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=20,
        regex='^[a-zA-Z0-9_]*$',
        description='Password (8-20 characters, alphanumeric)'
    )
    role: Optional[str] = Field(
        None,
        description='Role must be either customer, chef, or manager',
        enum=['customer', 'chef', 'manager']
    )

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserCreateResponse(BaseModel):
    message: str
    user: UserResponse

class UserUpdateResponse(BaseModel):
    message: str
    user: UserResponse
