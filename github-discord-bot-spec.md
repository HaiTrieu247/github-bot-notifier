# Đặc tả hệ thống GitHub Discord Bot

## 1. Tổng quan

### 1.1. Tên hệ thống

**GitHub Discord Bot**

### 1.2. Mục tiêu

Xây dựng một backend service kết nối **GitHub** với **Discord**, cho phép theo dõi một hoặc nhiều GitHub repository và gửi thông báo tự động vào Discord.

Bot đồng thời cung cấp Discord Slash Commands để người dùng chủ động kiểm tra trạng thái repository thông qua GitHub API.

### 1.3. Nguyên tắc thiết kế

MVP được thiết kế theo hướng **stateless**, không sử dụng PostgreSQL hoặc database.

GitHub là **source of truth** cho repository, commit, Pull Request, GitHub Actions và deployment.

Bot chỉ chịu trách nhiệm:

- Nhận GitHub Webhook.
- Xử lý GitHub event.
- Gửi notification đến Discord.
- Gọi GitHub API khi người dùng sử dụng command.
- Cung cấp Discord Slash Commands.
- Cung cấp HTTP health check.

Database chỉ được bổ sung ở các phiên bản sau nếu cần lưu lịch sử event, cấu hình phức tạp, multi-server hoặc các dữ liệu riêng của bot.

---

# 2. Kiến trúc hệ thống

```text
                        ┌──────────────────┐
                        │      GitHub      │
                        │                  │
                        │ Repository       │
                        │ Actions          │
                        │ Pull Requests    │
                        │ Issues           │
                        │ Deployments      │
                        └────────┬─────────┘
                                 │
                            Webhook Events
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │      FastAPI Backend   │
                    │                        │
                    │  /github/webhook       │
                    │  /health               │
                    │                        │
                    │  Webhook Handler       │
                    │  Event Processor       │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │      Discord Bot       │
                    │                        │
                    │  Slash Commands        │
                    │  Notifications         │
                    └───────────┬────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Discord Server  │
                       │                 │
                       │ #github-status  │
                       │ #github-pr      │
                       │ #github-deploy  │
                       └─────────────────┘

                         ┌──────────────┐
                         │ GitHub API   │
                         │              │
                         │ /status      │
                         │ /repos       │
                         │ /logs        │
                         │ /check       │
                         └──────────────┘
                                ▲
                                │
                         Discord Commands
```

---

# 3. Công nghệ

## 3.1. Backend

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic
- httpx

## 3.2. Discord

- discord.py
- Discord Application
- Discord Bot
- Discord Slash Commands
- Discord Embed

## 3.3. GitHub

- GitHub REST API
- GitHub Webhooks
- GitHub Actions

## 3.4. Infrastructure

- Docker
- Docker Compose
- Nginx hoặc Caddy
- HTTPS

## 3.5. Database

**Không sử dụng database trong MVP.**

---

# 4. Các thành phần chính

## 4.1. FastAPI Backend

Backend chịu trách nhiệm:

1. Nhận GitHub Webhook.
2. Xác thực Webhook signature.
3. Parse GitHub events.
4. Xác định repository và event type.
5. Chuyển event thành Discord notification.
6. Gửi notification thông qua Discord Bot.
7. Cung cấp health check.
8. Gọi GitHub API cho các request cần dữ liệu realtime.

Backend không lưu trạng thái GitHub vào database.

---

## 4.2. Discord Bot

Discord Bot chịu trách nhiệm:

- Đăng ký Slash Commands.
- Xử lý command từ người dùng.
- Gọi GitHub API.
- Trả về repository status.
- Gửi notification vào Discord channel.
- Format thông tin bằng Discord Embed.

---

## 4.3. GitHub Webhook Handler

GitHub gửi HTTP request đến:

```http
POST /github/webhook
```

Các event được hỗ trợ trong MVP:

- `push`
- `pull_request`
- `workflow_run`
- `deployment`
- `deployment_status`

Các event khác có thể bổ sung trong tương lai.

---

# 5. GitHub Push Event

Khi có:

```bash
git push
```

GitHub gửi webhook đến backend.

Bot gửi notification:

