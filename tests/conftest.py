"""Safe, explicit runtime settings and isolated fixtures for the local demo test suite."""

import os
import shutil
import tempfile
import pytest

# Ensure safe default environment variables
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Copies campusmind.db into a temporary directory so pytest never modifies real DB."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    real_db_path = os.path.join(root_dir, "campusmind.db")
    
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_campusmind.db")
    
    if os.path.exists(real_db_path):
        shutil.copy2(real_db_path, temp_db_path)
    
    db_url = f"sqlite:///{temp_db_path}"
    os.environ["DATABASE_URL"] = db_url

    import sys
    backend_path = os.path.join(root_dir, "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    try:
        from config import settings
        settings.DATABASE_URL = db_url
    except Exception:
        pass
        
    try:
        import logs.logger
        logs.logger.DB_PATH = temp_db_path
        logs.logger.init_db()
    except Exception:
        pass

    yield

    shutil.rmtree(temp_dir, ignore_errors=True)
