from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_db
from app.db.models import MenuItemCreate, MenuItem, RestaurantResponse
from app.core.deps import get_current_user_id
from app.api.restaurants import _doc_to_response

router = APIRouter(prefix="/api/restaurants", tags=["menu"])


@router.post(
    "/{restaurant_id}/menu",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_menu_item(
    restaurant_id: str,
    body: MenuItemCreate,
    user_id: str = Depends(get_current_user_id),
):

    db = get_db()
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid restaurant ID"
        )

    new_item = MenuItem(**body.model_dump())

    result = await db.restaurants.find_one_and_update(
        {"_id": oid, "owner_id": user_id},
        {"$push": {"menu": new_item.model_dump()}},
        return_document=True,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found or you are not the owner",
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid restaurant ID"
        )

    result = await db.restaurants.find_one_and_update(
        {"_id": oid, "owner_id": user_id},
        {"$pull": {"menu": {"item_id": item_id}}},
        return_document=True,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found or you are not the owner",
        )
    return _doc_to_response(result)


@router.get("/{restaurant_id}/menu/{item_id}", response_model=MenuItem)
async def get_menu_item(restaurant_id: str, item_id: str):

    db = get_db()
    try:
        oid = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid restaurant ID"
        )

    doc = await db.restaurants.find_one(
        {"_id": oid, "menu.item_id": item_id},
        {"menu.$": 1},
    )
    if not doc or not doc.get("menu"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found"
        )

    return MenuItem(**doc["menu"][0])
