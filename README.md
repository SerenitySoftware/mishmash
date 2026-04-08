# Mishmash

Collaborative data analysis platform. Upload datasets, run reproducible analyses, and share findings with the world.

## Features

### Core
- **User Accounts** — Registration, login, JWT auth, API keys for programmatic access
- **User Profiles** — `/u/{username}` showing datasets, analyses, publications with activity counts
- **Account Settings** — Edit profile, manage API keys

### Datasets
- **Upload & Version** — CSV, JSON, Parquet via presigned S3 URLs with automatic versioning
- **Metadata Extraction** — Column types, stats (min/max/mean), row counts, checksums (SHA-256)
- **Quality Analysis** — Quality score (0-100), null detection, duplicate checking, outlier flagging, mixed-type detection
- **Preview** — Paginated data table preview of any dataset version
- **Download** — Presigned download URLs with download counter
- **Licensing** — CC0, CC-BY, ODbL, MIT license selection
- **Changelogs** — Version-level changelog text for documenting changes

### Analyses
- **Code Editor** — Monaco editor for Python, R, and SQL with syntax highlighting
- **Environment Pinning** — Specify pip requirements or R packages for reproducibility
- **Sandboxed Execution** — Docker containers with no network, CPU/memory limits, read-only filesystem
- **Real-time Status** — Server-Sent Events for live run status updates via Redis pub/sub
- **Run History** — Full history with stdout/stderr, duration, status
- **Result Files** — Output file listing with presigned download URLs and MIME type detection
- **Dataset Linking** — Link analyses to specific dataset versions with aliases
- **Proof of Work** — Run locally with cryptographic verification tying results to specific inputs

### Social
- **Starring** — Star datasets and analyses, sorted leaderboards
- **Forking** — Fork datasets or analyses with lineage tracking
- **Comments** — Threaded comments with author attribution on all entities
- **Notifications** — Bell icon with unread count for comments, stars, forks, run completions

### Publications
- **Markdown Editor** — Write findings in Markdown with live preview
- **Reference Linking** — Link publications to datasets and analysis runs
- **Author Display** — Author names with profile links
- **Inline Editing** — Authors can edit published content

### Discovery
- **Unified Search** — Full-text search across datasets, analyses, and publications using PostgreSQL GIN indexes with relevance ranking
- **Filtering** — Sort by stars, downloads, recency; filter by language, tags, owner
- **Citation Generation** — BibTeX, APA, RIS, and plain text citations with stable identifiers and checksums

### Developer Experience
- **API Keys** — Create/revoke `msh_...` keys for CI/CD pipelines
- **CLI Tool** — `mishmash register/login/upload/run/list-datasets/list-analyses`
- **Swagger Docs** — Full OpenAPI at `/api/docs`

## Architecture

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Monaco Editor |
| Backend API | FastAPI (Python), SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 with JSONB, GIN full-text search |
| File Storage | S3-compatible (MinIO locally, S3 in prod) |
| Task Queue | Celery + Redis |
| Real-time | Server-Sent Events via Redis pub/sub |
| Code Execution | Docker containers (network-isolated) |
| Auth | JWT + API keys, bcrypt password hashing |
| CLI | Python CLI (click + rich + httpx) |

## Quick Start

```bash
# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Build runner images
docker build -t mishmash-runner-python runner/python/
docker build -t mishmash-runner-r runner/r/

# Access the app
open http://localhost:3000     # Frontend
open http://localhost:8000/docs # API docs (Swagger)
open http://localhost:9001     # MinIO console (mishmash / mishmash_dev)
```

## API Reference

### Auth & Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user |
| PUT | `/api/auth/me` | Update profile |
| GET | `/api/users/{username}` | User profile |
| GET | `/api/users/{username}/datasets` | User's datasets |
| GET | `/api/users/{username}/analyses` | User's analyses |
| GET | `/api/users/{username}/publications` | User's publications |

### API Keys
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/keys` | Create API key |
| GET | `/api/keys` | List API keys |
| DELETE | `/api/keys/{id}` | Revoke API key |

### Datasets
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/datasets` | Create dataset |
| GET | `/api/datasets` | List/search (q, tags, sort, owner) |
| GET | `/api/datasets/{slug}` | Get details |
| PUT | `/api/datasets/{id}` | Update (owner only) |
| DELETE | `/api/datasets/{id}` | Delete (owner only) |
| POST | `/api/datasets/{id}/upload` | Get presigned upload URL |
| POST | `/api/datasets/{id}/upload/complete` | Confirm upload |
| GET | `/api/datasets/{id}/preview` | Preview first N rows |
| GET | `/api/datasets/{id}/download` | Presigned download URL |
| POST | `/api/datasets/{id}/fork` | Fork a dataset |
| GET | `/api/datasets/{id}/validate` | Run quality validation |
| GET | `/api/datasets/{id}/stats` | Statistical summary |
| GET | `/api/datasets/{id}/cite` | Generate citation (bibtex/apa/ris) |
| POST | `/api/datasets/{id}/references` | Add cross-reference |
| GET | `/api/datasets/{id}/references` | List references |
| GET | `/api/datasets/{id}/versions` | List versions |

