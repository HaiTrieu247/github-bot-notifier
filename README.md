# GitHub Discord Bot

Backend service kết nối **GitHub** với **Discord** — nhận webhook events, gửi notifications, Discord Slash Commands.

Kiến trúc theo **SYSTEM_BLUEPRINT.md**: Layered Architecture (Route → Service → Repository → Database).

## Cấu trúc

```
backend/
├── src/
│   ├── __init__.py           ← FastAPI app factory + lifespan (init_db + Discord bot)
│   ├── config.py             ← Pydantic Settings (singleton Config)
│   ├── db/
│   │   └── main.py           ← init_db(), get_session(), _run_migrations() (no Alembic)
│   ├── models/               ← SQLModel tables
│   │   ├── repository.py
│   │   ├── event.py
│   │   ├── workflow_run.py
│   │   └── deployment.py
│   ├── repository/           ← Class-based DB access layer (CRUD thuần túy)
│   │   ├── repository.py     ← RepositoryRepo
│   │   ├── event.py          ← EventRepo (idempotency check)
│   │   ├── workflow_run.py   ← WorkflowRunRepo
│   │   └── deployment.py     ← DeploymentRepo
│   ├── schemas/              ← Pydantic request/response schemas
│   │   ├── repository.py
│   │   └── health.py
│   ├── services/             ← Business logic layer (DI pattern)
│   │   ├── event.py          ← EventService
│   │   ├── notification.py   ← NotificationService
│   │   └── repository.py     ← RepositoryService
│   ├── routes/               ← HTTP endpoints
│   │   ├── webhook.py        ← POST /github/webhook
│   │   ├── repositories.py   ← CRUD /api/v1/repositories
│   │   └── health.py         ← GET /health
│   ├── github/               ← GitHub REST client + event parsers
│   │   ├── client.py
│   │   ├── webhooks.py
│   │   └── events.py
│   └── bot/                  ← Discord bot + slash commands
│       ├── client.py
│       ├── notifications.py
│       └── commands/
│           ├── status.py     ← /status [repo]
│           ├── repos.py      ← /repos
│           ├── logs.py       ← /logs [repo] [limit]
│           └── check.py      ← /check [repo]
├── tests/
├── requirements.txt
├── Dockerfile
└── .env_example
```

## Layer Rules (Blueprint)

| Layer | Trách nhiệm | KHÔNG được làm |
|-------|-------------|----------------|
| **Route** | Nhận request, validate schema, gọi service | Không chứa logic, không query DB trực tiếp |
| **Service** | Business logic, orchestration, custom exceptions | Không gọi session/SQL trực tiếp |
| **Repository** | CRUD database (class-based) | Không chứa business logic |
| **Schema** | Request/response types (Pydantic) | Không nằm inline trong route |
| **Model** | SQLModel table definitions | Chỉ khai báo cấu trúc |

## Setup

```bash
# 1. Copy và điền env
cp .env.example .env

# 2. Chạy
docker compose up -d

# Staging (với Nginx HTTPS)
mkdir -p nginx/certs
openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout nginx/certs/privkey.pem \
  -out nginx/certs/fullchain.pem \
  -days 365 -subj '/CN=staging.example.com'

docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

Database tables được tạo tự động khi khởi động (qua `init_db()`). Không cần Alembic.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/github/webhook` | GitHub webhook receiver (HMAC verified) |
| `GET` | `/health` | Health check (DB + Discord) |
| `GET` | `/api/v1/repositories` | List monitored repos |
| `POST` | `/api/v1/repositories` | Add repository |
| `GET` | `/api/v1/repositories/{id}` | Get repository |
| `DELETE` | `/api/v1/repositories/{id}` | Remove repository |

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | ✅ | Discord Bot token |
| `DISCORD_GUILD_ID` | ✅ | Discord Server ID |
| `DISCORD_DEFAULT_CHANNEL_ID` | ✅ | Default notification channel |
| `DISCORD_REPO_CHANNEL_MAP` | | `owner/repo:channel_id,...` per-repo |
| `GITHUB_TOKEN` | ✅ | GitHub Personal Access Token |
| `GITHUB_WEBHOOK_SECRET` | ✅ | Webhook HMAC secret |
| `GITHUB_REPOSITORIES` | ✅ | `owner/repo,...` repos to monitor |
| `DATABASE_URL` | ✅ | PostgreSQL async URL |
| `POSTGRES_PASSWORD` | ✅ | Postgres password |
