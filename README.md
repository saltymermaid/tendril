# Tendril 🌱

A personal gardening planning and tracking PWA built for a home gardener in **St. Petersburg, Florida (USDA Zone 10a)**. Tendril's core goal is maximizing food production through succession planting — always having a new seedling ready to go in the ground the moment an old plant comes out.

Since Zone 10a has no frost, growing is year-round, and Tendril's planning model reflects that: no frost-date logic, outdoor starter trays instead of indoor grow lights, and a square-foot-gardening grid where every square tracks exactly what's planted and when it needs to be replaced.

## Features

- Google OAuth login, restricted to an allow-list of accounts
- Grid-based garden beds (square foot gardening) with companion planting rules
- Seed catalog with per-variety germination/harvest timing and planting method
- Seed packet photo import via the Claude API
- Gantt-style timeline views (full year + rolling 3-month) with computed lifecycle phases
- Time-slider view to see any bed as it looked on any past date
- "What can I plant here?" recommendation engine
- Auto-generated and manual tasks, irrigation tracking, and weather display
- Installable PWA with push notifications

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12 + FastAPI 0.115 |
| Frontend | React 18 + TypeScript + Vite 6 |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic |
| Auth | Google OAuth + JWT in httpOnly cookies |
| AI | Anthropic Claude API (seed packet extraction) |
| Push | Web Push (VAPID / pywebpush) |
| Storage | Cloudflare R2 (S3-compatible) |
| Infra | Docker Compose, nginx, Cloudflare Tunnel, GitHub Actions |

## Getting Started

**Prerequisites:** Docker Engine 24+ and Docker Compose v2.

```bash
git clone https://github.com/melissablades/tendril.git
cd tendril
cp .env.example .env
docker compose up -d
docker compose exec backend alembic upgrade head
```

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)

Log in without setting up Google OAuth using the dev login endpoint:

```bash
curl -X POST http://localhost:8000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@tendril.garden"}'
```

### Useful dev commands

```bash
# Reset local DB (drop all tables, re-migrate, re-seed dev data)
docker compose exec backend python -m scripts.reset_db

# Run migrations
docker compose exec backend alembic upgrade head

# Backend logs
docker compose logs -f backend
```

## Project Structure

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, pytest suite
frontend/   React + TypeScript + Vite PWA
deploy/     Production deployment guide, nginx, Cloudflare Tunnel config
docs/       Product requirements and frontend style guide
```

## Deployment

Tendril is designed to run on a self-hosted server behind a Cloudflare Tunnel (no open ports). See [deploy/README.md](deploy/README.md) for the full production setup guide.

## Documentation

- [Product Requirements](docs/tendril-PRD.md)
- [Frontend Style Guide](docs/style-guide.md)
