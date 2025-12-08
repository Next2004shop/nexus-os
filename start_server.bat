@echo off
title Nexus AI Server
color 0f
cls
echo.
echo  =======================================================
echo   NEXUS AI - RAW POWER STACK (PHP 8.3 + jQuery)
echo  =======================================================
echo.

REM Check for local portable PHP first
if exist "php\php.exe" (
    echo  [INFO] Using local portable PHP...
    set PHP_CMD=php\php.exe
) else (
    REM Fallback to global PHP
    WHERE php >nul 2>nul
    IF %ERRORLEVEL% NEQ 0 (
        echo  [ERROR] PHP not found locally or globally.
        echo  [INFO] Running auto-installer...
        powershell -ExecutionPolicy Bypass -File install_php.ps1
        if exist "php\php.exe" (
            set PHP_CMD=php\php.exe
        ) else (
            pause
            exit
        )
    ) else (
        set PHP_CMD=php
    )
)

echo  [INFO] Starting Server on http://localhost:8000
echo  [TIP]  Edit files in /pages to see changes instantly!
echo.
"%PHP_CMD%" -S localhost:8000
