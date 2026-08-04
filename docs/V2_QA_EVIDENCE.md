# MinuteMark V2 릴리스 QA 증거

> 이 문서의 A–M 표는 2026-08-02 로컬 RC 실행 기록이다. 최신 출시 판단은
> [`V2.1 버전업 실행 기록`](./V2_1_RELEASE_PLAN.md)을 정본으로 사용한다.

> 실행일: 2026-08-02
> 후보: `codex/redesign-v1` 로컬 RC
> 판정: 공개 화면·브라우저 OAuth·입력 경계 확인, 백엔드 회원 통합 FAIL, 전체 릴리스 BLOCKED

Windows Chrome 브리지는 작업 `019fc0b4-5517-7b92-a5a7-153cbf9ed593`에서 Chrome
제어 연결이 timeout 되어 `BLOCKED`로 끝났다. timeout을 PASS로 바꾸지 않았다.
공개 화면은 격리 Playwright와 `/usr/bin/google-chrome`으로 재검증했고, 실제
Google 로그인은 같은 Windows Chrome을 CDP Playwright로 제한해 검증했다. 이
fallback은 당시 개인 Google 계정 선택과 동의, 입력 경계, 모바일 메뉴,
로그아웃에만 사용했다. 저장 결과를 만들거나 성공 상태를 주입하지 않았다.

## 2026-08-04 배포 후보 추가 증거

| 항목 | 사용 URL·화면 | 실제 결과 | 저장소·HTTP 증거 | 스크린샷 | 판정 |
| --- | --- | --- | --- | --- | --- |
| 후보 일치 | `https://v2-rc---minutemark-2u3l25uhba-du.a.run.app/api/health` | 후보 `minutemark-00010-wix`가 branch head와 같은 commit으로 응답 | HTTP 200, commit `48a5fda14b5b68436bc6819d0b98185ab1be9729`, 트래픽 0%; V1 `minutemark-00007-w6c` 100% | 없음 | PASS |
| 공개 데스크톱·모바일 | 후보 `/samples`, `/privacy`, `/auth`; 1440×900·390×844 | 확정 포트폴리오 경고, 공개 메뉴, privacy, 새로고침·뒤로·앞으로, 가로 넘침 없음을 확인 | 화면 응답 정상. Chrome 점검 표면이 실패 요청 목록을 제공하지 않아 네트워크 워터폴은 미수집 | Windows Chrome 브리지 내부 캡처, 로컬 경로 없음 | PASS |
| Google 로그인 경계 | 후보 `/auth`; 1440×900 | Firebase 웹 API 키에 후보 referrer를 추가한 뒤 Google 소유 계정 선택 화면이 열림 | 수정 전 Identity Toolkit 403 `API_KEY_HTTP_REFERRER_BLOCKED`; 수정 뒤 프로젝트 설정 응답 성공 | Windows Chrome 브리지 내부 캡처, 로컬 경로 없음 | PASS |
| 실제 회원 로그인·저장 | 후보 `/meetings/new` → `/meetings/{id}` → `/meetings`; 1440×900 | 계정 A 로그인, 실제 데모 오디오 1회 분석·저장, 상세·오디오·새로고침·목록 복원 | Firestore 문서 1건과 Storage 오디오 존재 확인 | Chrome inline 캡처, 로컬 경로 없음 | PASS |
| 모바일 상세·회의 삭제 | 후보 `/meetings/{id}`; 390×844 | 제목·결과·오디오·메뉴와 overflow 없음 확인 뒤 삭제 확인 1회 | 삭제 전 문서·오디오 존재, 삭제 후 Firestore 0건·Storage 0건 | Chrome inline 캡처, 로컬 경로 없음 | PASS |
| 로그아웃 뒤 비노출 | 후보의 실제 저장 회의 주소 | 앱 로그아웃 뒤 이전 상세 주소 직접 진입 | `/auth?next=…`로 보호되고 계정 A 회의 제목·결과 비노출 | 없음 | PASS |
| 교차 사용자 접근 차단 | 계정 A 회의 `ba9f773d6774450d8eb4950ea2573c3d`; 1440×900 | 계정 B 목록과 A 직접 주소 접근 | B 목록에 A 제목 없음, 직접 주소 not-found, A 제목·결과 비노출 | Chrome 표면에서 HTTP 상태 미제공; 서버 소유권 UI 결과 확인 | 첨부·Chrome inline 캡처, 저장 경로 없음 | PASS |
| 계정 B 분석·복원 | 후보 `/meetings/new` → `/meetings/1f785cd046a04a1ba4d9f324b72476e9`; 1440×900 | 실제 데모 오디오 1회 분석·저장, 상세·오디오·새로고침 | 실제 결과·오디오 표시와 동일 상세 복원 | 저장 전 Firestore 문서 1건·Storage 오디오 1개 확인 | Chrome inline 캡처, 저장 경로 없음 | PASS |
| 계정 탈퇴 | 후보 `/account` → `/samples`; 1440×900 | `탈퇴` 입력, Google 재인증, MinuteMark B 계정 삭제 | 공개 샘플·로그아웃 UI 복귀, 삭제 회의 주소 비노출 | `DELETE /api/account` 204; B Firestore 문서·Storage 객체·고아 객체 0, Firebase Auth 사용자 부재 | 사용자 첨부·Chrome inline 캡처, 저장 경로 없음 | PASS |
| QA 데이터 정리 | 후보 `/meetings`와 계정 A의 마지막 QA 회의 상세; 1920×911 | 삭제 전 문서·오디오 존재 확인, 삭제 확인 1회, 목록·이전 상세 재확인 | 목록 0건, 이전 상세 not-found | Firestore 상세 404·사용자 회의 0건, Storage 사용자 경로 객체 0건 | 사용자 첨부·Chrome inline 캡처, 저장 경로 없음 | PASS |
| 최종 공개 V2 | `https://minutemark-2u3l25uhba-du.a.run.app`; 1440×900·390×844 | 공개 샘플 2개·고지·Google 계정 선택 진입·모바일 메뉴·가로 넘침 없음, console 0건 | health 200 commit `48b76d2…`, samples·privacy·auth 200, docs 404; `minutemark-00012-luh` 100% | Chrome inline 캡처, 저장 경로 없음 | PASS |

