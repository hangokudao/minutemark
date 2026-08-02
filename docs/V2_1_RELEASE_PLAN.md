# MinuteMark V2.1 버전업 실행 기록

> 기준일: 2026-08-03
> 작업 브랜치: `codex/redesign-v1` · 최종 후보 SHA는 배포 `/api/health`에서 확인한다.
> 단계: `RELEASE_CANDIDATE · IN_PROGRESS`
> 이 문서가 V2.1의 활성 범위·검증·출시 판단 기록이다.

## 1. 이번 버전의 결정

V2.1은 인증 체계를 다시 만드는 버전이 아니다. 이미 구현한 Firebase Google 인증을
포트폴리오에 맞게 유지하고, 개인정보 문의처와 QA 안전 경계를 명확히 한다.

- `Google로 계속하기` 한 가지 수단만 제공한다.
- 첫 Google 로그인은 회원가입, 이후 로그인은 기존 계정 로그인으로 처리한다.
- 자체 아이디·비밀번호, 비밀번호 재설정, 자체 세션 저장소는 만들지 않는다.
- 문의처는 `MinuteMark 개인정보 보호 담당 / hangokudao@gmail.com`으로 표시한다.
- 실제 Google 테스트 계정 A와 B는 소유자가 직접 로그인한다. 에이전트는 계정
  이메일·비밀번호·쿠키·token을 받거나 공개 QA 기록에 남기지 않는다.
- 테스트에는 민감하지 않은 데모 오디오만 사용하며 계정 탈퇴는 Google 계정이
  아니라 MinuteMark의 Firebase 사용자와 저장 데이터만 삭제한다.
- 공개 진입, 업로드, 로그인, 개인정보 화면에 정식 서비스가 아닌 포트폴리오
  데모임을 표시하고 민감하거나 실제 업무용인 파일을 올리지 말라고 안내한다.
- 업로드와 개인정보 화면에는 아래 확정 문구를 표시한다.

> 포트폴리오 데모입니다. 실제 업무·기밀·민감정보가 포함된 파일을 업로드하지
> 마세요. 업로더는 녹음·분석에 필요한 참여자 고지와 권한을 확보해야 합니다.
> 전사문은 결과 생성을 위해 A6API로 전송됩니다.

결정 질문은 하나다.

> 포트폴리오 범위에서 실제 Google 사용자 두 명의 저장·격리·삭제 흐름을 검증했는가?

현재 답은 `검증 진행 중`이다. 두 계정의 자격 증명은 소유자만 입력하며, 실제
저장소 상태까지 확인한 항목만 PASS로 판정한다.

## 2. 핵심 사용자 결과

1. 비회원이 공개 샘플과 개인정보처리방침을 로그인 없이 확인한다.
2. Google 사용자가 첫 로그인으로 회원가입하고 이후 다시 로그인·로그아웃한다.
3. 회원이 실제 오디오를 분석·저장하고 목록·상세·새로고침에서 다시 연다.
4. 다른 회원은 그 회의에 접근하지 못하고, 소유 회원은 회의와 계정을 삭제한다.

1번은 비로그인 상태에서 검증한다. 2~4번은 위 두 Google 계정으로 실제 브라우저에서
수행하되 비밀번호와 인증 정보는 소유자만 다룬다.

## 3. 비범위

- 자체 아이디·비밀번호와 비밀번호 찾기
- 에이전트가 Google 계정을 만들거나 비밀번호를 받는 작업
- 가짜 로그인·가짜 회의·가짜 저장 성공 상태
- 협업, 댓글, 결제, 팀, 공유 링크, 관리자 화면
- 출시 증거가 없는 상태에서 Cloud Run 트래픽을 V2로 전환하는 작업

## 4. 위험과 출시 게이트

