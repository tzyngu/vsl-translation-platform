from contextlib import asynccontextmanager

from asgiref.sync import sync_to_async
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import database_health
from .routers import auth, gestures, inference, models, training
from .services.model_registry import bootstrap_base_model


settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.media_path.mkdir(parents=True, exist_ok=True)
    await sync_to_async(bootstrap_base_model)()
    yield


app = FastAPI(title="VSL FastAPI Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(gestures.router, prefix="/api")
app.include_router(training.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(inference.router, prefix="/api")


@app.get("/api/health")
def health():
    return database_health()
