@echo off
title NEXUS CORE [SYSTEM LAUNCHER]
color 0f
cls
echo.
echo    N E X U S   C A P I T A L   W A R F A R E
echo    =========================================
echo    [SYSTEM] Initializing Core...
echo    [SYSTEM] Bypassing Packaging Protocols...
echo    [SYSTEM] Target: LOCALHOST RUNTIME
echo.
echo    [SYSTEM] Clearing Memory Banks...
taskkill /F /IM electron.exe >nul 2>&1
taskkill /F /IM "NEXUS Terminal.exe" >nul 2>&1
echo    [SYSTEM] Purging Corrupt Sectors (Cache Clean)...
rd /s /q "%APPDATA%\NEXUS Terminal" >nul 2>&1
rd /s /q "%APPDATA%\nexus-desktop" >nul 2>&1
echo.
echo    Launching...
echo.

cd /d "d:\nexus-ai\nexus-desktop"
:: Using 'call' to ensure batch doesn't exit immediately and 'start' to detach
start "" npm start

timeout /t 3 >nul
exit
