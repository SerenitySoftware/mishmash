# Mishmash

Collaborative data analysis platform. Upload datasets, run reproducible analyses, and share findings with the world.

## Features

- **User Accounts** — Register, login, user profiles showing all datasets/analyses/publications
- **Dataset Management** — Upload CSV, JSON, or Parquet files with automatic versioning, metadata extraction, and schema analysis
- **Forking & Starring** — Fork any dataset or analysis; star your favorites; discover popular content
- **Reproducible Analysis** — Write Python or R scripts that run in sandboxed containers or locally via the CLI
- **Proof of Work** — Run analyses on your own machine with cryptographic proof that ties results to specific inputs
- **Comments & Discussion** — Threaded comments with author attribution on datasets, analyses, and publications
- **Dataset References** — Link datasets (derived_from, joins_with, supplements, forked_from) to build a knowledge graph
- **Publications** — Write and share findings in Markdown, linked to source datasets and analysis runs
- **CLI Tool** — Upload datasets, run analyses locally, and manage your account from the terminal
- **Search & Discovery** — Full-text search, sort by stars/downloads/recency, filter by language/tags

## Architecture

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Monaco Editor |
| Backend API | FastAPI (Python), SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 with JSONB, full-text search |
| File Storage | S3-compatible (MinIO locally, S3 in prod) |
| Task Queue | Celery + Redis |
| Code Execution | Docker containers (network-isolated, resource-limited) |
| Auth | JWT tokens with bcrypt password hashing |
| CLI | Python CLI (click + rich + httpx) |

## Quick Start

```bash
# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Build runner images (for server-side execution)
docker build -t mishmash-runner-python runner/python/
docker build -t mishmash-runner-r runner/r/

# Access the app
open http://localhost:3000     # Frontend
open http://localhost:8000/docs # API docs (Swagger)
open http://localhost:9001     # MinIO console (mishmash / mishmash_dev)
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

### CLI Tool

```bash
cd cli
pip install -e .
mishmash register
mishmash upload data.csv --name "My Dataset" --tags "economics,2024"
mishmash run <analysis-id>
```

## API Endpoints

### Auth
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Get JWT token
- `GET /api/auth/me` — Current user
- `PUT /api/auth/me` — Update profile

### Users
- `GET /api/users/{username}` — User profile with counts
- `GET /api/users/{username}/datasets` — User's datasets
- `GET /api/users/{username}/analyses` — User's analyses
- `GET /api/users/{username}/publications` — User's publications

### Datasets
- `POST /api/datasets` — Create dataset (auth required)
- `GET /api/datasets` — List/search (query, tags, sort, owner)
- `GET /api/datasets/{slug}` — Get dataset details
- `PUT /api/datasets/{id}` — Update dataset (owner only)
- `DELETE /api/datasets/{id}` — Delete dataset (owner only)
- `POST /api/datasets/{id}/upload` — Get presigned upload URL
- `POST /api/datasets/{id}/upload/complete` — Confirm upload
- `GET /api/datasets/{id}/preview` — Preview data (first N rows)
- `GET /api/datasets/{id}/download` — Get presigned download URL
- `POST /api/datasets/{id}/fork` — Fork a dataset
- `POST /api/datasets/{id}/references` — Add dataset reference
- `GET /api/datasets/{id}/references` — List references

### Analyses
- `POST /api/analyses` — Create analysis
- `GET /api/analyses` — List/search analyses
- `GET /api/analyses/{id}` — Get analysis details
- `PUT /api/analyses/{id}` — Update analysis (owner only)
- `DELETE /api/analyses/{id}` — Delete analysis (owner only)
- `POST /api/analyses/{id}/fork` — Fork an analysis
- `POST /api/analyses/{id}/run` — Trigger server-side execution
- `POST /api/analyses/{id}/challenge` — Get proof-of-work challenge
- `POST /api/analyses/{id}/submit-proof` — Submit local execution results
- `GET /api/analyses/{id}/runs` — List run history

### Stars
- `POST /api/stars/{type}/{id}` — Star a dataset or analysis
- `DELETE /api/stars/{type}/{id}` — Unstar
- `GET /api/stars/{type}/{id}/check` — Check if starred

### Comments
- `POST /api/comments` — Create comment (auth required)
- `GET /api/comments?target_type=...&target_id=...` — List comments
- `PUT /api/comments/{id}` — Edit comment (author only)
- `DELETE /api/comments/{id}` — Delete comment (author only)

### Publications
- `POST /api/publications` — Create publication
- `GET /api/publications` — List/search publications
- `GET /api/publications/{slug}` — Read publication
- `PUT /api/publications/{id}` — Update (author only)
- `DELETE /api/publications/{id}` — Delete (author only)

## Proof of Work

The proof-of-work system allows users to run analyses locally and submit results with cryptographic verification:

1. **Challenge**: Request a computation challenge for an analysis
2. **Execute**: Run the analysis locally using the CLI (`mishmash run <id>`)
3. **Prove**: CLI computes SHA-256(source_hash | dataset_hashes | output_hash | nonce) meeting a difficulty target
4. **Submit**: Upload results with proof — server verifies and records the run

This doesn't prevent fabrication but proves computational work was done, and ties results to specific source code and input data versions.

## Code Execution Safety

Server-side analysis scripts run in Docker containers with:
- No network access (`--network=none`)
- CPU limit (1 core) and memory limit (512MB)
- Read-only filesystem (except `/output/`)
- 5-minute timeout
- Non-root user
- Datasets mounted read-only at `/data/`

## License

MIT
