import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from faster_whisper import WhisperModel


logger = logging.getLogger("minutemark")
SAMPLE_DIR = Path(os.environ.get("SAMPLE_DIR", "/samples"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/output"))
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
WHISPER_MODEL_PATH = os.environ.get("WHISPER_MODEL_PATH", WHISPER_MODEL)
WHISPER_CACHE = os.environ.get("WHISPER_CACHE", "/models/whisper")
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "auto").strip().lower()
MIN_AUDIO_FILES = int(os.environ.get("MIN_AUDIO_FILES", "2"))
A6_API_BASE = os.environ.get("A6_API_BASE", "https://api.a6api.com/v1").rstrip("/")
A6_API_KEY = os.environ.get("A6_API_KEY", "")
A6_MODEL = os.environ.get("A6_MODEL", "gpt-5.6-luna")
A6_VENDOR_ID = os.environ.get("A6_VENDOR_ID", "1729")
A6_INPUT_USD_PER_M = float(os.environ.get("A6_INPUT_USD_PER_M", "0.005256"))
A6_OUTPUT_USD_PER_M = float(os.environ.get("A6_OUTPUT_USD_PER_M", "0.0315"))
A6_RUN_BUDGET_USD = float(os.environ.get("A6_RUN_BUDGET_USD", "1.0"))
A6_REQUEST_TIMEOUT_SECONDS = float(
    os.environ.get("A6_REQUEST_TIMEOUT_SECONDS", "60")
)
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}

OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["decision", "action_item"],
                    },
                    "text": {"type": "string"},
                    "owner": {"type": "string"},
                    "due": {"type": "string"},
                    "segment_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": [
                    "kind",
                    "text",
                    "owner",
                    "due",
                    "segment_ids",
                ],
            },
        },
    },
    "required": ["items"],
}


def stage(label: str) -> None:
    print(f"\n== {label} ==", flush=True)


def normalize_segment_ids(value) -> list[str]:
    if isinstance(value, list):
        return [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def open_a6_request(request):
    for attempt in range(2):
        try:
            return urllib.request.urlopen(
                request,
                timeout=A6_REQUEST_TIMEOUT_SECONDS,
            )
        except urllib.error.HTTPError as error:
            if attempt == 0 and error.code in {500, 502, 503, 504}:
                time.sleep(1)
                continue
            raise
        except urllib.error.URLError:
            if attempt == 0:
                time.sleep(1)
                continue
            raise


def build_a6_request(request_body: dict) -> urllib.request.Request:
    return urllib.request.Request(
        f"{A6_API_BASE}/chat/completions",
        data=json.dumps(request_body).encode(),
        headers={
            "Authorization": f"Bearer {A6_API_KEY}",
            "Content-Type": "application/json",
        },
    )


def request_a6_json(request_body: dict) -> dict:
    try:
        response = open_a6_request(build_a6_request(request_body))
    except urllib.error.HTTPError as error:
        if error.code != 400 or "response_format" not in request_body:
            raise
        error.close()
        fallback_body = dict(request_body)
        fallback_body.pop("response_format")
        logger.warning(
            "A6 판매자가 json_schema를 거부해 일반 JSON 요청으로 폴백합니다."
        )
        response = open_a6_request(build_a6_request(fallback_body))
    with response:
        return json.load(response)


def parse_extraction(raw_extraction) -> dict:
    if not isinstance(raw_extraction, dict) or not isinstance(
        raw_extraction.get("items"), list
    ):
        raise RuntimeError("A6API 구조화 응답에 items 배열이 없습니다.")

    extraction = {"decisions": [], "action_items": []}
    for index, item in enumerate(raw_extraction["items"], start=1):
        if not isinstance(item, dict):
            raise RuntimeError(f"A6API items[{index}]가 객체가 아닙니다.")
        kind = item.get("kind")
        text = item.get("text")
        owner = item.get("owner")
        due = item.get("due")
        segment_ids = normalize_segment_ids(item.get("segment_ids"))
        if kind not in {"decision", "action_item"}:
            raise RuntimeError(f"A6API items[{index}]의 kind가 잘못됐습니다.")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"A6API items[{index}]의 text가 비어 있습니다.")
        if not isinstance(owner, str) or not isinstance(due, str):
            raise RuntimeError(
                f"A6API items[{index}]의 owner 또는 due가 문자열이 아닙니다."
            )
        if not segment_ids:
            raise RuntimeError(
                f"A6API items[{index}]에 근거 구간이 없습니다."
            )

        if kind == "decision":
            extraction["decisions"].append(
                {
                    "text": text.strip(),
                    "segment_ids": segment_ids,
                }
            )
        else:
            extraction["action_items"].append(
                {
                    "text": text.strip(),
                    "owner": owner.strip(),
                    "due": due.strip(),
                    "segment_ids": segment_ids,
                }
            )
    return extraction


