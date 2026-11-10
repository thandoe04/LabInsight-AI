@echo off
setlocal EnableDelayedExpansion
title LabInsight AI — Launcher

:: ============================================================
:: LabInsight AI — One-Click Startup Launcher
:: Double-click this file to start all services.
:: ============================================================

set "PROJECT_DIR=%~dp0"
set "COMPOSE_FILE=%PROJECT_DIR%docker-compose.yml"
set "FRONTEND_URL=http://localhost:5173"
set "BACKEND_URL=http://localhost:8000"
set "SWAGGER_URL=http://localhost:8000/docs"

cd /d "%PROJECT_DIR%"

echo.
echo  =========================================================
echo   LabInsight AI — Healthcare Laboratory Analytics Platform
echo  =========================================================
echo.

:: ── Step 1: Check Docker Desktop is running ────────────────
echo [1/6] Checking Docker Desktop...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] Docker Desktop is not running.
    echo.
    echo  Please:
    echo    1. Open Docker Desktop from the Start Menu or taskbar.
    echo    2. Wait until the Docker whale icon in the system tray is steady.
    echo    3. Then double-click this file again.
    echo.
    pause
    exit /b 1
)
echo         Docker Desktop is running. OK
echo.

:: ── Step 2: Check docker-compose.yml exists ────────────────
echo [2/6] Checking project files...
if not exist "%COMPOSE_FILE%" (
    echo  [ERROR] docker-compose.yml not found in:
    echo          %PROJECT_DIR%
    echo  Make sure you are running this from the LabInsight-AI folder.
    pause
    exit /b 1
)
echo         Project files found. OK
echo.

:: ── Step 3: Pull/build images and start all containers ─────
echo [3/6] Building and starting all services (this may take a few minutes on first run)...
echo         postgres ^| redis ^| backend ^| frontend
echo.
docker compose up --build -d
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] docker compose up failed.
    echo  Check Docker Desktop for error details, or run:
    echo          docker compose logs
    pause
    exit /b 1
)
echo.
echo         All containers started.
echo.

:: ── Step 4: Wait for backend health check ──────────────────
echo [4/6] Waiting for the backend API to become healthy...
echo         (Checking http://localhost:8000/api/v1/health every 5 seconds)
echo.

set /a ATTEMPTS=0
set /a MAX_ATTEMPTS=24

:WAIT_LOOP
set /a ATTEMPTS+=1
if %ATTEMPTS% GTR %MAX_ATTEMPTS% (
    echo.
    echo  [WARNING] Backend did not become healthy after 2 minutes.
    echo  The seed may not run. Check logs with:
    echo          docker compose logs backend
    echo.
    goto SKIP_SEED
)

:: Use PowerShell to do an HTTP GET (curl may not exist on all Windows installs)
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo         Backend is healthy after %ATTEMPTS% check(s). OK
    goto BACKEND_READY
)

<nul set /p=.
timeout /t 5 /nobreak >nul
goto WAIT_LOOP

:BACKEND_READY
echo.

:: ── Step 5: Seed the database ──────────────────────────────
echo [5/6] Seeding the database with sample data...
echo.
echo  This creates:
echo    - Admin, analyst, lab-technician, and viewer demo accounts
echo    - Synthetic patient records
echo    - Sample registrations, test results, and ML experiment data
echo.

:: Check if already seeded by counting users
docker compose exec -T backend python -c "
import asyncio, sys
from app.db.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select, func

async def check():
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(func.count()).select_from(User))
        count = result.scalar()
        print(count)
        sys.exit(0 if count == 0 else 2)

asyncio.run(check())
" 2>nul
set "SEED_CHECK=%ERRORLEVEL%"

if "%SEED_CHECK%"=="2" (
    echo         Database already seeded — skipping.
) else (
    docker compose exec -T backend python -m app.db.seed
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo  [WARNING] Seed script returned an error.
        echo  The application may still work if tables were already created.
        echo  To re-seed manually: docker compose exec backend python -m app.db.seed
    ) else (
        echo.
        echo         Database seeded successfully.
    )
)

:SKIP_SEED
echo.

:: ── Step 6: Open browser ───────────────────────────────────
echo [6/6] Opening LabInsight AI in your browser...
echo.
timeout /t 2 /nobreak >nul
start "" "%FRONTEND_URL%"
echo.

:: ── Summary ────────────────────────────────────────────────
echo  =========================================================
echo   LabInsight AI is running!
echo  =========================================================
echo.
echo   Frontend:    %FRONTEND_URL%
echo   Backend API: %BACKEND_URL%
echo   Swagger UI:  %SWAGGER_URL%
echo.
echo   Demo accounts (all use password: LabInsight2024!):
echo     admin@labinsight.dev      — Administrator
echo     analyst@labinsight.dev    — Data Analyst
echo     technician@labinsight.dev — Lab Technician
echo     viewer@labinsight.dev     — Read-only Viewer
echo.
echo   To stop all services:  Double-click STOP-LABINSIGHT.bat
echo   To view logs:          docker compose logs -f
echo   To run tests:          docker compose exec backend pytest
echo.
echo  =========================================================
echo.
echo  Press any key to close this window (services keep running).
pause >nul
endlocal
