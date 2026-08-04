# MinuteMark 인증·개인정보 결정 기록

> 기준일: 2026-08-02
> 성격: 포트폴리오 구현을 위한 실무 판단이며 법률 자문이 아니다.

## 결정

회원별 회의 저장 기능을 유지하는 동안에는 **Firebase Google 로그인을 유지하고,
자체 아이디·비밀번호는 만들지 않는다.** 공개 QA 문서에는 실제 테스트 계정 이메일을
표시하지 않고, MinuteMark의 회의 소유권에는 Firebase UID만 사용한다. 계정 화면에는
현재 로그인한 사용자 본인에게만 자신의 이메일을 표시한다.

개인정보처리방침의 주된 복잡성은 로그인보다 회의 음성·전사문·분석 결과의 저장과
A6API 전송에서 생긴다. 자체 아이디·비밀번호로 바꿔도 이 고지는 사라지지 않는다.

## 왜 자체 아이디·비밀번호가 더 단순하지 않은가

- 비밀번호는 복호화 가능한 암호화가 아니라 검증된 느린 해시로 저장해야 한다.
  OWASP는 비밀번호 복구, 안전한 비교, 변경, 재인증, 계정 존재 여부를 숨기는 오류,
  무차별 대입·credential stuffing 방어를 별도 요구사항으로 다룬다.
  [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- 저장 방식도 한 번 구현하고 끝나지 않는다. salt와 work factor를 적용하고,
  Argon2id·scrypt·bcrypt·PBKDF2 같은 적절한 방식과 향후 해시 업그레이드 경로를
  운영해야 한다.
  [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- 이메일을 받지 않는 자체 계정은 비밀번호를 잊었을 때 안전한 복구 수단이 없다.
  복구용 이메일을 다시 받으면 Google 로그인보다 수집 정보가 줄지 않으면서
  비밀번호 보안 책임까지 추가된다.

## 개인정보처리방침은 인증 방식을 바꿔도 필요하다

개인정보 보호법은 다른 정보와 쉽게 결합해 개인을 알아볼 수 있는 정보도 개인정보로
본다. 사용자 아이디가 회의 음성·전사문·접속 정보와 연결되면 단순 문자열만으로
취급하기 어렵다.
[개인정보 보호법 제2조](https://www.law.go.kr/법령/개인정보보호법/제2조)

개인정보처리자는 처리 목적, 보유 기간, 파기, 위탁, 이용자 권리, 담당 연락처 등을
처리방침으로 정하고 공개해야 한다. 따라서 자체 아이디로 바꾸더라도 MinuteMark의
음성·전사문·분석 결과·외부 AI 전송 고지는 유지해야 한다.
[개인정보 보호법 제30조](https://www.law.go.kr/법령/개인정보보호법/제30조)

## Google 로그인에서 최소화할 것

Firebase 사용자 레코드는 UID와 기본 프로필 정보인 이메일·이름·사진 URL 등을 가질
수 있고, 외부 로그인 제공자가 제공한 정보로 채워질 수 있다.
[Firebase 사용자 공식 문서](https://firebase.google.com/docs/auth/users)

MinuteMark에서는 다음처럼 범위를 줄인다.

1. Google 비밀번호와 Google API access token을 서버에 저장하지 않는다.
2. 회의 문서와 Storage 경로에는 Firebase UID만 소유권 키로 사용한다.
3. 이메일·이름·사진을 회의 문서, 앱 로그, 공개 QA 문서에 복제하지 않는다.
4. 계정 화면의 이메일은 로그인한 본인에게만 표시한다.
5. 탈퇴하면 Firebase 사용자와 그 UID 아래 회의 문서·오디오를 함께 삭제한다.

Firebase Authentication 자체에는 기본 이메일이 남으므로 처리방침에는 이를 숨기지
않고 `로그인과 계정 식별` 목적으로 처리한다고 짧게 명시한다.

## 선택지 비교

| 방식 | 개인정보처리방침 | 보안·운영 책임 | MinuteMark 적합성 |
| --- | --- | --- | --- |
| 계정 없는 공개 데모 | 가장 단순 | 저장·소유권 기능 없음 | 공개 샘플에 적합 |
| Firebase Google 로그인 | 필요 | Google/Firebase 처리 고지, UID 기반 권한 검증 | **회원 저장 기능에 권장** |
| 자체 아이디·비밀번호 | 여전히 필요 | 해시·복구·세션·공격 방어·유출 대응 추가 | 포트폴리오에 과함 |

## Windows Chrome 확인 증거

`wsl-local-chrome-bridge` 작업 `019fc1c5-3f68-71e0-b9c4-ddd0ef693e35`에서
OWASP Authentication, OWASP Password Storage, Firebase Google Sign-in, Firebase
Users, 국가법령정보센터 개인정보 보호법 제30조를 공개 새 탭으로 확인했다. 로그인과
폼 제출은 하지 않았고 브리지 판정은 `SUCCESS`였다.

## 최종 권고

Google 로그인을 유지하되 **실제 QA 계정 이메일의 공개 기록과 불필요한 이메일
복제는 제거한다.** 개인정보처리방침은 없애지 말고, 현재 실제 데이터 흐름에 맞춰
짧고 정확하게 유지한다. 정식 서비스로 전환할 때는 A6API의 보관·학습·처리
국가·재위탁 조건을 확인한 뒤 관련 문구를 다시 검토한다.
