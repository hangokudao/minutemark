# MinuteMark V2.1 버전업 실행 기록

> 기준일: 2026-08-04
> 작업 브랜치: `codex/redesign-v1` · 검증한 코드 후보 `48a5fda…` ·
> 최초 공개 merge commit `48b76d2cfd85aad3703fdfe4bacf67d8246e8095`
> 현재 공개 main `82114351968a726cef03b67a8cb9b1fb13d68f60` ·
> 맞춤 주소 `https://minutemark.yozm.dev`
> 단계: `RELEASED`
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
> 음성을 글로 옮긴 내용은 결과를 만들기 위해 A6API로 전송됩니다.

결정 질문은 하나다.

> 포트폴리오 범위에서 실제 Google 사용자 두 명의 저장·격리·삭제 흐름을 검증했는가?

현재 답은 `PASS`다. 두 계정의 자격 증명은 소유자만 입력했고, 다른 사용자 직접
주소 차단과 계정 탈퇴 뒤 Firestore·Storage·Firebase Auth 상태까지 확인했다.

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
| 실제 Google 로그인 | 배포 후보에서 Google 계정 선택·로그인 | 계정 선택 뒤 회원 화면 진입 | `PASS` · 계정 A와 B 모두 `/meetings` 회원 화면 진입 확인 |
| 사용자 소유권 | 다른 실제 Google 사용자 직접 요청 | 목록·상세·오디오가 404 | `PASS` · 계정 B 목록에 A 회의가 없고 A 직접 주소는 not-found, 제목·결과 비노출 |
| 저장·재열람 | 실제 회원 오디오 1회 | Firestore·Storage 저장 후 상세 복원 | `PASS` · 실제 분석·저장, 상세·오디오·새로고침·목록과 저장소 확인 |
| 삭제 | 실제 회의·계정 삭제 뒤 저장소 조회 | 문서·객체·Auth 사용자 잔여 0 | `PASS` · 회의 삭제와 B 계정 탈퇴 뒤 문서·객체 0건, Auth 사용자 부재 확인 |
| 공개 UI | Windows Chrome 1440×900·390×844 | privacy·샘플·메뉴에 막힘·넘침 없음 | `PASS` · 배포 후보의 공개 화면·라우팅·모바일 메뉴·가로 넘침 확인 |
| 회원가입 UI | 회원 기능을 켠 독립 후보의 `/auth` | 가입 안내와 Google 버튼 표시 | `PASS` · 실제 0% 후보에서 표시·새로고침 확인 |
| 개인정보 고지 | 공개 privacy 화면과 실제 데이터 흐름 | 문의처·수집·저장·외부 AI 전송 설명 일치 | `PASS` · 확정 문구 계약 테스트와 배포 후보 화면 확인 |
| A6 외부 처리 | 포트폴리오 한계·음성 인식 결과 전송·미확인 조건 고지 | 민감정보 업로드 금지와 확인 범위를 모든 사용자가 알 수 있음 | `PASS` · `/samples`·`/privacy`에서 확정 문구 확인 |
| 배포·복구 | 후보 commit·runtime·기존 V1 | 후보 검증 성공, V1 유지·rollback 가능 | `PASS` · main `48b76d2…`, V2 `minutemark-00012-luh` 100%, V1 복구 절차 유지 |

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

1. 공개 전환 직전에 Cloud Run의 현재 100% 트래픽 revision(배포 버전)과 새 V2 후보 revision(배포 버전)을
   다시 읽어 기록한다. 이번 작업의 기존 정상 revision(배포 버전)은 `minutemark-00007-w6c`다.
2. V2 후보의 `/api/health` commit이 GitHub `main` SHA와 같고 필수 QA가 모두
   PASS일 때만 새 revision(배포 버전)으로 트래픽을 전환한다.
3. 전환 후 health·공개 샘플·로그인 진입 스모크가 실패하면 아래 명령으로 기존
   정상 revision(배포 버전)에 트래픽 100%를 되돌린다.

```sh
gcloud run services update-traffic minutemark \
  --project=minutemark-portfolio \
  --region=asia-northeast3 \
  --to-revisions=minutemark-00007-w6c=100
```

