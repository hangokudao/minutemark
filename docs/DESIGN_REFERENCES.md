# MinuteMark 디자인 레퍼런스 10선

조사일: 2026-08-02
대상 흐름: `공개 샘플/음성 업로드 → 타임스탬프 전사 → 결정·할 일 → 근거 발화 이동`

> 아래의 기능 설명은 각 서비스의 공식 제품·도움말에서 확인한 사실입니다. “참고할 패턴”과 “주의”는 그 사실을 MinuteMark에 적용한 디자인 판단입니다. “대기업 여부”는 한국 법률상 분류가 아니라, 글로벌 대기업 소유 또는 대형 업무 플랫폼인지에 대한 레퍼런스 선정용 구분입니다.

## 먼저 볼 상위 3개

1. **Notion AI Meeting Notes** — 요약의 인용을 hover하면 전사 조각을 미리 보고, 클릭하면 해당 전사 줄로 이동한다. MinuteMark의 `근거 듣기`를 가장 직접적으로 다듬을 수 있는 레퍼런스다.
2. **Microsoft Teams Recap** — 재생 타임라인의 마커, 전사 패널, AI 요약·후속 작업을 하나의 recap 경험으로 묶는다. 결과 화면의 큰 정보 구조에 가장 유용하다.
3. **Otter.ai Conversation Page** — `Summary / Transcript` 분리와 각 할 일의 `View in transcript` 연결이 MinuteMark의 결과 모델과 거의 같다.

**조합 권고:** Teams처럼 상단에 고정 재생기와 시간축을 두고, Otter처럼 본문을 `회의 결과 / 전사` 두 영역으로 명확히 나눈다. 각 결정·할 일에는 Notion식 작은 근거 칩을 붙여 hover 시 인용문·시간을 미리 보여주고, 클릭 시 재생 위치 이동과 전사 강조를 동시에 실행한다. 첫 화면과 처리 중 화면은 이 결과 구조로 들어가기 위한 짧은 진입 단계로만 유지한다.

## 1. Microsoft — Teams Recap

