@echo off
echo ==========================================
echo      NXTradex-OS - DEPLOYMENT SCRIPT
echo ==========================================
echo.

echo [1/3] Building Application...
call npm run build
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Authenticating with Firebase...
echo A browser window will open. Please sign in to your Google account.
call npx firebase-tools login
if %errorlevel% neq 0 (
    echo Login failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Deploying to Firebase Hosting...
call npx firebase-tools deploy --only hosting
if %errorlevel% neq 0 (
    echo Deployment failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo      DEPLOYMENT SUCCESSFUL!
echo ==========================================
echo.
pause
