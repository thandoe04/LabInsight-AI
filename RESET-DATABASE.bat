@echo off
setlocal
title LabInsight AI — Reset Database

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo.
echo  =========================================================
echo   LabInsight AI — Reset and Re-seed Database
echo  =========================================================
echo.
echo  WARNING: This will DELETE all data and re-seed from scratch.
echo.
set /p CONFIRM=Type YES to continue, or press Enter to cancel: 

if /i not "%CONFIRM%"=="YES" (
    echo  Cancelled.
    pause
    exit /b 0
)

docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Docker Desktop is not running.
    pause
    exit /b 1
)

echo.
echo  Stopping services...
docker compose down

echo  Removing database volume...
docker volume rm labinsight-ai_postgres_data 2>nul
docker volume rm labinsight_ai_postgres_data 2>nul

echo.
echo  Rebuilding and restarting...
docker compose up --build -d

echo.
echo  Waiting for backend to become healthy...
:WAIT_LOOP
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health' -UseBasicParsing -TimeoutSec 3; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    <nul set /p=.
    timeout /t 5 /nobreak >nul
    goto WAIT_LOOP
)

echo.
echo  Seeding fresh data...
docker compose exec -T backend python -m app.db.seed

echo.
echo  Database reset complete.
echo  Open http://localhost:5173 to use the application.
echo.
pause
endlocal
