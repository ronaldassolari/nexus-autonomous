# Deployment Environments — Nexus Autonomous

ISO 25010:2023 — Portability: Adaptability & Installability

## Supported Environments

| Environment | Method | Requirements |
|-------------|--------|-------------|
| macOS (dev) | `bash scripts/install.sh` | Python 3.11+ |
| Linux (VPS) | `bash scripts/install.sh` | Python 3.11+ |
| Docker | `docker compose up` | Docker, Docker Compose |
| Cloud (Railway/Render) | Git push | Python 3.11 buildpack |

## Environment Configuration

All behavior controlled via environment variables and file paths:

```bash
# Development (default)
# No env vars needed — uses local filesystem

# Production (add to .env or export)
NEXUS_LOG_LEVEL=INFO              # DEBUG, INFO, WARN, ERROR
NEXUS_DATA_DIR=/data/nexus        # Custom data directory
SEMRUSH_API_KEY=sk-...            # Optional: SEMrush validation
COINGECKO_RATE_LIMIT=10           # Requests per minute
```

## Data Portability

```bash
# Backup (single directory)
tar -czf nexus-backup-$(date +%Y%m%d).tar.gz comunicacao/ inteligencia/ financeiro/ projetos_ativos/ log_execucao.md

# Restore
tar -xzf nexus-backup-20260315.tar.gz
```

## Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install pytrends
CMD ["python3", "dashboard.py", "--modo", "texto"]
```
