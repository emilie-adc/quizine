from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.api import cards, certifications, decks, generate


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        from seed_certifications import seed_certifications
        await seed_certifications(db)
    yield


app = FastAPI(title="Quizine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/generate", tags=["generate"])
app.include_router(certifications.router, prefix="/certifications", tags=["certifications"])
app.include_router(decks.router, prefix="/decks", tags=["decks"])
app.include_router(cards.router, prefix="/cards", tags=["cards"])
