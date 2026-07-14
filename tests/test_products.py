from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_create_product_success(client, admin_token, db):
    await db["categories"].insert_one(
        {"name": "electronics", "description": "Electronics"}
    )

    with patch("app.modules.products.service.upload_image") as mock_upload:
        mock_upload.return_value = {
            "secure_url": "https://fake.cloud/image.jpg",
            "public_id": "fake123",
        }

        resp = await client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"image": ("test.jpg", b"fakeimage", "image/jpeg")},
            data={
                "name": "Test Product",
                "sku": "TP-001",
                "category": "electronics",
                "purchasePrice": "10",
                "sellingPrice": "20",
                "stockQuantity": "5",
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Product"
    assert data["data"]["sku"] == "TP-001"


@pytest.mark.asyncio
async def test_create_product_without_image(client, admin_token):
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={
            "name": "No Image",
            "sku": "NI-001",
            "category": "electronics",
            "purchasePrice": "10",
            "sellingPrice": "20",
            "stockQuantity": "5",
        },
    )

    assert resp.status_code == 400 or resp.status_code == 422


@pytest.mark.asyncio
async def test_create_product_duplicate_sku(client, admin_token, db):
    await db["categories"].insert_one(
        {"name": "electronics", "description": "Electronics"}
    )

    with patch("app.modules.products.service.upload_image") as mock_upload:
        mock_upload.return_value = {
            "secure_url": "https://fake.cloud/image.jpg",
            "public_id": "fake456",
        }

        await client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"image": ("test.jpg", b"fakeimage", "image/jpeg")},
            data={
                "name": "First Product",
                "sku": "DUP-001",
                "category": "electronics",
                "purchasePrice": "10",
                "sellingPrice": "20",
                "stockQuantity": "5",
            },
        )

        resp = await client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"image": ("test.jpg", b"fakeimage", "image/jpeg")},
            data={
                "name": "Second Product",
                "sku": "DUP-001",
                "category": "electronics",
                "purchasePrice": "15",
                "sellingPrice": "25",
                "stockQuantity": "3",
            },
        )

    assert resp.status_code == 409
    data = resp.json()
    assert data["success"] is False