4. 복구 뒤 공개 `/api/health`가 HTTP 200인지 확인하고, Cloud Run 트래픽 조회에서
   기존 revision(배포 버전) 100%를 확인한다. 전환 전 후보가 실패하면 트래픽을 건드리지 않는다.

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

- revision(배포 버전): `minutemark-00010-wix`
- 태그 URL: `https://v2-rc---minutemark-2u3l25uhba-du.a.run.app`
- `/api/health`: 200, commit
  `48a5fda14b5b68436bc6819d0b98185ab1be9729`
- 런타임 계정: `minutemark-runtime@minutemark-portfolio.iam.gserviceaccount.com`
- 기존 공개 V1 `minutemark-00007-w6c`: 트래픽 100% 유지
- Firebase Authentication 승인 도메인에는 후보 태그 도메인이 등록돼 있다.
- 첫 로그인 실패의 원인은 Firebase 승인 도메인이 아니라 Firebase 자동 생성 웹 API
  키의 HTTP referrer 허용 목록에 후보 태그 주소가 없었던 것이었다. 후보 주소
  `https://v2-rc---minutemark-2u3l25uhba-du.a.run.app/*`만 추가하고 기존 referrer
  4개와 API 제한은 그대로 보존했다. key·token 값은 바꾸거나 출력하지 않았다.
- 수정 뒤 Identity Toolkit 프로젝트 설정 요청이 성공했고, Windows Chrome의
  `/auth`에서 Google이 소유한 계정 선택 화면까지 열리는 것을 확인했다.
- 브리지 작업: `019fc337-46d9-74d1-b912-3c586916f2ed`
- 공개 화면: 1440×900과 390×844에서 `/samples`, `/privacy`, `/auth`를 확인했다.
  확정 경고·공개 메뉴·라우팅·가로 넘침 없음은 PASS다. 캡처는 브리지 내부 증거만
  있으며 로컬 스크린샷 경로는 제공되지 않았다.
- 이후 계정 A와 B의 실제 로그인이 완료돼 저장·재열람·회의 삭제, 교차 사용자
  접근 차단과 MinuteMark 계정 탈퇴까지 검증했다.

### 실제 회원 저장·삭제·모바일 증거

- 계정 A의 실제 Google 인증이 완료돼 `/meetings` 빈 목록과 새로고침 복원을
  확인했다. 로그인 뒤 콘솔 error·warn은 0건이었다.
- 공개 데모 오디오 `ko-01-action.wav`를 제목 `V2 출시 QA`로 한 번 제출했다.
  약 30초 뒤 실제 상세로 이동했고 결과·오디오가 표시됐다. 같은 상세를 새로고침한
  뒤 복원되고 `/meetings` 목록에 같은 제목이 표시됐다.
- 해당 회의 `8208b01c87c34c29b67d4d75016c07fa`는 Firestore 문서 1건과 Storage
  오디오 객체가 실제로 존재하는 것을 읽어 확인한 뒤 모바일 390×844에서 열었다.
  제목·결과·오디오·메뉴가 보였고 `scrollWidth=390`, `clientWidth=390`으로 가로
  넘침이 없었다.
- 모바일에서 삭제 확인을 한 번 거쳐 회의를 삭제했다. 목록에서 사라지고 이전 상세는
  `회의를 찾을 수 없습니다.`를 표시했다. 이어 Firestore 문서 0건과 Storage 객체
  0건을 직접 읽어 확인했다.
- 로그아웃 뒤 실제 저장 회의 주소가 `/auth?next=…`로 보호되고 회의 제목·결과가
  노출되지 않는 것을 확인했다.
- 교차 사용자 검증을 위해 계정 A에 `V2 소유권 QA A` 회의
  `ba9f773d6774450d8eb4950ea2573c3d`를 생성했고 Firestore 문서와 Storage 오디오가
  실제 존재함을 확인했다. 계정 B에서는 목록에 이 회의가 없었고 직접 주소도
  `회의를 찾을 수 없습니다.`만 표시해 A 제목·결과를 노출하지 않았다.
