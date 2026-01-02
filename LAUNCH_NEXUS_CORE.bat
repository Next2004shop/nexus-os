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
echo    Launching...
echo.

cd /d "d:\nexus-ai\nexus-desktop"
:: Using 'call' to ensure batch doesn't exit immediately and 'start' to detach
start "" npm start

timeout /t 3 >nul
exit