```text
📦 New Push

Repository:
Kens0107/homestay-backend

Branch:
main

Author:
Kens0107

Commit:
a82f31c

Message:
fix authentication bug

View Commit
```

Notification phải chứa link trực tiếp đến commit trên GitHub.

---

# 6. GitHub Actions

Bot phải theo dõi GitHub Actions thông qua event:

```text
workflow_run
```

Các trạng thái cần xử lý:

```text
queued
in_progress
completed
```

Khi workflow hoàn thành, kiểm tra `conclusion`.

Các conclusion chính:

```text
success
failure
cancelled
skipped
timed_out
```

## 6.1. Success

```text
🟢 GitHub Action Success

Repository:
homestay-backend

Workflow:
CI

Branch:
main

Commit:
a82f31c

Duration:
2m 31s

View Workflow
```

## 6.2. Failure

```text
🔴 GitHub Action Failed

Repository:
homestay-backend

Workflow:
CI

Branch:
main

Commit:
a82f31c

Status:
failure

View Workflow
```

Notification phải có link đến GitHub Actions run.

---

# 7. Pull Request

Khi Pull Request được mở:

```text
🔵 Pull Request Opened

Repository:
homestay-backend

PR:
#42

Title:
Add authentication middleware

Author:
Kens0107

Branch:
feature/auth

→ main

View Pull Request
```

Khi Pull Request được merge:

```text
🟣 Pull Request Merged

Repository:
homestay-backend

PR:
#42

Title:
Add authentication middleware

Merged by:
Kens0107

View Pull Request
```

---

# 8. Deployment

Nếu repository sử dụng GitHub Deployments, bot có thể theo dõi:

```text
deployment
deployment_status
```

Ví dụ:

```text
🚀 Deployment Success

Repository:
homestay-backend

Environment:
production

Commit:
a82f31c

Status:
success

View Deployment
```

Khi thất bại:

```text
🔴 Deployment Failed

Repository:
homestay-backend

Environment:
production

Commit:
a82f31c

Status:
failure

View Deployment
```

---

# 9. Discord Slash Commands

## 9.1. `/status`

Hiển thị trạng thái của các repository đang được cấu hình.

```text
/status
```

Ví dụ:

```text
GitHub Status

🟢 homestay-backend
    CI: SUCCESS
    Deploy: SUCCESS

🟢 homestay-frontend
    CI: SUCCESS
    Deploy: SUCCESS

🔴 9router
    CI: FAILED
    Deploy: -

Last checked:
Just now
```

Bot lấy dữ liệu trực tiếp từ GitHub API.

---

# 10. `/status <repository>`

Ví dụ:

```text
/status homestay-backend
```

Bot gọi GitHub API và trả về:

```text
🟢 homestay-backend

Repository:
Kens0107/homestay-backend

Default branch:
main

Latest commit:
a82f31c

Author:
Kens0107

CI:
🟢 SUCCESS

Deployment:
🟢 SUCCESS

Last push:
2 minutes ago

Latest workflow:
CI

View Repository
```

Không lấy dữ liệu từ database.

---

# 11. `/repos`

Liệt kê repository được cấu hình để monitor.

```text
/repos
```

Ví dụ:

```text
Monitored Repositories

1. homestay-backend
   🟢 Active

2. homestay-frontend
   🟢 Active

3. 9router
   🟢 Active
```

Danh sách repository trong MVP có thể được cấu hình bằng environment variable hoặc file cấu hình.

Ví dụ:

```env
GITHUB_REPOSITORIES=Kens0107/homestay-backend,Kens0107/homestay-frontend
```

---

# 12. `/logs`

MVP không lưu event history vào database.

Do đó `/logs` phải lấy dữ liệu trực tiếp từ GitHub API.

Ví dụ:

```text
/logs homestay-backend
```

Bot có thể lấy:

- Recent commits
- Recent workflow runs
- Recent Pull Requests

Ví dụ response:

```text
Recent GitHub Activity

16:03 🟢 CI SUCCESS
homestay-backend

15:59 📦 PUSH
homestay-backend

15:43 🔴 CI FAILED
homestay-backend

15:40 🟣 PR MERGED
homestay-backend
```

---

# 13. `/check`