- 계정 B로 `V2 탈퇴 QA B` 회의 `1f785cd046a04a1ba4d9f324b72476e9`를 한 번 실제
  분석·저장했다. 상세 결과·오디오와 새로고침 복원을 확인한 뒤 `/account`에서
  `탈퇴` 입력과 Google 재인증으로 MinuteMark 계정을 삭제했다.
- 탈퇴 요청은 `minutemark-00010-wix`에서 `DELETE /api/account` HTTP 204로 끝났다.
  이어 B 회의 Firestore 문서 0건, B 사용자 경로 문서 0건, Storage 회의 객체 0건,
  B 사용자 경로에 삭제되지 않고 남은 객체가 0건임을 직접 읽어 확인했다. Firebase Console의 해당
  프로젝트 Authentication 사용자 목록에서도 삭제한 B 사용자가 존재하지 않았다.
- 탈퇴 뒤 브라우저는 공개 샘플로 돌아갔고, 삭제한 B 회의 주소는 로그인 화면으로
  보호되며 제목·결과·오디오를 노출하지 않았다. 콘솔 error·warn은 0건이었다.
- 교차 사용자 검증용으로 남아 있던 계정 A의 마지막 QA 회의도 삭제했다. 삭제 전
  Firestore 문서 1건과 Storage 오디오 1개를 확인했고, 삭제 뒤 목록 0건·이전 상세
  not-found·Firestore 상세 404·사용자 회의 0건·Storage 사용자 경로 객체 0건을
  확인했다. 계정 A 자체는 유지했다.
- 위 브라우저 캡처는 Chrome 실행 안의 inline 증거만 있으며 로컬 저장 경로는 없다.

### main 병합과 공개 배포

- GitHub 계정 `hangokudao`의 PR #5를 `main`에 병합했다. 최초 공개 시점의 merge
  commit과 원격 `main`은 `48b76d2cfd85aad3703fdfe4bacf67d8246e8095`로 일치했다.
- Cloud Build `3d1afa6a-a0dd-418e-b529-8ae46b61430a`의 Docker build, test,
  image push, 0% deploy 단계가 모두 `SUCCESS`로 끝났다.
- main SHA의 0% revision(배포 버전) `minutemark-00012-luh`에서 `/api/health` 200과 같은 commit,
  `/samples`·`/privacy`·`/auth` 200, `/docs` 404, 보안 헤더를 확인했다.
- 이후 `minutemark-00012-luh`로 공개 트래픽을 100% 전환했다. 실제 공개 주소의
  `/api/health`는 같은 main commit을 반환했다.
- Windows Chrome에서 공개 주소를 1440×900·390×844로 확인했다. 공개 샘플,
  privacy, Google 계정 선택 진입, 모바일 메뉴, 가로 넘침 없음, console error·warn
  0건이 모두 `PASS`였다. 로그인 완료·분석·삭제는 이미 같은 코드의 0% 후보에서
  수행했으므로 공개 전환 뒤에는 비파괴 스모크만 반복했다.
- 복구 대상 V1은 `minutemark-00007-w6c`이며 전환 뒤 복구는 필요하지 않았다.

### 맞춤 주소 Firebase 연결과 후속 QA

- 공개 맞춤 주소 `https://minutemark.yozm.dev`는 Cloudflare Worker가 같은 Cloud Run
  서비스로 요청을 전달한다. 확인 시점의 원본은 main `8211435…`를 실행하는
  `minutemark-00014-cah`이며 공개 트래픽 100%를 처리했다.
- Firebase Authentication 승인 도메인과 Firebase 브라우저 API 키의 허용 주소는
  서로 다른 설정이므로 두 곳에 맞춤 주소를 각각 추가했다. 기존 항목은 5개에서
  6개가 되었고 API 대상 제한 26개는 그대로 보존했다. API 키와 OAuth token 값은
  출력하거나 저장소 문서에 기록하지 않았다.
- Cloudflare 캐시는 `minutemark.yozm.dev` 호스트만 대상으로 갱신했다. 다른
  hostname과 `yozm.dev` 전체 캐시는 건드리지 않았다. 이어 Windows Chrome에서
  강력 새로고침을 수행해 V2 화면을 확인했다.
