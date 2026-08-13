# Render 클라우드 배포 가이드 (백엔드 24시간 상시 가동)

> 웹 브라우저(파이어베이스 사이트)는 보안상 사용자 PC의 로컬 서버를 직접 켤 수 없습니다.
> 대신 **백엔드(API + 크롤러 + DB)를 Render 클라우드에 배포**하면 PC 전원과 무관하게
> 24시간 서버가 가동되어, 웹사이트를 열면 항상 최신 데이터가 표시됩니다.

---

## 1. 배포 후 아키텍처

```
[사용자 브라우저]
      │  https://youtrend-9aa13.firebaseapp.com/ranking
      ▼
[Firebase Hosting]  ── (정적 Next.js 프론트엔드, 이미 배포됨)
      │  https://youtube-intel-backend.onrender.com/api
      ▼
[Render: youtube-intel-backend (Web)]
      │  FastAPI + Alembic + Seed
      ▼
[Render PostgreSQL: youtube-intel-db]
      ▲
[Render: youtube-intel-crawler (Worker)]
      5분 주기 크롤러 + 랭킹 엔진 (상시 구동)
```

---

## 2. 사전 준비

| 항목 | 설명 |
|------|------|
| GitHub 저장소 | 프로젝트를 GitHub에 푸시 (Render Blueprint 연동) |
| Render 계정 | https://render.com 회원가입 |
| `YOUTUBE_API_KEY` | Google Cloud Console에서 발급한 YouTube Data API v3 키 |

> ⚠️ `.env`, `youtube.db`, `cloudflared.exe`, `tunnel_url.json`은 Git에 커밋하지 마세요.
> 이미 `.gitignore`에 등록되어 있습니다.

---

## 3. Render 배포 절차 (Blueprint)

### 3.1. GitHub에 프로젝트 푸시
```powershell
git add -A
git commit -m "feat: add render cloud deployment support"
git push origin master
```

### 3.2. Blueprint로 배포
1. Render 대시보드 → **New** → **Blueprint** 선택
2. GitHub 저장소 연결 후 `render.yaml` 선택
3. 배포 대상 확인 → **Apply**

자동으로 아래 리소스가 생성됩니다:
- `youtube-intel-backend` (Web) — FastAPI API 서버
- `youtube-intel-crawler` (Worker) — 5분 주기 크롤러/랭킹
- `youtube-intel-db` (PostgreSQL) — 데이터베이스

### 3.3. 환경변수 설정
배포 후 각 서비스의 **Environment** 탭에서 설정합니다.

| 키 | 필수 | 값 |
|----|------|-----|
| `YOUTUBE_API_KEY` | ✅ | 발급받은 YouTube Data API v3 키 |
| `DATABASE_URL` | 자동 | Render가 자동 주입 (PostgreSQL 연결 문자열) |
| `AI_PROVIDER` | 자동 | `disabled` (클라우드에서는 LM Studio를 못 쓰므로 fallback 분석 사용) |

> `YOUTUBE_API_KEY`는 `sync: false`로 설정되어 Blueprint 배포 시 자동으로 채워지지 않습니다.
> 대시보드에서 직접 입력 후 **Deploy**를 눌러주세요.

### 3.4. 서버 URL 확인
배포가 완료되면 Web 서비스의 URL(예: `https://youtube-intel-backend.onrender.com`)을 복사합니다.
- 헬스체크: `https://youtube-intel-backend.onrender.com/` → `{"status": "healthy", ...}`
- API 문서: `https://youtube-intel-backend.onrender.com/docs`

---

## 4. 프론트엔드(Firebase) 재배포 — Render URL 연결

기존 프론트엔드는 로컬 서버 + Cloudflare 터널을 바라보고 있으므로,
Render URL을 가리키도록 **재빌드 + 재배포**해야 합니다.

