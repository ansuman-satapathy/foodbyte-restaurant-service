from bson import ObjectId
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from app.db.database import get_db
from app.db.models import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantUpdate,
    MenuItem,
    MenuItemCreate,
)
from app.core.deps import get_current_user_id

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.get("/categories")
async def get_categories():
    db = get_db()
    cuisines = await db.restaurants.distinct("cuisine")
    return cuisines


@router.get("/me", response_model=RestaurantResponse)
async def get_my_restaurant(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    doc = await db.restaurants.find_one({"owner_id": user_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You do not have a restaurant registered yet.",
        )
    return _doc_to_response(doc)


def _doc_to_response(doc: dict) -> RestaurantResponse:
    return RestaurantResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        slug=doc["slug"],
        cuisine=doc["cuisine"],
        category=doc.get("category", "Trending"),
        address=doc["address"],
        image_url=doc.get(
            "image_url", "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4"
        ),
        is_open=doc.get("is_open", True),
        menu=[MenuItem(**item) for item in doc.get("menu", [])],
        created_at=doc["created_at"],
    )


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    body: RestaurantCreate,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    doc = {
        **body.model_dump(),
        "menu": [],
        "owner_id": user_id,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = await db.restaurants.insert_one(doc)
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slug '{body.slug}' is already taken",
            )
        raise

    created = await db.restaurants.find_one({"_id": result.inserted_id})
    return _doc_to_response(created)


@router.get("", response_model=list[RestaurantResponse])
async def list_restaurants(category: str | None = None, cuisine: str | None = None):
    db = get_db()
    query = {}
    if category:
        query["category"] = category
    if cuisine:
        query["cuisine"] = cuisine

    docs = await db.restaurants.find(query).to_list(length=100)
    return [_doc_to_response(doc) for doc in docs]


@router.get("/search", response_model=list[RestaurantResponse])
async def search_restaurants(q: str):
    db = get_db()
    query = {
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"cuisine": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}},
        ]
    }
    docs = await db.restaurants.find(query).to_list(length=50)
    return [_doc_to_response(doc) for doc in docs]


@router.get("/categories", response_model=list[str])
async def list_categories():
    db = get_db()
    categories = await db.restaurants.distinct("category")
    defaults = ["Trending", "Fast Food", "Italian", "Indian", "Healthy"]
    return list(set(categories + defaults))


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: str):
    db = get_db()
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid restaurant ID"
        )

    doc = await db.restaurants.find_one({"_id": oid})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found"
        )
    return _doc_to_response(doc)


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: str,
    body: RestaurantUpdate,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid restaurant ID"
        )

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return await get_restaurant(restaurant_id)

    result = await db.restaurants.find_one_and_update(
        {"_id": oid, "owner_id": user_id},  # only owner can update
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found or you are not the owner",
        )
    return _doc_to_response(result)


# ── Menu Management ──────────────────────────────────────────────────────────


@router.post("/{restaurant_id}/menu", response_model=RestaurantResponse)
async def add_menu_item(
    restaurant_id: str,
    item: MenuItemCreate,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid restaurant ID")

    new_item = {
        "item_id": str(uuid.uuid4()),
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "is_available": True,
    }

    result = await db.restaurants.find_one_and_update(
        {"_id": oid, "owner_id": user_id},
        {"$push": {"menu": new_item}},
        return_document=True,
    )
    if not result:
        raise HTTPException(
            status_code=404, detail="Restaurant not found or unauthorized"
        )

    return _doc_to_response(result)


@router.patch("/{restaurant_id}/menu/{item_id}", response_model=RestaurantResponse)
async def update_menu_item(
    restaurant_id: str,
    item_id: str,
    item: MenuItem,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid restaurant ID")

    result = await db.restaurants.find_one_and_update(
        {"_id": oid, "owner_id": user_id, "menu.item_id": item_id},
        {
            "$set": {
                "menu.$.name": item.name,
                "menu.$.description": item.description,
                "menu.$.price": item.price,
                "menu.$.category": item.category,
                "menu.$.is_available": item.is_available,
            }
        },
        return_document=True,
    )
    if not result:
        raise HTTPException(
            status_code=404, detail="Restaurant/Item not found or unauthorized"
        )

    return _doc_to_response(result)


@router.delete("/{restaurant_id}/menu/{item_id}", response_model=RestaurantResponse)
async def remove_menu_item(
    restaurant_id: str,
    item_id: str,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid restaurant ID")

    result = await db.restaurants.find_one_and_update(
        {"_id": oid, "owner_id": user_id},
        {"$pull": {"menu": {"item_id": item_id}}},
        return_document=True,
    )
    if not result:
        raise HTTPException(
            status_code=404, detail="Restaurant not found or unauthorized"
        )

    return _doc_to_response(result)