- Windows Chrome 브리지에서 1440×900으로 실제 Google 로그인을 완료하고, 제목
  `맞춤 주소 QA 2026-08-04`와 공개 데모 오디오를 한 번만 분석·저장했다. 상세의
  결과와 오디오, 새로고침 복원, 목록 표시가 모두 정상이고 console error·warning은
  0건이었다.
- 같은 로그인 상태를 390×844로 확인했다. 회의 목록·새 회의·모바일 메뉴·상세
  결과·오디오가 보였고 가로 넘침이 없었다. 본문 캡처는 Windows Temp의
  `minutemark-custom-qa-desktop-detail.png`,
  `minutemark-custom-qa-mobile-detail.png`에 남겼다.
- 방금 만든 QA 회의만 확인 대화상자를 거쳐 삭제했다. 목록에서 사라지고 이전
  상세에는 `회의를 찾을 수 없습니다.`가 표시됐다. 이어 같은 제목의 Firestore
  문서 0건과 사용자 Storage 경로 객체 0건을 독립적으로 읽어 확인했다. 계정과
  다른 회의는 삭제하지 않았다.
- 보안상 맞춤 주소는 Firebase 로그인을 시작할 수 있는 허용 origin 하나를 늘린다.
  서버 secret이나 저장 데이터가 공개되는 변경은 아니다. 도메인은 이 프로젝트가
  관리하며, 서버의 Firebase ID token 검증과 사용자별 소유권 검사는 그대로다.
  저장소에는 공개 주소와 검증 결과만 기록하고 API 키 값·계정 이메일·UID·cookie·
  token·회의 ID는 기록하지 않는다.

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

- 데스크톱 `/samples`: 당시 공개 샘플 2개, 가로 넘침 없음, 최근 회의·예산 잔액 비노출
  (2026-08-05 이후 공개 샘플은 10개로 확장 — 아래 추가 기록)
- 데스크톱·모바일 `/privacy`: 담당 명칭과 `hangokudao@gmail.com` 표시
- 모바일 `/samples`: 390/390, 새 회의·메뉴 표시
- 모바일 메뉴: 공개 샘플·privacy·GitHub만 표시, 회원 전용 항목 비노출
- 콘솔 error·warn: 0
- 네트워크 워터폴은 Chrome 점검 API가 제공하지 않아 `BLOCKED`
- Google 로그인, 계정 전환, 샘플 분석, 업로드, 삭제는 수행하지 않음

## 9.1 공개 샘플 10개 확장 (2026-08-05)

MM-PUBLIC-AUDIT 선정 결과에 따라 공개 한국어 샘플을 정확히 10개로 맞췄다.

- 유지: `ko-01-action.wav`, `ko-02-decision.wav`
- 추가: `kmsav-01/03/04/05/06/07/08/10` (60초 · 16 kHz mono · CC BY 원본)
- 제외(번들 비포함): `kmsav-02`, `kmsav-09`
- 메타데이터: `app.py` `SAMPLES` 10개, 출처·저작자·라이선스·가공 표시
- UI: 샘플 카드 길이는 API `duration_seconds`를 표시(하드코드 34초 제거)

### 증거 구분

| 구분 | 대상 | 환경 | 상태 |
|---|---|---|---|
| 기존 라이브 증거 | `ko-01`, `ko-02` | 공개 Cloud Run 분석·POST 200 | 유지(재실행 아님) |
| 신규 로컬 의미 게이트 | 추가 8 WAV | 로컬 Docker · whisper small + A6 ×1 | 8/8 PASS · 외부 호출 8 |

### 신규 로컬 의미 게이트 8행 (sanitized, 시크릿 없음)

