from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongodb_url)
    _db = _client[settings.mongodb_db]
    await _ensure_indexes()


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not initialised. Was init_db() called?")
    return _db


async def _ensure_indexes() -> None:
    db = get_db()
    await db.restaurants.create_index("slug", unique=True)
    await db.restaurants.create_index([("_id", 1), ("menu.item_id", 1)])
