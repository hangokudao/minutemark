# MinuteMark

실제 회의 음성을 전사하고, 회의에서 확정된 결정과 할 일을 근거 발화와 함께
보여주는 AI 회의 노트입니다.

[실행해 보기](https://minutemark-2u3l25uhba-du.a.run.app) ·
[GitHub 저장소](https://github.com/hangokudao/minutemark) ·
[데모 녹화 대본](./docs/DEMO_SCRIPT.md)

![MinuteMark 데스크톱 화면](./docs/screenshots/minutemark-desktop.png)

## 무엇을 복제했나

Otter류 AI 회의 서비스의 핵심 경험만 3일 MVP 범위로 재구성했습니다.

1. 회의 음성 입력
2. 타임스탬프 전사
3. 결정과 할 일 구조화
4. 결과에서 근거 발화로 이동

계정, 협업, 댓글, 실시간 회의 봇은 제외했습니다. 포트폴리오에서 직접 조작해
볼 수 있는 한 개의 수직 흐름에 집중했습니다.

## 실제 AI 흐름

```mermaid
flowchart LR
    A["브라우저<br/>음성 또는 공개 샘플"] --> B["FastAPI<br/>Cloud Run"]
    B --> C["faster-whisper small<br/>CPU INT8 전사"]
    C --> D["전사문과 구간 ID만<br/>A6API GPT-5.6 Luna로 전송"]
    D --> E["결정·할 일 JSON"]
    E --> F["서버 구조·근거 검증"]
    F --> G["전사·결과·근거 듣기"]
```

음성 원본은 A6API에 보내지 않습니다. 서버에서 Whisper로 전사한 텍스트와
구간 ID만 전송합니다.

## 핵심 기능

- WAV, MP3, M4A, OGG, FLAC, WEBM 업로드
- 실제 공개 한국어 회의 샘플 2개
- `faster-whisper/small`의 타임스탬프 전사
- A6API `gpt-5.6-luna`의 결정·할 일 추출
- 존재하는 전사 구간만 허용하는 서버 검증
- 결과의 `근거 듣기`에서 오디오 seek와 전사 강조
- 처리 시간, 토큰, 예상 API 비용 표시
- 20MB·2분·동시 처리 1의 공개 데모 보호선

## 실제 실행 결과

2026-07-31 Windows Chrome에서 공개 배포를 직접 실행한 결과입니다.

| 입력 | 전체 처리 | 결과 | 근거 이동 | 예상 A6 비용 |
| --- | ---: | --- | --- | ---: |
| 법안 통과 후속 작업 | 39.75초 | 전사 7구간, 할 일 1개 | S5·S6 → 약 23.72초 | $0.00008890 |
| KTX 노선 변경 결정 | 35.94초 | 전사 13구간, 결정 1개 | 인용 구간 → 약 0.92초 | $0.00010337 |
| 직접 WAV 업로드 | 34.90초 | 전사 13구간, 결정 1개 | S1 → 약 0.40초 | $0.00010985 |

두 공개 샘플은 Cloud Run 로그에서 HTTP 200을 확인했습니다. 직접 WAV 업로드도
Windows Chrome에서 실제 결과와 오디오 이동을 확인했으며, 모든 결과의 근거
구간이 실제 전사에 존재했습니다.

## 장애를 제품 동작으로 바꾼 과정

A6 스마트 라우터는 판매자에 따라 OpenAI 호환 기능 지원 범위가 달랐습니다.

- 일시적 502: 네트워크·5xx에 한해 1회 재시도
- `response_format=json_schema`의 HTTP 400: 일반 JSON 요청으로 한 번 폴백
- 폴백 응답: 서버에서 필수 필드와 타입을 다시 검증
- 모델이 `"S5, S6"` 문자열을 반환한 사례: 구간 ID를 정규화한 뒤 실재 여부 재검증
- 검증 실패: 사용자 결과로 내보내지 않고 안전한 오류로 종료

공개 환경에서도 실제 400이 발생했으며, 폴백 후 HTTP 200과 근거 검증 통과를
확인했습니다.

## Docker와 배포

- 애플리케이션: FastAPI + Vanilla JavaScript
- 전사: `faster-whisper 1.2.1`, `small`, CPU INT8
- 구조화: A6API `gpt-5.6-luna`
- 패키징: Docker
- 호스팅: Google Cloud Run 서울 리전
- 리소스: 2 vCPU, 4 GiB, 동시 처리 1, 최소 0
- 현재 리비전: `minutemark-00004-65g`
- 이미지 digest:
  `sha256:c2fe6d8629b0928783885f4b44274ca7a65faf3ec7068c90856f947e3b48dfa5`

### 비용 보호

| 보호선 | 상태 |
| --- | --- |
| 앱 추정 A6 월 예산 | $1 |
| Cloud Run 서비스 최대 인스턴스 | 1, 확인 완료 |
| Google Cloud 프로젝트 예산 | 월 ₩1,000 |
| 결제 알림 | 50%·90%·100%, `myhanbro@gmail.com` |
| A6 토큰 하드 한도 $1 | 총 $1.00, 남은 $0.99 확인 완료 |

Google Cloud 예산은 알림이며 결제를 자동 중단하는 하드 캡이 아닙니다.
A6API 토큰 `local-meeting-notes-mvp`의 총한도는 $1.00으로 설정했습니다.

## 브라우저 QA 상태

| 검증 | 상태 | 증거 |
| --- | --- | --- |
| Windows Chrome 데스크톱 1440×900 | PASS | 겹침·잘림·비의도적 가로 스크롤 없음 |
| 공개 샘플 2개 실제 분석 | PASS | 화면 결과와 Cloud Run POST 200 |
| 근거 듣기 | PASS | 오디오 seek와 전사 강조 |
| 모바일 390×844 랜딩 | PASS | 격리 headless Chrome fallback |
| WAV 파일 업로드 | PASS | 실제 34.90초 분석과 근거 이동 확인 |
| 실패·재시도 상태 | PASS | 안전한 한국어 안내만 표시, 내부 오류·경로 없음 |
| 오류 경로 콘솔·네트워크 | PASS | 콘솔 오류 없음, Cloud Run POST 422 두 번 |

![MinuteMark 모바일 화면](./docs/screenshots/minutemark-mobile.png)

스크린샷과 검증 결과는 실제 공개 URL 기준입니다. 조작 영상이 필요한 경우
[데모 녹화 대본](./docs/DEMO_SCRIPT.md)의 66초 순서로 한 번만 녹화하면 됩니다.

## 로컬 실행

`.env.example`을 `.env`로 복사하고 A6API 키를 넣습니다.

```sh
docker compose run --rm sample-downloader
docker compose up --build web
```

브라우저에서 `http://localhost:8000`을 엽니다.

회귀 테스트:

```sh
docker compose run --rm -v ./tests:/tests:ro --entrypoint python web \
  -m unittest discover -s /tests -v
```

현재 A6 400 폴백, 일시적 502 재시도, 근거 정규화·검증, 예산·용량 보호선,
샘플 길이, 오류 정보 정제, 공개 샘플 저작자 표시와 배포 커밋 확인을 포함한
테스트 13개가 통과합니다.

## 자동 배포

GitHub `main`이 배포 정본입니다. `main`에 병합하면 Cloud Build가
[`cloudbuild.yaml`](./cloudbuild.yaml)에 따라 다음 순서로 실행합니다.

1. Docker 이미지 빌드
2. 회귀 테스트 13개
3. Git 커밋 SHA로 이미지 태그 후 Artifact Registry에 push
4. 기존 Cloud Run `minutemark` 서비스에 배포

`/api/health`의 `commit` 값과 GitHub `main` SHA가 같으면 배포가 동기화된
상태입니다. 기존 환경변수와 Secret Manager 연결은 유지하고, 최대 인스턴스
`1`과 동시 처리 `1`도 배포 명령에서 다시 고정합니다. 수동
[`cloudrun-deploy.sh`](./cloudrun-deploy.sh)는 최초 설정이나 복구용입니다.

## 문서

- [운영·검증 기록](./NOTES.md)
- [공개 오디오 출처와 라이선스](./PUBLIC_AUDIO_SAMPLES.md)
- [66초 데모 녹화 대본](./docs/DEMO_SCRIPT.md)

## 라이선스

소스 코드와 자체 제작 문서·이미지는 [MIT](./LICENSE)입니다. 번들된
`samples/korean/*.wav`는 MIT 적용 대상이 아니며, 각 원본의 CC BY 조건과
[저작자·출처·가공 표시](./PUBLIC_AUDIO_SAMPLES.md)를 따릅니다.

## 현재 제한

- Cloud Run의 로컬 SQLite 예산 장부는 인스턴스 재시작 시 초기화될 수 있습니다.
- 공개 데모는 한 번에 한 분석만 처리합니다.
- A6 스마트 라우터 판매자에 따라 구조화 출력 지원이 달라 서버 폴백과 검증을
  사용합니다.
