# CampusMind — Enterprise RAG Campus Assistant

CampusMind is a production-style Enterprise Retrieval-Augmented Generation (RAG) Campus Assistant designed for students, faculty, and administrative staff. It provides accurate, grounded answers using strictly retrieved official campus documents (timetables, circulars, fee deadlines, placement notices, and rules).

## 🚀 Key Features

- **Strictly Grounded RAG**: Zero hallucinations — if context is missing, CampusMind explicitly states "I don't have information on that".
- **Source Citations**: Every response references exact document sources, sections, and confidence scores.
- **Role-Based Access Control (RBAC)**: Fine-grained access for `student`, `faculty`, and `admin` roles enforced server-side.
- **Analytics & Feedback**: Thumbs up/down feedback logging per query and an Admin Dashboard for query volume, top topics, latency, and failure rates.
- **Enterprise Security**: Input sanitization, rate-limiting, and JWT authentication.

## 🛠️ Architecture & Tech Stack

- **Frontend**: React + Vite + TailwindCSS
- **Backend**: FastAPI (Python 3.10+)
- **Vector Database**: ChromaDB (Local, Persistent)
- **Embeddings**: `sentence-transformers` (all-MiniLM-L6-v2) or Gemini Embedding API
- **LLM Engine**: Google Gemini API (`gemini-1.5-flash`) via LangChain / Google GenAI SDK
- **Database**: SQLite (Metadata, Logs, Feedback)

## 🏁 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
# Add your GEMINI_API_KEY to .env
python main.py
```

### 2. Ingest Sample Data
```bash
cd backend
python -m rag.ingest
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to access CampusMind.
