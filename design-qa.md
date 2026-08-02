# MinuteMark redesign QA

## Design Contract

- `JOB`: 공개 샘플 또는 파일을 분석한 사용자가 결정·할 일을 먼저 확인하고, `근거 듣기`로 실제 발화 위치와 전사를 즉시 검증한다. 성공 신호는 오디오 seek, 재생, 해당 전사 강조가 한 번의 조작으로 함께 일어나는 것이다.
- `CONTENT`: 공개 샘플 2개, 사용자 업로드, 처리 중·오류·빈 결정/할 일·분석 완료 상태, 실제 처리 시간·토큰·비용·모델·출처, 길이가 달라지는 전사 구간과 근거 ID를 사용한다.
- `SYSTEM`: 기존 FastAPI + Vanilla JavaScript 진입점과 API 계약, 기존 MinuteMark 로고 마크와 단일 sans-serif 스택을 재사용한다. 새 시각 토큰은 선택 시안의 따뜻한 흰 배경, 짙은 텍스트, 파란 상호작용 색, 얇은 구분선, 낮은 radius를 따른다.
- `PRIMARY`: `/home/han/.codex/generated_images/019fbf1c-43e6-77d3-9499-33514467a025/exec-7e8a07a1-e456-4d5a-b258-ba9748d83e37.png`의 결과 화면. 1487×1058 원본을 1440×1024 구현 화면과 같은 비율로 비교한다.
- `MEDIA`: 번들된 실제 CC BY 한국어 회의 오디오를 브라우저 `<audio>`로 재생한다. 출처·저작자·라이선스는 결과에 표시하며, 로드 실패 시 브라우저 기본 미디어 실패 상태와 기존 재분석 경로를 유지한다.
- `INTERACTION`: `근거 듣기`를 포인터·터치·키보드로 누르면 오디오가 첫 근거 구간으로 이동해 재생되고 관련 전사가 강조·노출된다. 일반 모션에서는 부드럽게 이동하고 `prefers-reduced-motion`에서는 즉시 이동한다. 유효한 근거가 없으면 버튼을 만들지 않는다.
- `DECISIONS`:
  - 관찰: 시안은 왼쪽 결과, 오른쪽 전사, 위쪽 플레이어로 검증 순서를 고정한다. 적용: 완료 화면을 동일한 2열 결과 구조로 재배치한다. 대상: 분석 완료 상태.
  - 관찰: 시안은 카드보다 여백·구분선·타입 위계로 내용을 나눈다. 적용: 중첩 카드와 마케팅 hero를 제거하고 독립 경계에만 surface를 사용한다. 대상: 입력·결과·상태 화면.
  - 관찰: 근거 시간과 전사 강조에만 파란색을 집중한다. 적용: primary action, focus, evidence에만 파란색을 사용한다. 대상: 모든 상태.
  - `ORIGINAL`: 저장 기능이 없는 제품에 가짜 최근 회의 목록을 만들지 않고 실제 섹션 링크만 제공한다.
  - `REMOVED`: 시안의 공유, 휴지통, Pro 플랜, 즐겨찾기, 가짜 회의 기록은 현재 기능이 아니므로 제외한다.
- `NOT-OURS`: 기존 화면의 큰 마케팅 hero, 파란 방사형 배경, 카드 중첩, 영문 kicker 남발은 사용자가 거절한 “Codex스러운” 인상을 강화하므로 새 결과 화면의 기준으로 사용하지 않는다.

## QA status

- Source visual truth: `/home/han/.codex/generated_images/019fbf1c-43e6-77d3-9499-33514467a025/exec-7e8a07a1-e456-4d5a-b258-ba9748d83e37.png`
- Implementation screenshots:
  - `/home/han/.codex/worktrees/7fa6/minutemark/docs/screenshots/minutemark-desktop.png`
  - `/home/han/.codex/worktrees/7fa6/minutemark/docs/screenshots/minutemark-mobile.png`
- Viewports and density:
  - Source: 1487×1058 pixels, normalized to 1440×1024 for comparison.
  - Desktop implementation: 1440×1024 CSS pixels, device scale factor 1, 1440×1024 output pixels.
  - Narrow implementation: 390×844 CSS pixels, device scale factor 1, 390×844 output pixels.
