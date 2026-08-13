@echo off
chcp 65001 >nul
title YouTube Global Intelligence Platform - Launcher
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   YouTube Global Intelligence Platform - One-Click Run  ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: 작업 디렉토리를 이 배치파일이 있는 폴더로 확실하게 고정합니다.
cd /d "%~dp0"

echo [1/5] DB 마이그레이션 및 국가 시딩...
call .venv\Scripts\python -m alembic upgrade head 2>nul
call .venv\Scripts\python database/seed.py
echo.

echo [2/5] FastAPI 백엔드 서버 시작 (포트 8000)...
start "YT-Backend" /d "%~dp0" cmd /k ".venv\Scripts\python backend/main.py"
timeout /t 5 /nobreak >nul

echo [3/5] Cloudflare 터널 시작 및 URL 자동 감지...
:: 파워쉘 보안 정책 및 경로 인코딩 충돌을 회피하기 위해 파이썬 터널 런처를 실행합니다.
start "YT-Tunnel" /d "%~dp0" cmd /k ".venv\Scripts\python scripts/start_tunnel.py"
echo [Tunnel] 터널 URL을 감지하고 .env.production을 업데이트할 때까지 대기합니다 (15초)...
timeout /t 15 /nobreak >nul

echo [4/5] 크롤러 + 랭킹 엔진 스케줄러 시작 (5분 주기)...
start "YT-Crawler" /d "%~dp0" cmd /k ".venv\Scripts\python scheduler/tasks.py"
timeout /t 2 /nobreak >nul

echo [5/5] Next.js 프론트엔드 대시보드 시작 (포트 3000)...
start "YT-Frontend" /d "%~dp0" cmd /k "cd frontend && npm run dev"
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
