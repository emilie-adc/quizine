from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings, parse_cors_origins
from app.api import generate

app = FastAPI(title="Quizine")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(settings.CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(generate.router, prefix="/generate", tags=["generate"])
app.include_router(certifications.router, prefix="/certifications", tags=["certifications"])