Force kiểm tra trạng thái GitHub.

```text
/check homestay-backend
```

Bot gọi GitHub API để kiểm tra:

- Latest commit
- Latest workflow
- Workflow status
- Deployment status
- Open Pull Requests

Sau đó trả về trạng thái hiện tại.

---

# 14. GitHub Webhook Security

Webhook phải được xác thực bằng:

```text
X-Hub-Signature-256
```

GitHub webhook secret được lưu trong environment:

```env
GITHUB_WEBHOOK_SECRET=xxxxxxxx
```

Backend sử dụng HMAC SHA-256 để verify request.

Không được tin tưởng trực tiếp request từ Internet.

Webhook request không hợp lệ phải trả:

```http
401 Unauthorized
```

---

# 15. Authentication

GitHub API authentication không được hard-code.

Không được:

```python
GITHUB_TOKEN = "ghp_xxxxxxxxx"
```

Token phải được lưu bằng environment variable hoặc secret manager.

Ví dụ:

```env
GITHUB_TOKEN=ghp_xxxxxxxxx
DISCORD_TOKEN=xxxxxxxx
GITHUB_WEBHOOK_SECRET=xxxxxxxx
```

---

# 16. Discord Bot Permissions

Bot chỉ yêu cầu các permission cần thiết:

- View Channels
- Send Messages
- Embed Links
- Read Message History
- Use Slash Commands

Không cấp:

```text
Administrator
```

nếu không cần thiết.

---

# 17. Discord Channel

MVP có thể sử dụng một channel duy nhất:

```text
#github-status
```

Tất cả GitHub notification được gửi vào channel này.

Ví dụ:

```text
#github-status

📦 Push
🟢 CI Success
🔴 CI Failed
🔵 Pull Request
🟣 Pull Request Merged
🚀 Deployment
```

Trong tương lai có thể cấu hình nhiều channel:

```text
#github-status
#github-pr
#github-deploy
```

---

# 18. Event Processing

Webhook phải xử lý nhanh và trả response cho GitHub.

Flow:

```text
GitHub
   │
   ▼
POST /github/webhook
   │
   ▼
Verify Signature
   │
   ▼
Parse Event
   │
   ▼
Create Discord Notification
   │
   ▼
Discord Bot
   │
   ▼
Discord Server
   │
   ▼
HTTP 200
```

Không cần lưu event vào database.

---

# 19. Idempotency

GitHub có thể retry Webhook.

Do MVP không có database nên backend phải hạn chế xử lý duplicate event trong memory nếu cần.

Có thể sử dụng GitHub event ID:

```text
X-GitHub-Delivery
```

để nhận diện event.

Backend có thể duy trì một bộ nhớ tạm thời:

```python
processed_events = set()
```

với giới hạn kích thước hoặc TTL.

Lưu ý: cơ chế này chỉ nhằm giảm duplicate trong cùng một process và không đảm bảo persistence sau khi restart.

Nếu yêu cầu idempotency mạnh và persistence được đặt ra trong tương lai, cần bổ sung Redis hoặc database.

---

# 20. Error Handling

Nếu GitHub API lỗi:

```text
GitHub API
    ❌
```

Bot phải trả lỗi rõ ràng:

```text
❌ Unable to retrieve GitHub status.

Reason:
GitHub API request failed.

Please try again later.
```

Nếu Discord API lỗi:

```text
Discord API
    ❌
```

Backend phải log lỗi.

Không được làm crash toàn bộ application chỉ vì một notification thất bại.

---

# 21. Rate Limit

GitHub API có rate limit.

Backend phải:

- Kiểm tra HTTP status.
- Xử lý `403`.
- Đọc GitHub rate limit headers khi cần.
- Không gọi API dư thừa.
- Ưu tiên dữ liệu từ Webhook cho notification.
- Chỉ gọi GitHub API khi command yêu cầu dữ liệu realtime.

---

# 22. Logging

Backend phải log:

```text
INFO
WARNING
ERROR
```

Ví dụ:

```text
INFO  GitHub webhook received
INFO  Repository: Kens0107/homestay-backend
INFO  Event: push
INFO  Commit: a82f31c

INFO  Discord notification sent

ERROR Discord API request failed
ERROR GitHub API rate limit exceeded
```

