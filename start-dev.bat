@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [1/6] Check runtime environment
call :require_cmd python "Python was not found in PATH. Please install Python first."
call :require_cmd pip "pip was not found in PATH. Please confirm your Python installation."
call :require_cmd node "Node.js was not found in PATH. Please install Node.js first."
call :require_cmd npm "npm was not found in PATH. Please install Node.js first."

echo [2/6] Prepare .env files
if not exist "backend\.env" if exist "backend\.env.example" (
    copy /Y "backend\.env.example" "backend\.env" >nul
    echo Created backend\.env
)
if not exist "frontend\.env" if exist "frontend\.env.example" (
    copy /Y "frontend\.env.example" "frontend\.env" >nul
    echo Created frontend\.env
)

echo [3/6] Install backend dependencies
python -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo Backend dependency installation failed.
    exit /b 1
)

echo [4/6] Install frontend dependencies
npm install --prefix frontend
if errorlevel 1 (
    echo Frontend dependency installation failed.
    exit /b 1
)

echo [5/6] Start backend and frontend
start "CodeLens Backend" cmd /k "cd /d ""%ROOT_DIR%backend"" && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "CodeLens Frontend" cmd /k "cd /d ""%ROOT_DIR%frontend"" && npm run dev -- --host 127.0.0.1 --port 5173"

echo [6/6] Open browser
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5173"

echo.
echo CodeLens local dev environment started.
echo - Backend: http://127.0.0.1:8000
echo - Frontend: http://127.0.0.1:5173
echo Close the launched cmd windows to stop the services.
exit /b 0

:require_cmd
where %~1 >nul 2>nul
if errorlevel 1 (
    echo %~2
    exit /b 1
)
goto :eof
