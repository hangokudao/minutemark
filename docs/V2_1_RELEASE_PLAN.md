# MinuteMark V2.1 버전업 실행 기록

> 기준일: 2026-08-02
> 기준 커밋: `39cbb00`
> 단계: `RELEASE_CANDIDATE · BLOCKED`
> 이 문서가 V2.1의 활성 범위·검증·출시 판단 기록이다.

## 1. 이번 버전의 결정

V2.1은 인증 체계를 다시 만드는 버전이 아니다. 이미 구현한 Firebase Google 인증을
포트폴리오에 맞게 유지하고, 개인정보 문의처와 QA 안전 경계를 명확히 한다.

- `Google로 계속하기` 한 가지 수단만 제공한다.
- 첫 Google 로그인은 회원가입, 이후 로그인은 기존 계정 로그인으로 처리한다.
- 자체 아이디·비밀번호, 비밀번호 재설정, 자체 세션 저장소는 만들지 않는다.
- 문의처는 `MinuteMark 개인정보 보호 담당 / hangokudao@gmail.com`으로 표시한다.
- 문의용·운영용 개인 Google 계정은 브라우저 QA, 회의 생성·삭제, 계정 탈퇴,
  교차 사용자 접근 시험에 사용하지 않는다.
- 실제 회원 E2E는 별도의 폐기 가능한 Google QA 계정이 제공되기 전까지
  `BLOCKED`로 기록하며 자동 테스트 결과로 대신하지 않는다.

결정 질문은 하나다.

> 개인 계정을 건드리지 않고도 V2.1을 공개 가능한 회원 제품으로 판정할 수 있는가?

현재 답은 `아니오`다. 공개·읽기 전용 화면과 코드 경계는 검증할 수 있지만 실제
Google 회원 저장·삭제 흐름은 전용 QA 계정 없이는 검증할 수 없다.

## 2. 핵심 사용자 결과

1. 비회원이 공개 샘플과 개인정보처리방침을 로그인 없이 확인한다.
2. Google 사용자가 첫 로그인으로 회원가입하고 이후 다시 로그인·로그아웃한다.
3. 회원이 실제 오디오를 분석·저장하고 목록·상세·새로고침에서 다시 연다.
4. 다른 회원은 그 회의에 접근하지 못하고, 소유 회원은 회의와 계정을 삭제한다.

1번은 개인 계정 없이 검증한다. 2~4번은 별도의 폐기 가능한 Google QA 계정 2개가
있을 때만 실제 브라우저로 수행한다.

## 3. 비범위

- 자체 아이디·비밀번호와 비밀번호 찾기
- 개인 이메일을 QA 계정으로 재사용
- 에이전트가 Google 계정을 만들거나 비밀번호를 받는 작업
- 가짜 로그인·가짜 회의·가짜 저장 성공 상태
- 협업, 댓글, 결제, 팀, 공유 링크, 관리자 화면
- 출시 증거가 없는 상태에서 Cloud Run 트래픽을 V2로 전환하는 작업

## 4. 위험과 출시 게이트

| 위험 | 최소 증거 | 통과 기준 | 현재 상태 |
| --- | --- | --- | --- |
| 독립 빌드 | Docker 이미지와 전체 회귀 | 동일 소스 이미지 빌드·테스트 성공 | `PASS` · image `c8b0dc…`, 46/46 |
| 인증 경계 | 비인증·잘못된 provider·폐기 token 테스트 | 서버가 안전한 401로 거부 | 기존 자동 증거 PASS |
| 사용자 소유권 | 다른 실제 Google 사용자 직접 요청 | 목록·상세·오디오가 404 | `BLOCKED` · 전용 계정 없음 |
| 저장·재열람 | 실제 회원 오디오 1회 | Firestore·Storage 저장 후 상세 복원 | `BLOCKED` · 전용 계정 없음 |
| 삭제 | 실제 회의·계정 삭제 뒤 저장소 조회 | 문서·객체·Auth 사용자 잔여 0 | `BLOCKED` · 전용 계정 없음 |
| 공개 UI | Windows Chrome 1440×900·390×844 | privacy·샘플·메뉴에 막힘·넘침 없음 | `PASS` · Chrome 브리지 직접 확인 |
| 회원가입 UI | 회원 기능을 켠 독립 후보의 `/auth` | 가입 안내와 Google 버튼 표시, 개인 계정 접근 없음 | `BLOCKED` · 안전 QA 후보는 회원 기능 꺼짐 |
| 개인정보 고지 | 공개 privacy 화면과 실제 데이터 흐름 | 문의처·수집·저장·외부 AI 전송 설명 일치 | `PASS` · 공개 화면 직접 확인 |
| A6 외부 처리 | 공급자의 보관·학습·국가·재위탁 근거 | 회원 전사문 공개 전송을 설명할 근거 확보 | `BLOCKED` |
| 배포·복구 | 후보 commit·runtime·기존 V1 | 후보 검증 성공, V1 유지·rollback 가능 | `BLOCKED` · V1 유지 |

필수 행에 `FAIL` 또는 `BLOCKED`가 있으면 V2.1을 공개 배포하지 않는다. 기존 V1
트래픽은 그대로 유지한다.

## 5. 실행 순서

1. 문의처와 개인 계정 QA 금지 문구를 코드·문서·테스트에 반영한다.
2. Docker 빌드, 전체 회귀, `pip check`, `pip-audit`, 문법과 diff 검사를 실행한다.
3. `wsl-local-chrome-bridge`로 공개 `/samples`, `/privacy`와 모바일 메뉴를
   읽기 전용 검증한다. 회원 기능 `false` 후보의 `/auth`는 샘플로 복귀하고 준비 중
   안내를 표시하는 것이 기대 동작이다. 회원 기능을 켠 `/auth`는 전용 QA 계정이
   준비된 별도 후보에서만 확인한다.
4. 전용 Google QA 계정이 없으므로 로그인·업로드·삭제·탈퇴는 수행하지 않고
   `BLOCKED`로 닫는다.
5. RELEASE_CANDIDATE 게이트가 막힌 동안 push·PR·main 병합·Cloud Run 트래픽
   전환을 하지 않는다.

## 6. 브라우저 QA 규칙

- Windows Chrome 브리지의 실제 반환 상태를 그대로 기록한다.
- 브리지가 `FAILED` 또는 `BLOCKED`면 성공으로 바꾸지 않는다.
- 공개 화면 fallback은 읽기 전용 격리 브라우저만 허용한다.
- 로그인, 계정 전환, 파일 업로드, 회의·계정 삭제는 fallback으로 수행하지 않는다.
- 스크린샷에는 개인 이메일, token, cookie, Cloud Console을 포함하지 않는다.

## 7. 종료 기준

이번 작업 루프는 다음 두 조건에서 종료한다.

- 코드·자동 검사·공개 브라우저 QA가 끝나고 개인 계정 없이 확인할 수 있는 행이
  모두 `PASS`, `FAIL`, `BLOCKED`, `N/A` 중 하나로 닫힘
- 전용 QA 계정이 필요한 회원 흐름과 A6 외부 처리 조건을 출시 차단 항목으로 남겨
  V2.1을 공개했다고 잘못 보고하지 않음

## 8. 이번 실행 증거

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