Không được log:

- Discord token
- GitHub token
- Webhook secret

---

# 23. Health Check

Endpoint:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

Có thể kiểm tra thêm dependency ở phiên bản sau.

---

# 24. Project Structure

```text
github-discord-bot/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── github.py
│   │   └── health.py
│   │
│   ├── bot/
│   │   ├── client.py
│   │   ├── commands/
│   │   │   ├── status.py
│   │   │   ├── repos.py
│   │   │   ├── logs.py
│   │   │   └── check.py
│   │   └── notifications.py
│   │
│   ├── github/
│   │   ├── client.py
│   │   ├── webhook.py
│   │   └── events.py
│   │
│   └── services/
│       ├── github_service.py
│       └── notification_service.py
│
├── tests/
│   ├── test_github.py
│   ├── test_webhook.py
│   └── test_discord.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 25. Docker Architecture

MVP chỉ cần một application container.

```yaml
services:

  bot:
    build: .
    restart: unless-stopped

    environment:
      DISCORD_TOKEN: ${DISCORD_TOKEN}
      DISCORD_GUILD_ID: ${DISCORD_GUILD_ID}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      GITHUB_WEBHOOK_SECRET: ${GITHUB_WEBHOOK_SECRET}
      GITHUB_REPOSITORIES: ${GITHUB_REPOSITORIES}

    ports:
      - "8000:8000"
```

Không cần PostgreSQL.

Không cần Redis.

Không cần message queue trong MVP.

---

# 26. Environment Variables

`.env.example`:

```env
# Discord
DISCORD_TOKEN=
DISCORD_GUILD_ID=

# GitHub
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=

# Repositories
GITHUB_REPOSITORIES=Kens0107/homestay-backend,Kens0107/homestay-frontend

# Application
APP_ENV=production
LOG_LEVEL=INFO
PORT=8000
```

Không commit `.env`.

---

# 27. Deployment

Production architecture:

```text
                         Internet
                            │
                            ▼
                    ┌───────────────┐
                    │ Cloudflare    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Nginx / Caddy │
                    └───────┬───────┘
                            │
                            ▼
                    ┌─────────────────────┐
                    │ GitHub Discord Bot  │
                    │                     │
                    │ FastAPI :8000       │
                    │ Discord Bot         │
                    └──────────┬──────────┘
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
                GitHub API          Discord API
```

Public endpoint:

```text
https://github-bot.example.com/github/webhook
```

Chỉ webhook endpoint cần được expose cho GitHub.

Discord Bot chủ yếu sử dụng outbound connection đến Discord API.

---

# 28. MVP

## GitHub

- [ ] GitHub Webhook
- [ ] Push event
- [ ] Workflow run
- [ ] CI success
- [ ] CI failure
- [ ] Pull Request opened
- [ ] Pull Request merged
- [ ] Deployment status

## Discord

- [ ] Discord Bot
- [ ] Slash Commands
- [ ] `/status`
- [ ] `/repos`
- [ ] `/logs`
- [ ] `/check`
- [ ] Push notification
- [ ] CI notification
- [ ] Pull Request notification
- [ ] Deployment notification

## Backend

- [ ] FastAPI
- [ ] GitHub REST client
- [ ] Discord client
- [ ] Webhook signature verification
- [ ] Event parsing
- [ ] Error handling
- [ ] Logging
- [ ] Health check
- [ ] In-memory duplicate event protection

## Infrastructure

- [ ] Docker
- [ ] Docker Compose
- [ ] HTTPS
- [ ] Nginx/Caddy
- [ ] Environment secrets

---

# 29. Future Features

Database chỉ được bổ sung khi hệ thống cần các tính năng yêu cầu persistent state.

```text
GitHub Discord Bot
│
├── Repository monitoring
├── GitHub Actions
├── Deployment monitoring
├── Pull Requests
├── Issues
├── Release notification
├── Discord commands
│
├── Future:
│   ├── PostgreSQL
│   ├── Redis
│   ├── Event history
│   ├── Multi-server configuration
│   ├── Notification preferences
│   ├── Web dashboard
│   ├── GitHub App authentication
│   └── Metrics
│
└── AI assistant
      ├── Explain CI error
      ├── Summarize PR
      └── Analyze failed deployment
