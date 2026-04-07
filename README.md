# Mishmash

Collaborative data analysis platform. Upload datasets, run reproducible analyses, and share findings with the world.

## Features

- **Dataset Management** - Upload CSV, JSON, or Parquet files with automatic versioning and metadata extraction
- **Reproducible Analysis** - Write Python or R scripts that run in sandboxed containers against your datasets
- **Comments & Discussion** - Threaded comments on datasets, analyses, and publications
- **Dataset References** - Link datasets to show derivation, correlation, or supplementary relationships
- **Publications** - Write and share findings in Markdown, linked to source datasets and analysis runs

## Architecture

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend API | FastAPI (Python), SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| File Storage | S3-compatible (MinIO locally) |
| Task Queue | Celery + Redis |
| Code Execution | Docker containers (network-isolated, resource-limited) |

## Quick Start

```bash
# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Access the app
open http://localhost:3000     # Frontend
open http://localhost:8000/docs # API docs (Swagger)
open http://localhost:9001     # MinIO console
```

## Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Build Runner Images

```bash
docker build -t mishmash-runner-python runner/python/
docker build -t mishmash-runner-r runner/r/
```

## API Endpoints

### Datasets
- `POST /api/datasets` - Create dataset
- `GET /api/datasets` - List/search datasets
- `GET /api/datasets/{slug}` - Get dataset details
- `POST /api/datasets/{id}/upload` - Get presigned upload URL
- `POST /api/datasets/{id}/upload/complete` - Confirm upload
- `GET /api/datasets/{id}/preview` - Preview data (first N rows)
- `POST /api/datasets/{id}/references` - Add dataset reference
- `GET /api/datasets/{id}/references` - List references

### Analyses
- `POST /api/analyses` - Create analysis
- `GET /api/analyses` - List analyses
- `GET /api/analyses/{id}` - Get analysis details
- `PUT /api/analyses/{id}` - Update analysis
- `POST /api/analyses/{id}/run` - Trigger execution
- `GET /api/analyses/{id}/runs` - List run history

### Comments
- `POST /api/comments` - Create comment
- `GET /api/comments?target_type=...&target_id=...` - List comments
- `PUT /api/comments/{id}` - Edit comment
- `DELETE /api/comments/{id}` - Delete comment

### Publications
- `POST /api/publications` - Create publication
- `GET /api/publications` - List publications
- `GET /api/publications/{slug}` - Read publication
- `PUT /api/publications/{id}` - Update publication

## Code Execution Safety

Analysis scripts run in Docker containers with:
- No network access (`--network=none`)
- CPU limit (1 core) and memory limit (512MB)
- Read-only filesystem (except `/output/`)
- 5-minute timeout
- Non-root user
- Datasets mounted read-only at `/data/`

## License

MIT
