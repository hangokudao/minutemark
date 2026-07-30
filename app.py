import logging
import os
import sqlite3
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import av
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel
from starlette.concurrency import run_in_threadpool

from pipeline import (
    A6_MODEL,
    A6_RUN_BUDGET_USD,
    AUDIO_SUFFIXES,
    WHISPER_CACHE,
    WHISPER_MODEL,
    WHISPER_MODEL_PATH,
    a6_chat,
    transcribe,
    validate_grounding,
)


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
KOREAN_SAMPLE_DIR = Path(os.environ.get("KOREAN_SAMPLE_DIR", "/samples/korean"))
BUDGET_DB = Path(os.environ.get("BUDGET_DB", "/data/budget.sqlite3"))
BUDGET_PERSISTENCE = os.environ.get(
    "BUDGET_PERSISTENCE", "persistent"
).strip().lower()
A6_REQUEST_RESERVE_USD = float(
    os.environ.get("A6_REQUEST_RESERVE_USD", "0.01")
)
MAX_AUDIO_DURATION_SECONDS = float(
    os.environ.get("MAX_AUDIO_DURATION_SECONDS", "120")
)
MAX_ANALYSES_PER_INSTANCE = int(
    os.environ.get("MAX_ANALYSES_PER_INSTANCE", "0")
)
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
KST = timezone(timedelta(hours=9))
logger = logging.getLogger("minutemark")

SAMPLES = {
    "action": {
        "filename": "ko-01-action.wav",
        "title": "법안 통과 후속 작업",
        "description": "앞으로 수행할 구체적인 작업이 포함된 34초 공개 발화",
        "source_title": "[생방송] 이재명 당대표 주재 더불어민주당 최고위원회의",
        "source_url": "https://www.youtube.com/watch?v=-WZ18GPkDJg",
        "license": "Creative Commons Attribution",
    },
    "decision": {
        "filename": "ko-02-decision.wav",
        "title": "KTX 노선 변경 결정",
        "description": "지역 합의와 추진 여부에 대한 결정이 포함된 34초 공개 발화",
        "source_title": "[충북 시사토론 창] 위기의 KTX 오송역, 대응방안은?",
        "source_url": "https://www.youtube.com/watch?v=Nm0lLy1crg0",
        "license": "Creative Commons Attribution",
    },
}

app = FastAPI(title="MinuteMark AI 회의 노트")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_model = None
_model_lock = threading.Lock()
_analysis_lock = threading.Lock()
_analysis_count = 0


class BudgetExceeded(RuntimeError):
    pass


class CapacityExceeded(RuntimeError):
    pass


def current_month() -> str:
    return datetime.now(KST).strftime("%Y-%m")


def budget_snapshot() -> dict:
    BUDGET_DB.parent.mkdir(parents=True, exist_ok=True)
    month = current_month()
    with sqlite3.connect(BUDGET_DB) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS monthly_usage (
                month TEXT PRIMARY KEY,
                spent_usd REAL NOT NULL
            )
            """
        )
        row = connection.execute(
            "SELECT spent_usd FROM monthly_usage WHERE month = ?",
            (month,),
        ).fetchone()
    spent = float(row[0]) if row else 0.0
    return {
        "month": month,
        "spent_usd": round(spent, 8),
        "limit_usd": A6_RUN_BUDGET_USD,
        "remaining_usd": round(max(A6_RUN_BUDGET_USD - spent, 0), 8),
        "persistence": BUDGET_PERSISTENCE,
    }


def ensure_budget_room(reserve_usd: float = A6_REQUEST_RESERVE_USD) -> None:
    budget = budget_snapshot()
    if budget["spent_usd"] + reserve_usd > budget["limit_usd"]:
        raise BudgetExceeded(
            f"{budget['month']} 월간 API 예산 ${budget['limit_usd']:.2f}의 "
            "안전 한도에 도달했습니다."
        )


def record_budget(cost_usd: float) -> dict:
    BUDGET_DB.parent.mkdir(parents=True, exist_ok=True)
    month = current_month()
    with sqlite3.connect(BUDGET_DB) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS monthly_usage (
                month TEXT PRIMARY KEY,
                spent_usd REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO monthly_usage (month, spent_usd)
            VALUES (?, ?)
            ON CONFLICT(month)
            DO UPDATE SET spent_usd = spent_usd + excluded.spent_usd
            """,
            (month, cost_usd),
        )
        connection.commit()
    return budget_snapshot()


def reserve_analysis_slot() -> None:
    global _analysis_count
    if (
        MAX_ANALYSES_PER_INSTANCE > 0
        and _analysis_count >= MAX_ANALYSES_PER_INSTANCE
    ):
        raise CapacityExceeded(
            "이 데모 인스턴스의 분석 횟수 보호선에 도달했습니다. "
            "잠시 후 다시 시도해 주세요."
        )
    _analysis_count += 1


