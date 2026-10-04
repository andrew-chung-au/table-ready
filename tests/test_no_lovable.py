"""Guard for issue #9: the disconnected Lovable integration stays removed.

Lives outside frontend/src so the guard's own search term doesn't trip the
`rg -i lovable frontend/src` check it protects.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANNED_DIRS = [ROOT / "frontend", ROOT / "backend"]
# Dependencies and build output, all git-ignored.
SKIPPED_DIR_NAMES = {"node_modules", ".output", "dist", ".wrangler", ".tanstack", ".nitro", "__pycache__"}


def _files(base: Path):
    for path in base.rglob("*"):
        if any(part in SKIPPED_DIR_NAMES for part in path.relative_to(base).parts):
            continue
        if path.is_file():
            yield path


def test_frontend_and_backend_have_no_lovable_references():
    offenders = [
        str(path.relative_to(ROOT))
        for base in SCANNED_DIRS
        for path in _files(base)
        if b"lovable" in path.read_bytes().lower()
    ]
    assert offenders == []


def test_scan_covers_the_files_the_wrapper_used_to_touch():
    scanned = {str(p.relative_to(ROOT)) for base in SCANNED_DIRS for p in _files(base)}
    for expected in [
        "frontend/vite.config.ts",
        "frontend/package.json",
        "frontend/bun.lock",
        "frontend/bunfig.toml",
        "frontend/src/routes/__root.tsx",
        "backend/config.py",
    ]:
        assert expected in scanned


def test_lovable_only_files_are_deleted():
    assert not (ROOT / "frontend" / "AGENTS.md").exists()
    assert not (ROOT / "frontend" / "src" / "lib" / "lovable-error-reporting.ts").exists()
