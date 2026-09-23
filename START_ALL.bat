@echo off
title ComplyErg / Manak Setu — Full Stack Launcher
color 0A

echo.
echo  ============================================================
echo    ComplyErg ^| Manak Setu  ^|  Full Stack Launcher
echo  ============================================================
echo.
echo  Services:
echo   [1] Manak Setu Backend  (FastAPI)  ^-^> http://localhost:8000
echo   [2] ComplyErg Engine    (FastAPI)  ^-^> http://localhost:8001
echo   [3] React Frontend      (Vite)     ^-^> http://localhost:5173
echo.

REM ── 1. Manak Setu / ComplyErg Backend (port 8000) ───────────────
echo  [Starting] Backend API on port 8000...
start "Backend API :8000" cmd /k "cd /d %~dp0 && (if exist ocr_env\Scripts\activate.bat call ocr_env\Scripts\activate.bat) && python -m uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

REM ── 2. React frontend (port 5173) ────────────────────────────────────────
echo  [Starting] React Frontend on port 5173...
start "React Frontend :5173" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 5 /nobreak >nul

echo.
echo  ============================================================
echo   All services launched!
echo.
echo   React App   : http://localhost:5173
echo   Backend API : http://localhost:8000/docs
echo   Engine API  : http://localhost:8001/docs
echo.
echo   Demo Logins:
echo    Inspector    ^| inspector@manaksetu.gov.in ^| Inspector@123
echo    Supervisor   ^| supervisor@manaksetu.gov.in ^| Supervisor@123
echo    Admin        ^| admin@manaksetu.gov.in ^| Admin@123
echo  ============================================================
echo.

REM Open React app in browser after short delay
timeout /t 6 /nobreak >nul
start http://localhost:5173

pause
