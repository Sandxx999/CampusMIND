# CampusMIND 2.0 — System Architecture Document

## Overview

CampusMIND 2.0 is designed as a modular monolith campus intelligence platform. The system decouples presentation, route handling, business logic, data persistence, and vector retrieval into explicit, clean architectural boundaries.

```mermaid
graph TD
    subgraph Presentation Layer
        UI[React 18 / Vite Frontend]
    end

    subgraph API & Core Layer
        Router[FastAPI Route Handlers /api/v1/]
        Middleware[Correlation & Secret Masking Middleware]
        ErrorHandler[Centralized Exception Handlers]
    end

    subgraph Service Layer
        AuthSvc[Auth Service]
        StudentSvc[Student Service]
        AdminSvc[Admin Service]
        ChatSvc[Chat & RAG Service]
    end

    subgraph Data & Persistence Layer
        UserRepo[User Repository]
        StudentRepo[Student Repository]
        AuditRepo[Audit Repository]
        SQLAlchemy[SQLAlchemy 2.x Session & Engine Abstraction]
        PostgreSQL[(PostgreSQL Production DB)]
        SQLite[(SQLite Local/Test DB)]
        Chroma[(ChromaDB Vector Store)]
    end

    subgraph External Systems
        Gemini[Google Gemini 1.5 Flash API]
    end

    UI -->|HTTP / JWT| Router
    Router --> Middleware
    Middleware --> ErrorHandler
    Router --> AuthSvc
    Router --> StudentSvc
    Router --> AdminSvc
    Router --> ChatSvc

    AuthSvc --> UserRepo
    StudentSvc --> StudentRepo
    AdminSvc --> AuditRepo
    ChatSvc --> AuditRepo
    ChatSvc --> StudentRepo

    UserRepo --> SQLAlchemy
    StudentRepo --> SQLAlchemy
    AuditRepo --> SQLAlchemy
    SQLAlchemy --> PostgreSQL
    SQLAlchemy --> SQLite
    ChatSvc --> Chroma
    ChatSvc --> Gemini
```

---

## Key Architectural Principles

1. **Modular Monolith Layout**: Single backend repository organized by responsibility (`core/`, `db/`, `repositories/`, `services/`, `api/`, `models/`, `auth/`, `rag/`).
2. **Repository Pattern**: All database persistence is encapsulated inside repositories (`StudentRepository`, `AuditRepository`). Raw SQL statements are forbidden inside API route handlers.
3. **Service Layer**: Business rules, role authorization logic, and rate limiting reside inside domain services.
4. **Environment-Based Configuration**: Fail-closed configuration (`core/config.py`) enforcing strict production security rules (unique secrets, no demo mode in production, explicit CORS origins).
5. **API Versioning**: Standardized `/api/v1/` prefix with backwards-compatible `/api/` alias mounts for legacy callers.
6. **Structured Observability**: Centralized logging (`core/logging.py`) equipped with an automated `SecretMaskingFilter` that redacts passwords, JWTs, and API keys. Every request is assigned a unique `X-Request-ID`.

---

## Component Boundaries

| Module | Responsibility |
| :--- | :--- |
| `backend/core/` | Global settings, secret-masking logging, request correlation middleware. |
| `backend/db/` | SQLAlchemy 2.x ORM models, session factories, and Alembic versioned migrations. |
| `backend/repositories/` | Direct ORM data access (`StudentRepository`, `AcademicRepository`, `AttendanceRepository`, `AssessmentRepository`, `AnnouncementRepository`, `EventRepository`, `KnowledgeRepository`, `AuditRepository`). |
| `backend/services/` | Business logic, server-side RBAC, validation, and domain workflows (`AuthService`, `AcademicService`, `AttendanceService`, `AssessmentService`, `AnnouncementService`, `EventService`, `KnowledgeService`, `SearchService`, `StudentService`, `AdminService`, `ChatService`). |
| `backend/api/` | FastAPI routes (`routes_academics`, `routes_attendance`, `routes_assessments`, `routes_announcements`, `routes_events`, `routes_knowledge`, `routes_search`), validation, error handlers. |
| `backend/models/` | Pydantic request/response schemas and domain data contracts. |
| `backend/auth/` | JWT token generation, decoding, and server-side RBAC validation. |
| `backend/rag/` | Document chunking, embedding generation, and ChromaDB vector retrieval. |
