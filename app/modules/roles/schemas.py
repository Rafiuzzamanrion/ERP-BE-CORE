from pydantic import BaseModel, Field


class CreateRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    permissions: list[str] | None = None
    isSystem: bool | None = False


class UpdateRoleRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    permissions: list[str] | None = None
    isSystem: bool | None = None


class CreatePermissionRequest(BaseModel):
    key: str = Field(min_length=1)
    description: str = Field(min_length=1)


class UpdatePermissionRequest(BaseModel):
    key: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
