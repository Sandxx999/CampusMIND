# Repository Guidelines

## Project Structure & Module Organization

`frontend/` contains the React 18/Vite application. Keep reusable UI in
`frontend/src/components/`, route-level views in `frontend/src/pages/`, and HTTP
calls in `frontend/src/lib/api.js`. `backend/` is the FastAPI service:
`api/` holds route modules, `auth/` contains JWT/RBAC helpers, `models/` defines
schemas, and `rag/` implements ingestion, chunking, prompts, and retrieval.
Sample source material lives in `data/`; project documentation is in `docs/`.
Put Python tests in root-level `tests/` and RAG evaluation fixtures in
`tests/eval_qa_pairs.json`.

## Build, Test, and Development Commands

Run commands from the indicated directory:

```powershell
cd backend; python -m pip install -r requirements.txt  # install API dependencies
cd backend; python main.py                              # start FastAPI locally
cd backend; python -m rag.ingest                        # ingest documents into Chroma
python -m pytest tests                                  # run the Python test suite
cd frontend; npm install                                # install UI dependencies
cd frontend; npm run dev                                # run Vite development server
cd frontend; npm run build                              # produce a production bundle
```

## Coding Style & Naming Conventions

Follow the surrounding code. Python uses four-space indentation, `snake_case`
for functions and modules, `PascalCase` for Pydantic models, and explicit type
annotations where they improve API boundaries. React components and pages use
`PascalCase` filenames (for example, `MessageBubble.jsx`); hooks, local values,
and API helpers use `camelCase`. Keep UI behavior in components and backend
access behind `src/lib/api.js`. No formatter or linter is configured, so do not
add one incidentally; keep changes consistently formatted and small.

## Testing Guidelines

Use `pytest` and name files `test_*.py` and test functions `test_*`, matching
the existing suite. Add focused coverage for changed authentication, route, or
retrieval behavior; mock external model/API calls instead of requiring live
credentials. Run `python -m pytest tests` before opening a PR. There is no
declared coverage threshold or frontend test runner.

## Commit & Pull Request Guidelines

Recent commits use concise, imperative summaries, e.g. `Optimize FastAPI
startup` or `Add Render blueprint configuration`. Keep each commit scoped to
one change. PRs should state the user-facing effect, list validation performed,
link related issues, and include screenshots for UI changes. Call out schema,
environment, or ingestion changes explicitly.

## Security & Configuration

Keep secrets in `.env` files and never commit API keys, SQLite databases,
Chroma data, logs, virtual environments, `node_modules`, or build output.
Preserve server-side RBAC checks when adding endpoints, and avoid logging
tokens or student data.
