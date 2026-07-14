from pydantic import BaseModel, Field


class SaleItemRequest(BaseModel):
    productId: str = Field(min_length=1)
    quantity: int = Field(ge=1)


class CreateSaleRequest(BaseModel):
    items: list[SaleItemRequest] = Field(min_length=1)
