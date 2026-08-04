# Local Meeting Notes — Day 1 추론 게이트

## 답하려는 질문

GPU가 없는 i5-8400·11 GiB 환경에서 실제 회의 음성을 로컬 Whisper와
A6API LLM으로 처리해, 포트폴리오의 핵심 경험을 녹음당 60초 안에
재현할 수 있는가?

## 고정한 핵심 경험

1. 20–34초 회의 녹음 입력
2. Whisper가 시간 정보가 붙은 음성 기록을 만든다
3. A6API `claude-sonnet-5`가 결정과 할 일을 항목별로 정리한다
4. 서버가 모든 근거 구간 ID를 검증
5. 결과 항목에서 해당 오디오 구간으로 이동 가능

Day 1에서 1–4번의 기술 리스크를 먼저 검증했고, 한국어 게이트 통과 후
웹 UI와 재생 위치 이동을 MVP 범위에 포함했다.

## 실행

`.env.example`을 `.env`로 복사해 A6API 키를 로컬에서만 입력한다.

### 웹 MVP

실행:

```sh
docker compose up --build web
```

브라우저에서 `http://localhost:8000`을 연다. 공개 한국어 샘플을 누르거나
20MB·2분 이하 오디오를 끌어놓으면 매번 실제 Whisper와 A6API 추론을
실행한다.

웹의 월간 비용은 `budget-data` Docker volume의 SQLite 장부에 누적된다.
요청 전 `$0.01`의 안전 여유분을 확인하므로 월 누적 비용이 `.env`의
`A6_RUN_BUDGET_USD`를 넘기 전에 HTTP 429로 차단된다. 컨테이너를 재시작하거나
일반 `docker compose down` 후 다시 실행해도 장부는 유지된다.

백그라운드 실행과 상태 확인:

```sh
docker compose up -d --build web
docker compose ps web
docker compose logs -f web
```

종료:

```sh
docker compose down
```

월간 예산 제한만 다시 검사:

```sh
docker compose run --rm -v ./tests:/tests:ro --entrypoint python web \
  -m unittest discover -s /tests -v
```

가장 짧은 확인 순서는 다음과 같다.

1. `법안 통과 후속 작업` 샘플을 누른다.
2. 처리 완료 후 결정과 할 일이 모두 나오는지 확인한다.
3. `근거 듣기`를 눌러 오디오 위치와 해당 음성 기록 강조가 함께 이동하는지 확인한다.
4. 자신의 WAV 또는 M4A 파일을 올려 같은 흐름을 확인한다.

### Cloud Run

배포 이미지는 `faster-whisper/small` 모델과 공개 한국어 데모 2개를 포함하고,
Cloud Run의 `PORT`에서 웹 서버를 시작한다. 배포 기본값은 서울 리전,
요청 기반 과금, `2 vCPU / 4 GiB`, 최소 인스턴스 0, 최대 인스턴스 1,
동시 처리 1, 요청 제한 180초다. 공개 인스턴스는 2분 이하 오디오와
인스턴스당 분석 50회로 제한한다.

Cloud Run 파일시스템은 영구 저장소가 아니므로 웹 화면에서 로컬 SQLite 값을
월간 영구 잔액처럼 표시하지 않는다. A6API 비용의 최종 상한은 A6 토큰에
설정한 할당량이 담당하고, Cloud Run의 최대 인스턴스 1은 컴퓨트 비용의 동시
증폭을 제한한다.

#### Cloud Run 최초 설정

아래 명령의 `ACCOUNT_EMAIL`과 `PROJECT_ID`는 AI Pro 혜택을 가진 Google 계정과
그 계정의 Cloud 프로젝트로 바꾼다.

```sh
gcloud auth login ACCOUNT_EMAIL
gcloud config set project PROJECT_ID
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

gcloud secrets create minutemark-a6-api-key \
  --replication-policy=automatic
set -a
. ./.env
set +a
printf %s "$A6_API_KEY" | \
  gcloud secrets versions add minutemark-a6-api-key --data-file=-
unset A6_API_KEY

PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID \
  --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding minutemark-a6-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role=roles/secretmanager.secretAccessor
```

배포:

```sh
./cloudrun-deploy.sh PROJECT_ID
```

배포 상태와 로그:

```sh
gcloud run services describe minutemark \
  --region asia-northeast3 \
  --format='value(status.url,status.latestReadyRevisionName)'
gcloud run services logs read minutemark \
  --region asia-northeast3 \
  --limit 50
```

