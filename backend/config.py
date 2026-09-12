"""
Backwards-compatibility shim for core application settings.
Delegates setting instantiation to backend.core.config.
"""
from core.config import Settings, parse_cors_origins, settings

__all__ = ["Settings", "parse_cors_origins", "settings"]
