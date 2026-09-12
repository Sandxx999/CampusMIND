# CampusMIND 2.0 — Enterprise Campus Intelligence Platform

CampusMIND 2.0 is an enterprise-grade Retrieval-Augmented Generation (RAG) assistant designed for higher education institutions. It provides role-scoped access control (RBAC), citation tracking, student analytics, structured logging, and robust API security.

---

## Current Architecture (Phase 1 Baseline)

CampusMIND 2.0 uses a **Modular Monolith** architecture:

- **Presentation**: React 18 + Vite frontend styled with TailwindCSS & Lucide icons.
- **API & Routing**: FastAPI backend with `/api/v1/` versioned routes and `/api/` backwards-compatible mounts.
- **Core Architecture**:
  - `core/`: Environment-backed configuration, secret-masking logging, correlation middleware.
  - `db/`: Isolated connection session management for SQLite (PostgreSQL-ready).
  - `repositories/`: Repository pattern data access layer (`StudentRepository`, `AuditRepository`).
  - `services/`: Business logic services (`AuthService`, `StudentService`, `AdminService`, `ChatService`).
- **Security & Authorization**: JWT token authorization, server-enforced RBAC (Student, Faculty, Admin), IDOR protection, fail-closed production validation.
- **RAG Engine**: ChromaDB vector retrieval, `sentence-transformers` embeddings, and Google Gemini 1.5 Flash grounded synthesis fallback.

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
- [Local Development Guide](docs/DEVELOPMENT.md)
- [Database & Infrastructure Migration Strategy](docs/MIGRATION_STRATEGY.md)
