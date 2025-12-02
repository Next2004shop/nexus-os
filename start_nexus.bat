@echo off
echo Starting Nexus AI System...

:: Set PATH for this session
set PATH=%PATH%;C:\Program Files\nodejs;C:\Users\user\AppData\Local\Programs\Python\Python311;C:\Users\user\AppData\Local\Programs\Python\Python311\Scripts

:: Start Python Bridge (Backend)
start "Nexus Bridge (Python)" cmd /k ""C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" nexus_bridge.py"

:: Wait for Python to initialize
timeout /t 5

:: Start Node.js Server (Frontend Host)
echo Starting Node.js Host...
"C:\Program Files\nodejs\npm.cmd" run dev