일상 배포는 GitHub `main`과 연결된 Cloud Build 트리거
`minutemark-main-deploy`가 담당한다. Docker 빌드와 회귀 테스트가 통과한
커밋만 Cloud Run에 배포하며, `/api/health`의 `commit` 값으로 GitHub
`main`과 같은 버전인지 확인한다. `cloudrun-deploy.sh`는 최초 설정이나
자동 배포 복구용으로만 사용한다.

새 버전이 실패하면 Cloud Run 콘솔의 `Revisions`에서 이전 정상 revision(배포 버전)으로
트래픽을 되돌린다. 즉시 공개를 중단하려면 다음 명령으로 비인증 접근을 제거한다.

```sh
gcloud run services remove-iam-policy-binding minutemark \
  --region asia-northeast3 \
  --member=allUsers \
  --role=roles/run.invoker
```

#### 2026-07-31 Cloud Run 릴리스 후보

- 배포 후보 이미지: `sha256:5a6254349f491356b6d1192c96b76d6d397ff1096f7baed005d55cde78683d36`
- 이미지 크기: `634,895,839 bytes`
- Whisper `small` 모델과 한국어 공개 샘플 2개 이미지 포함 PASS
- 모델이 외부 다운로드 없이 `/models/whisper`에서 로드됨 PASS
- Cloud Run 기본 진입점, `/`, `/api/health`, `/api/samples` PASS
- 예산·오디오·근거 ID 정규화·인스턴스 보호선 테스트 6개 PASS
- 실제 공개 한국어 샘플 전체 흐름: 32.27초, 할 일 1개, 근거 검증 PASS,
  예상 A6API 비용 `$0.00017714`
- A6가 근거 ID 배열 대신 `"S5, S6"` 문자열을 반환한 실제 실패를 발견했고,
  서버 정규화 후 실제 구간 존재 검증을 다시 거치도록 수정함
- `RELEASE_CANDIDATE`: PASS
- `PRODUCTION`: BLOCKED — 활성 `gcloud` 계정이 없음. 로컬 설정에는
  `stitch-project-494107`만 남아 있으나 AI Pro 혜택 계정 소유 프로젝트인지
  확인되지 않아 임의로 배포하지 않음

#### 2026-07-31 Cloud Run 프로덕션

- Google Cloud 계정: 프로젝트 소유자 계정
- 프로젝트: `minutemark-portfolio` (`89192290289`)
- 결제 계정: `012A36-ED8E42-7CFE04`, 활성 상태
- 서비스: `minutemark`, 리전 `asia-northeast3`
- 공개 URL: `https://minutemark-2u3l25uhba-du.a.run.app`
- 배포 revision(버전): `minutemark-00004-65g`, 트래픽 100%
- 이미지 digest:
  `sha256:c2fe6d8629b0928783885f4b44274ca7a65faf3ec7068c90856f947e3b48dfa5`
- Cloud Build:
  `be35b41d-f99b-4636-8868-b5271cf115a9`, SUCCESS
- Secret Manager: `minutemark-a6-api-key` 버전 1, 런타임 서비스 계정에만
  Secret Accessor 부여
- 외부 `/`, `/api/health`, `/api/samples` HTTP 200
- 실제 한국어 샘플: 외부 경로 38.23초, 서버 처리 40.66초, 할 일 1개,
  근거 검증 PASS, 예상 A6API 비용 `$0.00015881`
- 첫 revision에서 A6 경로의 일시적 502 한 건 발생 후 같은 요청이 200으로
  성공함. revision 2에 네트워크·5xx 1회 재시도와 서버측 예외 로그를 추가함
- revision 2에서 A6 스마트 라우터가 선택한 일부 판매자가
  `response_format=json_schema`를 HTTP 400으로 거부하는 실제 실패를 확인함
- revision 3은 해당 400에 한해 일반 JSON 요청으로 한 번 다시 요청하고, 반환 구조와
  근거 구간을 서버에서 다시 검증함. Docker 회귀 테스트 9개 PASS
- revision 3 공개 검증에서 실제 재요청 로그 확인 후 AI POST HTTP 200,
  서버 처리 44.25초, 할 일 1개, 근거 검증 PASS, 예상 A6API 비용
  `$0.00006705`
