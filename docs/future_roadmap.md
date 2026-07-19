# YouTube Global Intelligence Platform - Future Roadmap & Tech Opinions

유튜브 트렌드 분석과 데이터 엔지니어링, AI 인프라 부문에서 최근 두각을 나타내는 기술적 트렌드와 본 플랫폼을 엔터프라이즈 레벨로 확장하기 위해 추가하면 좋을 **시니어 엔지니어 관점의 6대 핵심 추천 시스템/기능**입니다.

---

## 1. Data Engineering: Celery 분산 큐 및 TimescaleDB 시계열 최적화

현재 구축된 APScheduler 기반의 스케줄러 루프는 구조가 직관적이나, 채널 및 영상 수가 누적될수록 병목(Bottleneck)이 발생하기 쉽습니다.

* **Celery & Redis Worker로의 완전 디커플링**:
  * **수집(Crawler Task)**, **연산(Ranking Task)**, **AI 분석(AI Worker Task)**을 각각 독립된 프로세스로 분산 가동합니다.
  * 크롤링 속도가 느려져도 랭킹 계산기나 API 서버가 전혀 대기(Block)하지 않고 각자의 속도로 분산 큐를 처리합니다.
* **시계열 데이터베이스(TimescaleDB) 도입**:
  * 5분마다 생성되는 `ranking_history`와 조회수 이력은 단시간 내에 수백만~수천만 건의 로우(Row)를 만듭니다.
  * PostgreSQL 위에 **TimescaleDB Extension**을 얹어 시계열 파티셔닝(Hypertables) 및 자동 압축(Compression) 정책을 적용하면, 한 달이 지난 시계열 이력을 검색할 때도 인덱스 타지 않는 속도 저하 현상을 완벽하게 방지할 수 있습니다.

---

## 2. AI Engineering: 로컬 멀티모달(Llama-Vision) 연동 및 Vector Search

단순 텍스트(제목, 설명) 분석을 넘어, 시각적 요소가 지배하는 유튜브 생태계의 트렌드를 직접 파싱하는 것이 최근의 강력한 트렌드입니다.

* **로컬 멀티모달 LLM을 활용한 썸네일 진단**:
  * **Ollama/LM Studio**의 Vision 지원 모델(예: `Llama-3.2-Vision-11B` 또는 `Qwen2.5-VL`)을 연동합니다.
  * 썸네일 이미지 파일을 로컬 AI에 전달하여 **"클릭 유도성(Clickbait) 레이아웃 여부, 폰트 가독성, 색상 대비, 중심 피사체의 감정 상태"**를 종합적으로 진단합니다.
* **유사 의미 검색을 위한 Vector Embedding & OpenSearch**:
  * 비디오 제목과 설명글을 `bge-m3` 등 경량 임베딩 모델을 활용해 벡터화하여 데이터베이스에 함께 적재합니다.
  * 프론트엔드 검색란에 키워드가 정확히 일치하지 않더라도, 시청자의 의도(Intent)에 맞는 유사 동영상을 추천하는 **시맨틱 검색(Semantic Search)**을 서빙합니다.

---

## 3. Machine Learning: XGBoost 기반 24시간 조회수 예측 엔진

현재 모크 덤프로 반환되는 24시간 예측 수치를 데이터 기반의 예측 모델로 실체화합니다.

* **시계열 특징 피처(Feature) 추출**:
  * 영상의 초기 3시간 조회수 가속도($\Delta V_3$), 구독자 대비 초기 조회수 비율, 카테고리 정보, 시간대 정보를 특징값으로 추출합니다.
* **경량 예측 모델(XGBoost / LightGBM) 서빙**:
  * FastAPI 백엔드 내에 학습된 모델(`.bin` 또는 `.onnx` 파일)을 내장하거나 로드하여, 수집된 초기 트래픽 데이터 피드백을 통해 24시간 뒤에 도달할 **예상 누적 조회수**와 **예측 신뢰도(Confidence Score)**를 정량적으로 계산해 프론트엔드에 차트와 함께 출력합니다.

---

## 4. DevOps & MLOps: 로컬 모델 로드 밸런싱 및 API 서빙 이중화

* **vLLM을 통한 고속 동시성 추론**:
  * LM Studio는 개발 및 단일 추론용으로 탁월하지만 다중 동시 요청 시 대기열 병목이 생깁니다.
  * GPU 자원이 허용된다면 추론 프레임워크를 **vLLM**으로 교체하여 연속 배치(Continuous Batching) 및 vLLM API 이중화를 지원함으로써 실시간 AI 처리 속도를 5~10배 이상 끌어올릴 수 있습니다.
* **Playwright 프록시 풀(Proxy Pool) 연동**:
  * 8개국 데이터를 5분마다 Playwright로 크롤링할 때, 단일 IP 대역은 유튜브(Google) 방화벽의 DDoS 차단 필터에 걸려 Captcha 요구를 받거나 IP 차단을 당하기 쉽습니다.
  * 해외 프록시 제공업체(Proxy Pool)를 연동하여 Playwright가 요청 시마다 무작위 국가 IP로 우회하여 안정적으로 크롤링하도록 보호망을 구축합니다.

---

## 5. UI/UX & Product: 외부 채널 알림 연동 (Discord / Telegram Bot)

플랫폼 내부 대시보드를 켜놓지 않고도 마케터나 분석가가 즉각 트렌드를 감치하도록 아웃바운드 푸시를 연동합니다.

* **Discord/Slack Webhook 자동 발송**:
  * `ranking/engine.py`에서 Virality Score가 95점 이상이거나 획기적인 Hidden Gem 비디오를 실시간 발견했을 때, 해당 비디오의 제목, 썸네일, 예상 흥행 요인(AI Summary)을 구조화하여 즉시 운영 Discord 채널 또는 Telegram 단체방으로 큐레이팅 카드를 자동 쏘아 보내는 모듈을 추가합니다.

---

## 6. Business Value: 국가 간 문화 차이(Country Diff Semantic Grid) 분석

현재 구축한 Country Diff(단일 영상의 다국가 순위 매핑)에서 더 나아가, 특정 메가 트렌드가 국가 경계를 넘어 전파되는 양상을 AI가 추적하게 만듭니다.

* **트렌드 전파 타임라인**:
  * 예를 들어, 미국(US)에서 Virality 98을 기록한 숏츠 콘텐츠가 3일 뒤 일본(JP)과 대한민국(KR) 차트에 각각 진입하는 전파 시차(Propagation Delay)를 시각화하고, 국가 간 문화적 선호도 및 밈(Meme)의 한글화 번역 특징을 분석하는 AI 브리핑 뷰를 제공합니다.
