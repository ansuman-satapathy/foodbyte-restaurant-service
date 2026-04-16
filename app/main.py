from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import init_db, close_db
from app.api import restaurants, menu
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/restaurants/docs",
    lifespan=lifespan,
)

app.include_router(restaurants.router)
app.include_router(menu.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}