def audio_duration_seconds(audio_path: Path) -> float:
    with av.open(str(audio_path)) as container:
        if container.duration is not None:
            return float(container.duration / av.time_base)
        audio_stream = next(
            (stream for stream in container.streams if stream.type == "audio"),
            None,
        )
        if (
            audio_stream is None
            or audio_stream.duration is None
            or audio_stream.time_base is None
        ):
            return 0.0
        return float(audio_stream.duration * audio_stream.time_base)


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = WhisperModel(
                    WHISPER_MODEL_PATH,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=min(os.cpu_count() or 1, 6),
                    download_root=WHISPER_CACHE,
                )
    return _model


def analyze_audio(audio_path: Path, display_name: str) -> dict:
    with _analysis_lock:
        duration_seconds = audio_duration_seconds(audio_path)
        if duration_seconds > MAX_AUDIO_DURATION_SECONDS:
            raise ValueError(
                "오디오는 "
                f"{int(MAX_AUDIO_DURATION_SECONDS // 60)}분 이하여야 합니다."
            )
        reserve_analysis_slot()
        ensure_budget_room()
        started = time.perf_counter()
        segments, whisper_seconds = transcribe(get_model(), audio_path)
        if not segments:
            raise ValueError("음성에서 발화를 찾지 못했습니다.")

        extraction, llm_seconds, usage, estimated_cost, usage_reported = a6_chat(
            segments
        )
        budget = record_budget(estimated_cost)

        grounding_errors = validate_grounding(extraction, segments)
        if grounding_errors:
            raise RuntimeError(
                "AI 결과 근거 검증 실패: " + "; ".join(grounding_errors)
            )
        total_seconds = time.perf_counter() - started
        return {
            "audio": display_name,
            "audio_duration_seconds": round(duration_seconds, 2),
            "models": {
                "transcription": f"faster-whisper/{WHISPER_MODEL}:cpu-int8",
                "extraction": f"a6api/{A6_MODEL}",
            },
            "timing_seconds": {
                "whisper": round(whisper_seconds, 2),
                "llm": round(llm_seconds, 2),
                "total": round(total_seconds, 2),
            },
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "reported": usage_reported,
            },
            "estimated_cost_usd": round(estimated_cost, 8),
            "budget": budget,
            "segments": segments,
            "extraction": extraction,
            "grounding": {
                "valid": not grounding_errors,
                "errors": grounding_errors,
            },
        }


def sample_or_404(sample_id: str) -> tuple[dict, Path]:
    sample = SAMPLES.get(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="존재하지 않는 데모 샘플입니다.")
    audio_path = KOREAN_SAMPLE_DIR / sample["filename"]
    if not audio_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="데모 오디오가 준비되지 않았습니다. samples/korean을 확인하세요.",
        )
    return sample, audio_path


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/budget")
def budget() -> dict:
    return budget_snapshot()


@app.get("/api/samples")
def samples() -> list[dict]:
    return [
        {
            "id": sample_id,
            **sample,
            "available": (KOREAN_SAMPLE_DIR / sample["filename"]).is_file(),
            "audio_url": f"/audio/{sample_id}",
        }
        for sample_id, sample in SAMPLES.items()
    ]


@app.get("/audio/{sample_id}")
def sample_audio(sample_id: str) -> FileResponse:
    _, audio_path = sample_or_404(sample_id)
    return FileResponse(audio_path, media_type="audio/wav")


@app.post("/api/analyze-sample/{sample_id}")
def analyze_sample(sample_id: str) -> dict:
    sample, audio_path = sample_or_404(sample_id)
    try:
        result = analyze_audio(audio_path, sample["filename"])
    except BudgetExceeded as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except CapacityExceeded as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.exception("공개 샘플 AI 분석 실패")
        raise HTTPException(
            status_code=502,
            detail="AI 분석에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        ) from error
    result["sample"] = {"id": sample_id, **sample}
    result["audio_url"] = f"/audio/{sample_id}"
    return result


@app.post("/api/analyze")
async def analyze_upload(audio: UploadFile = File(...)) -> dict:
    filename = Path(audio.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in AUDIO_SUFFIXES:
        allowed = ", ".join(sorted(AUDIO_SUFFIXES))
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일입니다. 허용 형식: {allowed}",
        )

    content = await audio.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="파일은 20MB 이하여야 합니다.",
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(content)
            temp_path = Path(temp.name)
        return await run_in_threadpool(analyze_audio, temp_path, filename)
    except BudgetExceeded as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except CapacityExceeded as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except av.error.InvalidDataError as error:
        raise HTTPException(
            status_code=422,
            detail=(
                "오디오 파일을 읽을 수 없습니다. "
                "올바른 오디오 파일인지 확인해 주세요."
            ),
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.exception("업로드 오디오 AI 분석 실패")
        raise HTTPException(
            status_code=502,
            detail="AI 분석에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        ) from error
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)
