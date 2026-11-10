@echo off
setlocal
title LabInsight AI — Stop Services

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo.
echo  =========================================================
echo   LabInsight AI — Stopping all services
echo  =========================================================
echo.

docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  Docker Desktop is not running — nothing to stop.
    pause
    exit /b 0
)

echo  Stopping containers...
docker compose down

echo.
echo  All LabInsight AI services stopped.
echo  Your database data is preserved in the Docker volume.
echo.
echo  To start again: Double-click START-LABINSIGHT.bat
echo.
pause
endlocal
