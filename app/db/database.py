import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger(__name__)
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_db() -> None:
    global _client, _db
    for attempt in range(5):
        try:
            _client = AsyncIOMotorClient(settings.mongodb_url)
            await _client.admin.command('ping')
            _db = _client[settings.mongodb_db]
            await _ensure_indexes()
            logger.info("MongoDB initialized successfully")
            return
        except Exception as e:
            logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}")
            if attempt == 4:
                raise
            await asyncio.sleep(2)


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
