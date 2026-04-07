from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyses, comments, datasets, publications

app = FastAPI(
    title=settings.app_name,
    description="Collaborative data analysis platform - upload, analyze, and share datasets",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(analyses.router)
app.include_router(comments.router)
app.include_router(publications.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": settings.app_name}
