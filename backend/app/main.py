from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers tables with Base)
from app.config import settings
from app.db import Base, engine
from app.routes import report


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Creates missing tables on startup. Fine for an MVP; real projects use migrations (Alembic).
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="CF Trainer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
