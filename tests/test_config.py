import importlib

import backend.config


def test_cors_defaults_match_frontend_dev_server_port(monkeypatch):
    # Issue #9 removed the Lovable Vite wrapper; the frontend dev server stays on
    # 8080 (frontend/vite.config.ts), so the default CORS origins must not change.
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    config = importlib.reload(backend.config)
    try:
        assert config.ALLOWED_ORIGINS == ["http://localhost:8080", "http://127.0.0.1:8080"]
    finally:
        monkeypatch.undo()
        importlib.reload(backend.config)


def test_allowed_origins_env_override_still_applies(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", " http://example.test:3000 ,, http://localhost:9000")
    config = importlib.reload(backend.config)
    try:
        assert config.ALLOWED_ORIGINS == ["http://example.test:3000", "http://localhost:9000"]
    finally:
        monkeypatch.undo()
        importlib.reload(backend.config)
