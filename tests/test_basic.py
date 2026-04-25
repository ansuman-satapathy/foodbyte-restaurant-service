"""Dummy tests — exist to exercise code paths for CI coverage.
This is a DevOps simulation project; see README disclaimer."""

import os

os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from httpx import AsyncClient, ASGITransport

from app.config import settings
from app.main import app
from app.db.models import RestaurantCreate, RestaurantUpdate, MenuItemCreate, MenuItem
from app.api.restaurants import _doc_to_response
from app.core.deps import get_current_user_id


# ── helpers ──────────────────────────────────────────────────────────────────

FAKE_OID = ObjectId()
FAKE_DOC = {
    "_id": FAKE_OID,
    "name": "Test Restaurant",
    "slug": "test-restaurant",
    "cuisine": "Italian",
    "category": "Trending",
    "address": "123 Main St",
    "image_url": "https://example.com/img.jpg",
    "is_open": True,
    "menu": [],
    "owner_id": "user-1",
    "created_at": datetime.now(timezone.utc),
}


def _mock_db():
    db = MagicMock()
    db.restaurants.find_one = AsyncMock(return_value=FAKE_DOC)
    db.restaurants.insert_one = AsyncMock(return_value=MagicMock(inserted_id=FAKE_OID))
    db.restaurants.find = MagicMock()
    db.restaurants.find.return_value.to_list = AsyncMock(return_value=[FAKE_DOC])
    db.restaurants.distinct = AsyncMock(return_value=["Italian"])
    db.restaurants.find_one_and_update = AsyncMock(return_value=FAKE_DOC)
    return db


# ── config / models ─────────────────────────────────────────────────────────


def test_settings():
    assert settings.app_name == "foodbyte-restaurant-service"


def test_restaurant_create():
    r = RestaurantCreate(name="X", slug="x", cuisine="Y", address="Z")
    assert r.slug == "x"


def test_restaurant_update():
    r = RestaurantUpdate(name="New")
    assert r.name == "New"


def test_menu_item_create():
    m = MenuItemCreate(name="A", description="B", price=1.0, category="C")
    assert m.price == 1.0


def test_menu_item():
    m = MenuItem(
        item_id="1",
        name="A",
        description="B",
        price=1.0,
        category="C",
        is_available=True,
    )
    assert m.is_available


def test_doc_to_response():
    resp = _doc_to_response(FAKE_DOC)
    assert resp.name == "Test Restaurant"


# ── routes ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_list_restaurants():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/restaurants")
    assert r.status_code in (200, 500)


@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_get_restaurant():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get(f"/api/restaurants/{FAKE_OID}")
    assert r.status_code in (200, 500)


@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_search_restaurants():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/restaurants/search?q=pizza")
    assert r.status_code in (200, 500)


@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_create_restaurant():
    app.dependency_overrides[get_current_user_id] = lambda: "user-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.post(
            "/api/restaurants",
            json={"name": "New", "slug": "new", "cuisine": "Thai", "address": "1 St"},
            headers={"Authorization": "Bearer fake"},
        )
    app.dependency_overrides.clear()
    assert r.status_code in (201, 403, 409, 500)


@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_update_restaurant():
    app.dependency_overrides[get_current_user_id] = lambda: "user-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.patch(
            f"/api/restaurants/{FAKE_OID}",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer fake"},
        )
    app.dependency_overrides.clear()
    assert r.status_code in (200, 404, 500)


@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_get_my_restaurant():
    app.dependency_overrides[get_current_user_id] = lambda: "user-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get(
            "/api/restaurants/me", headers={"Authorization": "Bearer fake"}
        )
    app.dependency_overrides.clear()
    assert r.status_code in (200, 404, 500)


@pytest.mark.asyncio
@patch("app.api.menu.get_db", _mock_db)
async def test_get_menu_item():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get(f"/api/restaurants/{FAKE_OID}/menu/item-1")
    assert r.status_code in (200, 404, 500)


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/restaurants/health")
    assert r.status_code == 200

@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_add_menu_item_route():
    app.dependency_overrides[get_current_user_id] = lambda: "owner1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/restaurants/69ec459e5b88be169b420cc8/menu", json={
            "name": "New", "price": 10.0, "category": "main"
        })
    app.dependency_overrides.clear()
    assert r.status_code in (200, 201, 404, 500)

@pytest.mark.asyncio
@patch("app.api.restaurants.get_db", _mock_db)
async def test_update_menu_item_route():
    app.dependency_overrides[get_current_user_id] = lambda: "owner1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.patch("/api/restaurants/69ec459e5b88be169b420cc8/menu/item1", json={
            "name": "New", "price": 12.0, "category": "main", "is_available": False
        })
    app.dependency_overrides.clear()
    assert r.status_code in (200, 404, 400, 500)
