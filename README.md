# CampusMIND 2.0 — Enterprise Campus Intelligence Platform

CampusMIND 2.0 is an enterprise-grade Retrieval-Augmented Generation (RAG) assistant designed for higher education institutions. It provides role-scoped access control (RBAC), citation tracking, student analytics, structured logging, intelligent document chunking, hybrid vector/lexical retrieval, evidence quality scoring, prompt injection defense, and robust API security.

---

## Current Architecture (Phase 4 Advanced RAG & Campus Intelligence Engine)

CampusMIND 2.0 uses a **Modular Monolith** architecture:

- **Presentation**: React 18 + Vite frontend with Campus Intelligence Portal, Assistant Chat, Evidence Quality Indicators, First-Class Citations, and System Hub.
- **API & Routing**: FastAPI backend with `/api/v1/` versioned routes for Academics, Attendance, Assessments, Announcements, Campus Events, Knowledge Foundation, Search, and RAG Chat.
- **Core Architecture**:
  - `core/`: Environment-backed configuration, secret-masking logging, correlation middleware.
  - `db/`: SQLAlchemy 2.x ORM models & Alembic database migration pipeline (SQLite / PostgreSQL dual-dialect).
  - `repositories/`: Data access abstractions (`StudentRepository`, `AcademicRepository`, `AttendanceRepository`, `AssessmentRepository`, `AnnouncementRepository`, `EventRepository`, `KnowledgeRepository`, `AuditRepository`).
  - `services/`: Domain services (`AuthService`, `StudentService`, `AcademicService`, `AttendanceService`, `AssessmentService`, `AnnouncementService`, `EventService`, `KnowledgeService`, `SearchService`, `AdminService`, `ChatService`).
- **Advanced RAG Engine (`rag/`)**:
  - `embeddings.py`: `EmbeddingProvider` abstraction (SentenceTransformers, Gemini, Mock).
  - `vector_store.py`: `VectorStore` encapsulation around ChromaDB persistent client.
  - `chunker.py`: `InstitutionalChunker` section and heading aware text splitter.
  - `ingest.py`: `DocumentIngestionEngine` with SHA-256 checksums, idempotency, versioning, and stale vector purging.
  - `retriever.py`: `HybridCampusRetriever` combining vector similarity, keyword density, and server-side RBAC audience filtering.
  - `reranker.py`: `DeterministicHybridReranker` and empirical `evidence_quality` signal (`high`, `medium`, `low`, `insufficient`).
  - `query_processor.py`: `QueryProcessor` for sanitization, prompt-injection defense, and intent classification.
  - `evaluator.py`: `RAGEvaluator` benchmark harness for hit rate, citations, and security metrics.
- **Security & Authorization**: Server-side JWT validation, RBAC (`student`, `faculty`, `admin`), IDOR protection, student database isolation, prompt injection defense with XML framing, fail-closed configuration.

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
   pip install -r requirements.txt
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

## Running Tests & Verification

- **Run Python Backend Tests**:
  ```bash
  python -m pytest
  ```

- **Run RAG Evaluation Benchmark**:
  ```bash
  python -m rag.evaluator
  ```

- **Build Frontend Production Bundle**:
  ```bash
  cd frontend && npm run build
  ```

---

## Documentation

- [System Architecture](docs/architecture.md)
- [Advanced RAG Architecture](docs/RAG_ARCHITECTURE.md)
- [Production Data & Identity Architecture](docs/DATABASE_ARCHITECTURE.md)
- [Local Development Guide](docs/DEVELOPMENT.md)
- [Database & Infrastructure Migration Strategy](docs/MIGRATION_STRATEGY.md)
