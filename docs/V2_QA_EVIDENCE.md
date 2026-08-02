# MinuteMark V2 릴리스 QA 증거

> 실행일: 2026-08-02
> 후보: `codex/redesign-v1` 로컬 RC
> 판정: 공개 화면·브라우저 OAuth·입력 경계 확인, 백엔드 회원 통합 FAIL, 전체 릴리스 BLOCKED

Windows Chrome 브리지는 작업 `019fc0b4-5517-7b92-a5a7-153cbf9ed593`에서 Chrome
제어 연결이 timeout 되어 `BLOCKED`로 끝났다. timeout을 PASS로 바꾸지 않았다.
공개 화면은 격리 Playwright와 `/usr/bin/google-chrome`으로 재검증했고, 실제
Google 로그인은 같은 Windows Chrome을 CDP Playwright로 제한해 검증했다. 이
fallback은 `myhanbro@gmail.com` 계정 선택과 동의, 입력 경계, 모바일 메뉴,
로그아웃에만 사용했다. 저장 결과를 만들거나 성공 상태를 주입하지 않았다.

## 자동·HTTP 검증

| 항목 | 실제 결과 | 판정 |
| --- | --- | --- |
| 최종 Docker 이미지 빌드 | `minutemark-v2-rc`, image ID `sha256:ba6c642dd4f74d77f2f9362140222dfa915ebd9ba94712e0beb549a5d6a2bcf5` | PASS |
| 전체 회귀 | 최종 이미지에서 45/45 | PASS |
| Python 패키지 호환성 | `pip check`: broken requirement 0 | PASS |
| 알려진 의존성 취약점 | `pip-audit`: known vulnerability 0 | PASS |
| 런타임 사용자 | Docker `Config.User=minutemark` | PASS |
| API 문서 비공개 | `GET /docs` → 404 | PASS |
| 비인증 회원 API | `GET /api/meetings` → 401, `no-store` | PASS |
| 보안 헤더 | CSP, HSTS, COOP `same-origin-allow-popups`, `X-Frame-Options: DENY`, `nosniff`, `no-referrer` | PASS |
| Firestore 브라우저 접근 | 운영 release `cloud.firestore`가 `allow read, write: if false` | PASS |
| 회의 Storage | 서울 리전, PAP enforced, UBLA true, soft delete 0, versioning 없음 | PASS |

## 실제 사용자 흐름 A–M

`PASS`는 기대 결과와 실제 결과를 같은 대상에서 확인한 경우에만 쓴다. 아래
스크린샷은 로컬 V2 RC의 화면 증거다. Windows 경로의 파일은 실제 로그인 세션,
`/tmp` 경로의 파일은 격리 게스트 세션에서 만들었다. 저장 증거는 없다.