| ID | STT 구간 | 한글 | 결정 | 할 일 | grounding | 예상 비용(USD) |
|---|---:|---:|---:|---:|---|---:|
| kmsav-01 | 10 | 278 | 0 | 0 | valid | 0.00002768 |
| kmsav-03 | 14 | 311 | 0 | 0 | valid | 0.00002820 |
| kmsav-04 | 22 | 357 | 0 | 0 | valid | 0.00002926 |
| kmsav-05 | 10 | 306 | 0 | 0 | valid | 0.00002775 |
| kmsav-06 | 13 | 288 | 0 | 0 | valid | 0.00002804 |
| kmsav-07 | 14 | 262 | 0 | 0 | valid | 0.00002819 |
| kmsav-08 | 21 | 335 | 0 | 0 | valid | 0.00002921 |
| kmsav-10 | 14 | 321 | 0 | 0 | valid | 0.00002836 |

샘플별 실제 말의 핵심 내용과 제목·설명·제품 분석 결과를 대조한 판정은
[`PUBLIC_AUDIO_SAMPLES.md`](../PUBLIC_AUDIO_SAMPLES.md)의 로컬 의미 게이트 표에
기록했으며 8/8 일치했다.

A6 호출 자격은 **GCP Secret Manager 시크릿 `minutemark-a6-api-key`(버전 1,
프로젝트 `minutemark-portfolio`)** 범주에서 런타임 환경 변수로만 주입했다.
키 원문·파일·커밋·문서 표에는 남기지 않았다.

- 검증: 대상 단위 테스트, sample-tools Docker 전체 회귀 63/63 zero-skip,
  `samples/korean` WAV 개수=10

## 10. V2.1 업데이트 내역

### 추가

- Firebase Google 회원가입·로그인·로그아웃과 최근 재인증 기반 계정 탈퇴
- 사용자별 회의 분석·저장·목록·상세·오디오 재생·삭제
- `/meetings`, `/meetings/new`, `/meetings/{id}`, `/account`, `/privacy` 라우팅
- 모바일 회원 메뉴, 회의 제목, 참여자 확인, 작성 중 이탈 경고
- 공개 한국어 샘플 10개 세트 (`ko-01`·`ko-02` + 선정 KMSAV 8)

### 변경

- A6API 분석 모델을 `gpt-5.6-luna`로 전환
- 포트폴리오 안내를 실제 업무·기밀·민감정보 금지, 참여자 권한, 음성 인식 결과의 A6API 전송
  전송을 함께 알리는 확정 문구로 통일
- 실제 QA 계정 이메일을 공개 문서에서 `테스트 계정 A/B`로 익명화

### 버그 수정

- Firebase 모듈 준비 전에 `/auth` 화면이 사라지던 초기 로딩 문제 수정
- 0% 배포 후보가 Firebase 웹 API 키의 HTTP referrer 허용 목록에서 빠져 Google
  계정 선택 화면이 열리지 않던 설정 문제 수정
- 모바일에서 새 회의·목록에 접근하지 못하거나 데스크톱 최근 목록이 노출되던 문제 수정
- 뒤로가기·앞으로가기·새로고침과 작성 중 이탈 경고가 충돌하던 문제 수정
- 실패한 저장의 Storage 객체와 계정 탈퇴 중 남은 객체를 정리하도록 보완

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
| PR #5 Spec 리뷰 | `PASS` | 보조 Spec 충돌과 DELETE 404 계약 보완, 48/48 재통과 |
| PR #5 Standards/보안 리뷰 | `PASS` | P0/P1 코드 결함 0, 복구 절차 누락 보완 |
| PR #6 출시 문서 Spec·Standards 리뷰 | `PASS` | 상태 충돌·표 열·commit·리뷰 범위 수정 뒤 두 축 재검토, 추가 finding 0건 |
| GitHub PR | `PASS` | PR #5 MERGED, merge commit과 원격 main `48b76d2…` 일치 |
| Cloud Run 0% 후보 | `PASS` | main `48b76d2…`의 `minutemark-00012-luh`, health commit 일치 후 전환 |
| 배포 후보 공개 브라우저 QA | `PASS` | 1440×900·390×844 공개 화면과 Google 계정 선택 경계 |
| 실제 회원 저장·재열람·회의 삭제 | `PASS` | 실제 분석 1회, 상세 복원, 모바일 삭제, Firestore·Storage 0건 |
| 교차 사용자·계정 탈퇴 QA | `PASS` | B에서 A 목록 비노출·직접 주소 not-found, B 탈퇴 뒤 Firestore·Storage·Auth 부재 확인 |
| `main` 병합·공개 V2 | `PASS` | V2 100%, 공개 health·샘플·privacy·auth·데스크톱·모바일 스모크 통과 |
| 맞춤 주소 Firebase 연결·실사용 QA | `PASS` | Firebase 두 허용 목록, 호스트 캐시 갱신, 로그인·저장·모바일·삭제·저장소 0건 |

