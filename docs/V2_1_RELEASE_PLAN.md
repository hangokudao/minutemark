# MinuteMark V2.1 버전업 실행 기록

> 기준일: 2026-08-02
> 후보 커밋: `6756663d781bfa77155293ef4fe1a852e93f1f5a`
> 단계: `RELEASE_CANDIDATE · IN_PROGRESS`
> 이 문서가 V2.1의 활성 범위·검증·출시 판단 기록이다.

## 1. 이번 버전의 결정

V2.1은 인증 체계를 다시 만드는 버전이 아니다. 이미 구현한 Firebase Google 인증을
포트폴리오에 맞게 유지하고, 개인정보 문의처와 QA 안전 경계를 명확히 한다.

- `Google로 계속하기` 한 가지 수단만 제공한다.
- 첫 Google 로그인은 회원가입, 이후 로그인은 기존 계정 로그인으로 처리한다.
- 자체 아이디·비밀번호, 비밀번호 재설정, 자체 세션 저장소는 만들지 않는다.
- 문의처는 `MinuteMark 개인정보 보호 담당 / hangokudao@gmail.com`으로 표시한다.
- `hangokudao@gmail.com`과 `myhanbro@gmail.com`은 소유자가 직접 로그인하는
  실제 QA 계정으로 사용한다. 에이전트는 비밀번호·쿠키·token을 받거나 기록하지
  않는다.
- 테스트에는 민감하지 않은 데모 오디오만 사용하며 계정 탈퇴는 Google 계정이
  아니라 MinuteMark의 Firebase 사용자와 저장 데이터만 삭제한다.
- 공개 진입, 업로드, 로그인, 개인정보 화면에 정식 서비스가 아닌 포트폴리오
  데모임을 표시하고 민감하거나 실제 업무용인 파일을 올리지 말라고 안내한다.

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
| 독립 빌드 | Docker 이미지와 전체 회귀 | 동일 소스 이미지 빌드·테스트 성공 | `PASS` · image `2546706…`, 48/48 |
| 인증 경계 | 비인증·잘못된 provider·폐기 token 테스트 | 서버가 안전한 401로 거부 | 기존 자동 증거 PASS |
| 실제 Google 로그인 | 배포 후보에서 Google 계정 선택·로그인 | 계정 선택 뒤 회원 화면 진입 | `BLOCKED` · 승인 도메인은 추가됐으나 Chrome에서 계정 선택 창이 열리지 않음 |
| 사용자 소유권 | 다른 실제 Google 사용자 직접 요청 | 목록·상세·오디오가 404 | `BLOCKED` · 배포 후보에서 검증 예정 |
| 저장·재열람 | 실제 회원 오디오 1회 | Firestore·Storage 저장 후 상세 복원 | `BLOCKED` · 배포 후보에서 검증 예정 |
| 삭제 | 실제 회의·계정 삭제 뒤 저장소 조회 | 문서·객체·Auth 사용자 잔여 0 | `BLOCKED` · 배포 후보에서 검증 예정 |
| 공개 UI | Windows Chrome 1440×900·390×844 | privacy·샘플·메뉴에 막힘·넘침 없음 | `BLOCKED` · 샘플·auth·메뉴는 PASS, privacy 하단 시각 확인 timeout |
| 회원가입 UI | 회원 기능을 켠 독립 후보의 `/auth` | 가입 안내와 Google 버튼 표시 | `PASS` · 실제 0% 후보에서 표시·새로고침 확인 |
| 개인정보 고지 | 공개 privacy 화면과 실제 데이터 흐름 | 문의처·수집·저장·외부 AI 전송 설명 일치 | `PASS` · 공개 화면 직접 확인 |
| A6 외부 처리 | 포트폴리오 한계·전사문 전송·미확인 조건 고지 | 민감정보 업로드 금지와 확인 범위를 모든 사용자가 알 수 있음 | `PASS` · samples·privacy·auth 브라우저 확인 |
| 배포·복구 | 후보 commit·runtime·기존 V1 | 후보 검증 성공, V1 유지·rollback 가능 | `BLOCKED` · 0% 후보 정상, V1 100% 유지, 회원 QA 미완료 |

필수 행에 `FAIL` 또는 `BLOCKED`가 있으면 V2.1을 공개 배포하지 않는다. 기존 V1
트래픽은 그대로 유지한다.

## 5. 실행 순서

1. 문의처, 포트폴리오 한계 고지, 소유자 직접 로그인 QA 규칙을 코드·문서·테스트에 반영한다.
2. Spec 리뷰와 Standards/보안 리뷰를 각각 한 번 실행하고 차단 항목을 수정한다.
3. 수정된 최종 소스로 Docker 빌드, 전체 회귀, `pip check`, `pip-audit`, 문법과
   diff 검사를 실행한다.
4. 검증한 변경을 `codex/*` 브랜치에 push하고 PR로 main에 반영한다.
5. main의 Cloud Build가 만든 트래픽 0% Cloud Run 후보를 확인한다. 기존 V1 트래픽은
   유지한다.
6. `wsl-local-chrome-bridge`에서 계정 소유자가 두 Google 계정의 로그인을 직접
   완료하면 분석·저장·격리·삭제를 수행하고 Firestore·Storage·Firebase Auth 상태를
   함께 확인한다.
7. 필수 게이트가 통과한 동일 커밋의 후보에만 트래픽을 전환한다.

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

## 8. 이번 실행 증거

### 자동·HTTP

- Docker: `minutemark-v2-1-rc-final`, image
  `sha256:254670680c5b63fa4a0156e448e9d3d7cc53c58bd8741551eefe5f68d177fa80`
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