- 복구 revision: `minutemark-00003-gg8`
- `PRODUCTION` 런타임 게이트: PASS
- Google Cloud 프로젝트 전용 월 `₩1,000` 예산
  `c40f522a-a5f6-439f-bc24-5c598100d835` 생성. 현재 지출 50%·90%·100%에서
  프로젝트 결제 관리자에게 알림
- Cloud Run 서비스 수준 최대 인스턴스 `1`, 동시 처리 `1` 재확인
- Windows Chrome 1440×900 데스크톱 PASS
- Windows Chrome 공개 샘플 2개 실제 분석과 `근거 듣기` PASS. 서버 로그에서
  `/api/analyze-sample/action`과 `/api/analyze-sample/decision` 모두 HTTP 200
- 좁은 화면 390×844 랜딩은 격리 headless Chrome 대체 경로에서 PASS
- Windows Chrome에서 `minutemark-upload-test.wav` 실제 업로드 PASS:
  34.90초, 음성 기록 13구간, 결정 1개, 근거 S1 이동 0.40초,
  예상 A6API 비용 `$0.00010985`
- revision 4는 `av.error.InvalidDataError`만 안전한 422 한국어 메시지로 변환함.
  Docker 독립 빌드와 전체 회귀 테스트 10개 PASS
- Windows Chrome에서 잘못된 WAV와 재시도 1회 모두
  `오디오 파일을 읽을 수 없습니다. 올바른 오디오 파일인지 확인해 주세요.`만 표시
- `Errno`, `/tmp`, `Invalid data`, 스택, 비밀, 토큰, 내부 경로 없음.
  브라우저 콘솔 warn/error 없음
- Cloud Run 요청 로그에서 `/api/analyze` HTTP 422 두 건 확인.
  새 revision의 severity ERROR 로그 없음
- 프로젝트 소유 A6API 계정의 토큰 `local-meeting-notes-mvp` 총한도를
  `$1.00`으로 설정하고 남은 할당량 `$0.99`를 재확인
- 브라우저 전체 게이트: PASS

### CLI 추론 게이트

공개 AMI 회의 샘플 10개를 준비하려면:

```sh
docker compose run --rm sample-downloader
```

`samples/`에 오디오가 2개 이상 있으면 아래 명령으로 전부 처리한다.

```sh
./run.sh
```

첫 실행은 Docker 이미지와 Whisper 모델을 내려받으므로 warm 성능 판정에서 제외한다.
두 번째 실행의 `output/*.json`과 터미널 요약으로 판정한다.

## Kill gate

- 최종 녹음: 서로 다른 자연스러운 한국어 회의 음성 2개, 각 20–30초
- warm 전체 처리 시간: 녹음당 60초 이하
- 음성 인식: 미리 적은 핵심 사실 5개 중 4개 이상 보존
- 구조: `decisions`, `action_items` 배열 생성
- 근거: 모든 `segment_ids`가 실제 음성 기록 구간에 존재
- 유용성: 녹음마다 정확한 결정 또는 할 일 1개 이상
- 비용: 선택한 A6 가격 기준 실행 비용을 기록하고 월 상한 $1 이하

하나라도 실패하면 NO-GO다. 합성 음성, 고정 응답, 미리 계산한 결과로 통과시키지 않는다.

## 2026-07-30 중간 결과

- Docker Engine 29.3.0 및 Compose 5.1.0 확인
- `faster-whisper` 1.2.1 이미지 빌드 성공
- Whisper `small` CPU INT8 모델 로드 성공
- Ollama `qwen2.5:1.5b` 로컬 모델 등록 성공
- Qwen warm 결과 정리 추론: 6.32초
- 연기된 품질 문제:
  - 두 개의 필수 결과 배열을 모델이 직접 채울 때 같은 문장을 중복 분류함
  - 단일 `items` 배열에서 `decision | action_item`을 고르게 하고 서버가 나누자 해결됨
  - JSON Schema의 `enum`으로 실제 구간 ID만 생성하도록 제한함
- 아직 판정하지 못한 항목:
  - 실제 한국어 음성 인식 정확도
  - 녹음당 warm 전체 처리 시간
  - 실제 음성 기록을 바탕으로 한 결정·할 일의 의미 정확도

이 단계의 상태는 **입력 대기**였다. 이후 공개 라이선스의 자연스러운 한국어
실제 말이 담긴 샘플 2개를 확보해 합성 음성 없이 최종 판정했다.