def a6_chat(segments: list[dict]) -> tuple[dict, float, dict, float, bool]:
    allowed_segment_ids = [segment["id"] for segment in segments]
    output_schema = json.loads(json.dumps(OUTPUT_SCHEMA))
    id_schema = output_schema["properties"]["items"]["items"]["properties"][
        "segment_ids"
    ]["items"]
    id_schema["enum"] = allowed_segment_ids

    transcript = "\n".join(
        f"[{segment['id']}] {segment['start']:.2f}-{segment['end']:.2f}s "
        f"{segment['text']}"
        for segment in segments
    )
    prompt = f"""다음은 회의 전사다.

{transcript}

아래 규칙을 모두 지켜라.
1. decision은 회의에서 선택·승인·합의가 끝난 결과만 뜻한다.
2. action_item은 앞으로 누군가 수행해야 할 구체적인 작업만 뜻한다.
3. 단순 작업 지시는 decision에 중복해 넣지 마라.
4. 전사에 없는 사실, 담당자, 기한을 추측하지 마라.
5. text에는 구간 ID를 섞지 말고 회의 내용을 간결하게 써라.
6. segment_ids는 허용된 ID({", ".join(allowed_segment_ids)}) 중 근거가 있는 것만
   대괄호 없이 정확히 써라.
7. 담당자나 기한이 없으면 owner 또는 due를 빈 문자열로 써라.
8. 같은 내용을 decision과 action_item 양쪽에 중복하지 마라.
9. 최상위 키는 items 하나만 사용하고, 각 원소에는 kind, text, owner, due,
   segment_ids를 모두 넣어라.
10. 설명이나 Markdown 코드 펜스 없이 JSON 객체 하나만 출력하라.

분류 예:
- "디자인은 A안으로 확정합니다" → decision
- "지연이가 내일까지 시안을 보냅니다" → action_item
- 아직 합의하지 않은 제안·질문·잡담 → 어느 쪽에도 넣지 않음"""

    request_body = {
        "model": A6_MODEL,
        "stream": False,
        "temperature": 0,
        "reasoning_effort": "none",
        "max_completion_tokens": 2048,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "meeting_extraction",
                "strict": True,
                "schema": output_schema,
            },
        },
        "messages": [
            {
                "role": "system",
                "content": "너는 회의록에서 근거가 있는 결정과 할 일만 구조화하는 분석기다.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    started = time.perf_counter()
    payload = request_a6_json(request_body)
    elapsed = time.perf_counter() - started
    choice = payload["choices"][0]
    content = choice["message"].get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "A6API가 빈 구조화 응답을 반환했습니다 "
            f"(finish_reason={choice.get('finish_reason', 'unknown')})."
        )
    content = content.strip()
    if content.startswith("```") and content.endswith("```"):
        content = "\n".join(content.splitlines()[1:-1]).strip()
    try:
        raw_extraction = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError("A6API 구조화 응답이 유효한 JSON이 아닙니다.") from error
    extraction = parse_extraction(raw_extraction)
    usage = payload.get("usage", {})
    usage_reported = all(
        isinstance(usage.get(field), int)
        for field in ("prompt_tokens", "completion_tokens")
    )
    prompt_tokens = int(usage.get("prompt_tokens", 0))
    completion_tokens = int(usage.get("completion_tokens", 0))
    estimated_cost = (
        prompt_tokens * A6_INPUT_USD_PER_M
        + completion_tokens * A6_OUTPUT_USD_PER_M
    ) / 1_000_000
    return extraction, elapsed, usage, estimated_cost, usage_reported


def validate_grounding(extraction: dict, segments: list[dict]) -> list[str]:
    errors = []
    valid_ids = {segment["id"] for segment in segments}
    for field in ("decisions", "action_items"):
        if not isinstance(extraction.get(field), list):
            errors.append(f"{field}: array가 아님")
            continue
        for index, item in enumerate(extraction[field], start=1):
            ids = item.get("segment_ids")
            if not isinstance(ids, list) or not ids:
                errors.append(f"{field}[{index}]: 근거 구간 없음")
                continue
            invalid_ids = sorted(set(ids) - valid_ids)
            if invalid_ids:
                errors.append(
                    f"{field}[{index}]: 존재하지 않는 구간 {', '.join(invalid_ids)}"
                )
    return errors


def transcribe(model: WhisperModel, audio_path: Path) -> tuple[list[dict], float]:
    started = time.perf_counter()
    raw_segments, _ = model.transcribe(
        str(audio_path),
        language=None if WHISPER_LANGUAGE == "auto" else WHISPER_LANGUAGE,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    segments = [
        {
            "id": f"S{index}",
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
        }
        for index, segment in enumerate(raw_segments, start=1)
        if segment.text.strip()
    ]
    return segments, time.perf_counter() - started


def main() -> int:
    if not A6_API_KEY:
        print(
            "설정 오류: A6_API_KEY가 없습니다. .env.example을 .env로 복사한 뒤 "
            "키를 로컬에서만 입력하세요.",
            file=sys.stderr,
        )
        return 2

    audio_files = sorted(
        path
        for path in SAMPLE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
    )
    if len(audio_files) < MIN_AUDIO_FILES:
        print(
            f"입력 오류: {SAMPLE_DIR}에 회의 녹음이 최소 {MIN_AUDIO_FILES}개 "
            f"필요합니다 (현재 {len(audio_files)}개).",
            file=sys.stderr,
        )
        return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stage(f"Whisper {WHISPER_MODEL} 로드 (CPU INT8)")
    model = WhisperModel(
        WHISPER_MODEL_PATH,
        device="cpu",
        compute_type="int8",
        cpu_threads=min(os.cpu_count() or 1, 6),
        download_root=WHISPER_CACHE,
    )

    summaries = []
    for audio_path in audio_files:
        stage(f"{audio_path.name}: 실제 Whisper 전사")
        total_started = time.perf_counter()
        segments, whisper_seconds = transcribe(model, audio_path)
        for segment in segments:
            print(
                f"{segment['id']} [{segment['start']:.2f}-{segment['end']:.2f}] "
                f"{segment['text']}"
            )

        stage(f"{audio_path.name}: 실제 A6API {A6_MODEL} 구조화 추론")
        extraction, llm_seconds, usage, estimated_cost, usage_reported = a6_chat(
            segments
        )
        grounding_errors = validate_grounding(extraction, segments)
        total_seconds = time.perf_counter() - total_started
        result = {
            "audio": audio_path.name,
            "models": {
                "transcription": f"faster-whisper/{WHISPER_MODEL}:cpu-int8",
                "extraction": f"a6api/{A6_MODEL}",
                "preferred_vendor_id": A6_VENDOR_ID,
            },
            "timing_seconds": {
                "whisper": round(whisper_seconds, 2),
                "llm": round(llm_seconds, 2),
                "total": round(total_seconds, 2),
            },
            "usage": usage,
            "estimated_cost_usd": round(estimated_cost, 8),
            "segments": segments,
            "extraction": extraction,
            "grounding": {
                "valid": not grounding_errors,
                "errors": grounding_errors,
            },
            "automatic_gate": {
                "under_60_seconds": total_seconds <= 60,
                "schema_present": all(
                    isinstance(extraction.get(field), list)
                    for field in ("decisions", "action_items")
                ),
                "all_evidence_ids_exist": not grounding_errors,
                "has_candidate_result": bool(
                    extraction.get("decisions") or extraction.get("action_items")
                ),
                "usage_reported": usage_reported,
            },
        }
        result_path = OUTPUT_DIR / f"{audio_path.stem}.json"
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summaries.append(result)
        print(json.dumps(result["extraction"], ensure_ascii=False, indent=2))
        print(
            f"시간: Whisper {whisper_seconds:.2f}s + LLM {llm_seconds:.2f}s "
            f"= {total_seconds:.2f}s"
        )
        print(
            f"토큰: 입력 {usage.get('prompt_tokens', '미제공')} / "
            f"출력 {usage.get('completion_tokens', '미제공')} · "
            f"예상 비용 ${estimated_cost:.8f}"
        )
        print(f"근거 ID 검증: {'PASS' if not grounding_errors else 'FAIL'}")

    stage("자동 판정 요약")
    total_estimated_cost = sum(item["estimated_cost_usd"] for item in summaries)
    within_run_budget = total_estimated_cost <= A6_RUN_BUDGET_USD
    automatic_pass = (
        all(all(item["automatic_gate"].values()) for item in summaries)
        and within_run_budget
    )
    for item in summaries:
        gate = item["automatic_gate"]
        print(
            f"{item['audio']}: "
            + ", ".join(
                f"{key}={'PASS' if value else 'FAIL'}" for key, value in gate.items()
            )
        )
    print(
        f"실행 총 예상 비용: ${total_estimated_cost:.8f} / "
        f"${A6_RUN_BUDGET_USD:.2f} "
        f"({'PASS' if within_run_budget else 'FAIL'})"
    )
    print(
        "\n자동 게이트: "
        f"{'PASS' if automatic_pass else 'FAIL'}\n"
        "수동 게이트: 공개 샘플은 ami-samples.tsv의 expected_decision, "
        "직접 녹음은 NOTES.md의 주석 사실과 output/*.json을 대조해야 합니다."
    )
    return 0 if automatic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
