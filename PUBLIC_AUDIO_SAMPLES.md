# 공개 회의 음성 샘플 조사

조사일: 2026-07-30

## AMI Meeting Corpus 10개를 최종 선택

현재 MVP의 결정·할 일 추출 테스트에는
[AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/corpus/)를 사용한다.

- 실제 다자간 회의 100시간과 사람이 직접 글로 옮긴 기록·의사결정 주석을 제공한다.
- 공식 서버에서 로그인 없이 직접 WAV를 받을 수 있다.
- 라이선스는 `CC BY 4.0`이다.
- 의사결정 주석이 명시적인 서로 다른 회의 구간 10개를 골랐다.
- 정확한 회의 ID·시작 시각·길이·기대 결정은
  [`ami-samples.tsv`](./ami-samples.tsv)를 하나의 기준 파일로 사용한다.

오디오는 Git과 Docker 이미지에 넣지 않는다. 아래 명령이 공식
[AMI 다운로드 서버](https://groups.inf.ed.ac.uk/ami/download/)에서 필요한
20–34초만 받아 16 kHz mono WAV로 만든다.

```sh
docker compose run --rm sample-downloader
```

## 2026-07-30 실제 실행 결과

- 실제 모델: `faster-whisper/small` CPU INT8 + A6API `gpt-5.6-luna`
- 판매자 경로 메타데이터: ID `1729`
- 자동 게이트: 10/10 PASS
- 처리 시간: 평균 20.09초, 최대 28.36초
- 모든 결과: 60초 이하, JSON 구조 정상, 근거 구간 ID 유효
- 10개 총 예상 API 비용: `$0.00026196`
- 수동 의사결정 정답 대조: 9/10
- 남은 오류: `ami-02`는 LCD·spinning wheel 내용을 찾았지만 `decision`이 아닌
  `action_item`으로 분류했다.

공개 영어 회의 세트는 기술 경로를 통과했다. 이후 아래 공개된 자연 발화(사람이 실제로
자연스럽게 한 말) 샘플 2개로 제품 품질의 최종 GO 판정도 완료했다.

## 공개 한국어 샘플 10개 (2026-08-05)

제품 공개 샘플은 정확히 10개다. 기존 제품 GO 샘플 2개(`ko-01`, `ko-02`)를
유지하고, MM-PUBLIC-AUDIT에서 선정한 회귀 후보 8개(`kmsav-01/03/04/05/06/07/08/10`)를
`samples/korean/`에 넣었다. 제외된 `kmsav-02`(예능 카톡 말투)·`kmsav-09`(집회·음악
구간)는 공개 번들에 포함하지 않는다.

두 원본 GO 샘플은 조사 시점에 YouTube 메타데이터의
`Creative Commons Attribution license (reuse allowed)`를 확인했다. 추가 8개도
2026-08-05에 동일 라이선스·`public`·한국어를 재확인했다. 전체 영상을 재배포하지
않고 필요한 구간만 16 kHz mono WAV로 변환했다.

| 로컬 파일 | 원본·저작자 | 라이선스·가공 | 사용 구간 | 검증 목적 |
|---|---|---|---:|---|
| `ko-01-action.wav` | [[생방송] 이재명 당대표 주재 더불어민주당 최고위원회의](https://www.youtube.com/watch?v=-WZ18GPkDJg) · 시사발전소 현장LIVE | [YouTube Creative Commons Attribution (CC BY)](https://support.google.com/youtube/answer/2797468) · 34초 발췌, 16 kHz mono WAV 변환 | 2058–2092초 | 구체적인 후속 작업 추출 |
| `ko-02-decision.wav` | [[충북 시사토론 창] 위기의 KTX 오송역, 대응방안은?](https://www.youtube.com/watch?v=Nm0lLy1crg0) · 안녕!MBC충북 | [YouTube Creative Commons Attribution (CC BY)](https://support.google.com/youtube/answer/2797468) · 34초 발췌, 16 kHz mono WAV 변환 | 814–848초 | 이미 합의된 결정 추출 |
| `kmsav-01-07zhNSvDR0A.wav` | [여수MBC토론 - 시사데스크](https://www.youtube.com/watch?v=07zhNSvDR0A) · GS칼텍스 예울마루 | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 211–271초 | 다화자 시사 토론 강건성 |
| `kmsav-03-9g6USDTbGhg.wav` | [[피플인사이드] 장만채 전남도 교육감](https://www.youtube.com/watch?v=9g6USDTbGhg) · KBC 콘텐츠 | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 263–323초 | 공식 인터뷰 ASR |
| `kmsav-04-0e76Mv3YWso.wav` | [치매를 미리 예방할 수 있을까?](https://www.youtube.com/watch?v=0e76Mv3YWso) · 카오스 사이언스 | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 366–426초 | 과학 전문용어 ASR |
| `kmsav-05-3uuLmiV-HNI.wav` | [뇌를 조작해서 포만감을…](https://www.youtube.com/watch?v=3uuLmiV-HNI) · 카오스 사이언스 | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 158–218초 | 연구 설명 질의응답 |
| `kmsav-06-0FzNHep2onE.wav` | [4.15 부정선거 시사대담…](https://www.youtube.com/watch?v=0FzNHep2onE) · 공병호TV | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 548–608초 | 다화자 시사 대담 |
| `kmsav-07-9h7CCmpcirA.wav` | [[자치분권대학 특강] 똑똑, 자치분권입니다 5화](https://www.youtube.com/watch?v=9h7CCmpcirA) · 젬비씨 JEMBC | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 1408–1468초 | 공공 정책 특강 |
| `kmsav-08-9vY0YzdjoMU.wav` | [김만배, 현직기자가…](https://www.youtube.com/watch?v=9vY0YzdjoMU) · 김성수TV 성수대로 | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 579–639초 | 빠른 다화자 토크 |
| `kmsav-10-9bTYC7hkWAI.wav` | [가우스도 놀란 리만의 강의는?](https://www.youtube.com/watch?v=9bTYC7hkWAI) · 카오스 사이언스 | [KMSAV CC BY-NC-SA 4.0](https://github.com/etri/kmsav) + 원본 CC BY · 60초 발췌, 16 kHz mono WAV | 436–496초 | 수학 전문용어 ASR |

위 WAV는 원본 영상의 CC BY 조건을 따르며 루트 `LICENSE`의 MIT 적용 대상이
아니다. 추가 8개는 KMSAV 목록으로 원본을 찾았고, 데이터셋 조건
`CC BY-NC-SA 4.0`과 원본 CC BY·저작자·출처·발췌·포맷 변환 사실을 앱 결과
화면에 함께 표시한다.

### 제품 GO 샘플 2개 — 기존 라이브 Cloud Run 증거

아래는 **이미 공개 배포 경로에서 확인된** 제품 GO 결과다. 이번 10개 확장 작업의
로컬 재분석이 아니다.

- `ko-01-action.wav`: 처리 25.47초, 결정 1개·할 일 1개, 근거 PASS
- `ko-02-decision.wav`: 처리 23.52초, 결정 1개, 근거 PASS
- 총 예상 A6API 비용: `$0.00007391`
- 자동 게이트 2/2, 수동 의미 대조 2/2, Cloud Run POST 200

### 추가 8개 — 2026-08-05 로컬 의미 게이트 (신규 분석)

추가 8개는 **로컬 Docker**에서 faster-whisper/small STT + 제품 A6 추출을 샘플당
1회씩 돌린 결과다(외부 A6 호출 8/8). 라이브 Cloud Run 재검증이 아니다.
결정·할 일 0건은 회의 정답 세트가 아닌 강건성 샘플로 허용한다.

| ID | STT 구간 | 한글 글자 수 | 결정 | 할 일 | grounding | 예상 비용(USD) | 결과 |
|---|---:|---:|---:|---:|---|---:|---|
| kmsav-01 | 10 | 278 | 0 | 0 | valid | 0.00002768 | PASS |
| kmsav-03 | 14 | 311 | 0 | 0 | valid | 0.00002820 | PASS |
| kmsav-04 | 22 | 357 | 0 | 0 | valid | 0.00002926 | PASS |
| kmsav-05 | 10 | 306 | 0 | 0 | valid | 0.00002775 | PASS |
| kmsav-06 | 13 | 288 | 0 | 0 | valid | 0.00002804 | PASS |
| kmsav-07 | 14 | 262 | 0 | 0 | valid | 0.00002819 | PASS |
| kmsav-08 | 21 | 335 | 0 | 0 | valid | 0.00002921 | PASS |
| kmsav-10 | 14 | 321 | 0 | 0 | valid | 0.00002836 | PASS |

실제 음성을 글로 옮긴 내용을 원본 구간의 공개 자막과 대조해 제목·설명과 주제가
맞는지도 확인했다. 아래 핵심 내용은 긴 음성 기록이나 개인정보를 복사하지 않고
검수에 필요한 뜻만 요약한 것이다. 추가 8개는 회의 결정·할 일 정답 세트가 아니므로
제품 분석의 0건 결과가 주제 불일치를 뜻하지 않는다.

| ID | 확인한 실제 말의 핵심 내용 | 제목·설명 대조 | 제품 분석 결과 대조 |
|---|---|---|---|
| kmsav-01 | 지역 문화시설 운영을 논의하는 여러 사람의 지역 시사 토론 | 일치 | 결정·할 일 0건, 근거 검증 PASS |
| kmsav-03 | 학생 프로그램과 교육 정책을 설명하는 공식 인터뷰 | 일치 | 결정·할 일 0건, 근거 검증 PASS |
| kmsav-04 | 치매 예방과 뇌·신체 연구의 흐름을 설명하는 과학 질의응답 | 일치 | 결정·할 일 0건, 근거 검증 PASS |
| kmsav-05 | 포만감 관련 뇌 연구의 현황과 신호를 설명하는 과학 질의응답 | 일치 | 결정·할 일 0건, 근거 검증 PASS |
| kmsav-06 | 의도와 허위 여부 같은 법적 쟁점을 다루는 여러 사람의 시사 대담 | 일치 | 결정·할 일 0건, 근거 검증 PASS |
| kmsav-07 | 지방자치와 지역 간 협력 체계를 설명하는 정책 특강 | 일치 | 결정·할 일 0건, 근거 검증 PASS |
| kmsav-08 | 연금 개혁과 공직자 문제를 빠르게 주고받는 여러 사람의 시사 토크 | 일치 | 결정·할 일 0건, 근거 검증 PASS |
| kmsav-10 | 3차원 기하와 리만의 수학 개념을 설명하는 강연 질의응답 | 일치 | 결정·할 일 0건, 근거 검증 PASS |

## 한국어 보조 후보 KMSAV

ETRI의 [KMSAV](https://github.com/etri/kmsav)는 한국어 다화자 자연 대화이고,
데이터셋 라이선스는 `CC BY-NC-SA 4.0`이다. 공식
[Data Preparation](https://github.com/etri/kmsav/blob/main/HOWTO.md)은
`yt-dlp` 다운로드와 16 kHz WAV 변환 절차를 안내한다.

단, 업무 회의만 모은 자료가 아니라 인터뷰·시사토론·과학 Q&A·그룹 리뷰가
섞여 있다. 아래 10개는 ASR·다화자 강건성 보조 테스트에는 적합하지만,
결정·할 일 정답 세트로는 사용하지 않는다.

## KMSAV 보조 후보 10개

아래 10개는 추가 회귀 후보다. 공식 KMSAV 목록에 등재되어 있고, 조사 시점에 `yt-dlp
--skip-download`로 `public` 및 `Creative Commons Attribution license (reuse
allowed)` 메타데이터를 확인했다. 오디오는 아직 내려받지 않았다.

| # | KMSAV 영상 ID | 유형 | 화자 | 길이 | split | 제목 / 원본 |
|---:|---|---|---:|---:|---|---|
| 1 | `Bj2U6jiGntk` | 시사·직장 | 6 | 9:00 | train | [내 회사는 좋소기업일까?](https://www.youtube.com/watch?v=Bj2U6jiGntk) |
| 2 | `Atcf-qsu4gk` | 경제 | 3 | 3:55 | train | [오피스텔 동향 및 투자](https://www.youtube.com/watch?v=Atcf-qsu4gk) |
| 3 | `GJfrXfaJCJM` | 시사·노동 | 3 | 6:20 | train | [택배노조 노동환경 개선 호소](https://www.youtube.com/watch?v=GJfrXfaJCJM) |
| 4 | `V2Rz2QmWi1w` | 경제 | 3 | 14:14 | valid | [FOMC와 인플레이션 토론](https://www.youtube.com/watch?v=V2Rz2QmWi1w) |
| 5 | `07zhNSvDR0A` | 지역 토론 | 4 | 8:01 | train | [여수MBC 시사데스크 토론](https://www.youtube.com/watch?v=07zhNSvDR0A) |
| 6 | `WleFk3JI3Qw` | 그룹 리뷰 | 6 | 4:36 | test | [립밤 5종 비교](https://www.youtube.com/watch?v=WleFk3JI3Qw) |
| 7 | `-ySffCRdGl8` | 일상 대화 | 6 | 8:12 | train | [남자들의 카톡 말투 유형](https://www.youtube.com/watch?v=-ySffCRdGl8) |
| 8 | `9g6USDTbGhg` | 인터뷰 | 3 | 9:46 | train | [전남도 교육감 인터뷰](https://www.youtube.com/watch?v=9g6USDTbGhg) |
| 9 | `0e76Mv3YWso` | 과학 Q&A | 3 | 13:12 | train | [치매를 미리 예방할 수 있을까?](https://www.youtube.com/watch?v=0e76Mv3YWso) |
| 10 | `3uuLmiV-HNI` | 과학 Q&A | 4 | 6:17 | train | [뇌를 조작해 포만감을 느끼게 할 수 있을까?](https://www.youtube.com/watch?v=3uuLmiV-HNI) |

선정 의도:

- 1–5: 업무·경제·공공 토론에 가까워 결정 후보 추출을 확인하기 좋다.
- 6–8: 빠른 말투, 농담, 인터뷰 등 일반 대화 강건성을 확인한다.
- 9–10: 전문용어가 포함된 질의응답의 음성 인식 품질을 확인한다.
- `valid`와 `test` 후보를 각각 하나 넣어 한 split에만 치우치지 않았다.

## 이용 조건과 공개 포트폴리오 주의사항

1. KMSAV 데이터셋은 비상업 용도만 허용한다. 유료 서비스, 광고 수익화 또는
   상업적 배포에는 쓰지 않는다.
2. KMSAV와 각 원본 YouTube 영상의 제목·채널·URL을 함께 표기하고, 오디오
   자르기·포맷 변환 사실도 표시한다.
3. 가공물을 재배포하면 `CC BY-NC-SA 4.0`의 동일조건변경허락 의무를 확인한다.
4. 가장 안전한 운영 방식은 원본 오디오를 Git 저장소나 배포 이미지에 넣지 않고,
   로컬 테스트 때만 내려받아 사용하는 것이다. 공개 포트폴리오에는 출처
   manifest와 결과 화면만 남긴다.
5. KMSAV의 공식 HOWTO가 `yt-dlp`를 안내하지만 원본 전달은 YouTube를 거친다.
   영상이 삭제되거나 플랫폼 조건이 바뀌면 재현이 깨질 수 있다.

## 비교한 다른 소스

### AI Hub 회의 데이터 — 도메인은 맞지만 자동화에는 부적합

- [회의 음성](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=132)은
  3,000시간의 한국어 회의·토론·토크 WAV와 음성 기록을 제공하며, 페이지는 원천
  데이터의 저작권 문제가 해결됐다고 설명한다.
- [주요 영역별 회의 음성인식 데이터](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=464)는
  7,000시간의 한국어 WAV+JSON, 다화자 회의·방송·의회·팟캐스트 데이터를
  제공한다.
- 그러나 두 페이지 모두 데이터 신청을 내국인으로 제한하고, 경량 샘플 버튼도
  비로그인 상태에서는 로그인 함수로 연결된다. 따라서 현재 자동 다운로드
  소스로 채택하지 않았다.

### Seoul Corpus — 로그인 없이 받을 수 있지만 회의 자료는 아님

[OpenSLR SLR113](https://www.openslr.org/113/)은 자연스러운 한국어 말투가 담긴 FLAC과
TextGrid 형식의 음성 기록을 로그인 없이 내려받을 수 있고 `CC BY-NC 2.0`이다. 하지만
[원 논문 설명](https://library.nih.go.kr/ncmiklib/elib/kom/articleDtl.do?pk_pb_seq=PB06166598)처럼
40명 각각의 인터뷰형 녹음이며 주 화자만 헤드셋 마이크를 사용했다. 다화자 회의
제품 검증에는 맞지 않아 보조 ASR 자료로만 분류했다.

## 2026-08-04 한국어 개발·CI 회귀 샘플 10개

위 후보 풀에서 정확히 10개를 다시 확인해 공개 상태와
`Creative Commons Attribution license (reuse allowed)` 표시를 확인한 뒤, 각 영상의
60초 구간을 로컬에서 16 kHz mono PCM WAV로 만들었다. 정본은
[`korean-sample-manifest.json`](./korean-sample-manifest.json)이며, 실행 가능한
다운로드·검증기는 [`download-korean-regression.py`](./download-korean-regression.py)다.

```sh
python3 download-korean-regression.py
python3 download-korean-regression.py --check-only
```

실행 시점 검증·로컬 신호 결과는 다음과 같다. 모든 출력은 요청 길이 60초와 실제
45–75초 범위를 통과했고, SHA-256 전체 값은 manifest에 기록했다.

| ID | YouTube 영상 | 시작 | 길이 | RMS | active signal | 결과 |
|---|---|---:|---:|---:|---:|---|
| `kmsav-01` | `07zhNSvDR0A` · GS칼텍스 예울마루 | 211초 | 60.00초 | -17.3 dBFS | 0.85 | PASS |
| `kmsav-02` | `-ySffCRdGl8` · Ripple_S | 216초 | 60.00초 | -17.4 dBFS | 0.91 | PASS |
| `kmsav-03` | `9g6USDTbGhg` · KBC 콘텐츠 | 263초 | 60.00초 | -26.2 dBFS | 0.72 | PASS |
| `kmsav-04` | `0e76Mv3YWso` · 카오스 사이언스 | 366초 | 60.00초 | -25.4 dBFS | 0.73 | PASS |
| `kmsav-05` | `3uuLmiV-HNI` · 카오스 사이언스 | 158초 | 60.00초 | -23.4 dBFS | 0.73 | PASS |
| `kmsav-06` | `0FzNHep2onE` · 공병호TV | 548초 | 60.00초 | -16.1 dBFS | 0.84 | PASS |
| `kmsav-07` | `9h7CCmpcirA` · 젬비씨 JEMBC | 1408초 | 60.00초 | -24.7 dBFS | 0.67 | PASS |
| `kmsav-08` | `9vY0YzdjoMU` · 김성수TV 성수대로 | 579초 | 60.00초 | -23.8 dBFS | 0.66 | PASS |
| `kmsav-09` | `0rj144h8MeE` · 안진걸TV | 712초 | 60.00초 | -22.2 dBFS | 0.86 | PASS |
| `kmsav-10` | `9bTYC7hkWAI` · 카오스 사이언스 | 436초 | 60.00초 | -24.4 dBFS | 0.68 | PASS |

실행 환경에는 `yt-dlp`, `ffmpeg`, `ffprobe`가 필요하다. `--check-only`는 네트워크 없이
기존 로컬 파일의 형식·길이·신호·SHA-256만 다시 확인한다.

미디어는 `samples/korean-regression/` 아래에만 저장하고 Git에는 넣지 않는다. 검증기는
정확한 YouTube ID allowlist, HTTPS 원본 경계, 45–75초 구간, 출력 경로, 임시 파일과
원자적 이름 변경, 다운로드·출력 바이트 상한, `ffprobe` 오디오 형식·길이, SHA-256,
무음이 아닌 신호를 확인한다. YouTube 언어 메타데이터와 로컬 신호는 한국어 음성이
있을 가능성을 확인하는 프록시일 뿐이므로, 외부 음성 인식 없이 의미 품질을 증명했다고
표현하지 않으며 manifest의 `NOT_PROVEN_WITHOUT_STT` 게이트를 유지한다.

KMSAV 데이터셋의 `CC BY-NC-SA 4.0` 조건과 각 원본 영상의 CC BY 조건을 함께 따른다.
따라서 이 샘플은 비상업적 로컬 회귀 검증에만 사용하고, 공개·상업 배포 전에 동일조건
변경허락과 원본 저작자 표시 의무를 다시 확인한다.

## 닫힌 게이트와 보류 작업

사람이 실제로 자연스럽게 말한 한국어 샘플 2개로 Day 1 게이트는 GO로 마무리했다.
개발·CI 회귀 샘플 10개는 위 manifest와 검증기로 로컬에서 수집·검증한다. 외부 음성
인식 기반 의미 품질 평가는 별도 승인 없이는 수행하지 않는다.
