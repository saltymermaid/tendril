# Tendril — Deployment Guide

## Architecture

```
Internet → Cloudflare (SSL/CDN) → Cloudflare Tunnel → nginx (frontend:80)
                                                          ├── Static assets (React SPA)
                                                          └── /api/* → backend:8000 (gunicorn+uvicorn)
                                                                          └── PostgreSQL (db:5432)
```

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- Git
- A domain managed by Cloudflare (for tunnel/SSL)
- Google OAuth credentials (for authentication)

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/melissablades/tendril.git
cd tendril

# Create production environment file
cp .env.production.example .env
# Edit .env with your actual values
nano .env
```

### 2. Initial Setup

```bash
# Start the database first
docker compose -f docker-compose.prod.yml up -d db

# Run database migrations
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Seed initial data — run ONCE on first deployment
docker compose -f docker-compose.prod.yml run --rm backend python -m scripts.seed_production

# Start all services
docker compose -f docker-compose.prod.yml up -d
```

### 3. Enable Cloudflare Tunnel (Optional)

```bash
# Add CLOUDFLARE_TUNNEL_TOKEN to .env, then:
docker compose -f docker-compose.prod.yml --profile tunnel up -d
```

### 4. Enable Automated Backups

```bash
docker compose -f docker-compose.prod.yml --profile backup up -d
```

## Updating

```bash
# Pull latest code
git pull origin main

# Pull/rebuild images
docker compose -f docker-compose.prod.yml build

# Run any new migrations
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Restart with new images
docker compose -f docker-compose.prod.yml up -d
```

## Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| `db` | tendril-db | 5432 (internal) | PostgreSQL 16 |
| `backend` | tendril-backend | 8000 (internal) | FastAPI + Gunicorn |
| `frontend` | tendril-frontend | 80 (exposed) | nginx + React SPA |
| `cloudflared` | tendril-tunnel | — | Cloudflare Tunnel (optional) |
| `db-backup` | tendril-db-backup | — | Daily backup cron (optional) |

## Backups

### Automated
The `db-backup` service runs daily at 2 AM:
- Daily backups kept for 30 days
- Weekly backups (Sunday) kept for 90 days
- Stored in `deploy/backups/`

### Manual Backup
```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U tendril -Fc tendril | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore
```bash
./deploy/scripts/restore.sh deploy/backups/daily/tendril_20260401_020000.sql.gz
```

## Monitoring

```bash
# Check all services
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Health check
curl http://localhost/api/health

# Database size
docker compose -f docker-compose.prod.yml exec db \
  psql -U tendril -c "SELECT pg_size_pretty(pg_database_size('tendril'));"
```

## Troubleshooting

### Backend won't start
```bash
docker compose -f docker-compose.prod.yml logs backend
# Check if database is ready
docker compose -f docker-compose.prod.yml exec db pg_isready -U tendril
```

### Frontend returns 502
```bash
# Check if backend is healthy
docker compose -f docker-compose.prod.yml exec frontend \
  wget -q --spider http://backend:8000/api/health && echo "OK" || echo "FAIL"
```

### Reset everything
```bash
docker compose -f docker-compose.prod.yml down -v
# Then follow Quick Start from step 2
```

## Environment Variables

See [`.env.production.example`](../.env.production.example) for all required variables.

### Required for Production
| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Strong database password |
| `SECRET_KEY` | JWT signing key (64+ chars) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `ALLOWED_EMAILS` | Comma-separated allowed emails |

### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `FRONTEND_PORT` | Host port for frontend | `80` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://tendril.garden` |
| `CLOUDFLARE_TUNNEL_TOKEN` | Tunnel token | — |
| `ANTHROPIC_API_KEY` | For seed packet AI | — |
| `VAPID_*` | Push notification keys | — |
| `R2_*` | Cloudflare R2 storage | — |