| 위험 | 최소 증거 | 통과 기준 | 현재 상태 |
| --- | --- | --- | --- |
| 독립 빌드 | Docker 이미지와 전체 회귀 | 동일 소스 이미지 빌드·테스트 성공 | `PASS` · image `025ea4c2…`, 48/48 |
| 인증 경계 | 비인증·잘못된 provider·폐기 token 테스트 | 서버가 안전한 401로 거부 | 기존 자동 증거 PASS |
| 실제 Google 로그인 | 배포 후보에서 Google 계정 선택·로그인 | 계정 선택 뒤 회원 화면 진입 | `BLOCKED` · 승인 도메인은 추가됐으나 Chrome에서 계정 선택 창이 열리지 않음 |
| 사용자 소유권 | 다른 실제 Google 사용자 직접 요청 | 목록·상세·오디오가 404 | `BLOCKED` · 배포 후보에서 검증 예정 |
| 저장·재열람 | 실제 회원 오디오 1회 | Firestore·Storage 저장 후 상세 복원 | `BLOCKED` · 배포 후보에서 검증 예정 |
| 삭제 | 실제 회의·계정 삭제 뒤 저장소 조회 | 문서·객체·Auth 사용자 잔여 0 | `BLOCKED` · 배포 후보에서 검증 예정 |
| 공개 UI | Windows Chrome 1440×900·390×844 | privacy·샘플·메뉴에 막힘·넘침 없음 | `BLOCKED` · 샘플·auth·메뉴는 PASS, privacy 하단 시각 확인 timeout |
| 회원가입 UI | 회원 기능을 켠 독립 후보의 `/auth` | 가입 안내와 Google 버튼 표시 | `PASS` · 실제 0% 후보에서 표시·새로고침 확인 |
| 개인정보 고지 | 공개 privacy 화면과 실제 데이터 흐름 | 문의처·수집·저장·외부 AI 전송 설명 일치 | `BLOCKED` · 확정 문구 자동 계약 PASS, 새 후보 브라우저 확인 예정 |
| A6 외부 처리 | 포트폴리오 한계·전사문 전송·미확인 조건 고지 | 민감정보 업로드 금지와 확인 범위를 모든 사용자가 알 수 있음 | `BLOCKED` · 확정 문구 자동 계약 PASS, 새 후보 브라우저 확인 예정 |
| 배포·복구 | 후보 commit·runtime·기존 V1 | 후보 검증 성공, V1 유지·rollback 가능 | `BLOCKED` · 0% 후보 정상, V1 100% 유지, 회원 QA 미완료 |

필수 행에 `FAIL` 또는 `BLOCKED`가 있으면 V2.1을 공개 배포하지 않는다. 기존 V1
트래픽은 그대로 유지한다.

## 5. 실행 순서

1. 확정 문구와 버전업 규칙을 코드·문서·테스트에 반영한다.
2. 남은 로컬 변경을 하나의 V2.1 범위로 정리하고 공개 QA 계정 이메일은 익명화한다.
3. 전체 회귀, Docker 빌드, `pip check`, `pip-audit`, 문법·diff·보안 경계를 확인한다.
4. Spec 리뷰와 Standards/보안 리뷰를 각각 한 번 실행하고 출시 차단 항목을 수정한다.
5. 검증한 변경을 GitHub 계정 `hangokudao`의 `codex/redesign-v1` 브랜치에 push한다.
6. Google Cloud 프로젝트 `minutemark-portfolio`의 Cloud Run `minutemark`에 최신
   커밋을 트래픽 0% 시험 후보로 배포하고 기존 V1 트래픽을 유지한다.
7. 실제 Google 테스트 계정의 소유자가 로그인을 직접 완료하면 분석·저장·격리·
   재열람·삭제를 수행하고 Firestore·Storage·Firebase Auth 상태를 함께 확인한다.
8. 필수 게이트가 모두 PASS인 경우에만 PR을 `main`에 병합하고, 동일 커밋의 공개
   V2 트래픽을 전환한 뒤 비파괴 스모크를 수행한다.

## 6. 브라우저 QA 규칙

- Windows Chrome 브리지의 실제 반환 상태를 그대로 기록한다.
- 브리지가 `FAILED` 또는 `BLOCKED`면 성공으로 바꾸지 않는다.
- 공개 화면 fallback은 읽기 전용 격리 브라우저만 허용한다.
- 로그인, 계정 전환, 파일 업로드, 회의·계정 삭제는 Windows Chrome에서만 수행하고
  실패 시 fallback으로 성공 처리하지 않는다.
- 스크린샷에는 개인 이메일, token, cookie, Cloud Console을 포함하지 않는다.

## 7. 종료 기준

이번 작업 루프는 다음 두 조건에서 종료한다.

- 코드·자동 검사와 공개·회원 브라우저 QA가 끝나고 모든 행이 `PASS`, `FAIL`,
  `BLOCKED`, `N/A` 중 하나로 닫힘
- 정식 서비스 전환 전에는 A6API의 보관·학습·처리 국가·재위탁 조건을 별도로
  확인해야 한다는 제한을 유지함

### 공개 전환과 복구

1. 공개 전환 직전에 Cloud Run의 현재 100% 트래픽 리비전과 새 V2 후보 리비전을
   다시 읽어 기록한다. 이번 작업의 기존 정상 리비전은 `minutemark-00007-w6c`다.
2. V2 후보의 `/api/health` commit이 GitHub `main` SHA와 같고 필수 QA가 모두
   PASS일 때만 새 리비전으로 트래픽을 전환한다.
3. 전환 후 health·공개 샘플·로그인 진입 스모크가 실패하면 아래 명령으로 기존
   정상 리비전에 트래픽 100%를 되돌린다.

```sh
gcloud run services update-traffic minutemark \
  --project=minutemark-portfolio \
  --region=asia-northeast3 \
  --to-revisions=minutemark-00007-w6c=100
```

