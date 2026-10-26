import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, claim, group, user, leaderboard, rubric, notification, admin
from app.db.db import SessionLocal
from app.crud.rubric import seed_default_rubric


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically seed default rubric values if database is accessible
    try:
        db = SessionLocal()
        seed_default_rubric(db)
        db.close()
    except Exception:
        pass
    yield


app = FastAPI(
    title="AMRITA MITHRA — Student Achievement Leaderboard API",
    version="2.1",
    lifespan=lifespan,
)

# CORS configuration
allowed_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
if "*" in allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(claim.router, prefix="/claim", tags=["Claims"])
app.include_router(group.router, prefix="/group", tags=["MITHRA Verticals & Queues"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Public Leaderboard"])
app.include_router(rubric.router, prefix="/rubric", tags=["Scoring Rubric"])
app.include_router(notification.router, prefix="/notification", tags=["Notifications"])
app.include_router(admin.router, prefix="/admin", tags=["Admin Console & Reports"])


@app.get("/")
def root():
    return {
        "title": "AMRITA MITHRA — Student Achievement Leaderboard API",
        "campus": "Amrita Vishwa Vidyapeetham — Amritapuri Campus",
        "version": "2.1",
        "docs_url": "/docs",
    }