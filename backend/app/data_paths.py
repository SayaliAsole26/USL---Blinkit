"""Resolve monorepo data/ directory for local dev and Docker (/app/data)."""

from pathlib import Path


def get_data_dir() -> Path:
    app_package = Path(__file__).resolve().parent
    for base in (app_package.parent, app_package.parent.parent):
        data = base / "data"
        if (data / "catalog-fixtures.json").exists():
            return data
    return app_package.parent / "data"
