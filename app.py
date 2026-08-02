import copy
import hashlib
import logging
import os
import sqlite3
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import av
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile as StarletteUploadFile

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
from members import (
    FirebaseMeetingStore,
    FirebaseSampleCache,
    delete_account,
    delete_firebase_user,
    ensure_meeting_capacity,
    get_owned_meeting,
    meeting_title,
    new_meeting_id,
    sha256_file,
    verify_bearer_token,
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
APP_COMMIT_SHA = os.environ.get("APP_COMMIT_SHA", "local")
MAX_AUDIO_DURATION_SECONDS = float(
    os.environ.get("MAX_AUDIO_DURATION_SECONDS", "120")
)
MAX_ANALYSES_PER_INSTANCE = int(
    os.environ.get("MAX_ANALYSES_PER_INSTANCE", "0")
)
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_MULTIPART_BYTES = MAX_UPLOAD_BYTES + 1024 * 1024
MEMBER_FEATURES_ENABLED = os.environ.get(
    "MEMBER_FEATURES_ENABLED", "false"
).strip().lower() in {"1", "true", "yes"}
PERSISTENT_SAMPLE_CACHE_ENABLED = os.environ.get(
    "PERSISTENT_SAMPLE_CACHE_ENABLED", "false"
).strip().lower() in {"1", "true", "yes"}
FIREBASE_WEB_CONFIG = {
    "apiKey": os.environ.get(
        "FIREBASE_WEB_API_KEY", "AIzaSyDUbSfqf2Y_9zZGKeBILP_XKZMM978cztY"
    ),
    "authDomain": os.environ.get(
        "FIREBASE_AUTH_DOMAIN", "minutemark-portfolio.firebaseapp.com"
    ),
    "projectId": os.environ.get(
        "FIREBASE_PROJECT_ID", "minutemark-portfolio"
    ),
    "appId": os.environ.get(
        "FIREBASE_WEB_APP_ID",
        "1:89192290289:web:84ecbd14df29823908d650",
    ),
}
KST = timezone(timedelta(hours=9))
logger = logging.getLogger("minutemark")

SAMPLES = {
    "action": {
        "filename": "ko-01-action.wav",
        "title": "법안 통과 후속 작업",
        "description": "앞으로 수행할 구체적인 작업이 포함된 34초 공개 발화",
        "source_title": "[생방송] 이재명 당대표 주재 더불어민주당 최고위원회의",
        "source_url": "https://www.youtube.com/watch?v=-WZ18GPkDJg",
        "author": "시사발전소 현장LIVE",
        "license": "Creative Commons Attribution (CC BY)",
        "license_url": "https://support.google.com/youtube/answer/2797468",
        "modification": "34초 발췌·16 kHz mono WAV 변환",
    },
    "decision": {
        "filename": "ko-02-decision.wav",
        "title": "KTX 노선 변경 결정",
        "description": "지역 합의와 추진 여부에 대한 결정이 포함된 34초 공개 발화",
        "source_title": "[충북 시사토론 창] 위기의 KTX 오송역, 대응방안은?",
        "source_url": "https://www.youtube.com/watch?v=Nm0lLy1crg0",
        "author": "안녕!MBC충북",
        "license": "Creative Commons Attribution (CC BY)",
        "license_url": "https://support.google.com/youtube/answer/2797468",
        "modification": "34초 발췌·16 kHz mono WAV 변환",
    },
}

app = FastAPI(
    title="MinuteMark AI 회의 노트",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_model = None
_model_lock = threading.Lock()
_analysis_lock = threading.Lock()
_analysis_count = 0
_meeting_store = None
_meeting_store_lock = threading.Lock()
_sample_cache_store = None
_sample_cache_store_lock = threading.Lock()
_sample_result_cache = {}
_sample_result_cache_lock = threading.Lock()


class BudgetExceeded(RuntimeError):
    pass


class CapacityExceeded(RuntimeError):
    pass


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "connect-src 'self' https://*.firebaseapp.com https://*.firebaseio.com "
        "https://*.googleapis.com; "
        "font-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "frame-src https://accounts.google.com https://*.firebaseapp.com; "
        "img-src 'self' data: https://*.googleusercontent.com; "
        "media-src 'self' blob: https://storage.googleapis.com "
        "https://*.storage.googleapis.com; "
        "object-src 'none'; "
        "script-src 'self' https://www.gstatic.com; "
        "style-src 'self'; "
        "worker-src 'self' blob:"
    )
    response.headers["Permissions-Policy"] = (
        "camera=(), geolocation=(), microphone=()"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


def get_meeting_store() -> FirebaseMeetingStore:
    global _meeting_store
    if not MEMBER_FEATURES_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="회원 기능을 준비하고 있습니다. 잠시 후 다시 시도해 주세요.",
        )
    if _meeting_store is None:
        with _meeting_store_lock:
            if _meeting_store is None:
                _meeting_store = FirebaseMeetingStore()
    return _meeting_store


def get_sample_cache_store() -> FirebaseSampleCache:
    global _sample_cache_store
    if _sample_cache_store is None:
        with _sample_cache_store_lock:
            if _sample_cache_store is None:
                _sample_cache_store = FirebaseSampleCache()
    return _sample_cache_store


def authenticated_user(request: Request):
    return verify_bearer_token(request.headers.get("authorization"))


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


def sample_cache_key(sample_id: str, audio_path: Path) -> str:
    source = ":".join(
        (
            "v1",
            APP_COMMIT_SHA,
            A6_MODEL,
            WHISPER_MODEL,
            sample_id,
            sha256_file(audio_path),
        )
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/samples")
@app.get("/auth")
@app.get("/meetings")
@app.get("/meetings/new")
@app.get("/account")
@app.get("/privacy")
def app_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/meetings/{meeting_id}")
def meeting_page(meeting_id: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "commit": APP_COMMIT_SHA}


@app.get("/api/config")
def public_config() -> dict:
    return {
        "member_features_enabled": MEMBER_FEATURES_ENABLED,
        "firebase": FIREBASE_WEB_CONFIG,
        "limits": {
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "max_audio_duration_seconds": MAX_AUDIO_DURATION_SECONDS,
        },
    }


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
    cache_key = sample_cache_key(sample_id, audio_path)
    with _sample_result_cache_lock:
        result = copy.deepcopy(_sample_result_cache.get(cache_key))
        if result is None and PERSISTENT_SAMPLE_CACHE_ENABLED:
            try:
                result = get_sample_cache_store().get(cache_key)
            except Exception as error:
                logger.exception("공개 샘플 캐시 조회 실패")
                raise HTTPException(
                    status_code=503,
                    detail="공개 샘플 결과를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
                ) from error
        if result is None:
            try:
                result = analyze_audio(audio_path, sample["filename"])
            except BudgetExceeded as error:
                raise HTTPException(status_code=429, detail=str(error)) from error
            except CapacityExceeded as error:
                raise HTTPException(status_code=429, detail=str(error)) from error
            except ValueError as error:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "오디오 파일을 처리할 수 없습니다. "
                        "올바른 오디오 파일인지 확인해 주세요."
                    ),
                ) from error
            except Exception as error:
                logger.exception("공개 샘플 AI 분석 실패")
                raise HTTPException(
                    status_code=502,
                    detail="AI 분석에 실패했습니다. 잠시 후 다시 시도해 주세요.",
                ) from error
            _sample_result_cache[cache_key] = copy.deepcopy(result)
            if PERSISTENT_SAMPLE_CACHE_ENABLED:
                try:
                    get_sample_cache_store().put(cache_key, result)
                except Exception:
                    logger.exception("공개 샘플 캐시 저장 실패")
        else:
            _sample_result_cache[cache_key] = copy.deepcopy(result)
        result = copy.deepcopy(result)
    result["sample"] = {"id": sample_id, **sample}
    result["audio_url"] = f"/audio/{sample_id}"
    return result