- State: 공개 샘플의 populated result, S5·S6 근거 활성화; initial, delayed loading, safe error도 별도 실행 확인.
- Browser: Windows Chrome에서 initial 화면·샘플 2개·콘솔을 확인했다. 결과 직접 주입은 Chrome 격리 컨텍스트 제한으로 실패해, 격리 headless Chrome fallback에서 같은 로컬 URL과 메모리 POST 응답으로 결과·상호작용·반응형을 검증했다. 실제 A6 POST는 실행하지 않았다.
- Full-view comparison evidence: `/tmp/minutemark-design-comparison.png`에 정규화한 source와 desktop implementation을 같은 크기로 나란히 비교했다.
- Focused comparison evidence:
  - `/tmp/minutemark-comparison-header.png`: 제목, 메타, 메트릭, 오디오 영역.
  - `/tmp/minutemark-comparison-result.png`: 결정·할 일, 근거 컨트롤, 전사 강조 영역.

## Findings

- P0/P1/P2: 없음.
- Fonts and typography: 단일 Pretendard/system sans-serif 스택, 제목의 크기·굵기·행간, 작은 메타의 위계와 실제 한국어 줄바꿈이 source와 같은 역할을 만든다. 텍스트 잘림이나 비의도적 truncation은 없다.
- Spacing and layout rhythm: 276px rail, 결과 제목·메트릭의 공통 기준선, full-width player, 왼쪽 결과/오른쪽 전사 분할과 얇은 구분선이 source의 주요 축과 일치한다. 데스크톱·좁은 화면 모두 가로 overflow가 없다.
- Colors and visual tokens: 따뜻한 흰 canvas, 짙은 잉크, 낮은 대비의 line, 근거와 primary action에만 쓰는 blue, 검증 상태의 green을 source에 맞췄다. 대비를 해치는 장식 gradient나 shadow는 없다.
- Image quality and asset fidelity: source에 사진·일러스트·제품 이미지가 없다. 기존 MinuteMark brand mark를 재사용했고, 가짜 파형이나 임의 아이콘을 만들지 않았다. 실제 CC BY 샘플 오디오는 브라우저의 접근 가능한 native media control로 표시한다.
- Copy and content: 실제 샘플 제목·파일명·출처·저작자·라이선스·처리 시간·토큰·비용·모델·전사·할 일만 사용했다. source의 공유, 휴지통, Pro 플랜, 별표, 가짜 최근 회의는 제외했다.
- Interaction and accessibility: Space 키로 `근거 듣기`를 활성화하면 오디오가 S5 시작 22.76초로 이동해 재생되고 S5·S6가 `aria-current=true`와 함께 강조된다. `prefers-reduced-motion`에서는 즉시 이동한다. 포커스 표시는 유지된다.
- Responsive states: 390×844에서 제목, 메트릭, 실제 오디오 컨트롤, 할 일, 근거 컨트롤, 전사가 단일 열로 유지되고 horizontal overflow가 없다.
- Runtime states: initial 샘플 2개가 활성 상태로 표시되고, delayed loading은 경과 시간과 대상 제목을 보여준다. 502 오류는 안전한 한국어 메시지만 표시하며 내부 경로·키·decoder detail을 노출하지 않는다.
- Console/network: console error 0, failed request 0. QA의 분석 POST 1회는 브라우저 메모리에서 응답했고 서버나 A6로 전달되지 않았다.

## Comparison history

1. 첫 비교에서 결과 화면 위에 입력 화면의 끝부분이 남아 제목·플레이어·분할 영역이 source보다 아래로 밀린 P2를 확인했다.
2. 입력과 결과를 명시적인 view state로 분리하고 sidebar를 276px로 맞췄다. `새 분석으로 돌아가기`, rail의 `음성 선택`/`분석 결과`로 두 상태를 왕복할 수 있게 했다.
3. post-fix evidence는 `/home/han/.codex/worktrees/7fa6/minutemark/docs/screenshots/minutemark-desktop.png`이며, source와의 full/focused comparison에서 추가 P0/P1/P2를 찾지 못했다.

## Accepted deviations

- Source의 custom waveform, timeline pin, 별도 volume/speed 아이콘 대신 실제 파일을 재생하는 browser-native `<audio>`를 유지했다. 가짜 파형이나 코드로 그린 아이콘을 만들지 않고 접근성·실제 동작을 우선한 의도된 차이다.
- 저장 기능이 없는 현재 제품에 source의 최근 회의 목록과 협업 navigation을 만들지 않았다.

## Implementation checklist

- [x] 실제 입력·loading·error·populated result 상태
- [x] desktop/narrow responsive rendering
- [x] pointer·touch·keyboard 가능한 근거 이동과 오디오 seek
- [x] source/implementation full-view 및 focused comparison
- [x] 콘솔·실패 요청·가로 overflow·민감정보 확인

## Follow-up polish

- 없음. custom audio timeline은 별도 기능 범위가 승인될 때만 검토한다.

final result: passed