리뷰에서 발견한 보조 Spec의 QA 정책 충돌은 현재 기준 문서에 맞게 수정했고, 없는 회의와
다른 사용자 회의의 `DELETE`가 동일하게 404를 반환하도록 계약과 구현을 맞췄다.
관련 회귀 48/48을 다시 통과해 Spec 리뷰를 PASS로 닫았다.

비차단 유지보수 항목은 `cloudbuild.yaml`과 `cloudrun-deploy.sh`의 배포 환경변수
중복 한 건이다. 현재 값은 일치한다. 둘 중 하나를 다음에 변경할 때 공통 기준 또는
일치 검사를 먼저 마련하지 않으면 설정이 어긋날 수 있으므로 `BEFORE_NEXT_CHANGE`로
기록한다.

## 12. 2026-08-05 업로드 방어·한국어 회귀 샘플 후속 후보

PR #9는 V2.1의 인증·저장 구조를 바꾸지 않고, 확인된 업로드 경계 두 곳과 한국어
개발·CI 회귀 자료를 보강한다. 기존 48/48 기록은 최초 V2.1 출시 당시의 역사적
증거이며, 아래 결과가 이번 후속 후보의 정본이다.

### 범위와 설계 결정

- 길이를 확인할 수 없거나 0 이하·NaN·무한대인 음원은 quota 예약, 음성 텍스트
  변환(STT), A6 분석 호출 전에 거부한다.
- `Content-Length`가 없는 chunked multipart 요청도 실제 ASGI body를 누적해 제한하고,
  초과하면 전체 form 파싱이 끝나기 전에 413을 반환한다.
- 성공·실패 경로에서 multipart form, 업로드 임시 파일과 분석 임시 파일을 닫고
  삭제한다. 정상 업로드와 정상 chunked 요청의 기존 동작은 유지한다.
- 한국어 샘플 10개는 manifest와 검증 도구만 Git에 넣는다. 음원 바이너리는
  `samples/korean-regression/`에 로컬로 보관하고 Git에서 제외한다.
- `--check-only`는 10개 모두에 기준 SHA-256이 있어야 실행되며, 형식·45~75초 길이·
  16 kHz mono PCM·신호·해시를 네트워크 없이 확인한다.

### 데이터·보안 영향과 검증

- 새 개인정보나 운영 저장소는 추가하지 않는다. 샘플 출처·라이선스·구간·해시만
  manifest에 기록한다.
- PR #8 병합 직후 Docker 전체 회귀 48/48, 보안 통합 뒤 52/52, 샘플 통합 뒤
  59/59, 리뷰 수정 뒤 최종 전체 회귀 60/60을 통과했다.
- 실제 로컬 음원 10개는 최종 검증 도구로 형식·길이·신호·SHA-256 10/10을 통과했고,
  음원 바이너리가 Git에 추적되지 않음을 확인했다.
- PR #9 Spec 리뷰에서 `--check-only`의 빈 SHA-256 허용 1건을 발견해 실패 처리와
  회귀 테스트를 추가했다. Standards/보안 리뷰는 애플리케이션 보안 P0~P3와 코드
  스멜을 발견하지 않았고, 이 활성 출시 기록 누락을 차단 항목으로 지적해 보완했다.

### 배포·복구와 남은 문제

- PR #9에는 배포와 트래픽 변경이 포함되지 않는다. 병합 뒤 배포가 필요하면 별도
  승인을 받고, 배포 실패 시 PR #9 merge commit을 되돌려 이전 `main`으로 복구한다.
- 호출 quota의 추가 보강과 외부 음성 인식 기반 의미 품질 평가는 backlog로 남긴다.
  두 항목은 이번 PR의 병합을 막지 않는다.
