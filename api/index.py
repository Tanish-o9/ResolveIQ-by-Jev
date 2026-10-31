from __future__ import annotations
import sys
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import app as fastapi_app


async def app(scope, receive, send):
    """Vercel ASGI wrapper that normalizes rewritten paths from /api/index.py to root routes."""
    if scope.get("type") in ("http", "websocket"):
        path = scope.get("path", "")
        for prefix in ("/api/index.py", "/api/index"):
            if path.startswith(prefix):
                normalized = path[len(prefix):] or "/"
                scope["path"] = normalized
                scope["raw_path"] = normalized.encode("utf-8")
                break
    await fastapi_app(scope, receive, send)
