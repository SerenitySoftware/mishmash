from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyses, api_keys, auth, comments, datasets, notifications, publications, stars, users, validation

app = FastAPI(
    title=settings.app_name,
    description="Collaborative data analysis platform — upload, analyze, and share datasets with reproducible results",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth & users
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(api_keys.router)

# Core features
app.include_router(datasets.router)
app.include_router(analyses.router)
app.include_router(comments.router)
app.include_router(publications.router)
app.include_router(stars.router)
app.include_router(notifications.router)
app.include_router(validation.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "version": "0.3.0"}
