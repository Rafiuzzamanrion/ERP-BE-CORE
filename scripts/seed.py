import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import hash_password
from app.infrastructure.mongo.client import init_db, close_db, get_db
from app.infrastructure.logging import setup_logging, create_logger

setup_logging()
logger = create_logger("seed")


async def seed():
    await init_db()
    db = get_db()

    logger.info("clearing_existing_data")
    collections = ["users", "permissions", "roles", "categories", "products", "sales"]
    for coll in collections:
        await db[coll].delete_many({})

    logger.info("creating_permissions")
    perm_data = [
        {"key": "product:create", "description": "Create products"},
        {"key": "product:update", "description": "Update products"},
        {"key": "product:delete", "description": "Delete products"},
        {"key": "product:view", "description": "View products"},
        {"key": "sale:create", "description": "Create sales"},
        {"key": "sale:view", "description": "View sales history"},
        {"key": "user:manage", "description": "Manage users"},
        {"key": "role:manage", "description": "Manage roles and permissions"},
        {"key": "dashboard:view", "description": "View dashboard statistics"},
    ]
    result = await db["permissions"].insert_many(perm_data)

    perms = []
    for pid in result.inserted_ids:
        p = await db["permissions"].find_one({"_id": pid})
        if p:
            perms.append(p)

    def _perm_id(key: str):
        for p in perms:
            if p["key"] == key:
                return p["_id"]
        return None

    logger.info("creating_roles")
    admin_perms = [p["_id"] for p in perms]
    manager_perms = [_perm_id(k) for k in [
        "product:create", "product:update", "product:delete", "product:view",
        "sale:create", "sale:view", "dashboard:view",
    ] if _perm_id(k)]
    employee_perms = [_perm_id(k) for k in [
        "product:view", "sale:create", "sale:view", "dashboard:view",
    ] if _perm_id(k)]

    role_docs = [
        {"name": "admin", "permissions": admin_perms, "isSystem": True},
        {"name": "manager", "permissions": manager_perms, "isSystem": True},
        {"name": "employee", "permissions": employee_perms, "isSystem": True},
    ]
    role_result = await db["roles"].insert_many(role_docs)

    roles = []
    for rid in role_result.inserted_ids:
        r = await db["roles"].find_one({"_id": rid})
        if r:
            roles.append(r)

    admin_role = roles[0]
    manager_role = roles[1]
    employee_role = roles[2]

    logger.info("creating_admin_user")
    admin_user = await db["users"].insert_one({
        "name": "Admin User",
        "email": "admin@erp.com",
        "password": hash_password("Admin@123"),
        "role": admin_role["_id"],
        "isActive": True,
    })
    print(f"  Admin: admin@erp.com / Admin@123")

    logger.info("creating_manager_user")
    await db["users"].insert_one({
        "name": "Manager User",
        "email": "manager@erp.com",
        "password": hash_password("Manager@123"),
        "role": manager_role["_id"],
        "isActive": True,
    })
    print(f"  Manager: manager@erp.com / Manager@123")

    logger.info("creating_employee_user")
    await db["users"].insert_one({
        "name": "Employee User",
        "email": "employee@erp.com",
        "password": hash_password("Employee@123"),
        "role": employee_role["_id"],
        "isActive": True,
    })
    print(f"  Employee: employee@erp.com / Employee@123")

    logger.info("creating_categories")
    category_data = [
        {"name": "electronics", "description": "Electronic devices and accessories"},
        {"name": "accessories", "description": "Computer and mobile accessories"},
        {"name": "office", "description": "Office supplies and equipment"},
        {"name": "stationery", "description": "Stationery items"},
        {"name": "furniture", "description": "Office furniture"},
    ]
    await db["categories"].insert_many(category_data)
    print(f"  Created {len(category_data)} categories")

    logger.info("creating_sample_products")
    sample_products = [
        {"name": "Wireless Mouse", "sku": "WM-001", "category": "electronics", "purchasePrice": 15, "sellingPrice": 29.99, "stockQuantity": 50, "imageUrl": "https://placehold.co/400x400?text=Wireless+Mouse", "imagePublicId": "seed/wm001", "createdBy": admin_user.inserted_id},
        {"name": "Mechanical Keyboard", "sku": "MK-002", "category": "electronics", "purchasePrice": 45, "sellingPrice": 89.99, "stockQuantity": 30, "imageUrl": "https://placehold.co/400x400?text=Mechanical+Keyboard", "imagePublicId": "seed/mk002", "createdBy": admin_user.inserted_id},
        {"name": "USB-C Hub", "sku": "UH-003", "category": "accessories", "purchasePrice": 20, "sellingPrice": 39.99, "stockQuantity": 100, "imageUrl": "https://placehold.co/400x400?text=USB-C+Hub", "imagePublicId": "seed/uh003", "createdBy": admin_user.inserted_id},
        {"name": "27\" Monitor", "sku": "MON-004", "category": "electronics", "purchasePrice": 150, "sellingPrice": 299.99, "stockQuantity": 15, "imageUrl": "https://placehold.co/400x400?text=27+Monitor", "imagePublicId": "seed/mon004", "createdBy": admin_user.inserted_id},
        {"name": "Desk Lamp", "sku": "DL-005", "category": "office", "purchasePrice": 12, "sellingPrice": 24.99, "stockQuantity": 75, "imageUrl": "https://placehold.co/400x400?text=Desk+Lamp", "imagePublicId": "seed/dl005", "createdBy": admin_user.inserted_id},
        {"name": "Notebook", "sku": "NB-006", "category": "stationery", "purchasePrice": 3, "sellingPrice": 7.99, "stockQuantity": 200, "imageUrl": "https://placehold.co/400x400?text=Notebook", "imagePublicId": "seed/nb006", "createdBy": admin_user.inserted_id},
        {"name": "Webcam HD", "sku": "WC-007", "category": "electronics", "purchasePrice": 25, "sellingPrice": 49.99, "stockQuantity": 3, "imageUrl": "https://placehold.co/400x400?text=Webcam+HD", "imagePublicId": "seed/wc007", "createdBy": admin_user.inserted_id},
        {"name": "Standing Desk", "sku": "SD-008", "category": "furniture", "purchasePrice": 200, "sellingPrice": 449.99, "stockQuantity": 5, "imageUrl": "https://placehold.co/400x400?text=Standing+Desk", "imagePublicId": "seed/sd008", "createdBy": admin_user.inserted_id},
        {"name": "Ergonomic Chair", "sku": "EC-009", "category": "furniture", "purchasePrice": 180, "sellingPrice": 349.99, "stockQuantity": 8, "imageUrl": "https://placehold.co/400x400?text=Ergonomic+Chair", "imagePublicId": "seed/ec009", "createdBy": admin_user.inserted_id},
        {"name": "Wireless Headphones", "sku": "WH-010", "category": "electronics", "purchasePrice": 35, "sellingPrice": 79.99, "stockQuantity": 2, "imageUrl": "https://placehold.co/400x400?text=Wireless+Headphones", "imagePublicId": "seed/wh010", "createdBy": admin_user.inserted_id},
    ]
    await db["products"].insert_many(sample_products)
    print(f"  Created {len(sample_products)} sample products")

    logger.info("creating_sample_sales")
    products = await db["products"].find().to_list(length=None)
    admin_doc = await db["users"].find_one({"email": "admin@erp.com"})
    manager_doc = await db["users"].find_one({"email": "manager@erp.com"})
    employee_doc = await db["users"].find_one({"email": "employee@erp.com"})

    sellers = [u for u in [admin_doc, manager_doc, employee_doc] if u]
    sample_sales = []

    for _ in range(30):
        num_items = random.randint(1, 3)
        sale_items = []
        grand_total = 0
        used_ids = set()

        for _ in range(num_items):
            available = [p for p in products if str(p["_id"]) not in used_ids]
            product = random.choice(available) if available else None
            if not product:
                continue
            used_ids.add(str(product["_id"]))
            quantity = random.randint(1, 3)
            subtotal = round(product["sellingPrice"] * quantity, 2)
            grand_total += subtotal
            sale_items.append({
                "product": product["_id"],
                "productName": product["name"],
                "quantity": quantity,
                "unitPrice": product["sellingPrice"],
                "subtotal": subtotal,
            })

        days_ago = random.randint(0, 6)
        created_at = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(0, 12))
        seller = random.choice(sellers)

        sample_sales.append({
            "items": sale_items,
            "grandTotal": round(grand_total, 2),
            "soldBy": seller["_id"],
            "createdAt": created_at,
        })

    if sample_sales:
        await db["sales"].insert_many(sample_sales)
    print(f"  Created {len(sample_sales)} sample sales")

    print("\n" + "=" * 44)
    print("            SEED COMPLETE")
    print("=" * 44)
    print(f"  Admin:     admin@erp.com / Admin@123")
    print(f"  Manager:   manager@erp.com / Manager@123")
    print(f"  Employee:  employee@erp.com / Employee@123")
    print("=" * 44 + "\n")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
