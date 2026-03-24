from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine

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


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
