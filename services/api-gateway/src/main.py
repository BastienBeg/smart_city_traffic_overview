from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.database import init_db
from src.routers import triage

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title="Smart City Sentinel API",
    description="Backend API for Smart City Traffic Overview",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(triage.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
