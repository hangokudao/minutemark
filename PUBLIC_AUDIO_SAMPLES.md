# 공개 회의 음성 샘플 조사

조사일: 2026-07-30

## 최종 선택: AMI Meeting Corpus 10개

현재 MVP의 결정·할 일 추출 테스트에는
[AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/corpus/)를 사용한다.

- 실제 다자간 회의 100시간과 수동 전사·의사결정 주석을 제공한다.
- 공식 서버에서 로그인 없이 직접 WAV를 받을 수 있다.
- 라이선스는 `CC BY 4.0`이다.
- 의사결정 주석이 명시적인 서로 다른 회의 구간 10개를 골랐다.
- 정확한 회의 ID·시작 시각·길이·기대 결정은
  [`ami-samples.tsv`](./ami-samples.tsv)를 단일 정본으로 사용한다.

오디오는 Git과 Docker 이미지에 넣지 않는다. 아래 명령이 공식
[AMI 다운로드 서버](https://groups.inf.ed.ac.uk/ami/download/)에서 필요한
20–34초만 받아 16 kHz mono WAV로 만든다.

```sh
docker compose run --rm sample-downloader
```

## 2026-07-30 실제 실행 결과

- 실제 모델: `faster-whisper/small` CPU INT8 + A6API `claude-sonnet-5`
- 판매자 경로 메타데이터: ID `1263`
- 자동 게이트: 10/10 PASS
- 처리 시간: 평균 20.09초, 최대 28.36초
- 모든 결과: 60초 이하, JSON 구조 정상, 근거 구간 ID 유효
- 10개 총 예상 API 비용: `$0.00026196`
- 수동 의사결정 정답 대조: 9/10
- 남은 오류: `ami-02`는 LCD·spinning wheel 내용을 찾았지만 `decision`이 아닌
  `action_item`으로 분류했다.

공개 영어 회의 세트는 기술 경로를 통과했다. 이후 아래 공개 한국어 자연 발화
2개로 제품 품질의 최종 GO 판정도 완료했다.

## 한국어 최종 샘플 2개

두 원본은 KMSAV 목록에 등재되어 있으며 조사 시점에 YouTube 메타데이터의
`Creative Commons Attribution license (reuse allowed)`를 확인했다. 전체
영상을 재배포하지 않고 판정에 필요한 구간만 16 kHz mono WAV로 변환했다.

| 로컬 파일 | 원본 | 사용 구간 | 검증 목적 |
|---|---|---:|---|
| `ko-01-action.wav` | [[생방송] 이재명 당대표 주재 더불어민주당 최고위원회의](https://www.youtube.com/watch?v=-WZ18GPkDJg) | 2058–2092초 | 구체적인 후속 작업 추출 |
| `ko-02-decision.wav` | [[충북 시사토론 창] 위기의 KTX 오송역, 대응방안은?](https://www.youtube.com/watch?v=Nm0lLy1crg0) | 814–848초 | 이미 합의된 결정 추출 |

실제 결과:

- `ko-01-action.wav`: 25.47초, 결정 1개·할 일 1개, 근거 PASS
- `ko-02-decision.wav`: 23.52초, 결정 1개, 근거 PASS
- 총 예상 A6API 비용: `$0.00007391`
- 자동 게이트 2/2, 수동 의미 대조 2/2

## 한국어 강건성 보조 후보: KMSAV

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
- 9–10: 전문용어가 포함된 질의응답 전사 품질을 확인한다.
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

### AI Hub 회의 데이터: 도메인은 최적이지만 자동화에 부적합

- [회의 음성](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=132)은
  3,000시간의 한국어 회의·토론·토크 WAV와 전사를 제공하며, 페이지는 원천
  데이터의 저작권 문제가 해결됐다고 설명한다.
- [주요 영역별 회의 음성인식 데이터](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=464)는
  7,000시간의 한국어 WAV+JSON, 다화자 회의·방송·의회·팟캐스트 데이터를
  제공한다.
- 그러나 두 페이지 모두 데이터 신청을 내국인으로 제한하고, 경량 샘플 버튼도
  비로그인 상태에서는 로그인 함수로 연결된다. 따라서 현재 자동 다운로드
  소스로 채택하지 않았다.

### Seoul Corpus: 로그인 없이 받을 수 있지만 회의가 아님

[OpenSLR SLR113](https://www.openslr.org/113/)은 한국어 자발화 FLAC과
TextGrid 전사를 로그인 없이 내려받을 수 있고 `CC BY-NC 2.0`이다. 하지만
[원 논문 설명](https://library.nih.go.kr/ncmiklib/elib/kom/articleDtl.do?pk_pb_seq=PB06166598)처럼
40명 각각의 인터뷰형 녹음이며 주 화자만 헤드셋 마이크를 사용했다. 다화자 회의
제품 검증에는 맞지 않아 보조 ASR 자료로만 분류했다.

## 닫힌 게이트와 보류 작업

한국어 자연 발화 2개로 Day 1 게이트는 GO로 닫았다. KMSAV 추가 후보 10개
다운로드와 별도 ASR 회귀는 현재 웹 MVP를 막지 않는 보류 작업이다.
