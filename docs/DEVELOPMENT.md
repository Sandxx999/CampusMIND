# CampusMIND 2.0 — Local Development & Setup Guide

## Prerequisites

- **Python**: 3.11.x (Recommended runtime version for PyTorch and cross-platform compatibility).
- **Node.js**: v18+ / v20+
- **Docker & Docker Compose**: (Optional, for containerized local development)

---

## Environment Setup

1. **Clone and create local environment configuration**:
   ```bash
   cp .env.example .env
   ```

2. **Configure Python Virtual Environment**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements-dev.txt
   ```

3. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

---

## Running the Application Locally

### Option A: Local Process Execution

1. **Start FastAPI Backend**:
   ```bash
   cd backend
   python main.py
   # Or using uvicorn: uvicorn main:app --reload --port 8000
   ```
   API Documentation available at: [http://localhost:8000/docs](http://localhost:8000/docs)
   Health Check available at: [http://localhost:8000/health](http://localhost:8000/health)

2. **Start React Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   UI application accessible at: [http://localhost:5173](http://localhost:5173)

---

### Option B: Docker Compose Container Execution

Build and run all services in isolated containers:
```bash
docker-compose up --build
```
- Backend container runs on `http://localhost:8000`
- Production Nginx frontend runs on `http://localhost:5173`

---

## Running Tests & Quality Verification

Run full Python backend test suite (includes security, RBAC, retrieval, system health, and architecture tests):
```bash
python -m pytest -v
```

Verify Frontend production bundle build:
```bash
cd frontend
npm run build
```