```

---

# 30. Tiêu chí hoàn thành MVP

MVP được xem là hoàn thành khi:

1. Discord Bot kết nối thành công với Discord Server.
2. GitHub Webhook gửi event thành công.
3. Backend verify được webhook signature.
4. Push code lên repository tạo Discord notification.
5. GitHub Action success tạo Discord notification.
6. GitHub Action failure tạo Discord notification.
7. Pull Request event tạo Discord notification.
8. Deployment event tạo Discord notification.
9. `/status` trả về trạng thái repository từ GitHub API.
10. `/repos` trả về danh sách repository được cấu hình.
11. `/logs` lấy được hoạt động gần đây từ GitHub API.
12. `/check` kiểm tra trạng thái realtime từ GitHub.
13. Backend xử lý webhook duplicate ở mức in-memory.
14. Backend chạy ổn định bằng Docker Compose.
15. Webhook endpoint chạy qua HTTPS.
16. Không có GitHub/Discord secret nào được commit vào repository.
17. Không cần PostgreSQL hoặc Redis trong MV

# Đặc tả hệ thống GitHub Discord Bot

## 1. Tổng quan

### 1.1. Tên hệ thống

**GitHub Discord Bot**

### 1.2. Mục tiêu

Xây dựng một backend service kết nối **GitHub** với **Discord**, cho phép theo dõi trạng thái của nhiều GitHub repository và gửi thông báo tự động đến Discord.

Hệ thống đồng thời cung cấp Discord Bot với các command để người dùng chủ động kiểm tra trạng thái repository.

### 1.3. Mục tiêu chính

- Theo dõi nhiều GitHub repository.
- Nhận GitHub Webhook events theo thời gian thực.
- Theo dõi trạng thái GitHub Actions.
- Gửi notification đến Discord.
- Cung cấp Discord Slash Commands.
- Lưu lịch sử event và trạng thái repository.
- Có khả năng mở rộng thêm repository mà không cần sửa source code.
- Chạy được bằng Docker.
- Có thể deploy trên VPS.

---

# 2. Kiến trúc hệ thống

```text
                        ┌──────────────────┐
                        │      GitHub      │
                        │                  │
                        │ Repository       │
                        │ Actions          │
                        │ Pull Requests    │
                        │ Issues           │
                        └────────┬─────────┘
                                 │
                            Webhook Events
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │      FastAPI Backend   │
                    │                        │
                    │  /github/webhook       │
                    │  /repositories         │
                    │  /health               │
                    │                        │
                    │  Event Processor       │
                    │  GitHub API Client     │
                    └───────────┬────────────┘
                                │
                   ┌────────────┴────────────┐
                   │                         │
                   ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐
          │   PostgreSQL    │       │  Discord Bot    │
          │                 │       │                 │
          │ Repositories    │       │ Slash Commands  │
          │ Events          │       │ Notifications   │
          │ Workflow Runs   │       │                 │
          └─────────────────┘       └────────┬────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Discord Server   │
                                    │                  │
                                    │ #github-status   │
                                    │ #deploy          │
                                    │ #github-alerts   │
                                    └──────────────────┘
```

---

# 3. Công nghệ

## 3.1. Backend

- Python 3.12+
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- Pydantic
- httpx

## 3.2. Discord

- discord.py
- Discord Application
- Discord Bot
- Discord Slash Commands
- Discord Embed

## 3.3. GitHub

- GitHub REST API
- GitHub Webhooks
- GitHub Actions
- GitHub Personal Access Token hoặc GitHub App

## 3.4. Database

- PostgreSQL

## 3.5. Infrastructure

- Docker
- Docker Compose
- Nginx
- HTTPS

---

# 4. Các thành phần chính

## 4.1. FastAPI Backend

Backend chịu trách nhiệm:

1. Nhận GitHub Webhook.
2. Xác thực Webhook.
3. Parse GitHub events.
4. Lưu event vào database.
5. Cập nhật trạng thái repository.
6. Gửi notification đến Discord.
7. Cung cấp REST API.
8. Cung cấp health check.

## 4.2. Discord Bot

Discord Bot chịu trách nhiệm:

- Đăng ký Slash Commands.
- Xử lý command từ người dùng.
- Query database.
- Query GitHub API khi cần.
- Trả về repository status.
- Gửi notification vào Discord channel.

## 4.3. GitHub Webhook Handler

GitHub gửi HTTP request đến:

```http
POST /github/webhook
```

Các event được hỗ trợ:

- `push`
- `pull_request`
- `workflow_run`
- `workflow_job`
- `issues`
- `deployment`
- `deployment_status`

---

# 5. GitHub Events

## 5.1. Push

Khi có:

```bash
git push
```

Bot gửi:

```text
📦 New Push

