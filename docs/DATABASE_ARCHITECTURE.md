# CampusMIND 2.0 — Production Data & Identity Architecture

## Executive Overview

Phase 2 establishes a production-grade relational database architecture for CampusMIND 2.0. The platform transitions to a normalized relational schema backed by **SQLAlchemy 2.x ORM** and **Alembic** migrations.

The architecture supports dual-database operation:
- **Production**: Managed PostgreSQL (`postgresql://` via `psycopg2-binary`) with environment-driven connection pooling.
- **Development & Testing**: Local SQLite (`sqlite:///`) with automatic fallback support for rapid iteration and test isolation.

---

## Entity Relationship (ER) Diagram

```mermaid
erDiagram
    roles ||--o{ users : "assigned to"
    users ||--o| student_profiles : "has profile"
    users ||--o| faculty_profiles : "has profile"
    users ||--o| admin_profiles : "has profile"
    users ||--o{ query_logs : "author"
    users ||--o{ audit_events : "actor"

    departments ||--o{ programs : "offers"
    departments ||--o{ courses : "offers"
    departments ||--o{ student_profiles : "enrolled in"
    departments ||--o{ faculty_profiles : "belongs to"

    programs ||--o{ student_profiles : "studies in"

    student_profiles ||--o{ enrollments : "enrolled"
    courses ||--o{ enrollments : "enrolled"

    query_logs ||--o{ query_feedback : "has feedback"

    roles {
        string id PK
        string name UK
        string description
        timestamp created_at
    }

    users {
        string id PK
        string username UK
        string email UK
        string display_name
        string password_hash
        string status
        string role_id FK
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }

    departments {
        string id PK
        string code UK
        string name
        timestamp created_at
    }

    programs {
        string id PK
        string code UK
        string name
        string department_id FK
        integer duration_years
        timestamp created_at
    }

    courses {
        string id PK
        string code UK
        string title
        string department_id FK
        integer credits
        timestamp created_at
    }

    student_profiles {
        string id PK
        string user_id FK,UK
        string enrollment_no UK
        string department_id FK
        string program_id FK
        string branch
        integer year
        integer semester
        string courses_enrolled
        float sgpa
        float cgpa
        float attendance_pct
        integer backlogs
        string fee_status
        string mobile_no
        timestamp created_at
        timestamp updated_at
    }

    faculty_profiles {
        string id PK
        string user_id FK,UK
        string employee_id UK
        string department_id FK
        string designation
        timestamp created_at
        timestamp updated_at
    }

    admin_profiles {
        string id PK
        string user_id FK,UK
        string employee_id UK
        string designation
        timestamp created_at
        timestamp updated_at
    }

    enrollments {
        string id PK
        string student_profile_id FK
        string course_id FK
        string academic_year
        integer semester
        string grade
        timestamp created_at
    }

    query_logs {
        string id PK
        string user_id FK
        timestamp timestamp
        string username
        string role
        text question
        text answer
        float latency_ms
        integer chunk_count
        float confidence
        boolean is_fallback
        timestamp created_at
    }

    query_feedback {
        integer id PK
        string query_id FK
        boolean is_positive
        timestamp timestamp
    }

    audit_events {
        string id PK
        string event_type
        string user_id FK
        string actor_username
        string ip_address
        text details
        timestamp timestamp
    }
```

---

## Key Architectural Principles

### 1. Identity & Domain Profile Separation
User authentication (`User`, `Role`) is strictly separated from domain-specific academic profiles (`StudentProfile`, `FacultyProfile`, `AdminProfile`). This decouples authentication mechanics from academic business logic and prepares the system for OIDC / Single Sign-On (SSO) integration.

### 2. Database Abstraction Layer
The domain service layer (`StudentService`, `AuthService`, `ChatService`) interacts with repositories (`UserRepository`, `StudentRepository`, `AuditRepository`). Repositories consume SQLAlchemy 2.x sessions, hiding SQL dialect differences between SQLite and PostgreSQL.

### 3. Connection Pooling
PostgreSQL production connections are pooled via SQLAlchemy engine configuration:
- `DB_POOL_SIZE`: Default 5
- `DB_MAX_OVERFLOW`: Default 10
- `DB_POOL_TIMEOUT`: Default 30s
- `DB_POOL_RECYCLE`: Default 1800s
- `pool_pre_ping=True`: Ensures stale or dropped connections are detected before query execution.

---

## Alembic Migration Workflow

Alembic manages versioned database migrations in `backend/alembic/`.

### Development Workflow
1. Apply migrations to active database:
   ```bash
   cd backend
   alembic upgrade head
   ```
2. Generate a new revision:
   ```bash
   cd backend
   alembic revision -m "Describe migration"
   ```
3. Rollback last migration:
   ```bash
   cd backend
   alembic downgrade -1
   ```

### Production Workflow
During automated container startup or deployment pipelines:
```bash
cd backend && alembic upgrade head
```

---

## Data Migration Strategy

To transition legacy SQLite databases (`campusmind.db`) to PostgreSQL or canonical SQLite schemas without data loss:

```bash
python backend/scripts/migrate_sqlite_to_pg.py --source-sqlite ./backend/campusmind.db --target-db_url "postgresql://user:pass@localhost:5432/campusmind"
```

The script:
1. Reads legacy `students`, `query_logs`, and `query_feedback` tables.
2. Creates corresponding canonical `User`, `StudentProfile`, `QueryLog`, and `QueryFeedback` ORM entities.
3. Validates record counts to ensure 100% data integrity.

---

## Test Database Strategy

All unit and integration tests run in isolated temporary SQLite databases initialized during pytest session execution (`tests/conftest.py`). Production credentials are never used in test runs.
