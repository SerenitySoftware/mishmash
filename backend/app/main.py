from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyses, auth, comments, datasets, publications, stars, users

app = FastAPI(
    title=settings.app_name,
    description="Collaborative data analysis platform — upload, analyze, and share datasets with reproducible results",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth & users
app.include_router(auth.router)
app.include_router(users.router)

# Core features
app.include_router(datasets.router)
app.include_router(analyses.router)
app.include_router(comments.router)
app.include_router(publications.router)
app.include_router(stars.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "version": "0.2.0"}
