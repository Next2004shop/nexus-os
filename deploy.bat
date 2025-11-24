@echo off
echo [1/3] Building Application...
set NODE_OPTIONS=--max_old_space_size=4096
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
echo [4/4] Pushing to GitHub (Triggers Render/Vercel/Netlify)...
git add .
git commit -m "Deploy: Real-World Upgrade & Login Fixes"
git push origin main
if %errorlevel% neq 0 (
    echo Git Push failed! (You might need to set up git remote)
    echo Continuing...
)

echo.
echo ==========================================
echo      DEPLOYMENT SUCCESSFUL!
echo ==========================================
echo.
pause