## 2026-07-30 모델 결정

- 기본 모델: `claude-sonnet-5`
- A6 개인 스마트 라우터 우선 판매자: ID 1263
- 화면 확인 가격: 입력 `$0.0180/1M`, 출력 `$0.0900/1M`
- 월 API 소비 상한: `$1`
- 전송 범위: 음성 원본이 아닌 Whisper 음성 인식 결과와 구간 ID만 전송
- 주의: 판매자 ID는 API 요청 필드로 추측해 보내지 않는다. A6 개인 스마트 라우터에서 설정한다.
- 결과 정리: OpenAI 호환 `response_format=json_schema`, `strict=true`
- 검증: 서버가 모든 근거 구간 ID의 실제 존재 여부를 다시 검사

로컬 Qwen/Ollama는 A6API 경로로 대체했다. 기존 중간 결과는 비교 기록으로만 남긴다.

### 연결 준비 검증

- `https://api.a6api.com/v1/models`: 키 없이 401 JSON 응답 확인
- Compose 구성 검사 통과
- A6API 파이프라인 Docker 이미지 빌드 통과
- `.env`는 Git과 Docker 빌드 컨텍스트에서 제외
- 키가 없으면 외부 호출 전 종료
- 음성 2개가 없으면 외부 호출 전 종료
- 실제 A6 연결 및 결과 정리 호출 성공

## 2026-07-30 공개 AMI 회의 10개 결과

- 출처·선정 근거: [`PUBLIC_AUDIO_SAMPLES.md`](./PUBLIC_AUDIO_SAMPLES.md)
- 정확한 구간·기대 결정: [`ami-samples.tsv`](./ami-samples.tsv)
- 자동 게이트: 10/10 PASS
- 녹음당 처리 시간: 평균 20.09초, 최대 28.36초
- 10개 총 예상 API 비용: `$0.00026196`
- 수동 의사결정 정답 대조: 9/10
- 남은 의미 오류: `ami-02`의 LCD·spinning wheel 결정을 `action_item`으로 분류

공개 영어 회의로 Docker·음성 인식·결과 정리·근거 검증·비용 경로는 통과했다.
한국어 최종 GO/NO-GO는 아래 자연 발화(사람이 실제로 자연스럽게 한 말) 샘플 2개로 판정했다.

## 2026-07-30 한국어 최종 게이트

- 자연 발화(사람이 실제로 자연스럽게 한 말) 샘플 출처: KMSAV에 등재된 공개 YouTube 영상 2개
- 라이선스 확인: 각 영상 `Creative Commons Attribution license (reuse allowed)`
- `ko-01-action.wav`: 25.47초, 결정 1개와 할 일 1개, 근거 ID 검증 PASS
- `ko-02-decision.wav`: 23.52초, 결정 1개, 근거 ID 검증 PASS
- 두 파일 총 예상 A6API 비용: `$0.00007391`
- 합성 음성·고정 응답·미리 계산한 추출 결과를 사용하지 않음

자동 게이트 2/2와 수동 의미 대조 2/2가 모두 통과했다. Day 1 기술 판정은
**GO**다.

## 2026-07-30 Web MVP 실제 검증

- Docker 이미지 빌드 PASS
- `GET /api/health` → `{"status":"ok"}`
- `GET /api/budget` → 현재 월 사용액·상한·잔액 반환
- 공개 한국어 샘플 2개 인식 PASS
- 최종 빌드 샘플 분석 API: 42.45초, `$0.00003521`, 근거 검증 PASS
- 최종 빌드 multipart 파일 업로드: 33.07초, `$0.00003825`, 근거 검증 PASS
- 두 호출 월간 누적: `$0.00007346`, 잔액 `$0.99992654`
- 컨테이너 재시작 후 누적 금액 유지 PASS
- 월 한도 누적·사전 차단·샘플 길이 단위 테스트 3개 PASS
- 지원하지 않는 `.md` 업로드: HTTP 415와 한국어 오류 메시지
- Python·JavaScript 문법 검사와 Compose 구성 검사 PASS

화면은 데스크톱 2열, 860px 이하 단일 열, 560px 이하 소형 화면 규칙을
구현했다. 실제 Chrome 화면 캡처 검증은 브라우저 직접 조작 승인을 받은 뒤
별도로 수행한다.

## Web MVP Design Contract

### JOB

