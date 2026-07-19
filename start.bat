@echo off
chcp 65001 >nul
title YouTube Global Intelligence Platform - Launcher
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   YouTube Global Intelligence Platform - One-Click Run  ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/4] DB 마이그레이션 및 국가 시딩...
call .venv\Scripts\python -m alembic upgrade head 2>nul
call .venv\Scripts\python database/seed.py
echo.

echo [2/4] FastAPI 백엔드 서버 시작 (포트 8000)...
start "YT-Backend" cmd /k ".venv\Scripts\python backend/main.py"
timeout /t 3 /nobreak >nul

echo [3/4] 크롤러 + 랭킹 엔진 스케줄러 시작 (5분 주기)...
start "YT-Crawler" cmd /k ".venv\Scripts\python scheduler/tasks.py"
timeout /t 2 /nobreak >nul

echo [4/4] Next.js 프론트엔드 대시보드 시작 (포트 3000)...
start "YT-Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo  ============================================================
echo   모든 서비스가 가동되었습니다!
echo.
echo   Dashboard:  http://localhost:3000
echo   API Docs:   http://localhost:8000/docs
echo  ============================================================
echo.
echo   종료하려면 열린 터미널 창들을 각각 닫아주세요.
echo.
pause