Repository:
Kens0107/homestay-backend

Branch:
main

Author:
Kens0107

Commit:
a82f31c

Message:
fix authentication bug

Files changed:
7

View Commit
```

---

# 6. GitHub Actions

Hệ thống phải theo dõi GitHub Actions.

Các trạng thái:

- `queued`
- `in_progress`
- `completed`

Khi `completed`, kiểm tra:

- `success`
- `failure`
- `cancelled`
- `skipped`
- `timed_out`

### Success

```text
🟢 GitHub Action Success

Repository:
homestay-backend

Workflow:
CI

Branch:
main

Commit:
a82f31c

Duration:
2m 31s
```

### Failure

```text
🔴 GitHub Action Failed

Repository:
homestay-backend

Workflow:
CI

Branch:
main

Commit:
a82f31c

Job:
test

Status:
failure

View Logs
```

---

# 7. Pull Request

Khi tạo Pull Request:

```text
🔵 Pull Request Opened

Repository:
homestay-backend

PR:
#42

Title:
Add authentication middleware

Author:
Kens0107

Branch:
feature/auth

→ main
```

Khi merge:

```text
🟣 Pull Request Merged

PR #42

Add authentication middleware

Merged by:
Kens0107
```

---

# 8. Discord Commands

## 8.1. `/status`

Không truyền parameter.

```text
/status
```

Trả về tổng quan:

```text
GitHub Status

🟢 homestay-backend
    CI: SUCCESS
    Deploy: SUCCESS

🟢 homestay-frontend
    CI: SUCCESS
    Deploy: SUCCESS

🔴 9router
    CI: FAILED
    Deploy: -

Last update: 2 minutes ago
```

## 8.2. `/status <repository>`

Ví dụ:

```text
/status homestay-backend
```

Response:

```text
🟢 homestay-backend

Repository:
Kens0107/homestay-backend

Default branch:
main

Latest commit:
a82f31c

Author:
Kens0107

CI:
🟢 SUCCESS

Deployment:
🟢 SUCCESS

Last push:
2 minutes ago

Last workflow:
CI
2m 31s

Open GitHub
```

## 8.3. `/repos`

Liệt kê repository đang được monitor:

```text
/repos
```

Response:

```text
Monitored Repositories

1. homestay-backend
   🟢 Active

2. homestay-frontend
   🟢 Active

3. 9router
   🟢 Active
```

## 8.4. `/logs`

```text
/logs
```

Hiển thị event gần nhất:

```text
Recent GitHub Events

16:03 🟢 CI SUCCESS
homestay-backend

15:59 📦 PUSH
homestay-frontend

15:43 🔴 CI FAILED
9router