### Analyses
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyses` | Create analysis |
| GET | `/api/analyses` | List/search (q, language, sort) |
| GET | `/api/analyses/{id}` | Get details |
| PUT | `/api/analyses/{id}` | Update (owner only) |
| DELETE | `/api/analyses/{id}` | Delete (owner only) |
| POST | `/api/analyses/{id}/fork` | Fork an analysis |
| POST | `/api/analyses/{id}/run` | Trigger server-side execution |
| POST | `/api/analyses/{id}/challenge` | Get PoW challenge |
| POST | `/api/analyses/{id}/submit-proof` | Submit local results |
| GET | `/api/analyses/{id}/runs` | List run history |
| GET | `/api/analyses/{id}/runs/{run_id}` | Get run details |
| GET | `/api/analyses/{id}/runs/{run_id}/results` | List output files |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search?q=...&type=all` | Unified full-text search |

### Real-time
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events/runs/{run_id}/stream` | SSE for run status |

### Stars
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/stars/{type}/{id}` | Star |
| DELETE | `/api/stars/{type}/{id}` | Unstar |
| GET | `/api/stars/{type}/{id}/check` | Check if starred |

### Comments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/comments` | Create comment |
| GET | `/api/comments?target_type=...&target_id=...` | List comments |
| PUT | `/api/comments/{id}` | Edit (author only) |
| DELETE | `/api/comments/{id}` | Delete (author only) |

### Publications
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/publications` | Create publication |
| GET | `/api/publications` | List/search |
| GET | `/api/publications/{slug}` | Read publication |
| PUT | `/api/publications/{id}` | Update (author only) |
| DELETE | `/api/publications/{id}` | Delete (author only) |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | List notifications |
| POST | `/api/notifications/{id}/read` | Mark as read |
| POST | `/api/notifications/read-all` | Mark all as read |
| GET | `/api/notifications/unread-count` | Get unread count |

## Database Schema (14 tables + 4 migrations)

- `users` — accounts with bcrypt passwords
- `datasets` — versioned data files with metadata, stars, forks
- `dataset_versions` — immutable snapshots with checksums and quality profiles
- `dataset_references` — cross-links between datasets
- `analyses` — code with environment requirements
- `analysis_datasets` — analysis-to-dataset links with version pinning
- `analysis_runs` — execution history with PoW fields
- `comments` — threaded, polymorphic (on any entity)
- `publications` — markdown findings
- `publication_references` — links to datasets and analysis runs
- `stars` — user stars on datasets and analyses
- `api_keys` — hashed API keys for programmatic access
- `notifications` — user notifications with read status

## Proof of Work

Enables users to run analyses locally and submit cryptographically verified results:

1. `POST /api/analyses/{id}/challenge` — Get challenge (source hash + dataset hashes + nonce seed)
2. Run locally via `mishmash run <id>` — Executes code, computes output hash
3. Find nonce where `SHA-256(source_hash | dataset_hashes | output_hash | nonce)` has N leading zeros
4. `POST /api/analyses/{id}/submit-proof` — Submit with proof hash, nonce, output, environment info

## Code Execution Safety

Server-side analysis scripts run in Docker containers with:
- No network access (`--network=none`) — unless requirements need installing
- CPU limit (1 core) and memory limit (512MB)
- Read-only filesystem (except `/output/` and `/tmp/`)
- 5-minute timeout
- Non-root user
- Datasets mounted read-only at `/data/`

## Future Roadmap

- [ ] Organizations and team-based access control
- [ ] Jupyter notebook import/export
- [ ] Preview caching with Redis
- [ ] OAuth login (GitHub, ORCID)
- [ ] Rate limiting with Redis sliding windows
- [ ] Python/R SDK packages (`mishmash.load("owner/slug")`)
- [ ] Webhook integrations for external pipelines
- [ ] Activity feed with follow system
- [ ] Dataset version diffs (row/column changes)
- [ ] Vega-Lite chart rendering from analysis outputs

## License

MIT