```powershell
# 1) 프로젝트 루트에서
cd frontend

# 2) Render 백엔드 URL로 환경변수 설정 (기존 .env.production 내용 교체)
#    frontend/.env.production
#    NEXT_PUBLIC_API_URL=https://youtube-intel-backend.onrender.com/api

# 3) 정적 빌드 (Next.js export)
npm run build

# 4) Firebase 배포 (프로젝트 루트에서)
cd ..
npx firebase deploy --only hosting
```

> 💡 `frontend/src/lib/api.ts`의 `getApiBaseUrl()`은 localStorage → 환경변수 → localhost 순서로
> API URL을 결정합니다. 배포된 사이트에서도 기존에 저장된 터널 URL(localStorage)이 우선이라면
> **설정 페이지(또는 배너)에서 API 주소를 Render URL로 변경**하거나, 브라우저에서 사이트 데이터를
> 삭제하면 새 빌드 환경변수가 적용됩니다.

### 배포 확인
1. https://youtrend-9aa13.firebaseapp.com/ranking 접속
2. 랭킹 데이터가 표시되면 성공
3. 상단 API 연결 배너에 경고가 뜨면 → 설정 페이지에서 Render API URL 입력

---

## 5. 무료 플랜 제약 및 주의사항 ⚠️

Render 무료 티어에는 아래 제약이 있습니다.

| 제약 | 설명 | 대응 |
|------|------|------|
| **Web 서비스 sleep** | 15분간 요청이 없으면 자동 sleep | 첫 접속 시 1~2분 재시작 대기 필요. 유료(Starter $7/월) 전환 시 해결 |
| **Worker 무료 시간** | 월 750시간 (항상 구동 가능) | 크롤러 스케줄러는 무료로 상시 가동 가능 |
| **PostgreSQL 무료** | 1GB 용량, **30일 후 자동 삭제** | 유료 플랜으로 전환하거나, 30일 후 새 DB 생성 후 재배포 |
| **빌드 시간** | 무료 플랜은 1개월 500분 한도 | 자주 재배포하지 않도록 주의 |

> 📌 **데이터 영속화가 중요하면** PostgreSQL을 유료 플랜(Pro, $7/월)으로 업그레이드하는 것을 권장합니다.
> 무료 DB가 만료되어 삭제되면 랭킹/수집 데이터가 초기화됩니다.

---

## 6. 트러블슈팅

### 6.1. 배포 후 API가 503 또는 응답 없음
- Render 로그(`Dashboard → backend → Logs`)에서 `alembic upgrade head` 오류 여부 확인
- 대부분 첫 배포 시 `YOUTUBE_API_KEY`가 설정 안 된 상태에서 크롤러가 시작되어 발생합니다.
  → 환경변수 설정 후 **Manual Deploy → Deploy latest commit** 실행

### 6.2. Playwright 설치 실패로 빌드 실패
- `render.yaml`의 빌드 명령에 `|| true`가 있어 chromium 설치 실패는 빌드를 막지 않습니다.
- chromium이 없으면 YouTube API 키가 있을 때 정상 동작합니다 (API 전용 모드).
- `crawler/collector.py`는 API/Playwright 중 하나만 있어도 graceful하게 동작하도록 수정되어 있습니다.

### 6.3. YouTube API Quota 초과 시
- `crawler/collector.py`가 자동으로 Playwright(헤드리스 크롬) 폴백을 시도합니다.
- Playwright도 설치되어 있지 않으면 해당 국가 수집을 건너뜁니다 (다음 주기에 재시도).

### 6.4. AI 분석이 fallback 텍스트로 표시됨
- Render에서는 로컬 LM Studio에 접근할 수 없으므로 `AI_PROVIDER=disabled`로 설정되어 있으며,
  `services/ai_service.py`가 사전 정의된 fallback 분석을 저장합니다. 정상 동작입니다.

### 6.5. 기존 로컬 데이터(sqlite)를 클라우드로 옮기고 싶다면
- Render PostgreSQL은 빈 DB로 시작합니다. 첫 크롤러 실행 시 데이터가 자동으로 쌓입니다.
- 기존 `youtube.db`의 데이터를 이전하려면 DB 덤프/복원 툴(pgloader 등)을 사용하세요.