15:40 🟣 PR MERGED
homestay-backend
```

Có thể hỗ trợ:

```text
/logs repository:homestay-backend
/logs limit:20
```

## 8.5. `/check`

Force kiểm tra trạng thái GitHub:

```text
/check
```

Bot gọi GitHub API để kiểm tra:

- Latest commit
- Latest workflow
- Workflow status
- Deployment status

Sau đó cập nhật database.

---

# 9. Repository Management

## Thêm repository

```http
POST /repositories
```

Request:

```json
{
  "owner": "Kens0107",
  "name": "homestay-backend"
}
```

## Xóa repository

```http
DELETE /repositories/{repository_id}
```

## Danh sách repository

```http
GET /repositories
```

## Repository detail

```http
GET /repositories/{repository_id}
```

---

# 10. Database

## 10.1. `repositories`

```text
repositories
├── id
├── owner
├── name
├── full_name
├── default_branch
├── github_id
├── webhook_id
├── active
├── created_at
└── updated_at
```

## 10.2. `events`

```text
events
├── id
├── repository_id
├── event_type
├── github_event_id
├── payload
├── created_at
└── processed_at
```

`payload` lưu GitHub Webhook payload dưới dạng JSONB.

## 10.3. `workflow_runs`

```text
workflow_runs
├── id
├── repository_id
├── github_run_id
├── workflow_name
├── branch
├── commit_sha
├── status
├── conclusion
├── started_at
├── completed_at
└── created_at
```

## 10.4. `deployments`

```text
deployments
├── id
├── repository_id
├── github_deployment_id
├── environment
├── status
├── commit_sha
├── created_at
└── updated_at
```

---

# 11. GitHub Webhook Security

Webhook phải được xác thực bằng:

```text
X-Hub-Signature-256
```

GitHub webhook secret được lưu trong environment:

```env
GITHUB_WEBHOOK_SECRET=xxxxxxxx
```

Backend sử dụng HMAC SHA-256 để verify request.

Không được tin tưởng trực tiếp request từ Internet.

---

# 12. Authentication

GitHub API authentication không được hard-code.

Không được:

```python
GITHUB_TOKEN = "ghp_xxxxxxxxx"
```

Token phải được lưu bằng environment variable hoặc secret manager.

Ví dụ:

```env
GITHUB_TOKEN=ghp_xxxxxxxxx
DISCORD_TOKEN=xxxxxxxx
DISCORD_WEBHOOK_URL=xxxxxxxx
DATABASE_URL=postgresql://...
```

---

# 13. Discord Bot Permissions

Bot chỉ yêu cầu các permission cần thiết:

- View Channels
- Send Messages
- Embed Links
- Read Message History
- Use Slash Commands

Không cấp:

```text
Administrator
```

nếu không cần thiết.

---

# 14. Discord Channel

Có thể cấu hình channel cho từng loại notification:

```text
Discord Server

├── #github-status
│   ├── push
│   └── workflow
│
├── #github-pr
│   └── pull request
│
└── #github-deploy
    └── deployment
```

Database có thể lưu:

```text
repository_notification_config
├── repository_id
├── discord_guild_id
├── push_channel_id
├── workflow_channel_id
├── pr_channel_id
└── deployment_channel_id
```

---

# 15. Event Processing

Webhook không nên xử lý toàn bộ logic trực tiếp trong request.

Flow:

```text
GitHub
   │
   ▼
Webhook
   │
   ▼
Verify Signature
   │
   ▼
Save Event
   │
   ▼
Return HTTP 200
   │
   ▼
Event Processor
   │
   ├── Update Database
   │
   └── Send Discord Message
```

Điều này giúp GitHub không phải chờ Discord API hoặc các xử lý khác.

---

# 16. Idempotency

GitHub có thể retry Webhook.

Backend phải tránh xử lý event nhiều lần.

Sử dụng:

```text
github_event_id
```

làm unique key.

Ví dụ:

```text
event ID:
123456789

Nếu event đã tồn tại:

→ Không xử lý lại
```

---

# 17. Error Handling

Nếu Discord API lỗi:

```text
GitHub Event
      ↓
Database
      ↓
Discord ❌
```

Event vẫn phải được lưu.

Hệ thống có thể retry gửi Discord.

Không được để Discord lỗi làm mất GitHub event.

---

# 18. Logging

Backend phải log:

- `INFO`
- `WARNING`
- `ERROR`

Ví dụ:

```text
INFO  GitHub webhook received
INFO  Repository: Kens0107/homestay-backend
INFO  Event: push
INFO  Commit: a82f31c

INFO  Discord notification sent

ERROR Discord API request failed
ERROR GitHub API rate limit exceeded
```

---

# 19. Health Check

Endpoint:

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "database": "ok",
  "discord": "ok",
  "github": "ok"
}
```

Docker healthcheck sử dụng endpoint này.

---

# 20. Project Structure