면접관 또는 데모 시청자가 회의 음성을 직접 넣거나 공개 샘플을 선택해,
실제 AI가 만든 음성 기록·결정·할 일을 확인하고 각 결과의 근거가 된 음성으로 바로
이동할 수 있어야 한다.

### CONTENT

- 입력: 실제 오디오 파일명, 크기, 공개 한국어 데모 2개
- 처리 상태: Whisper 음성 인식과 A6API 결과 정리 단계
- 결과: 시간 정보가 붙은 음성 기록, 결정, 할 일, 담당자, 기한, 근거 구간
- 검증 정보: 모델, 처리 시간, 토큰 기반 예상 비용, 근거 유효성
- 경계 상태: 파일 미선택, 지원하지 않는 확장자, 20MB 초과, API 실패,
  결과 없음, 긴 음성 기록

### SYSTEM

프로젝트 소유의 CSS 토큰을 사용한다. 시스템 sans-serif 한 계열, 밝은 중성
배경, 흰 작업면, 짙은 남색 본문, 파란색 주 액션, 보라색 결정, 청록색 할 일로
제한한다. 데스크톱은 음성 기록과 결과를 나란히, 좁은 화면은 단일 열로 배치한다.

### PRIMARY

직접 확인한 1차 레퍼런스는 Otter 공식 Help Center의
[Conversation Page Overview](https://help.otter.ai/hc/en-us/articles/5093228433687-Conversation-Page-Overview)다.
정확히 확인한 상태는 처리 완료 후 Conversation의 `Summary`와 `Transcript`
영역이며, Action Item의 `View in transcript`가 근거 내용으로 이동한다.

### MEDIA

실제 공개 한국어 오디오를 브라우저 기본 플레이어로 재생한다. 장식용 이미지나
가짜 파형은 만들지 않는다. 샘플에는 원본 영상 링크와 라이선스를 표시한다.

### INTERACTION

결정·할 일 카드의 `근거 듣기`를 누르면 첫 근거 구간으로 오디오가 이동하고
해당 음성 기록 구간이 강조된다. 마우스와 키보드 모두 지원하며,
`prefers-reduced-motion`에서는 부드러운 스크롤만 제거하고 기능은 유지한다.

### DECISIONS

Otter에서 가져오는 것은 `요약/음성 기록 분리`, `결정·할 일`, `근거로 이동`이라는
핵심 경험뿐이다. 사이드바, 협업, 채팅, 댓글, 계정, 실시간 회의 기능은
3일 MVP 범위에서 제외한다. 가짜 KPI와 마케팅용 hero도 만들지 않는다.

## 민감정보 없는 판정용 녹음안

아래 두 문단을 스마트폰이나 PC 마이크로 각각 자연스럽게 읽어 20–30초 파일로 만든다.
조금 머뭇거리거나 말투를 바꾸는 것은 괜찮지만, 사실은 바꾸지 않는다.

### sample-a

> 그럼 이번 주 배포 일정부터 정리할게요. 배포는 금요일 오후 세 시로 확정하죠.
> 민수님은 목요일 점심 전까지 체크리스트를 정리해 주세요.
> 지연님은 오늘 안에 공지 문구를 작성하고요.
> 장애가 생기면 지난 버전으로 바로 롤백하는 걸로 합의하겠습니다.

주석 사실 5개:

1. 배포일은 금요일이다.
2. 배포 시각은 오후 3시다.
3. 민수는 목요일 점심 전까지 체크리스트를 정리한다.
4. 지연은 오늘 안에 공지 문구를 작성한다.
5. 장애 시 지난 버전으로 롤백하기로 합의했다.

### sample-b

> 온보딩 개선안은 A안으로 가겠습니다.
> 첫 화면의 가입 단계는 세 단계로 줄이고,
> 수현님이 내일 오후까지 새 와이어프레임을 올려 주세요.
> 사용자 테스트는 다음 주 화요일 다섯 명을 대상으로 진행하죠.
> 결과 리뷰는 수요일 오전 열 시로 잡겠습니다.

주석 사실 5개:

1. 온보딩 개선안은 A안이다.
2. 가입 단계는 3단계로 줄인다.
3. 수현은 내일 오후까지 새 와이어프레임을 올린다.
4. 사용자 테스트는 다음 주 화요일에 5명을 대상으로 한다.
5. 결과 리뷰는 수요일 오전 10시다.
