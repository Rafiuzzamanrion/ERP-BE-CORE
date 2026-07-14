from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception:
                raise ValueError(f"Invalid ObjectId: {v}")
        raise ValueError(f"Invalid ObjectId: {v}")

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema, _handler):
        return {"type": "string"}


class BaseDocument(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )

    def to_mongo(self, exclude_unset: bool = False) -> dict[str, Any]:
        data = self.model_dump(
            by_alias=True, exclude={"id"}, exclude_unset=exclude_unset
        )
        if "_id" in data and data["_id"] is not None:
            data["_id"] = (
                ObjectId(data["_id"]) if isinstance(data["_id"], str) else data["_id"]
            )
        else:
            data.pop("_id", None)
        return data

    @classmethod
    def from_mongo(cls, data: dict[str, Any]) -> "BaseDocument":
        if data is None:
            return None
        data["id"] = str(data["_id"]) if "_id" in data else None
        return cls(**data)


class TimestampMixin:
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
