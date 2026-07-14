from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=50)
    category: str = Field(min_length=1, max_length=50)
    purchasePrice: float = Field(ge=0)
    sellingPrice: float = Field(ge=0)
    stockQuantity: int | None = Field(default=0, ge=0)


class UpdateProductRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    purchasePrice: float | None = Field(default=None, ge=0)
    sellingPrice: float | None = Field(default=None, ge=0)
    stockQuantity: int | None = Field(default=None, ge=0)