| 항목 | 사용 URL | 화면 크기 | 수행한 행동 | 기대 결과 | 실제 결과 | HTTP·저장소 상태 | 스크린샷 경로 | 판정 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 공개 샘플·개인정보처리방침 | `http://127.0.0.1:6993/samples`, `/privacy`; 일회용 V2 RC `/api/analyze-sample/action` | 1440×900 | 샘플 2개 노출, privacy 열기·닫기, 실제 V2 샘플 분석 | 비로그인 접근, 실제 샘플 결과 확인 | 목록·privacy·복귀 확인. 실제 V2 분석은 Luna·grounding true였으나 결과 화면 클릭 증거는 미수집 | 화면 200, 분석 POST 200, 요청 실패 0 | `/tmp/minutemark-v2-desktop.png` | 미검증 |
| B. 실제 Google 로그인 | `http://localhost:8000/auth?next=%2Fmeetings%2Fnew` | 1440×900 | 실제 `myhanbro@gmail.com` 선택·동의 | Google 로그인 후 백엔드 회원 API까지 인증 | 브라우저 OAuth·로그아웃·재로그인은 성공했지만 백엔드 통합은 로컬 ADC 권한 때문에 실패 | Firebase token `aud=minutemark-portfolio`, issuer·provider·시간 정상. `GET /api/meetings` → 401 | `C:\Users\myhan\AppData\Local\Temp\minutemark-v2-windows-signed-in.png` | FAIL |
| C. 제목·참여자 고지 | `http://localhost:8000/meetings/new` | 1440×900 | 제목 입력, 실제 `ko-01-action.wav` 선택, 고지 확인, 이탈 취소·확인 | 세 항목 뒤 저장 버튼 활성화, 파일 선택 시 이탈 경고 | 버튼 활성화, 동일 경고 2회, 취소 시 화면 유지·확인 시 `/samples` 이동 | 분석·저장 POST 없음 | `C:\Users\myhan\AppData\Local\Temp\minutemark-v2-windows-meeting-draft.png` | PASS |
| D. 오디오 분석·저장 | `http://localhost:8000/meetings/new` | 1440×900 | 실제 파일 선택까지만 수행 | A6 분석 뒤 Firestore·Storage 저장 | 로컬 ADC에 runtime `signBlob` 권한이 없어 저장 성공을 만들지 않음. 별도 일회용 V2 공개 샘플 분석만 Luna·grounding true | 회원 POST 미수행, Firestore·Storage 변화 없음 | 입력 화면은 C와 같음 | 미검증 |
| E. 회의 목록 | `http://localhost:8000/meetings` | 1440×900 | 로그인 뒤 목록·새로고침 요청 | 실제 저장 회의 표시 | 화면 진입·새로고침은 됐지만 로컬 ADC가 token 폐기 확인용 `firebaseauth.users.get`을 수행하지 못해 오류 상태 표시 | `GET /api/meetings` → 401, `PermissionDeniedError`; 운영 runtime 역할에는 해당 권한 있음 | `C:\Users\myhan\AppData\Local\Temp\minutemark-v2-windows-meetings.png` | FAIL |
| F. 상세·오디오·근거 듣기 | 로컬 `/meetings/{id}` 예정 | 1440×900 | 상세·재생·근거 이동 예정 | 실제 오디오 seek와 전사 강조 | 미수행 | signed URL 미발급 | 없음 | 미검증 |
| G. 상세 새로고침 복원 | 로컬 `/meetings/{id}` 예정 | 1440×900 | 새로고침 예정 | 같은 상세 복원 | 미수행 | 상세 GET 미수행 | 없음 | 미검증 |
| H. 뒤로·앞으로 | `http://localhost:8000/meetings`, `/account` | 1440×900 | `/meetings` 새로고침, `/account` 이동, 뒤로·앞으로 | 주소와 화면 동기화 | 뒤로 `/meetings`, 앞으로 `/account`, 다시 뒤로 `/meetings` 확인 | 화면 200, 목록 API는 E의 401 | desktop meetings 스크린샷 | PASS |
| I. 로그아웃 뒤 비노출 | `http://localhost:8000/samples`, `/meetings` | 1440×900 | 실제 로그아웃 뒤 개인 경로 직접 진입 | 개인 DOM 제거, 인증 화면으로 전환 | 계정 표기가 `Google로 시작하기`로 바뀌고 빈 목록 DOM은 숨겨졌으며 `/meetings`는 `/auth?next=%2Fmeetings`로 전환됨. 실제 저장 회의·전사·signed URL이 있던 세션의 DOM 제거는 확인하지 못함 | 공개 API 200, 개인 요청은 로그인 화면에서 차단 | `C:\Users\myhan\AppData\Local\Temp\minutemark-v2-windows-signed-out-private-route.png` | 미검증 |
| J. 다른 계정 접근 차단 | 후보 `/meetings/{id}` 예정 | 1440×900 | 실제 계정 2로 계정 1 URL 접근 예정 | 404 | 테스트 계정 2개 세션 없음 | 실제 HTTP 미수집 | 없음 | 미검증 |
| K. 회의 삭제 | 후보 `/meetings/{id}` 예정 | 1440×900 | 확인 모달 뒤 삭제 예정 | Firestore 문서·Storage 객체 모두 0 | 코드·mock 회귀만 통과 | 실제 저장소 변화 미수행 | 없음 | 미검증 |
| L. 계정 탈퇴 | 후보 `/account` 예정 | 1440×900 | `탈퇴` 입력·Google 재인증 예정 | 회의·고아 객체·Auth 사용자 모두 0 | 코드·mock 회귀만 통과 | 실제 Auth·저장소 변화 미수행 | 없음 | 미검증 |
| M. 모바일 회원 흐름 | `http://localhost:8000/meetings`, `/samples` | 390×844 | 실제 로그인 상태 메뉴 확인, CSS 수정 뒤 캐시 비활성화·회원 클래스 회귀 확인 | 새 회의·목록·계정·로그아웃 접근, 데스크톱 최근 목록 비노출, 저장 상세·삭제 접근 | 실제 로그인 때 필수 메뉴가 모두 표시됨. 수정 뒤 최근 목록은 `display:none`·비노출, 가로 넘침 없음. 상세·삭제는 저장 회의가 없어 미수행 | 메뉴·모바일 숨김 규칙 PASS, 목록 API는 E의 401 | `C:\Users\myhan\AppData\Local\Temp\minutemark-v2-windows-mobile-css-fixed.png` | 미검증 |

Google 팝업은 기능적으로 완료됐지만 Chrome 콘솔에 COOP 관련 `window.closed`·
`window.close` 메시지 4건이 남았다. 앱 응답에는
`Cross-Origin-Opener-Policy: same-origin-allow-popups`가 적용돼 있다. 이를 숨기거나
콘솔 0건으로 기록하지 않았다. 같은 세션의 401 한 건은 E의 로컬 ADC 권한 한계다.
CSS 수정 뒤 모바일 재확인은 저장 성공을 가장하지 않도록 실제 로그인 때 확인한 메뉴
증거와 별개로 `body.is-member` 표시 상태만 재현했다. 따라서 M의 전체 판정은 계속
`미검증`이다.

## GCP 출시 게이트

- 활성 secret은 `minutemark-a6-api-key` 버전 `1` 하나다. 사용자는 token은
  바꾸지 않고 A6 라우터만 바꿨다고 확인했다. 버전 `1`을 일회용 V2 RC에만 주입해
  공개 샘플을 실제 분석했고 HTTP 200, `a6api/gpt-5.6-luna`, grounding true를
  확인했다. 값은 화면·로그에 출력하지 않았고 임시 파일과 컨테이너는 즉시
  삭제했다.
- `minutemark-runtime@minutemark-portfolio.iam.gserviceaccount.com`에는 해당 secret
  하나의 `roles/secretmanager.secretAccessor`가 부여돼 있다. 기존 compute 계정
  권한은 제거하지 않았다.
- 운영 runtime 커스텀 역할에는 `firebaseauth.users.get/delete`, Firestore CRUD가,
  별도 정책에는 Storage 객체 권한과 runtime SA self `signBlob`가 있다. 로컬 개인
  ADC에는 이 권한을 추가하지 않았다.
- 현재 공개 서비스는 `minutemark-00007-w6c`, 기존 compute 서비스 계정, V1 트래픽
  100%다. V2 배포는 수행하지 않았다.
- A6API 공개 사이트에서 공급자 보관 기간·학습 사용·처리 국가·재위탁 조건을
  확인할 수 있는 정책을 찾지 못했다. 회원 전사문 공개 전송은 법적·운영 확인 전
  출시 차단 상태다.
