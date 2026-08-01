# Cloudflare 프록시

`minutemark.yozm.dev`의 모든 요청을 기존 Google Cloud Run 원본으로
스트리밍하는 Cloudflare Worker입니다. 루트 `yozm.dev`에는 연결하지 않습니다.

- Cloudflare 계정: `Hangokudao@gmail.com's Account`
- Worker: `minutemark-proxy`
- Custom Domain: `minutemark.yozm.dev`
- 원본: `minutemark-2u3l25uhba-du.a.run.app`

Cloudflare 인증이 끝난 환경에서 이 디렉터리의 설정을 배포합니다.

```sh
cd cloudflare
npx wrangler deploy
```

배포 후 다음 주소로 연결 상태를 확인합니다.

```sh
curl https://minutemark.yozm.dev/api/health
```
