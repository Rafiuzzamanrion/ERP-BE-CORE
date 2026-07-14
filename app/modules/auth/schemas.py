from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class LoginUserResponse(BaseModel):
    _id: str
    name: str
    email: str
    role: str
    isActive: bool


class LoginResponse(BaseModel):
    token: str
    user: LoginUserResponse


class MeResponse(BaseModel):
    _id: str
    name: str
    email: str
    role: str
    isActive: bool