4. 복구 뒤 공개 `/api/health`가 HTTP 200인지 확인하고, Cloud Run 트래픽 조회에서
   기존 리비전 100%를 확인한다. 전환 전 후보가 실패하면 트래픽을 건드리지 않는다.

## 8. 이번 실행 증거

### 자동·HTTP

- Docker: `minutemark-v2-1-rc-20260803`, image
  `sha256:025ea4c28485e72df8d4fe3ba1fd11ebec7fb06da993a577e04b4dbcee5e2113`
- 기본 실행 사용자: `minutemark`
- 회귀: 48/48 `PASS`
- `pip check`: 충돌 0
- `pip-audit`: 알려진 취약점 0
- JavaScript·shell 문법, `git diff --check`: `PASS`
- `GET /api/health`: 200, `no-store`
- `GET /auth`: 200
- `GET /docs`: 404
- 비인증 `GET /api/meetings`: 401, `no-store`
- CSP, HSTS, COOP `same-origin-allow-popups`, `X-Frame-Options: DENY`,
  `nosniff`, `no-referrer`: 응답 헤더에서 확인
- WSL Codex 워크트리 상위 폴더 권한 때문에 읽기 전용 `/tests` 마운트는 테스트
  컨테이너에만 `--user 0`을 사용했다. 제품 이미지의 `Config.User=minutemark`와
  실제 HTTP 실행은 비루트 기본값으로 별도 확인했다.

### Windows Chrome 브리지

- 브리지 작업: `019fc1c5-3f68-71e0-b9c4-ddd0ef693e35`
- URL: `http://localhost:18080/samples`, `/privacy`, `/auth`
- 화면: 1440×900, 390×844
- 행동: 공개 샘플·privacy·회원가입 모달 확인, `/auth` 새로고침 복원, 모바일 메뉴 열기
- 기대·실제: 포트폴리오·민감 파일 경고, 담당명·문의 이메일, 첫 로그인 가입 문구,
  Google 버튼, 공개 메뉴가 모두 표시됨
- 콘솔 error·warn: 0
- 네트워크 실패 목록: Chrome 점검 API가 제공하지 않아 `BLOCKED`
- 스크린샷: 브리지 실행 안에서 캡처했으나 로컬 저장 경로는 제공되지 않음
- 판정: 최초 수정 전 `/auth` 확인은 `FAILED`; 외부 Firebase 모듈보다 먼저 모달을
  표시하고 준비 전 Google 버튼을 비활성화하도록 수정한 뒤, 최초 진입과 연속
  새로고침 3회가 실제 캡처에서 모두 `SUCCESS`

### 실제 Cloud Run 0% 후보

- 리비전: `minutemark-00009-xac`
- 태그 URL: `https://v2-rc---minutemark-2u3l25uhba-du.a.run.app`
- `/api/health`: 200, commit
  `6756663d781bfa77155293ef4fe1a852e93f1f5a`
- 런타임 계정: `minutemark-runtime@minutemark-portfolio.iam.gserviceaccount.com`
- 기존 공개 V1 `minutemark-00007-w6c`: 트래픽 100% 유지
- Firebase Authentication 승인 도메인: 기존 4개를 보존하고 후보 태그 도메인 1개를
  추가한 뒤 Admin API에서 5개를 다시 읽어 확인
- Google 로그인 재시험: `/auth`, 1440×900에서 버튼을 한 번 눌렀으나 계정 선택
  화면이 열리지 않아 `BLOCKED`. 비밀번호·MFA·cookie·token은 입력하거나 기록하지 않음
- 로그인 전제 조건이 충족되지 않아 업로드·유료 분석·저장·삭제는 수행하지 않음

## 9. 이전 실행 증거

아래 내용은 `0170848`까지의 이전 실행 기록이며, 이번 변경분 검증 결과로 재사용하지
않는다.

### 자동·HTTP

- Docker: `minutemark-v2-1-rc`, image
  `sha256:c8b0dcacf7d849141d7e1dce191b264347e08b5372d007febd4f7f3f72bfd2f0`
- 기본 실행 사용자: `minutemark`
- 회귀: 46/46 `PASS`
- `pip check`: 충돌 0
- `pip-audit`: 알려진 취약점 0
- JavaScript·shell 문법, `git diff --check`: `PASS`
- `/samples`, `/privacy`, `/auth`: 서버 응답 200
- `/docs`: 404
- 비인증 `/api/meetings`: 401, `no-store`

### Windows Chrome 브리지

브리지 작업: `019fc1c5-3f68-71e0-b9c4-ddd0ef693e35`

