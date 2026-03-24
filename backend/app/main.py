from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.secrets import router as secrets_router
from app.routers.beneficiaries import router as beneficiaries_router
import app.models  # noqa: F401 — ensures all models are registered before create_all

# Create all tables on startup (development convenience)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LastKey API",
    description="Digital Inheritance Vault — secure secrets released to beneficiaries via dead man's switch",
    version="0.1.0",
)

# CORS — allow frontend origin only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(secrets_router)
app.include_router(beneficiaries_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
