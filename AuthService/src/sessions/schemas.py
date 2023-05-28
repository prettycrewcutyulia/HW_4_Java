from pydantic import BaseModel, Field, EmailStr


class SessionCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=20,
        regex='^[a-zA-Z0-9_]*$',
        alias='password',
        title='Password',
        description='Password (8-20 characters, alphanumeric)'
    )


class SessionCreateResponse(BaseModel):
    access_token: str


class SessionInfoRequest(BaseModel):
    token: str


class SessionInfoResponse(BaseModel):
    user_id: int
    expires_at: str


class SessionDeleteRequest(BaseModel):
    access_token: str


class SessionDeleteResponse(BaseModel):
    message: str