- **대기업 여부:** 예 — Microsoft의 대형 협업 플랫폼. [공식 Teams Recap 도움말](https://support.microsoft.com/en-US/teams/meetings/recap-in-microsoft-teams)
- **확인된 유사 기능:** 녹화 타임라인 마커를 눌러 해당 시점으로 이동할 수 있고, 전사 기반 AI 요약에서 노트와 후속 작업을 제공한다.
- **참고할 패턴:** `고정 플레이어 + 의미 있는 타임라인 마커`; `AI summary / Transcript`처럼 결과 종류를 짧은 탭으로 구분한다.
- **주의:** 참가자·화면 공유·멘션 등 Teams 전용 마커와 엔터프라이즈 탐색 구조까지 가져오면 1회성 공개 데모가 무거워진다.

## 2. Google — Google Meet “Take notes for me”

- **대기업 여부:** 예 — Google의 대형 회의 플랫폼. [공식 Google Meet 도움말](https://support.google.com/meet/answer/14754931?hl=en)
- **확인된 유사 기능:** 회의 노트를 Google Docs로 자동 정리하며, 요약·결정·다음 단계·상세 섹션을 지원한다. 결정 섹션은 공식 문서상 일부 언어/사용자에 제한될 수 있다.
- **참고할 패턴:** `Summary / Decisions / Next steps / Details`처럼 사용자가 찾는 답을 먼저 보여주는 섹션 순서; 짧은 “요약 먼저” 위계.
- **주의:** Docs·Calendar·이메일로 결과를 분산하는 생태계 흐름은 복제하지 않는다. MinuteMark는 한 화면에서 결과와 근거가 닫혀야 한다.

## 3. Zoom Communications — Zoom Smart Recording

- **대기업 여부:** 예 — 대형 상장 화상회의 플랫폼. [공식 Zoom Smart Recording 도움말](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0061101)
- **확인된 유사 기능:** 녹화를 스마트 챕터로 나누고, 하이라이트·요약·다음 단계를 제공한다. 챕터를 클릭하면 그 타임스탬프부터 재생되며 전사 패널을 함께 관리할 수 있다.
- **참고할 패턴:** 긴 전사를 몇 개의 `시간이 붙은 챕터`로 압축; 플레이어 옆에 현재 구간의 전사를 두는 구성.
- **주의:** 편집·분석·코칭 지표까지 노출하면 결정과 할 일의 우선순위가 약해진다. 챕터는 전사가 긴 경우에만 보조 탐색으로 쓴다.

## 4. Cisco — Webex AI Assistant Meeting Recap

- **대기업 여부:** 예 — Cisco의 대형 협업 플랫폼. [공식 Webex 도움말](https://help.webex.com/default/article/gkzgoe)
- **확인된 유사 기능:** 회의 후 요약에서 주요 결정과 담당자가 있는 할 일을 주제별로 보여주며, `Messages / Summary / Transcript / Recording` 항목으로 바로 이동할 수 있다.
- **참고할 패턴:** 결과 상단의 간결한 `Notes / Action items` 구획; 회의라는 하나의 컨테이너 안에서 기록 종류를 오가는 보조 탐색.
- **주의:** 여러 화면으로 분리된 구조를 그대로 따르면 근거 연결이 숨는다. MinuteMark에서는 결과 카드와 전사를 같은 화면에 유지한다.

## 5. Salesforce — Slack Huddles AI Notes

- **대기업 여부:** 예 — Salesforce가 소유한 대형 협업 플랫폼. [공식 Slack 도움말](https://slack.com/help/articles/31377193680019-Use-AI-to-take-huddle-notes-in-Slack)
- **확인된 유사 기능:** 실시간 대화와 huddle thread 메시지를 바탕으로 핵심 요점과 할 일을 Canvas에 만들고, 전사를 그 Canvas에 함께 넣는다.
- **참고할 패턴:** 결과를 별도 리포트가 아니라 `회의가 발생한 맥락에 붙은 문서`로 보이게 하는 구성; 핵심 요점과 할 일을 먼저 스캔하게 하는 Canvas 위계.
- **주의:** 채널·DM·스레드 같은 Slack 셸은 MinuteMark에 필요 없다. 또 공식 설명상 요약에서 오디오 시점으로 가는 직접 연결은 핵심 패턴이 아니다.

## 6. NAVER Cloud — NAVER WORKS CLOVA Note

- **대기업 여부:** 예 — NAVER 계열의 대형 업무 플랫폼. [공식 CLOVA Note 소개](https://help.worksmobile.com/ko/use-guides/clovanote/overview/) · [노트 생성 도움말](https://help.worksmobile.com/ko/use-guides/clovanote/create/note/)
- **확인된 유사 기능:** 녹음 또는 파일 업로드를 텍스트로 변환하고, 전체 요약·회의 주제·다음 할 일·단락별 주요 내용을 추출한다. 녹음 중 북마크와 메모도 지원한다.
- **참고할 패턴:** 한국어 중심의 짧고 익숙한 결과 라벨; `전체 요약 → 주제 → 다음 할 일 → 단락` 순서와 북마크 기반 중요 구간 표시.
- **주의:** 기업 보안·폴더·공유 관리 UI는 제외한다. “다음 할 일 추천”과 실제로 확정된 할 일을 시각적으로 구분하지 않으면 신뢰가 떨어질 수 있다.

## 7. Notion — AI Meeting Notes

- **대기업 여부:** 대형 독립 SaaS 플랫폼. [공식 Notion 도움말](https://www.notion.com/help/ai-meeting-notes)
- **확인된 유사 기능:** 실시간 녹음뿐 아니라 기존 오디오 업로드도 전사·요약하며, 핵심 요점과 할 일을 만든다. 요약의 인용을 hover하면 전사 조각을 보고 클릭하면 해당 전사 줄로 이동한다.
- **참고할 패턴:** 결과 문장 끝의 작고 일관된 `근거 인용 칩`; hover 미리보기 후 클릭 이동이라는 2단계 확인 경험.
- **주의:** 문서 편집기·템플릿·데이터베이스 기능까지 닮게 만들면 제품 정체성이 흐려진다. MinuteMark의 클릭은 전사 이동뿐 아니라 오디오 seek까지 분명히 보여야 한다.

## 8. Otter.ai — Conversation Page

- **대기업 여부:** 아니오 — AI 회의 기록 전문 서비스. [공식 Otter Conversation Page 도움말](https://help.otter.ai/hc/en-us/articles/5093228433687-Conversation-Page-Overview)
- **확인된 유사 기능:** `Summary / Transcript` 탭에서 자동 요약·할 일·개요와 전사를 제공하며, AI가 만든 할 일의 `View in transcript` 아이콘으로 생성 근거가 된 전사 위치를 연다.
- **참고할 패턴:** 결과와 원문을 나누되 한 번에 전환 가능한 2탭 구조; 각 할 일 우측의 작고 반복 가능한 `전사에서 보기` 액션.
- **주의:** 채팅·댓글·할 일 편집/할당까지 복제하면 범위를 넘는다. 근거가 없는 수동 항목과 AI 근거가 있는 항목을 섞지 않는 원칙만 참고한다.

## 9. Fireflies.ai — Notepad

- **대기업 여부:** 아니오 — AI 회의 기록 전문 서비스. [공식 Fireflies Notepad 도움말](https://guide.fireflies.ai/articles/6653885315-learn-about-the-fireflies-notepad)
- **확인된 유사 기능:** 한 회의 화면에 AI 요약·전체 전사·녹화·할 일을 모으고, `왼쪽 요약 / 오른쪽 전사` 2패널을 제공한다. 재생은 전사와 동기화되고 전사 선택으로 Soundbite를 만들 수 있다.
- **참고할 패턴:** 데스크톱 결과 화면의 명확한 2열 비대칭 레이아웃; 현재 재생 중인 전사 문장을 패널 안에서 강조한다.
- **주의:** AI 필터·CRM 연동·분석 아이콘이 많아 그대로 따르면 도구 모음이 주인공이 된다. MinuteMark에서는 재생·근거 이동 외 조작을 최소화한다.

## 10. Granola — AI-enhanced Notes

- **대기업 여부:** 아니오 — AI 회의 노트 전문 서비스. [공식 Granola 도움말](https://help.granola.ai/article/ai-enhanced-notes)
- **확인된 유사 기능:** 전사·사용자 메모·일정 정보를 합쳐 구조화된 노트를 만들고, 각 노트 옆 돋보기로 그 내용이 나온 전사 또는 원문 메모를 확인할 수 있다.
- **참고할 패턴:** 결과마다 상시 노출하지 않고 hover/focus 때 나타나는 조용한 `출처 보기` 아이콘; 생성 결과와 사용자가 직접 쓴 메모의 시각적 구분.
- **주의:** Granola의 사람 중심 “AI가 내 메모를 보강” 모델은 완전 자동 분석인 MinuteMark와 다르다. 수동 노트 입력이나 재생성 기능을 새로 추가할 근거로 쓰지 않는다.

## MinuteMark에 적용할 한 화면 원칙

- **위계:** 회의 제목·길이 → 결정 → 할 일 → 전사 순서로 읽히게 하고, 처리 시간·비용은 보조 정보로 낮춘다.
- **근거:** 모든 결정·할 일에 동일한 근거 칩을 사용한다. `S5·S6` 같은 내부 ID보다 `00:24 · 발화 2개`처럼 사람이 이해하는 표기를 우선한다.
- **이동 피드백:** 근거 클릭 시 플레이어 시간 이동, 해당 전사 자동 스크롤, 2~3초 강조를 한 동작으로 묶는다.
- **레이아웃:** 넓은 화면은 결과와 전사를 2열로, 좁은 화면은 `결과 / 전사` 탭으로 바꾼다. 플레이어는 두 상태 모두 화면 안에 남긴다.
- **범위 제한:** 협업, 댓글, CRM, 캘린더, 검색, 챕터 편집은 이번 리디자인의 핵심이 아니다.

## 결론

**결정:** 새 시각 언어보다 먼저 `Teams의 재생 맥락 + Otter의 결과 구조 + Notion의 근거 인용` 조합으로 결과 화면의 정보 구조를 고정한다.
**근거:** MinuteMark의 차별점은 일반적인 AI 요약이 아니라 결정·할 일이 실제 발화로 되돌아가는 검증 가능성이다.
**확신도:** 높음.
**다음 행동:** 구현 전, 이 조합으로 데스크톱 결과 화면 와이어프레임 1개만 만든다.
**종료 기준:** 결정·할 일 하나를 보고 근거 발화를 재생하기까지 한 번의 클릭이면 되는 구조가 확인되면 레퍼런스 탐색을 종료한다.
