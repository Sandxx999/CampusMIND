# CampusMIND 2.0 — Enterprise Campus Intelligence Platform

CampusMIND 2.0 is an enterprise-grade Retrieval-Augmented Generation (RAG) assistant designed for higher education institutions. It provides role-scoped access control (RBAC), citation tracking, student analytics, structured logging, and robust API security.

---

## Current Architecture (Phase 3 Foundation)

CampusMIND 2.0 uses a **Modular Monolith** architecture:

- **Presentation**: React 18 + Vite frontend with Campus Intelligence Portal, Assistant Chat, and System Hub.
- **API & Routing**: FastAPI backend with `/api/v1/` versioned routes for Academics, Attendance, Assessments, Announcements, Campus Events, Knowledge Foundation, and Search.
- **Core Architecture**:
  - `core/`: Environment-backed configuration, secret-masking logging, correlation middleware.
  - `db/`: SQLAlchemy 2.x ORM models & Alembic database migration pipeline (SQLite / PostgreSQL dual-dialect).
  - `repositories/`: Data access abstractions (`StudentRepository`, `AcademicRepository`, `AttendanceRepository`, `AssessmentRepository`, `AnnouncementRepository`, `EventRepository`, `KnowledgeRepository`, `AuditRepository`).
  - `services/`: Business logic services (`AuthService`, `StudentService`, `AcademicService`, `AttendanceService`, `AssessmentService`, `AnnouncementService`, `EventService`, `KnowledgeService`, `SearchService`, `AdminService`, `ChatService`).
- **Security & Authorization**: Server-controlled JWT token validation, RBAC (Student, Faculty, Admin), IDOR protection, audience-filtered institutional queries, fail-closed validation.
- **RAG Engine & Knowledge Foundation**: Knowledge document metadata tracking, ChromaDB vector retrieval, `sentence-transformers` embeddings, and Google Gemini 1.5 Flash grounded synthesis fallback.


---

## Quick Start

### Local Development

1. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```

2. **Backend Setup & Run**:
   ```bash
   cd backend
   python -m venv venv
   # Activate virtual environment
   # Windows: .\venv\Scripts\activate | Linux/macOS: source venv/bin/activate
   pip install -r requirements-dev.txt
   python main.py
   ```

3. **Frontend Setup & Run**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker Compose Execution

```bash
docker-compose up --build
```

---

## Running Tests & Builds

- **Run Python Backend Tests**:
  ```bash
  python -m pytest -q
  ```

- **Build Frontend Bundle**:
  ```bash
  cd frontend && npm run build
  ```

---

## Documentation

- [System Architecture](docs/ARCHITECTURE.md)
- [Production Data & Identity Architecture](docs/DATABASE_ARCHITECTURE.md)
- [Local Development Guide](docs/DEVELOPMENT.md)
- [Database & Infrastructure Migration Strategy](docs/MIGRATION_STRATEGY.md)
