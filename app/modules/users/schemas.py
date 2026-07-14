from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str
    password: str = Field(min_length=6)
    role: str | None = None
    isActive: bool | None = True


class UpdateUserRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    email: str | None = None
    password: str | None = Field(default=None, min_length=6)
    role: str | None = None
    isActive: bool | None = None


class UserResponse(BaseModel):
    _id: str
    name: str
    email: str
    role: str | None = None
    isActive: bool
    createdAt: str | None = None
    updatedAt: str | None = None