```text
github-discord-bot/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── github.py
│   │   ├── repositories.py
│   │   └── health.py
│   │
│   ├── bot/
│   │   ├── client.py
│   │   ├── commands/
│   │   │   ├── status.py
│   │   │   ├── repos.py
│   │   │   ├── logs.py
│   │   │   └── check.py
│   │   └── notifications.py
│   │
│   ├── github/
│   │   ├── client.py
│   │   ├── webhooks.py
│   │   └── events.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── repositories.py
│   │
│   ├── services/
│   │   ├── repository_service.py
│   │   ├── event_service.py
│   │   └── notification_service.py
│   │
│   └── config.py
│
├── migrations/
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 21. Docker Architecture

```yaml
services:

  bot:
    build: .
    restart: unless-stopped

    environment:
      DATABASE_URL: ${DATABASE_URL}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      GITHUB_WEBHOOK_SECRET: ${GITHUB_WEBHOOK_SECRET}
      DISCORD_TOKEN: ${DISCORD_TOKEN}

    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped

    environment:
      POSTGRES_DB: github_bot
      POSTGRES_USER: github_bot
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

# 22. Environment Variables

`.env.example`:

```env
# Discord
DISCORD_TOKEN=
DISCORD_GUILD_ID=

# GitHub
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=

# Database
POSTGRES_DB=github_bot
POSTGRES_USER=github_bot
POSTGRES_PASSWORD=
DATABASE_URL=

# Application
APP_ENV=production
LOG_LEVEL=INFO
```

Không commit `.env`.

---

# 23. Deployment

Production architecture:

```text
                         Internet
                            │
                            ▼
                    ┌───────────────┐
                    │ Cloudflare    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Nginx / Caddy │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ FastAPI       │
                    │ :8000         │
                    └───────┬───────┘
                            │
                    ┌───────┴────────┐
                    ▼                ▼
              PostgreSQL       Discord API
```

Public endpoint:

```text
https://github-bot.example.com/github/webhook
```

Chỉ endpoint webhook cần public.

Discord Bot có thể kết nối outbound tới Discord API.

---

# 24. MVP

## GitHub

- [ ] Repository management
- [ ] Webhook
- [ ] Push event
- [ ] Workflow run
- [ ] CI success
- [ ] CI failure

## Discord

- [ ] Discord Bot
- [ ] `/status`
- [ ] `/repos`
- [ ] `/logs`
- [ ] `/check`
- [ ] Push notification
- [ ] CI notification

## Backend

- [ ] FastAPI
- [ ] PostgreSQL
- [ ] SQLAlchemy
- [ ] Webhook signature verification
- [ ] Event persistence
- [ ] Error handling
- [ ] Logging
- [ ] Health check

## Infrastructure

- [ ] Docker
- [ ] Docker Compose
- [ ] HTTPS
- [ ] Nginx/Caddy
- [ ] Environment secrets

---

# 25. Future Features

```text
GitHub Discord Bot
│
├── Repository monitoring
├── GitHub Actions
├── Deployment monitoring
├── Pull Requests
├── Issues
├── Release notification
├── Discord commands
├── Role-based permissions
├── Multi-server support
├── Web dashboard
├── GitHub App authentication
├── Notification preferences
├── Retry queue
├── Metrics
└── AI assistant
      ├── Explain CI error
      ├── Summarize PR
      └── Analyze failed deployment
```

---

# 26. Tiêu chí hoàn thành MVP

MVP được xem là hoàn thành khi:

1. Thêm được GitHub repository vào hệ thống.
2. GitHub Webhook gửi event thành công.
3. Backend verify được webhook signature.
4. Push code lên `main` tạo Discord notification.
5. GitHub Action success tạo Discord notification.
6. GitHub Action failure tạo Discord notification.
7. `/status` trả về trạng thái repository.
8. `/repos` trả về danh sách repository.
9. `/logs` trả về các event gần nhất.
10. `/check` có thể đồng bộ trạng thái trực tiếp từ GitHub.
11. Event không bị xử lý trùng khi GitHub retry webhook.
12. Database lưu được lịch sử event.
13. Backend chạy ổn định bằng Docker Compose.
14. Webhook endpoint chạy qua HTTPS.
15. Không có GitHub/Discord secret nào được commit vào repository.
