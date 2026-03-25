from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.beneficiaries import router as beneficiaries_router
from app.routers.checkin import router as checkin_router
from app.routers.secrets import router as secrets_router
from app.routers.verifier import public_verify_router, router as verifier_router
from app.services.scheduler import run_checkin_job, scheduler
import app.models  # noqa: F401 — ensures all models are registered before create_all

# Create all tables on startup (development convenience)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(run_checkin_job, "cron", hour=2, minute=0, id="daily_checkin")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="LastKey API",
    description="Digital Inheritance Vault — secure secrets released to beneficiaries via dead man's switch",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(verifier_router)
app.include_router(public_verify_router)
app.include_router(checkin_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
