# MinuteMark V2 릴리스 QA 증거

> 실행일: 2026-08-02
> 후보: `codex/redesign-v1` 로컬 RC
> 판정: 공개 게스트 화면 PASS, 회원 실사용 흐름은 미검증, 전체 릴리스 BLOCKED

Windows Chrome 브리지는 작업 `019fc0b4-5517-7b92-a5a7-153cbf9ed593`에서
Chrome 제어 연결이 timeout 되어 `BLOCKED`로 끝났다. timeout을 PASS로 바꾸지
않았다. 공개·읽기 전용 화면만 격리 Playwright와 `/usr/bin/google-chrome`으로
재검증했다. 회원 데이터 변경 흐름에는 이 fallback을 사용하지 않았다.

## 자동·HTTP 검증

| 항목 | 실제 결과 | 판정 |
| --- | --- | --- |
| 최종 Docker 이미지 빌드 | `minutemark-v2-rc`, image ID `ec5e3893a772` | PASS |
| 전체 회귀 | 최종 이미지에서 43/43 | PASS |
| Python 패키지 호환성 | `pip check`: broken requirement 0 | PASS |
| 알려진 의존성 취약점 | `pip-audit`: known vulnerability 0 | PASS |
| 런타임 사용자 | Docker `Config.User=minutemark` | PASS |
| API 문서 비공개 | `GET /docs` → 404 | PASS |
| 비인증 회원 API | `GET /api/meetings` → 401, `no-store` | PASS |
| 보안 헤더 | CSP, HSTS, `X-Frame-Options: DENY`, `nosniff`, `no-referrer` | PASS |
| Firestore 브라우저 접근 | 운영 release `cloud.firestore`가 `allow read, write: if false` | PASS |
| 회의 Storage | 서울 리전, PAP enforced, UBLA true, soft delete 0, versioning 없음 | PASS |

## 실제 사용자 흐름 A–M

`PASS`는 기대 결과와 실제 결과를 같은 대상에서 확인한 경우에만 쓴다. 아래
스크린샷은 로컬 V2 RC의 게스트 화면 증거이며 회원 로그인·저장 증거가 아니다.

| 항목 | 사용 URL | 화면 크기 | 수행한 행동 | 기대 결과 | 실제 결과 | HTTP·저장소 상태 | 스크린샷 경로 | 판정 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 공개 샘플·개인정보처리방침 | `http://127.0.0.1:6993/samples`, `/privacy` | 1440×900 | 샘플 2개 노출, privacy 열기·닫기 | 비로그인 접근, 실제 샘플 결과 확인 | 목록·privacy·복귀는 확인. 새 A6 token 부재로 V2 샘플 분석 결과 실행은 미수행 | 화면 200, 요청 실패 0 | `/tmp/minutemark-v2-desktop.png` | 미검증 |
| B. 실제 Google 로그인 | 로컬 `/auth` 예정 | 1440×900 | Windows Chrome 연결 시도 | Google 로그인 완료 | 브리지 timeout 전 페이지 조작 불가 | 인증 HTTP 미수집 | 없음 | 미검증 |
| C. 제목·참여자 고지 | 로컬 `/meetings/new` 예정 | 1440×900 | 실제 계정 입력 예정 | 제목·파일·고지 확인 후만 제출 | 코드·테스트만 확인 | 저장 요청 미수행 | 없음 | 미검증 |
| D. 오디오 분석·저장 | 로컬 `/meetings/new` 예정 | 1440×900 | 실제 오디오 1회 예정 | A6 분석 뒤 Firestore·Storage 저장 | 새 secret과 로그인 QA가 없어 미수행 | Firestore·Storage 변화 없음 | 없음 | 미검증 |
| E. 회의 목록 | 로컬 `/meetings` 예정 | 1440×900 | 저장 결과 확인 예정 | 방금 저장한 회의 표시 | 미수행 | Firestore 읽기 미수행 | 없음 | 미검증 |
| F. 상세·오디오·근거 듣기 | 로컬 `/meetings/{id}` 예정 | 1440×900 | 상세·재생·근거 이동 예정 | 실제 오디오 seek와 전사 강조 | 미수행 | signed URL 미발급 | 없음 | 미검증 |
| G. 상세 새로고침 복원 | 로컬 `/meetings/{id}` 예정 | 1440×900 | 새로고침 예정 | 같은 상세 복원 | 미수행 | 상세 GET 미수행 | 없음 | 미검증 |
| H. 뒤로·앞으로 | 로컬 회원 경로 예정 | 1440×900 | 브라우저 history 조작 예정 | 주소와 화면 동기화 | 공개 `/privacy`→`/samples` 복귀만 확인, 회원 경로는 미수행 | 공개 화면 200 | `/tmp/minutemark-v2-desktop.png` | 미검증 |
| I. 로그아웃 뒤 비노출 | 로컬 `/samples` 예정 | 1440×900 | 회원 상세에서 로그아웃 예정 | 개인 DOM·signed URL 즉시 제거 | 코드 경합 수정·테스트만 확인 | 실제 세션 미수행 | 없음 | 미검증 |
| J. 다른 계정 접근 차단 | 후보 `/meetings/{id}` 예정 | 1440×900 | 실제 계정 2로 계정 1 URL 접근 예정 | 404 | 테스트 계정 2개 세션 없음 | 실제 HTTP 미수집 | 없음 | 미검증 |
| K. 회의 삭제 | 후보 `/meetings/{id}` 예정 | 1440×900 | 확인 모달 뒤 삭제 예정 | Firestore 문서·Storage 객체 모두 0 | 코드·mock 회귀만 통과 | 실제 저장소 변화 미수행 | 없음 | 미검증 |
| L. 계정 탈퇴 | 후보 `/account` 예정 | 1440×900 | `탈퇴` 입력·Google 재인증 예정 | 회의·고아 객체·Auth 사용자 모두 0 | 코드·mock 회귀만 통과 | 실제 Auth·저장소 변화 미수행 | 없음 | 미검증 |
| M. 모바일 회원 흐름 | `http://127.0.0.1:6993/samples`, 회원 경로 예정 | 390×844 | 게스트 메뉴 열기·닫기 | 새 회의·목록·상세·삭제 접근 | 게스트 새 회의·메뉴·privacy는 확인, 회원 흐름은 미수행 | 공개 화면 200, 요청 실패 0 | `/tmp/minutemark-v2-mobile.png` | 미검증 |

## GCP 출시 게이트

- 활성 secret 버전은 `minutemark-a6-api-key` 버전 `1` 하나뿐이다. 값은 읽거나
  출력하지 않았다. A6에서 교체한 token이 들어간 새 버전이라는 증거가 없으므로
  배포 설정의 정확한 버전을 아직 확정할 수 없다.
- `minutemark-runtime@minutemark-portfolio.iam.gserviceaccount.com`에는 해당 secret
  하나의 `roles/secretmanager.secretAccessor`가 부여돼 있다. 기존 compute 계정
  권한은 제거하지 않았다.
- 현재 공개 서비스는 `minutemark-00007-w6c`, 기존 compute 서비스 계정, V1 트래픽
  100%다. V2 배포는 수행하지 않았다.
- A6API 공개 사이트에서 공급자 보관 기간·학습 사용·처리 국가·재위탁 조건을
  확인할 수 있는 정책을 찾지 못했다. 회원 전사문 공개 전송은 법적·운영 확인 전
  출시 차단 상태다.
