@echo off
echo Starting Nexus AI System...

:: Set PATH for this session
set PATH=%PATH%;C:\Program Files\nodejs;C:\Users\user\AppData\Local\Programs\Python\Python311;C:\Users\user\AppData\Local\Programs\Python\Python311\Scripts

:: Start Python Bridge (Backend)
start "Nexus Bridge (Python)" cmd /k ""C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" nexus_bridge.py"

:: Wait for Python to initialize
timeout /t 5

:: Start Node.js Backend Server (API Host)
echo Starting Node.js Backend...
start "Nexus Host (Node)" cmd /k "node server.cjs"

:: Wait for Backend to initialize
timeout /t 5

:: Start React/Vite (Frontend)
echo Starting React Frontend...
"C:\Program Files\nodejs\npm.cmd" run dev
