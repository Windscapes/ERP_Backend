import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.database import Base, engine
import app.models  # required

app = FastAPI(title="Windscapes Backend")


def _parse_csv_env(var_name: str, default: str) -> list[str]:
    raw = os.getenv(var_name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# Configure CORS
allowed_origins = _parse_csv_env(
    "CORS_ORIGINS",
    "https://windscapesai.com,https://www.windscapesai.com,http://localhost:3000,http://127.0.0.1:3000",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")

