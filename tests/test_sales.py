from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_create_sale_success_and_stock_deduction(client, employee_token, db):
    await db["categories"].insert_one(
        {"name": "electronics", "description": "Electronics"}
    )
    await db["users"].update_one(
        {"email": "employee@test.com"},
        {"$set": {"role": (await db["roles"].find_one({"name": "employee"}))["_id"]}},
    )

    with patch("app.modules.products.service.upload_image") as mock_upload:
        mock_upload.return_value = {
            "secure_url": "https://fake.cloud/img.jpg",
            "public_id": "fk001",
        }

    await db["products"].insert_one(
        {
            "name": "Stock Product",
            "sku": "SP-001",
            "category": "electronics",
            "purchasePrice": 5,
            "sellingPrice": 10,
            "stockQuantity": 20,
            "imageUrl": "https://fake.cloud/img.jpg",
            "imagePublicId": "fk001",
        }
    )
    product = await db["products"].find_one({"sku": "SP-001"})

    from app.infrastructure.mongo.client import get_client as _gcl

    with patch("app.infrastructure.mongo.client.get_client") as mock_get_client:
        mock_get_client.side_effect = _gcl

        resp = await client.post(
            "/api/v1/sales",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={
                "items": [
                    {"productId": str(product["_id"]), "quantity": 3},
                ],
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["grandTotal"] == 30.0

    updated = await db["products"].find_one({"_id": product["_id"]})
    assert updated["stockQuantity"] == 17


@pytest.mark.asyncio
async def test_create_sale_insufficient_stock(client, employee_token, db):
    await db["categories"].insert_one(
        {"name": "electronics", "description": "Electronics"}
    )

    await db["products"].insert_one(
        {
            "name": "Low Stock Product",
            "sku": "LS-001",
            "category": "electronics",
            "purchasePrice": 5,
            "sellingPrice": 10,
            "stockQuantity": 2,
            "imageUrl": "https://fake.cloud/img.jpg",
            "imagePublicId": "fk002",
        }
    )
    product = await db["products"].find_one({"sku": "LS-001"})

    resp = await client.post(
        "/api/v1/sales",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "items": [
                {"productId": str(product["_id"]), "quantity": 10},
            ],
        },
    )

    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False

    still = await db["products"].find_one({"_id": product["_id"]})
    assert still["stockQuantity"] == 2
