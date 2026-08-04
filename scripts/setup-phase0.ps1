$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

docker compose up -d

Set-Location backend
python -m pip install -r requirements.txt -q
alembic upgrade head
python scripts/seed_catalog.py

Write-Host "Phase 0 setup complete."
Write-Host "Backend: uvicorn app.main:app --reload --app-dir backend"
Write-Host "Frontend: cd frontend && npm install && npm run dev"
