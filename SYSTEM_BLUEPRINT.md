# 🏗️ SYSTEM BLUEPRINT - Bản Thiết Kế Siêu Cấp Hệ Thống Full-Stack

> **Mục đích**: Tài liệu này là bản thiết kế tổng thể (blueprint) để xây dựng bất kỳ hệ thống web full-stack nào từ đầu. Nó đúc kết toàn bộ kiến trúc, quy tắc, pattern và luồng vận hành đã được kiểm chứng thực tế từ project BDS WEB.
>
> **Cách dùng**: Copy file này vào project mới, thay thế tên thực thể (Homestay → Product, Booking → Order, v.v.) và bắt đầu triển khai theo từng section.

---

## MỤC LỤC

1. [Tổng Quan Kiến Trúc](#1-tổng-quan-kiến-trúc)
2. [Tech Stack & Phiên Bản](#2-tech-stack--phiên-bản)
3. [Cấu Trúc Thư Mục Chuẩn](#3-cấu-trúc-thư-mục-chuẩn)
4. [Backend Architecture (FastAPI)](#4-backend-architecture-fastapi)
5. [Frontend Architecture (Next.js)](#5-frontend-architecture-nextjs)
6. [Database Design Pattern](#6-database-design-pattern)
7. [Authentication & Authorization](#7-authentication--authorization)
8. [API Design Convention](#8-api-design-convention)
9. [Business Logic Patterns](#9-business-logic-patterns)
10. [AI/Chatbot Integration Pattern](#10-aichatbot-integration-pattern)
11. [Docker & Deployment](#11-docker--deployment)
12. [Quy Tắc Bắt Buộc](#12-quy-tắc-bắt-buộc)
13. [Checklist Triển Khai Project Mới](#13-checklist-triển-khai-project-mới)

---

## 1. TỔNG QUAN KIẾN TRÚC

```
┌─────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE                            │
├────────────────┬────────────────────┬───────────────────────────┤
│   Frontend     │     Backend        │      Database             │
│   (Next.js)    │     (FastAPI)      │    (PostgreSQL + pgvector)│
│   Port: 3000   │     Port: 8000     │      Port: 5432          │
│                │                    │                           │
│  React 19      │  Python 3.12       │  pgvector/pgvector:pg16   │
│  TypeScript    │  Async/Await       │                           │
│  Tailwind v4   │  SQLModel ORM      │                           │
│  App Router    │  Pydantic v2       │                           │
└────────────────┴────────────────────┴───────────────────────────┘
        │                    │                       │
        │    HTTP/REST       │   asyncpg             │
        └────────────────────┴───────────────────────┘
```

### Nguyên tắc cốt lõi:
- **Tách biệt hoàn toàn**: Frontend & Backend chạy độc lập, giao tiếp qua REST API
- **Async-first**: Backend sử dụng async/await xuyên suốt (asyncpg, AsyncSession)
- **Type-safe**: TypeScript (frontend) + Pydantic (backend) đảm bảo type safety 2 chiều
- **Container-ready**: Mọi service đều chạy trong Docker từ development đến production

---

## 2. TECH STACK & PHIÊN BẢN

### Backend
| Công nghệ | Phiên bản | Vai trò |
|-----------|-----------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.136+ | Web framework |
| SQLModel | 0.0.38 | ORM (kết hợp SQLAlchemy + Pydantic) |
| SQLAlchemy | 2.0+ | Database engine (async) |
| asyncpg | 0.31+ | PostgreSQL async driver |
| Pydantic | 2.13+ | Data validation & serialization |
| pydantic-settings | 2.14+ | Environment configuration |
| PyJWT | 2.9+ | JWT token handling |
| google-genai | 2.8+ | AI/LLM integration (Gemini) |
| pgvector | 0.4+ | Vector search cho semantic cache |
| cloudinary | 1.41+ | Cloud image storage |
| uvicorn | 0.49+ | ASGI server |

### Frontend
| Công nghệ | Phiên bản | Vai trò |
|-----------|-----------|---------|
| Next.js | 16.x | React framework (App Router) |
| React | 19.x | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Utility-first CSS |
| Node.js | 20 (Alpine) | Runtime |

### Infrastructure
| Công nghệ | Phiên bản | Vai trò |
|-----------|-----------|---------|
| PostgreSQL | 16 | Database chính |
| pgvector | extension | Vector similarity search |
| Docker Compose | latest | Container orchestration |

---

## 3. CẤU TRÚC THƯ MỤC CHUẨN

```
PROJECT_ROOT/
├── backend/
│   ├── src/
│   │   ├── __init__.py          # FastAPI app factory, lifespan, middleware, router registration
│   │   ├── auth.py              # JWT logic, password hashing, require_admin dependency
│   │   ├── config.py            # Pydantic Settings (env vars)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── main.py          # Async engine, session factory, init_db(), migrations
│   │   ├── models/              # SQLModel table definitions (database schema)
│   │   │   ├── __init__.py      # Re-export all models
│   │   │   ├── [entity].py      # Mỗi entity 1 file
│   │   │   └── ...
│   │   ├── repository/          # Database access layer (CRUD thuần túy)
│   │   │   ├── [entity].py      # Mỗi entity 1 file
│   │   │   └── ...
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── [entity].py      # Mỗi entity 1 file
│   │   │   └── ...
│   │   ├── services/            # Business logic layer
│   │   │   ├── [entity].py      # Mỗi entity 1 file
│   │   │   └── ...
│   │   └── routes/              # HTTP endpoint definitions (routers)
│   │       ├── [entity].py      # Mỗi entity 1 file
│   │       └── ...
│   ├── uploads/                 # Local file storage (dev)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env_example
│
├── frontend/
│   ├── src/                     # Toàn bộ mã nguồn frontend
│   │   ├── app/                 # Next.js App Router (Routing Pages)
│   │   │   ├── layout.tsx       # Root layout chính (fonts, Header/Footer wrappers)
│   │   │   ├── page.tsx         # Trang chủ công khai
│   │   │   ├── admin/
│   │   │   │   └── page.tsx     # Trang admin dashboard chính
│   │   │   └── details/[id]/
│   │   │       └── page.tsx     # Trang chi tiết homestay/thực thể theo ID
│   │   ├── features/            # Cấu trúc modular theo miền nghiệp vụ (Domain Features)
│   │   │   ├── [feature]/       # Mỗi folder đại diện cho một nghiệp vụ độc lập (admin, booking, chatbot...)
│   │   │   │   ├── api/         # Gọi các API endpoints tương ứng (e.g. `booking.ts`)
│   │   │   │   ├── components/  # React components dành riêng cho feature này
│   │   │   │   ├── dto/         # Định nghĩa TypeScript interfaces (DTOs) tương thích backend
│   │   │   │   └── schemas/     # Client-side validation schemas
│   │   ├── shared/              # Thành phần dùng chung toàn dự án (Shared Layer)
│   │   │   ├── components/      # UI components dùng chung (Header.tsx, Footer.tsx...)
│   │   │   └── utils/           # Các hàm helper, format chung (format.ts)
│   │   └── styles/
│   │       └── global.css       # Cấu hình thiết kế CSS Tailwind v4 & custom variables
│   ├── package.json
│   ├── Dockerfile
│   └── tsconfig.json            # Cấu hình path aliases (ví dụ: `@/*` -> `./src/*`)
│
├── docker-compose.yml           # Orchestrate db + backend + frontend
├── .env                         # Environment variables (gitignored)
└── .gitignore
```

### Nguyên tắc đặt tên file:
- **Backend**: snake_case (`booking.py`, `room_inventory.py`)
- **Frontend components**: PascalCase (`BookingSection.tsx`, `HomestayCard.tsx`)
- **Frontend APIs/DTOs/hooks**: camelCase (`booking.ts`, `useChatbot.ts`)

---

## 4. BACKEND ARCHITECTURE (FastAPI)

### 4.1 Layered Architecture (Bắt buộc)

```
Request → Route → Service → Repository → Database
                     ↕
                  Schemas (validate input/output)
```

| Layer | Trách nhiệm | KHÔNG được làm |
|-------|-------------|----------------|
| **Route** | Nhận request, validate schema, gọi service, trả response | Không chứa logic nghiệp vụ, không truy vấn DB |
| **Service** | Xử lý logic nghiệp vụ, validation, điều phối | Không gọi session/SQL trực tiếp |
| **Repository** | CRUD database, query thuần túy | Không chứa logic nghiệp vụ |
| **Schema** | Định nghĩa request/response types | Không nằm inline trong route |
| **Model** | Định nghĩa bảng database | Chỉ khai báo cấu trúc, không logic |

### 4.2 App Entry Point (`src/__init__.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB, run migrations, seed data
    await init_db()
    yield
    # Shutdown: cleanup

app = FastAPI(title="App Name", version="0.1.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Production: specific origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with versioned prefix
app.include_router(entity_router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
```

### 4.3 Configuration (`src/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: float = 24
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    # Third-party API keys
    AI_API_KEY: str = ""
    # Cloud storage
    CLOUD_NAME: Optional[str] = None
    API_KEY: Optional[str] = None
    API_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

Config = Settings()
```

### 4.4 Database Setup (`src/db/main.py`)

```python
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(Config.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        # Enable extensions (pgvector, etc.)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)
        # Run manual migrations
        await _run_migrations(conn)
    # Seed initial data
    async with AsyncSessionLocal() as session:
        await seed_admin(session)
```

### 4.5 Model Pattern (`src/models/entity.py`)

```python
from datetime import datetime, timezone, timedelta
import uuid
from sqlmodel import Field, SQLModel

VN_TZ = timezone(timedelta(hours=7))

def _now_vn() -> datetime:
    """Thời gian hiện tại GMT+7, naive datetime (compatible with PostgreSQL)"""
    return datetime.now(VN_TZ).replace(tzinfo=None)

class Entity(SQLModel, table=True):
    __tablename__ = "entities"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    name: str
    # ... fields
    created_at: datetime = Field(default_factory=_now_vn)
    updated_at: datetime = Field(default_factory=_now_vn)
```

### 4.6 Repository Pattern (`src/repository/entity.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

class EntityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Entity]:
        result = await self.session.execute(select(Entity).order_by(Entity.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, entity_id: str) -> Entity | None:
        result = await self.session.execute(select(Entity).where(Entity.id == entity_id))
        return result.scalar_one_or_none()

    async def create(self, entity: Entity) -> Entity:
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: Entity) -> Entity:
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: Entity) -> None:
        await self.session.delete(entity)
        await self.session.commit()
```

### 4.7 Service Pattern (`src/services/entity.py`)

```python
class EntityNotFoundError(Exception):
    pass

class EntityService:
    def __init__(self, repo: EntityRepository):
        self.repo = repo

    async def list_entities(self) -> list[Entity]:
        return await self.repo.get_all()

    async def get_entity(self, entity_id: str) -> Entity:
        entity = await self.repo.get_by_id(entity_id)
        if not entity:
            raise EntityNotFoundError("Entity not found")
        return entity

    async def create_entity(self, payload: EntityCreate) -> Entity:
        entity = Entity(**payload.model_dump())
        return await self.repo.create(entity)

    async def update_entity(self, entity_id: str, payload: EntityUpdate) -> Entity:
        entity = await self.get_entity(entity_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        return await self.repo.update(entity)

    async def delete_entity(self, entity_id: str) -> None:
        entity = await self.get_entity(entity_id)
        await self.repo.delete(entity)
```

### 4.8 Schema Pattern (`src/schemas/entity.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class EntityBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""

class EntityCreate(EntityBase):
    pass

class EntityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class EntityRead(EntityBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
```

### 4.9 Route Pattern (`src/routes/entity.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

async def get_service(session: AsyncSession = Depends(get_session)) -> EntityService:
    repo = EntityRepository(session)
    return EntityService(repo)

@router.get("", response_model=list[EntityRead])
async def list_entities(service: EntityService = Depends(get_service)):
    return await service.list_entities()

@router.get("/{entity_id}", response_model=EntityRead)
async def get_entity(entity_id: str, service: EntityService = Depends(get_service)):
    try:
        return await service.get_entity(entity_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    payload: EntityCreate,
    service: EntityService = Depends(get_service),
    _: Admin = Depends(require_admin),  # Protected endpoint
):
    return await service.create_entity(payload)
```

---

## 5. FRONTEND ARCHITECTURE (Next.js)

### 5.1 App Router & Feature Structure (Modular Architecture)

Next.js 16 được tổ chức theo cấu trúc **Modular/Feature-Sliced** để tăng khả năng bảo trì và phân tách rõ ràng trách nhiệm. Toàn bộ mã nguồn nằm dưới thư mục `src/`:

```
frontend/src/
├── app/                  # Routing Pages (Next.js App Router)
│   ├── layout.tsx        # Bố cục bao quanh trang (Fonts, Header, Footer)
│   ├── page.tsx          # Trang chủ công khai
│   ├── admin/
│   │   └── page.tsx      # Trang admin dashboard chính
│   └── details/[id]/
│       └── page.tsx      # Trang chi tiết homestay/thực thể
├── features/             # Miền nghiệp vụ độc lập (Domain Features)
│   ├── [feature]/        # Mỗi folder đại diện cho một nghiệp vụ (auth, booking, chatbot, homestay...)
│   │   ├── api/          # Lớp gọi API tập trung cho feature này (e.g. `booking.ts`)
│   │   ├── components/   # React components chuyên biệt (e.g. `BookingSection.tsx`)
│   │   ├── dto/          # TypeScript interfaces (DTOs) tương thích backend
│   │   └── schemas/      # Client-side validation schemas
├── shared/               # Thành phần dùng chung toàn dự án (Shared Layer)
│   ├── components/       # UI components dùng chung (Header.tsx, Footer.tsx...)
│   └── utils/            # Các hàm helper, format chung (format.ts)
└── styles/
    └── global.css        # Cấu hình thiết kế CSS Tailwind v4 & custom variables
```

### 5.2 Root Layout Pattern (`src/app/layout.tsx`)

```tsx
import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Be_Vietnam_Pro } from "next/font/google";
import "../styles/global.css";
import Header from "@/shared/components/Header";
import Footer from "@/shared/components/Footer";

const plusJakartaSans = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["vietnamese", "latin"],
});

const beVietnamPro = Be_Vietnam_Pro({
  variable: "--font-be-vietnam",
  subsets: ["vietnamese", "latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "Happy Oasis Sea - Đặt Phòng Khách Sạn Thông Minh",
  description: "Trang web tìm kiếm và đặt phòng khách sạn chất lượng cao.",
  icons: { icon: "/logo.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${plusJakartaSans.variable} ${beVietnamPro.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-on-background font-sans transition-colors duration-300">
        <Header />
        <div className="flex-1 flex flex-col w-full">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
```

### 5.3 API Client Layer Pattern (ví dụ `@/features/homestay/api/homestays.ts`)

Các cuộc gọi API phải sử dụng cơ chế phát hiện hostname linh hoạt từ `window` trên client và `process.env` trên server nhằm xử lý đúng trong Docker network:

```typescript
import { type Homestay, type HomestayInput } from "../dto/homestays";

const getApiOrigin = () => {
  if (typeof window !== "undefined") {
    // Tự động sử dụng origin hiện tại nếu ở môi trường production thực tế chạy qua Nginx
    if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      return window.location.origin;
    }
    const envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const urlObj = new URL(envUrl);
      if (urlObj.hostname === "localhost" || urlObj.hostname === "127.0.0.1" || urlObj.hostname === "backend") {
        if (urlObj.hostname === "backend") return window.location.origin;
        urlObj.hostname = window.location.hostname;
        return urlObj.toString().replace(/\/$/, "");
      }
    } catch (e) {
      console.error("Failed to parse NEXT_PUBLIC_API_URL:", e);
    }
    return envUrl.replace(/\/$/, "");
  }
  return (process.env.NEXT_PUBLIC_API_URL || "http://backend:8000").replace(/\/$/, "");
};

export const API_ORIGIN = getApiOrigin();
export const API_BASE = `${API_ORIGIN}/api/v1`;

// Generic response handler
export async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {}
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Fetch public list
export async function fetchHomestays(): Promise<Homestay[]> {
  const res = await fetch(`${API_BASE}/homestays`, { cache: "no-store" });
  return handle<Homestay[]>(res);
}

// Fetch single by ID
export async function fetchHomestay(id: string): Promise<Homestay> {
  const res = await fetch(`${API_BASE}/homestays/${encodeURIComponent(id)}`, { cache: "no-store" });
  return handle<Homestay>(res);
}

// Image URL resolver
export function resolveImageUrl(url: string | undefined | null): string {
  if (!url) return "";
  if (/^https?:\/\//i.test(url) || url.startsWith("data:")) return url;
  if (url.startsWith("/")) return `${API_ORIGIN}${url}`;
  return url;
}
```

### 5.4 Page Component Pattern (`src/app/page.tsx`)

```tsx
"use client";

import React, { useState, useEffect } from "react";
import { fetchHomestays } from "@/features/homestay/api/homestays";
import { type Homestay } from "@/features/homestay/dto/homestays";
import HomestayCard from "@/features/homestay/components/HomestayCard";

export default function HomePage() {
  const [homestays, setHomestays] = useState<Homestay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchHomestays()
      .then((data) => { if (active) setHomestays(data); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  if (loading) return <p>Đang tải danh sách homestay...</p>;
  if (error) return <p className="text-error">{error}</p>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {homestays.map((item) => (
        <HomestayCard key={item.id} homestay={item} />
      ))}
    </div>
  );
}
```

### 5.5 Admin Page Wrapper Pattern (`src/app/admin/page.tsx`)

```tsx
"use client";

import React, { useState, useEffect } from "react";
import { adminMe, TOKEN_KEY } from "@/features/auth/api/auth";
import LoginForm from "@/features/auth/components/LoginForm";
import AdminDashboard from "@/features/admin/components/AdminDashboard";

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
    if (stored) {
      adminMe(stored)
        .then(() => setToken(stored))
        .catch(() => localStorage.removeItem(TOKEN_KEY))
        .finally(() => setChecking(false));
    } else {
      setChecking(false);
    }
  }, []);

  if (checking) return <p className="text-center py-20">Đang kiểm tra phiên đăng nhập...</p>;
  
  if (!token) {
    return (
      <LoginForm
        onSuccess={(t) => {
          localStorage.setItem(TOKEN_KEY, t);
          setToken(t);
        }}
      />
    );
  }

  return (
    <AdminDashboard
      token={token}
      onLogout={() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      }}
    />
  );
}
```

---

## 6. DATABASE DESIGN PATTERN

### 6.1 Quy tắc chung

- **Primary Key**: UUID string (`str`, generated bằng `uuid.uuid4()`)
- **Timestamps**: `created_at` và `updated_at` dùng `_now_vn()` (hoặc timezone bạn chọn)
- **Naive datetime**: `.replace(tzinfo=None)` để tránh conflict với PostgreSQL TIMESTAMP WITHOUT TIMEZONE
- **Auto-migration**: `init_db()` chạy `create_all` + manual migration SQL có điều kiện `IF NOT EXISTS`

### 6.2 Migration Pattern (không dùng Alembic)

```python
async def _run_migrations(conn):
    """Manual migrations - safe to run multiple times"""
    await conn.execute(text("""
        DO $$
        BEGIN
            -- Add new column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'entities' AND column_name = 'new_field'
            ) THEN
                ALTER TABLE entities ADD COLUMN new_field TEXT DEFAULT '';
            END IF;
            -- Remove deprecated column
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'entities' AND column_name = 'old_field'
            ) THEN
                ALTER TABLE entities DROP COLUMN old_field;
            END IF;
        END $$;
    """))
```

### 6.3 Inventory/Availability Pattern (Quản lý tồn kho theo ngày)

Khi hệ thống cần quản lý tài nguyên có giới hạn theo thời gian (phòng, slot, vé...):

```python
class ResourceInventory(SQLModel, table=True):
    __tablename__ = "resource_inventory"

    inventory_id: int | None = Field(default=None, primary_key=True)
    resource_id: str = Field(index=True)          # FK to resource
    inv_date: str = Field(index=True)             # ISO date YYYY-MM-DD
    total_slots: int = Field(default=0)           # Tổng capacity
    booked_slots: int = Field(default=0)          # Đã đặt
    # available = total_slots - booked_slots
```

### 6.4 PostgreSQL Array Fields

```python
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY
import sqlalchemy as sa

class Entity(SQLModel, table=True):
    tags: list[str] = Field(
        sa_column=Column(ARRAY(sa.String), nullable=False, server_default="{}"),
    )
```

### 6.5 Vector Field (cho Semantic Search)

```python
from pgvector.sqlalchemy import Vector

class SemanticCache(SQLModel, table=True):
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(384)))
```

---

## 7. AUTHENTICATION & AUTHORIZATION

### 7.1 Password Hashing (PBKDF2 + HMAC)

```python
import hashlib, hmac, secrets

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${h.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    salt, digest = hashed.split("$", 1)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return hmac.compare_digest(h.hex(), digest)
```

### 7.2 JWT Token

```python
import jwt
from datetime import datetime, timedelta, timezone

def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
```

### 7.3 FastAPI Dependency (Require Admin qua HttpOnly Cookie)

```python
from fastapi import Depends, HTTPException, status, Request

async def require_admin(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Admin:
    # 1. Lấy token từ HttpOnly Cookie (ưu tiên) hoặc Authorization Header (fallback)
    token = request.cookies.get("admin_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # 2. Kiểm tra Token Blacklist (chống dùng lại token sau khi logout)
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    # 3. Decode token
    username = decode_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 4. Kiểm tra user trong database
    admin = await get_admin_by_username(session, username)
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
        
    # 5. Lưu token vào state để API logout có thể revoke chính token này
    request.state.admin_token = token
    return admin
```

### 7.4 Auto-seed Admin trên mỗi lần boot

```python
async def seed_admin(session: AsyncSession) -> None:
    existing = await get_admin_by_username(session, Config.ADMIN_USERNAME)
    if existing is None:
        admin = Admin(username=Config.ADMIN_USERNAME, password_hash=hash_password(Config.ADMIN_PASSWORD))
        session.add(admin)
    else:
        # Sync password from env (env is source of truth)
        existing.password_hash = hash_password(Config.ADMIN_PASSWORD)
        session.add(existing)
    await session.commit()
```

### 7.5 Frontend Token Management (HttpOnly Cookie)

Tuyệt đối KHÔNG lưu trữ JWT trong `localStorage` để phòng ngừa tấn công XSS. Toàn bộ quá trình lưu trữ sẽ do trình duyệt đảm nhận ngầm thông qua `Set-Cookie`.

```typescript
// Login: Server trả về header Set-Cookie: admin_token=...; HttpOnly; SameSite=Strict; Secure
await adminLogin(username, password);

// API calls: Trình duyệt TỰ ĐỘNG đính kèm cookie
// BẮT BUỘC thêm credentials: "include" vào tất cả các fetch request
const res = await fetch(`${API_BASE}/admin/resource`, {
  credentials: "include", 
});

// Logout: Gọi API backend để thu hồi (revoke) token và xóa cookie
await adminLogout(); 

// Auto-check on page load
try {
  await adminMe(); // Gọi API, trình duyệt tự đính cookie. Nếu HTTP 401 -> Cookie đã bị hủy/hết hạn
} catch (error) {
  // Redirect về trang đăng nhập
}
```

### 7.6 Rate Limiting & Chống Tấn Công (Defense in Depth)

- **Brute-force Protection**: Áp dụng giới hạn request cho API login bằng Nginx (`limit_req_zone rate=5r/m`) và FastAPI (`@limiter.limit("5/minute")`).
- **CORS Protection**: Thay vì `allow_origins=["*"]`, API admin phải chỉ định rõ tên miền production (`https://yourdomain.com`) và bật `allow_credentials=True`.

### 7.7 Future Security Enhancements (Lộ trình Nâng cấp)

Khi thiết kế hệ thống lớn hơn (Enterprise level), Blueprint này cần được mở rộng thêm các modules bảo mật sau:
1. **Multi-Factor Authentication (MFA)**: Tích hợp TOTP (Time-based One-Time Password) kết hợp với thư viện `pyotp` tại Python backend để tăng cường xác thực.
2. **Role-Based Access Control (RBAC)**: Bổ sung bảng `roles` và `permissions` vào database; tạo dependency `require_permissions("manage_booking")` tại FastAPI thay vì chỉ `require_admin`.
3. **Audit Trails (Lưu vết Hệ thống)**: Mọi thao tác POST/PUT/PATCH/DELETE từ admin phải được ghi vào bảng `audit_logs` (Bao gồm: user_id, action, resource, payload, ip_address).
4. **Admin IP Whitelisting**: Chặn truy cập từ bên ngoài mạng nội bộ/VPN bằng Nginx (`allow 192.168.1.0/24; deny all;`) cho các routes `/admin`.
5. **Idle Session Timeout**: Cấu hình frontend tự động gửi request logout hoặc cảnh báo nếu không phát hiện sự kiện chuột/phím sau 30 phút.
6. **File Upload Security**: Backend phải validate signature (magic numbers) của file ảnh tải lên, không chỉ dựa vào extension `.jpg/.png` để chống Webshell.

---

## 8. API DESIGN CONVENTION

### 8.1 URL Structure

```
/api/v1/{resource}                    # Public: list, create
/api/v1/{resource}/{id}               # Public: get by id
/api/v1/{resource}/{id}/{action}      # Public: specific action (cancel, confirm)

/api/v1/admin/login                   # Auth
/api/v1/admin/me                      # Verify token
/api/v1/admin/{resource}              # Admin CRUD
/api/v1/admin/{resource}/{id}/{action}  # Admin actions (confirm, checkin, checkout, cancel)
```

### 8.2 HTTP Methods Convention

| Method | Mục đích | Ví dụ |
|--------|----------|-------|
| GET | Lấy dữ liệu | `GET /api/v1/entities` |
| POST | Tạo mới | `POST /api/v1/entities` |
| PUT | Cập nhật toàn bộ | `PUT /api/v1/admin/entities/{id}` |
| PATCH | Cập nhật một phần / Action | `PATCH /api/v1/admin/bookings/{id}/confirm` |
| DELETE | Xóa | `DELETE /api/v1/admin/entities/{id}` |

### 8.3 Response Pattern

```python
# Success - Single entity
{ "id": "...", "name": "...", ... }

# Success - List with pagination
{
    "items": [...],
    "total": 100,
    "page": 1,
    "limit": 20
}

# Success - Action result
{
    "success": true,
    "message": "Đã thực hiện thành công",
    "entity": { ... }  # Optional: updated entity
}

# Error
{ "detail": "Mô tả lỗi bằng tiếng Việt" }
```

### 8.4 Pagination & Filtering (Query Params)

```python
@router.get("/entities")
async def list_entities(
    category: str | None = Query(None, description="Lọc theo category"),
    status: str | None = Query(None, description="Lọc theo trạng thái"),
    search: str | None = Query(None, description="Tìm kiếm theo tên/SĐT"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    ...
```

### 8.5 File Upload Pattern

```python
@router.post("/uploads")
async def upload_files(
    files: list[UploadFile] = File(...),
    _: Admin = Depends(require_admin),
):
    # Validate file type & size
    # Upload to Cloudinary (production) or save locally (dev)
    # Return list of URLs
    return {"files": [{"url": "...", "filename": "..."}]}
```

---

## 9. BUSINESS LOGIC PATTERNS

### 9.1 State Machine (Vòng đời trạng thái)

Bất kỳ entity nào có lifecycle (order, booking, ticket, task) đều cần state machine:

```
[Initial State] ──(Action)──> [Next State] ──(Action)──> [Final State]
       │                              │
    (Cancel)                       (Cancel)
       │                              │
       ▼                              ▼
  [Cancelled]                    [Cancelled]
```

**Ví dụ Booking Lifecycle:**
```
pending → confirmed → checked_in → checked_out
   ↓           ↓
cancelled  cancelled
```

**Quy tắc kiểm tra chuyển trạng thái:**
```python
VALID_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["checked_in", "cancelled"],
    "checked_in": ["checked_out"],
    "checked_out": [],
    "cancelled": [],
}

def can_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, [])
```

### 9.2 Inventory Management (Quản lý tồn kho)

```python
async def book_resource(self, resource_id: str, dates: list[str]) -> tuple[bool, str | None]:
    # 1. Check availability for all dates
    for date in dates:
        inventory = await self._ensure_inventory(resource_id, date)
        available = inventory.total_slots - inventory.booked_slots
        if available <= 0:
            return False, f"Hết slot vào ngày {date}"

    # 2. Reserve (increment booked)
    for date in dates:
        await self.repo.update_inventory_booked(resource_id, date, +1)

    # 3. Commit
    await self.repo.commit()
    return True, None

async def cancel_resource(self, resource_id: str, dates: list[str]):
    # Revert inventory (decrement booked)
    for date in dates:
        await self.repo.update_inventory_booked(resource_id, date, -1)
    await self.repo.commit()
```

### 9.3 Availability Calendar

```python
def get_status(available: int) -> str:
    if available <= 0: return "full"
    elif available == 1: return "low"
    else: return "available"

async def get_monthly_availability(self, resource_id: str, year: int, month: int) -> list[dict]:
    # Get all inventory records for the month
    # Fill gaps with default total capacity
    # Return [{date, available, status}, ...]
```

### 9.4 Search & Filter Pattern

```python
async def get_all_with_filters(
    self,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Entity], int]:
    query = select(Entity)
    count_query = select(func.count(Entity.id))
    filters = []

    if category:
        filters.append(Entity.category == category)
    if status:
        filters.append(Entity.status == status)
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Entity.name.ilike(pattern), Entity.phone.ilike(pattern)))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = (await self.session.execute(count_query)).scalar() or 0
    offset = (page - 1) * limit
    query = query.order_by(Entity.updated_at.desc()).offset(offset).limit(limit)
    result = await self.session.execute(query)

    return list(result.scalars().all()), total
```

---

## 10. AI/CHATBOT INTEGRATION PATTERN

### 10.1 Architecture

```
User Question → ChatbotService → AI Provider (Gemini/OpenAI)
                     │                    │
                     │              System Prompt + Context
                     │                    │
                     ▼                    ▼
              Parse Response ← Raw AI Response
                     │
                     ├── Normal answer → Return to user
                     └── Special action (CHECK_ROOM) → Fetch real data → AI Round 2 → Return
```

### 10.2 Session Management

```python
class ChatSessionManager:
    def __init__(self):
        self._sessions: dict[str, Any] = {}
        self._client: Optional[Any] = None

    def get_or_create_session(self, session_id: str) -> Any:
        if session_id not in self._sessions:
            self._sessions[session_id] = self._create_chat_session()
        return self._sessions[session_id]

    async def send_message(self, session_id: str, question: str) -> str:
        chat = self.get_or_create_session(session_id)
        response = await asyncio.to_thread(chat.send_message, question)
        return response.text or ""

chat_session_manager = ChatSessionManager()  # Singleton
```

### 10.3 Structured AI Output Parsing

AI trả về response theo format cố định, backend parse thành structured data:

```python
import re, json

def parse_response(raw_text: str) -> tuple[list[str], str]:
    """Parse AI response: extract IDs + clean text"""
    match = re.match(r"^ENTITY_IDS:\s*(\[.*?\])", raw_text, re.IGNORECASE)
    if match:
        try:
            ids = json.loads(match.group(1))
        except json.JSONDecodeError:
            ids = []
        clean = re.sub(r"^ENTITY_IDS:\s*\[.*?\]", "", raw_text, count=1).strip()
        return ids, clean
    return [], raw_text
```

### 10.4 Two-round AI Pattern (cho real-time data)

Khi AI cần dữ liệu thực tế (phòng trống, giá hiện tại, stock):
1. **Round 1**: AI nhận câu hỏi → trả về "action command" (CHECK_ROOM, CHECK_STOCK...)
2. **Backend**: Parse command → query database → build context
3. **Round 2**: Gửi context + câu hỏi gốc cho AI → AI trả lời dựa trên data thực

### 10.5 Chat Log & Analytics

```python
class ChatLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: str | None = Field(index=True)
    user_query: str
    bot_response: str
    room_ids: list[str] | None = Field(sa_column=Column(JSONB, nullable=True))
    user_ip: str | None
    intent: str | None
    latency_ms: float | None
    feedback: str | None  # "like" | "dislike"
    created_at: datetime
```

### 10.6 Semantic Cache (Vector Search)

```python
class SemanticCache(SQLModel, table=True):
    question: str
    answer: str
    embedding: list[float] = Field(sa_column=Column(Vector(384)))
    created_at: datetime

# Lookup: find similar cached answers
async def lookup_cache(self, query_embedding: list, threshold: float = 0.95):
    # Use pgvector cosine similarity: 1 - (embedding <=> query)
    # Return cached answer if similarity > threshold
```

---

## 11. DOCKER & DEPLOYMENT

### 11.1 docker-compose.yml Template

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password123}
      POSTGRES_DB: appdb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD:-password123}@db:5432/appdb
      - JWT_SECRET=${JWT_SECRET:-change-me}
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}
      - AI_API_KEY=${AI_API_KEY}
      - CLOUD_NAME=${CLOUD_NAME}
      - API_KEY=${API_KEY}
      - API_SECRET=${API_SECRET}
    depends_on:
      - db
    volumes:
      - ./backend:/app
      - /app/env
      - uploads:/app/uploads

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  pgdata:
  uploads:
```

### 11.2 Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Dev mode
CMD ["fastapi", "dev", "src/__init__.py", "--host", "0.0.0.0", "--port", "8000"]

# Production mode (uncomment):
# CMD ["uvicorn", "src:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 11.3 Frontend Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000
ENV NEXT_TELEMETRY_DISABLED 1

# Dev mode
CMD ["npm", "run", "dev"]

# Production mode (uncomment):
# RUN npm run build
# CMD ["npm", "start"]
```

### 11.4 .env Template

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password123@db:5432/appdb

# Auth
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword
JWT_SECRET=your-jwt-secret-key

# AI
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-2.5-flash

# Cloud Storage (Cloudinary)
CLOUD_NAME=your-cloud-name
API_KEY=your-api-key
API_SECRET=your-api-secret

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 11.5 Quick Commands

```bash
# Start everything
docker compose up --build

# Start in background
docker compose up -d

# View backend logs
docker compose logs backend -f --tail=100

# Access PostgreSQL shell
docker compose exec db psql -U postgres -d appdb

# Rebuild single service
docker compose up --build backend
```

---

## 12. QUY TẮC BẮT BUỘC

### 12.1 Backend Rules

1. **Layered Architecture**: Route → Service → Repository. KHÔNG bỏ qua layer.
2. **Schema ngoài file riêng**: NGHIÊM CẤM định nghĩa Pydantic schema inline trong route.
3. **Async everywhere**: Tất cả database operations phải là async.
4. **Timezone nhất quán**: Chọn 1 timezone (VD: GMT+7), dùng hàm helper `_now_tz()` xuyên suốt.
5. **Naive datetime**: `.replace(tzinfo=None)` trước khi lưu PostgreSQL TIMESTAMP WITHOUT TZ.
6. **UUID primary keys**: Dùng UUID string cho tất cả entity chính.
7. **Dependency Injection**: Dùng FastAPI `Depends()` để inject service/repo vào route.
8. **Error handling**: Service raise custom exception → Route catch và trả HTTPException.
9. **Migrations idempotent**: Dùng `IF NOT EXISTS` / `IF EXISTS` trong SQL migration.
10. **Environment as source of truth**: Admin password sync từ env mỗi lần boot.

### 12.2 Frontend Rules

1. **API Client tập trung**: Mọi fetch call đều nằm trong `src/features/[feature]/api/*.ts`, KHÔNG gọi fetch trực tiếp trong component.
2. **Interface mirror backend**: TypeScript interface phải nằm trong DTOs (`src/features/[feature]/dto/*.ts`) và match 1:1 với backend response schema.
3. **Token key nhất quán**: Dùng constant `TOKEN_KEY` cho localStorage (được export từ `@/features/auth/api/auth`).
4. **Error handling**: Dùng `handle<T>()` wrapper để parse error detail bằng tiếng Việt từ backend.
5. **Image URL resolve**: Luôn dùng `resolveImageUrl()` cho ảnh từ backend để tránh lỗi sai origin khi chạy trong Docker/Production.
6. **No emoji in admin UI**: Dùng SVG icons (Heroicons) dạng inline JSX để giao diện chuyên nghiệp và đồng bộ.
7. **Vietnamese font**: Load font hỗ trợ tiếng Việt có cấu hình Variable Font (Be Vietnam Pro cho body text, Plus Jakarta Sans cho tiêu đề hiển thị).
8. **Responsive**: Thiết kế dạng Mobile-first tận dụng các breakpoints của Tailwind CSS.
9. **`"use client"`**: Page hoặc Components nào sử dụng hooks (`useState`, `useEffect`, `useContext`) đều bắt buộc phải khai báo dòng đầu tiên là `"use client"`.
10. **Cleanup in useEffect**: Luôn sử dụng `active` boolean flag hoặc `AbortController` khi fetch data không đồng bộ nhằm tránh memory leak hoặc thay đổi trạng thái sau khi unmount.
11. **Path Alias (@)**: Sử dụng `@/*` làm alias thay vì đường dẫn tương đối dài và phức tạp (ví dụ: `@/features/...`, `@/shared/...`, `@/styles/...`).

### 12.3 Naming Conventions

| Context | Convention | Ví dụ |
|---------|-----------|-------|
| DB table name | snake_case plural | `room_inventory`, `bookings` |
| Python file | snake_case | `booking.py`, `admin.py` |
| Python class | PascalCase | `BookingService`, `RoomInventory` |
| Python function | snake_case | `get_booking`, `create_entity` |
| TS/React component | PascalCase | `BookingSection.tsx` |
| TS function | camelCase | `fetchHomestays`, `adminLogin` |
| TS interface | PascalCase | `BookingResponse`, `HomestayInput` |
| API URL | kebab-case or plural noun | `/api/v1/homestays`, `/api/v1/bookings` |
| Environment var | UPPER_SNAKE_CASE | `DATABASE_URL`, `JWT_SECRET` |

### 12.4 ID Synchronization Rule

Frontend và Backend PHẢI thống nhất tên field cho ID của mỗi entity:
- Booking: dùng `booking_id` (KHÔNG dùng `id`)
- Các entity khác: dùng `id`

---

## 13. CHECKLIST TRIỂN KHAI PROJECT MỚI

### Phase 1: Infrastructure Setup (30 phút)

- [ ] Tạo folder structure (`backend/src/{models,repository,schemas,services,routes,db}`, `frontend/src/{app,features,shared,styles}`)
- [ ] Thiết lập alias path trong `frontend/tsconfig.json` (`"@/*": ["./src/*"]`)
- [ ] Tạo `docker-compose.yml` (db + backend + frontend)
- [ ] Tạo `backend/Dockerfile` + `backend/requirements.txt`
- [ ] Tạo `frontend/Dockerfile` + `frontend/package.json`
- [ ] Tạo `.env` + `.env_example`
- [ ] Tạo `.gitignore` (node_modules, __pycache__, .env, .next, uploads)
- [ ] Chạy `docker compose up --build` verify 3 services start

### Phase 2: Backend Core (1-2 giờ)

- [ ] `src/config.py` - Environment settings
- [ ] `src/db/main.py` - Engine, session factory, init_db()
- [ ] `src/models/` - Tất cả entity models + `_now_tz()` helper
- [ ] `src/auth.py` - Hash password, JWT, require_admin dependency
- [ ] `src/__init__.py` - FastAPI app, lifespan, CORS, router registration
- [ ] Test: `docker compose up --build` → tables created, admin seeded

### Phase 3: Backend CRUD per Entity (30 phút mỗi entity)

Cho mỗi entity, tạo theo thứ tự:
1. [ ] `models/entity.py` - SQLModel table
2. [ ] `schemas/entity.py` - Create, Update, Read schemas
3. [ ] `repository/entity.py` - CRUD functions
4. [ ] `services/entity.py` - Business logic + custom exceptions
5. [ ] `routes/entity.py` - Public + Admin endpoints
6. [ ] Register router trong `src/__init__.py`
7. [ ] Test endpoints với curl hoặc Swagger UI (`/docs`)

### Phase 4: Frontend Core (1-2 giờ)

- [ ] `src/app/layout.tsx` - Root layout, load Variable Fonts, Header/Footer
- [ ] `src/styles/global.css` - Tailwind directives & design tokens (CSS Variables)
- [ ] `src/shared/components/Header.tsx` + `Footer.tsx`
- [ ] `src/features/[entity]/dto/[entity].ts` - Định nghĩa TypeScript interfaces (DTOs)
- [ ] `src/features/[entity]/api/[entity].ts` - Lớp gọi API client (fetch functions)
- [ ] `src/app/page.tsx` - Trang chủ hiển thị danh sách và lấy dữ liệu
- [ ] Test: xem trang chủ load data từ backend thành công

### Phase 5: Frontend Features (2-4 giờ)

- [ ] Entity list page (cards/grid)
- [ ] Entity detail page (`src/app/details/[id]/page.tsx`)
- [ ] Admin login flow (`src/features/auth/components/LoginForm.tsx`)
- [ ] Admin dashboard main container (`src/features/admin/components/AdminDashboard.tsx`)
- [ ] Admin CRUD UI per entity (các tab quản lý đặt phòng, homestay, tiện ích...)
- [ ] File upload UI
- [ ] Responsive design verification

### Phase 6: Advanced Features (Optional)

- [ ] Chatbot integration (AI service + widget ở `src/features/chatbot/components/Chatbot.tsx`)
- [ ] Booking/Ordering system với room inventory quản lý tồn kho theo ngày
- [ ] Lịch hiển thị ngày trống (`src/features/booking/components/AvailabilityCalendar.tsx`)
- [ ] Semantic search / Semantic cache cho chatbot AI
- [ ] Image gallery/slideshow
- [ ] Real-time notifications

### Phase 7: Production Prep

- [ ] Đổi Dockerfile CMD sang production mode (uvicorn workers, next build + start)
- [ ] Set strong JWT_SECRET, ADMIN_PASSWORD
- [ ] Configure specific CORS origins
- [ ] Add health check endpoints
- [ ] Setup logging
- [ ] Backup strategy cho PostgreSQL volume

---

## APPENDIX: COPY-PASTE TEMPLATES

### A. Thêm Entity Mới (Backend)

Khi cần thêm 1 entity mới (VD: "Review"), copy 5 file sau và thay tên:

```
backend/src/models/review.py      ← Copy từ models/amenity.py
backend/src/schemas/review.py     ← Copy từ schemas/amenity.py
backend/src/repository/review.py  ← Copy từ repository/amenity.py
backend/src/services/review.py    ← Copy từ services/amenity.py
backend/src/routes/review.py      ← Copy từ routes/amenities.py
```

Rồi:
1. Import model trong `models/__init__.py`
2. Import router trong `src/__init__.py` và `app.include_router()`
3. Chạy lại server → table tự tạo

### B. Thêm Entity Mới (Frontend)

```
frontend/src/features/review/api/review.ts                 ← Copy từ features/homestay/api/amenities.ts (đổi URL)
frontend/src/features/review/dto/review.ts                 ← Định nghĩa interface Review
frontend/src/features/review/components/ReviewManagement.tsx  ← Copy từ features/homestay/components/AmenityManagement.tsx
```

Rồi thêm tab mới vào AdminDashboard.

---

> **💡 Tip cuối**: File này là "living document". Mỗi khi bạn phát hiện pattern mới hoặc quy tắc cần bổ sung, hãy cập nhật vào đây. Blueprint càng chi tiết, việc khởi tạo project mới càng nhanh.
