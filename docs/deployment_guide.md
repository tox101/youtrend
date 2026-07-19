# YouTube Global Intelligence Platform - Deployment & Operations Guide

본 가이드는 **YouTube Global Intelligence Platform**의 안정적인 배포와 중단 없는 수집·연산 서비스 운영을 위한 매뉴얼입니다.

---

## 1. 아키텍처 및 구동 개요

플랫폼은 총 5개의 핵심 마이크로서비스로 분할되어 컨테이너 격리 배포됩니다.

1. **`db` (PostgreSQL 15)**: 실시간 수집된 영상, 채널 메타, 랭킹 차트 정보, AI 요약 리포트를 영구 저장합니다.
2. **`redis` (Redis 7)**: 인메모리 임시 캐시 및 분산 데이터베이스 입출력 부하를 완화합니다.
3. **`backend` (FastAPI)**: Clean Architecture 및 Repository Pattern 기반의 데이터 쿼리 API 서버를 가동하며 OpenAPI/Swagger 문서를 자동 생성합니다.
4. **`crawler-scheduler` (Playwright & Daemon)**: 5분마다 깨어나 유튜브 공식 API 또는 Playwright 헤드리스 크롬 브라우저를 토글하여 8개국 인기 영상을 수집하고 랭킹을 동적 연산하는 백그라운드 워커입니다.
5. **`frontend` (Next.js & React)**: Recharts 분석 차트와 다이나믹 Framer Motion 애니메이션이 장착된 미려한 다크 모드 대시보드를 제공합니다.

---

## 2. 프로덕션 환경설정 (.env)

배포 전 프로젝트 루트 디렉토리에 `.env` 파일을 복사하여 실물 비밀 키와 주소를 튜닝해야 합니다.

```bash
# 환경 설정 (development / production)
ENV=production

# 데이터베이스 접속 정보 (PostgreSQL)
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_NAME=youtube_global_intel

# Redis 접속 정보
REDIS_HOST=redis
REDIS_PORT=6379

# 유튜브 Data API 키 (일일 Quota 제한 대비를 위해 실제 작동 키 사용)
YOUTUBE_API_KEY=AIzaSyAW0xpYfW8DW0iofaD3lNwkTbLO-gb3gHs

# 인공지능 요약 모델 및 LM Studio 서버 (Qwen AgentWorld 35B)
AI_PROVIDER=lm_studio
LM_STUDIO_API_BASE=http://host.docker.internal:1234/v1
AI_MODEL_NAME=Qwen AgentWorld 35B A3B UD
```

> [!IMPORTANT]
> 로컬 호스트 컴퓨터(Windows)에서 실행 중인 LM Studio에 도커 컨테이너 내부에서 접속하려면 호스트 내부 브릿지 IP인 `http://host.docker.internal:1234/v1` 로 설정하는 것이 호환성 및 네트워크 라우팅 관점에서 가장 안정적입니다.

---

## 3. Docker Compose 기동 매뉴얼

프로젝트 루트 폴더(docker-compose.yml이 위치한 곳)에서 아래 명령어를 순차 가동합니다.

### 3.1. 최초 가동 및 빌드
```powershell
# 컨테이너 일괄 빌드 및 백그라운드 데몬 구동
docker-compose up --build -d
```

### 3.2. 데이터베이스 스키마 초기화 및 마이그레이션
최초 구동 시 백엔드 컨테이너 내부로 진입하여 Alembic 데이터베이스 마이그레이션과 시드 처리를 마쳐야 정상 작동합니다:
```powershell
# 백엔드 컨테이너 내 쉘 진입
docker-compose exec backend ash

# 스키마 최신 버전 업데이트
alembic upgrade head

# 8개 수집 대상국 정보 시딩
python database/seed.py
```

### 3.3. 서비스 상태 및 모니터링
```powershell
# 서비스 작동 여부 및 포트 바인딩 확인
docker-compose ps

# 수집 데몬 또는 백엔드 로그 실시간 트래킹
docker-compose logs -f crawler-scheduler
```

---

## 4. 운영 및 트러블슈팅 (Troubleshooting)

### 4.1. 유튜브 API Quota(할당량) 초과 시 조치
- **증상**: `crawler-scheduler` 컨테이너 로그에 `YouTube API Quota exceeded` 경고가 출력됨.
- **자동 대응**: 플랫폼은 할당량 한도 고갈을 감지하면 즉시 **Playwright Fallback 스크래퍼**로 자동 전환하여 헤드리스 크롬으로 유튜브 급상승 탭을 긁어옵니다. 서비스는 온전히 유지됩니다.
- **추천 조치**: 장기적인 안정성과 정밀 채널 세부 데이터(구독자 증감 등) 확보를 위해 Google Developer Console에서 추가 API Key를 발급받아 교대하는 것을 권장합니다.

### 4.2. LM Studio Qwen 모델 끊김 장애 대처
- **증상**: 비디오 분석 요청 시 타임아웃 에러 또는 연결 끊김 발생.
- **자동 대응**: `ai_service.py` 내부의 Fail-Safe 메커니즘이 작동하여, 시스템이 크러시되지 않고 사전에 정의된 모크 보고서를 캐시에 강제 적재하여 프론트엔드가 즉시 렌더링되게 방어합니다.
- **조치 방안**:
  1. LM Studio가 포트 `1234`에서 정상적으로 로컬 대기열을 띄워 서비스 중인지 확인합니다.
  2. Qwen 모델이 활성화(Loaded) 되어 있는지 인스턴스 메모리를 검사합니다.

### 4.3. 랭킹 스코어(Virality Score) 가중치 미세 조정 (Fine-Tuning)
영상의 인기 척도 변화를 반영하고 싶다면, `ranking/engine.py` 클래스 내부의 가중치 변수를 소스 수정 후 배포하면 즉시 반영됩니다:
- `w_velocity` (조회수 가속 가중치, 기본값 `0.4`): 단기 폭발성이 큰 비디오가 상위에 오르게 하려면 높입니다.
- `w_like` (좋아요율, 기본값 `0.25`): 대중의 정성적 호감도를 우선 반영합니다.
- `w_comment` (댓글율, 기본값 `0.15`): 시청자의 직접적인 소통 참여도를 우선 반영합니다.
- `w_sub_ratio` (구독자 대비 조회 폭발력, 기본값 `0.2`): Hidden Gem 발굴 감도를 높이고 싶다면 해당 가중치를 증가시킵니다.
- **경과 시간 페널티 (Gravity Coefficient, 기본값 `1.5`)**: 시간이 흐른 영상이 너무 빨리 차트아웃된다면 계수를 `1.2`~`1.3` 선으로 낮춰 완만한 감쇄를 유도합니다.
