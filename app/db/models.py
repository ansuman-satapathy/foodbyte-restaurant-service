import uuid
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, field_validator


class MenuItem(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    price: Annotated[float, Field(gt=0)]  # must be positive
    category: str = "main"
    is_available: bool = True


class MenuItemCreate(BaseModel):
    name: str
    description: str = ""
    price: Annotated[float, Field(gt=0)]
    category: str = "main"


# ── Restaurant ────────────────────────────────────────────────────────────────


class RestaurantCreate(BaseModel):
    name: str
    slug: str
    cuisine: str
    category: str = "Trending"
    address: str
    image_url: str = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4"
    is_open: bool = True

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        import re

        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug must be lowercase letters, numbers, and hyphens only"
            )
        return v


class RestaurantResponse(BaseModel):
    id: str
    name: str
    slug: str
    cuisine: str
    category: str
    address: str
    image_url: str
    is_open: bool
    menu: list[MenuItem] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RestaurantUpdate(BaseModel):
    name: str | None = None
    cuisine: str | None = None
    category: str | None = None
    address: str | None = None
    image_url: str | None = None
    is_open: bool | None = None
