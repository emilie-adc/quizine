from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import generate

app = FastAPI(title="Quizine")


@app.on_event("startup")
def configure_cors() -> None:
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(generate.router, prefix="/generate", tags=["generate"])