- 최신 Windows Chrome 브리지 작업은
  `019fc337-46d9-74d1-b912-3c586916f2ed`다.
- Firebase Authentication 승인 도메인과 웹 API 키의 referrer 제한은 서로 다른
  설정이다. 승인 도메인은 이미 있었지만 후보 referrer가 빠져 로그인이 막혔다.
- 기존 referrer 4개와 API 제한은 보존했고 후보 주소 하나만 추가했다. key·token·
  cookie·개인 이메일은 출력하거나 QA 증거에 남기지 않았다.
- 실제 계정 선택·재인증은 소유자가 수행했다. 계정 A의 저장·재열람·회의 삭제와
  계정 B의 교차 사용자 차단·저장·계정 탈퇴를 실제 브라우저에서 수행했다.
  Firestore·Storage는 삭제 뒤 사용자 경로까지 0건을 직접 읽었고 Firebase Console
  Authentication 사용자 목록에서도 삭제한 B 사용자가 존재하지 않음을 확인했다.
- 교차 사용자 검증에 사용한 계정 A의 마지막 QA 회의도 삭제했다. 계정 A는
  유지했으며 Firestore 사용자 회의와 Storage 사용자 경로 객체는 모두 0건이다.
- PR #5 merge commit과 원격 main, 공개 `/api/health` commit이 일치했다. 공개 전환
  뒤 Windows Chrome 브리지의 데스크톱·모바일 비파괴 스모크도 통과했다.

## 2026-08-02 자동·HTTP 검증

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
| B. 실제 Google 로그인 | `http://localhost:8000/auth?next=%2Fmeetings%2Fnew` | 1440×900 | 당시 개인 Google 계정 선택·동의 | Google 로그인 후 백엔드 회원 API까지 인증 | 브라우저 OAuth·로그아웃·재로그인은 성공했지만 백엔드 통합은 로컬 ADC 권한 때문에 실패 | Firebase token `aud=minutemark-portfolio`, issuer·provider·시간 정상. `GET /api/meetings` → 401 | `C:\Users\myhan\AppData\Local\Temp\minutemark-v2-windows-signed-in.png` | FAIL |
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

위 실행 당시에는 개인 Google 계정을 추가 QA에 사용하지 않기로 했으므로 실제
로그인·저장·삭제·탈퇴·교차 사용자 흐름을 반복하지 않고 `BLOCKED`로 기록했다.
이후 변경된 V2.1 QA 계정 정책은
[V2.1 버전업 실행 기록](./V2_1_RELEASE_PLAN.md)을 정본으로 따른다.

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
- 이 절의 원 실행 시점에는 공개 서비스가 `minutemark-00007-w6c`, 기존 compute
  서비스 계정, V1 트래픽 100%였고 V2 배포를 수행하지 않았다. 최신 상태는 위
  2026-08-04 절처럼 V2 `minutemark-00010-wix`가 트래픽 0% 후보로 추가됐으며,
  공개 전환 전까지 V1 트래픽은 100%였다. 최종적으로 main `48b76d2…`의 V2
  `minutemark-00012-luh`가 공개 트래픽 100%를 처리한다.
- A6API 공개 사이트에서 공급자 보관 기간·학습 사용·처리 국가·재위탁 조건을
  확인할 수 있는 정책을 찾지 못했다. 이는 2026-08-02 당시 정식 서비스 기준의
  출시 차단 판단이다. 최신 포트폴리오 후보는 민감정보 업로드 금지와 전사문 전송을
  명시하고, 정식 서비스 전환 전에 공급자 조건을 별도로 확인하는 결정으로 갱신됐다.