```text
Windows Chrome bridge: FAILED
Reason: member-disabled-safe-candidate-auth-unavailable
URLs: http://localhost:8000/samples, /privacy, /auth
Result: 공개 샘플·privacy·모바일 메뉴는 통과. /auth는 회원 기능 false 설정에 따라
        /samples로 복귀하고 준비 중 안내를 표시해 전체 작업 기대와 달랐음.
Evidence: Chrome 새 에이전트 탭, 1440×900·390×844 캡처. 개인 계정 UI 없음.
```

- 데스크톱 `/samples`: 공개 샘플 2개, 가로 넘침 없음, 최근 회의·예산 잔액 비노출
- 데스크톱·모바일 `/privacy`: 담당 명칭과 `hangokudao@gmail.com` 표시
- 모바일 `/samples`: 390/390, 새 회의·메뉴 표시
- 모바일 메뉴: 공개 샘플·privacy·GitHub만 표시, 회원 전용 항목 비노출
- 콘솔 error·warn: 0
- 네트워크 워터폴은 Chrome 점검 API가 제공하지 않아 `BLOCKED`
- Google 로그인, 계정 전환, 샘플 분석, 업로드, 삭제는 수행하지 않음

## 10. V2.1 업데이트 내역

### 추가

- Firebase Google 회원가입·로그인·로그아웃과 최근 재인증 기반 계정 탈퇴
- 사용자별 회의 분석·저장·목록·상세·오디오 재생·삭제
- `/meetings`, `/meetings/new`, `/meetings/{id}`, `/account`, `/privacy` 라우팅
- 모바일 회원 메뉴, 회의 제목, 참여자 확인, 작성 중 이탈 경고

### 변경

- A6API 분석 모델을 `gpt-5.6-luna`로 전환
- 포트폴리오 안내를 실제 업무·기밀·민감정보 금지, 참여자 권한, 전사문 A6API
  전송을 함께 알리는 확정 문구로 통일
- 실제 QA 계정 이메일을 공개 문서에서 `테스트 계정 A/B`로 익명화

### 버그 수정

- Firebase 모듈 준비 전에 `/auth` 화면이 사라지던 초기 로딩 문제 수정
- 모바일에서 새 회의·목록에 접근하지 못하거나 데스크톱 최근 목록이 노출되던 문제 수정
- 뒤로가기·앞으로가기·새로고침과 작성 중 이탈 경고가 충돌하던 문제 수정
- 실패한 저장의 Storage 객체와 계정 탈퇴 중 고아 객체를 정리하도록 보완

### 보안

- Firebase UID 기반 소유권 확인, 다른 사용자 리소스 404 처리
- Firestore 브라우저 직접 접근 차단, 비공개 Storage와 짧은 signed URL 사용
- 인증 전 요청 body 거부, 비공개 API `no-store`, CSP·HSTS·프레임·MIME 보호
- A6 secret을 전용 Cloud Run 런타임 계정과 단일 Secret Manager 리소스로 제한

## 11. PR 리뷰와 출시 체크

| 항목 | 결과 | 증거 |
| --- | --- | --- |
| 확정 문구·버전업 규칙 | `PASS` | 업로드·privacy 계약 테스트와 `AGENTS.md`·README 연결 |
| 전체 자동 테스트·Docker 빌드 | `PASS` | 48/48, image `025ea4c2…`, 비루트 `minutemark` |
| 의존성·보안 점검 | `PASS` | `pip check` 0, `pip-audit` 0, 404·401·`no-store`·보안 헤더 |
| Spec 리뷰 | `PASS` | 보조 Spec 충돌과 DELETE 404 계약 보완, 48/48 재통과 |
| Standards/보안 리뷰 | `PASS` | P0/P1 코드 결함 0, 복구 절차 누락 보완 |
| GitHub PR | 대기 | PR #5 head SHA와 merge gate |
| Cloud Run 0% 후보 | 대기 | 리비전·tag URL·`/api/health` commit |
| 실제 회원 QA | `BLOCKED` | 계정 소유자 로그인 후 저장·격리·삭제 증거 필요 |
| `main` 병합·공개 V2 | `BLOCKED` | 위 필수 게이트가 모두 PASS일 때만 진행 |

리뷰에서 발견한 보조 Spec의 QA 정책 충돌은 현재 정본에 맞게 수정했고, 없는 회의와
다른 사용자 회의의 `DELETE`가 동일하게 404를 반환하도록 계약과 구현을 맞췄다.
관련 회귀 48/48을 다시 통과해 Spec 리뷰를 PASS로 닫았다.

비차단 유지보수 항목은 `cloudbuild.yaml`과 `cloudrun-deploy.sh`의 배포 환경변수
중복 한 건이다. 현재 값은 일치한다. 둘 중 하나를 다음에 변경할 때 공통 정본 또는
일치 검사를 먼저 마련하지 않으면 설정이 어긋날 수 있으므로 `BEFORE_NEXT_CHANGE`로
기록한다.
