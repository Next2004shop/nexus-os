@echo off
title Nexus AI - UNIFIED LAUNCHER
color 0b
cls

echo.
echo  =======================================================
echo   NEXUS AI - ULTIMATE TRADING SYSTEM
echo  =======================================================
echo   [1] Initializing Environment...
echo.

REM 1. Start Python Backend (Hidden Window, Output to Logs)
echo   [2] Launching Neural Backend (Port 5001)...
start /B "NexusBackend" cmd /c "python nexus_bridge.py > backend.log 2>&1"

REM 2. Determine PHP Command
set PHP_CMD=php
if exist "php\php.exe" set PHP_CMD=php\php.exe

REM 3. Start PHP Frontend
echo   [3] Launching Visual Interface (Port 8000)...
echo.
echo   [SUCCESS] SYSTEM ONLINE.
echo   [INFO] Access the Terminal at: http://localhost:8000
echo.
echo   Press Ctrl+C to shutdown.
echo.

"%PHP_CMD%" -S localhost:8000
