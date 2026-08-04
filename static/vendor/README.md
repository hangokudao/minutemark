# Firebase Auth 브라우저 모듈

`firebase-auth-12.16.0-patched.js`는 Google의 공식 CDN 파일을 고정한 사본이다.

- 원본: `https://www.gstatic.com/firebasejs/12.16.0/firebase-auth.js`
- 패치 파일 SHA-256: `902cd602e8a78b19f49b5eeea05fcc9313d5b65b2d1ac7bfdb6e27a628960261`
- 라이선스: Firebase JavaScript SDK와 동일한
  [Apache License 2.0](./LICENSE.firebase-js-sdk.txt)

공식 12.16.0 브라우저 모듈의 `_isIframeWebStorageSupported`는 지원 여부가 정상
응답돼도 곧바로 `auth/internal-error` 예외를 발생시킨다. 이 사본은 해당 분기에서 빠진
조건 처리를 한 군데만 복구한다. 다른 코드는 바꾸지 않았다.

업스트림에서 수정된 버전이 나오면 이 사본을 제거하고 공식 CDN import로 되돌린다.