def raise_safe_analysis_error(error: Exception) -> None:
    if isinstance(error, (BudgetExceeded, CapacityExceeded)):
        raise HTTPException(status_code=429, detail=str(error)) from error
    if isinstance(error, av.error.InvalidDataError):
        raise HTTPException(
            status_code=422,
            detail=(
                "오디오 파일을 읽을 수 없습니다. "
                "올바른 오디오 파일인지 확인해 주세요."
            ),
        ) from error
    if isinstance(error, ValueError):
        raise HTTPException(
            status_code=422,
            detail=(
                "오디오 파일을 처리할 수 없습니다. "
                "올바른 오디오 파일인지 확인해 주세요."
            ),
        ) from error
    logger.exception("업로드 오디오 AI 분석 실패")
    raise HTTPException(
        status_code=502,
        detail="AI 분석에 실패했습니다. 잠시 후 다시 시도해 주세요.",
    ) from error


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
    except Exception as error:
        raise_safe_analysis_error(error)
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


@app.get("/api/me")
def current_user(request: Request) -> dict:
    user = authenticated_user(request)
    return {"email": user.email, "provider": "google.com"}


@app.get("/api/meetings")
def list_meetings(request: Request) -> list[dict]:
    user = authenticated_user(request)
    try:
        return get_meeting_store().list(user.uid)
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("회의 목록 조회 실패")
        raise HTTPException(
            status_code=503,
            detail="회의 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from error


@app.get("/api/meetings/{meeting_id}")
def meeting_detail(meeting_id: str, request: Request) -> dict:
    user = authenticated_user(request)
    try:
        return get_owned_meeting(get_meeting_store(), user.uid, meeting_id)
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("회의 상세 조회 실패")
        raise HTTPException(
            status_code=503,
            detail="회의를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from error


@app.post("/api/meetings")
async def create_meeting(request: Request) -> dict:
    user = authenticated_user(request)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_MULTIPART_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="파일은 20MB 이하여야 합니다.",
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="올바르지 않은 업로드 요청입니다.",
            )

    store = get_meeting_store()
    idempotency_key = request.headers.get("idempotency-key", "").strip()
    if idempotency_key and not (
        len(idempotency_key) == 32
        and all(character in "0123456789abcdef" for character in idempotency_key)
    ):
        raise HTTPException(
            status_code=400,
            detail="올바르지 않은 분석 요청 식별자입니다.",
        )
    meeting_id = idempotency_key or new_meeting_id()
    if idempotency_key:
        existing = await run_in_threadpool(store.get, user.uid, meeting_id)
        if existing is not None:
            return existing
    await run_in_threadpool(ensure_meeting_capacity, store, user.uid)
    try:
        form = await request.form()
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="업로드 요청을 읽을 수 없습니다.",
        ) from error
    audio = form.get("audio")
    if not isinstance(audio, StarletteUploadFile):
        raise HTTPException(status_code=400, detail="오디오 파일을 선택해 주세요.")

    raw_title = form.get("title")
    if not isinstance(raw_title, str) or not raw_title.strip():
        raise HTTPException(status_code=400, detail="회의 제목을 입력해 주세요.")
    if len(raw_title.strip()) > 80:
        raise HTTPException(
            status_code=400,
            detail="회의 제목은 80자 이하여야 합니다.",
        )
    if form.get("participant_notice_confirmed") != "true":
        raise HTTPException(
            status_code=400,
            detail="회의 참여자에게 녹음과 분석 사실을 알렸는지 확인해 주세요.",
        )

    filename = Path(audio.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in AUDIO_SUFFIXES:
        allowed = ", ".join(sorted(AUDIO_SUFFIXES))
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일입니다. 허용 형식: {allowed}",
        )

    title = meeting_title(raw_title)
    content_type = audio.content_type or "application/octet-stream"
    temp_path = None
    size_bytes = 0
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_path = Path(temp.name)
            while chunk := await audio.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="파일은 20MB 이하여야 합니다.",
                    )
                temp.write(chunk)
        try:
            await run_in_threadpool(
                store.ensure_total_audio_capacity,
                size_bytes,
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.exception("전체 오디오 저장 한도 확인 실패")
            raise HTTPException(
                status_code=503,
                detail="저장 공간을 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.",
            ) from error
        try:
            analysis = await run_in_threadpool(analyze_audio, temp_path, title)
        except Exception as error:
            raise_safe_analysis_error(error)
        try:
            return await run_in_threadpool(
                store.create,
                user.uid,
                meeting_id,
                title,
                temp_path,
                content_type,
                size_bytes,
                sha256_file(temp_path),
                analysis,
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.exception("회의 저장 실패")
            raise HTTPException(
                status_code=503,
                detail="분석은 끝났지만 회의를 저장하지 못했습니다. 다시 시도해 주세요.",
            ) from error
    except HTTPException:
        raise
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


@app.delete("/api/meetings/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: str, request: Request) -> None:
    user = authenticated_user(request)
    try:
        get_meeting_store().delete(user.uid, meeting_id)
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("회의 삭제 실패")
        raise HTTPException(
            status_code=503,
            detail="회의를 삭제하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from error


@app.delete("/api/account", status_code=204)
def delete_user_account(request: Request) -> None:
    user = authenticated_user(request)
    try:
        delete_account(
            user,
            get_meeting_store(),
            delete_firebase_user,
        )
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("계정 삭제 실패")
        raise HTTPException(
            status_code=503,
            detail="계정을 삭제하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from error
