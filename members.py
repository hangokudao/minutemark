import hashlib
import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Protocol

from fastapi import HTTPException


FIREBASE_PROJECT_ID = os.environ.get(
    "FIREBASE_PROJECT_ID", "minutemark-portfolio"
)
MEETING_AUDIO_BUCKET = os.environ.get(
    "MEETING_AUDIO_BUCKET", "minutemark-portfolio-meetings"
)
RUNTIME_SERVICE_ACCOUNT = os.environ.get(
    "RUNTIME_SERVICE_ACCOUNT",
    "minutemark-runtime@minutemark-portfolio.iam.gserviceaccount.com",
)
MAX_MEETINGS_PER_USER = int(os.environ.get("MAX_MEETINGS_PER_USER", "5"))
RECENT_AUTH_SECONDS = int(os.environ.get("RECENT_AUTH_SECONDS", "300"))
SIGNED_URL_MINUTES = int(os.environ.get("SIGNED_URL_MINUTES", "5"))
MAX_TOTAL_AUDIO_BYTES = int(
    os.environ.get("MAX_TOTAL_AUDIO_BYTES", str(512 * 1024 * 1024))
)
MAX_FIRESTORE_DOCUMENT_BYTES = 750 * 1024

_firebase_lock = threading.Lock()


@dataclass(frozen=True)
class AuthUser:
    uid: str
    email: str
    auth_time: int


class MeetingStore(Protocol):
    def count(self, uid: str) -> int: ...

    def ensure_total_audio_capacity(self, incoming_bytes: int) -> None: ...

    def list(self, uid: str) -> list[dict]: ...

    def get(self, uid: str, meeting_id: str) -> dict | None: ...

    def create(
        self,
        uid: str,
        meeting_id: str,
        title: str,
        audio_path: Path,
        content_type: str,
        size_bytes: int,
        sha256: str,
        analysis: dict,
    ) -> dict: ...

    def delete(self, uid: str, meeting_id: str) -> bool: ...

    def delete_all(self, uid: str) -> None: ...


def initialize_firebase() -> None:
    import firebase_admin

    if firebase_admin._apps:
        return
    with _firebase_lock:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(options={"projectId": FIREBASE_PROJECT_ID})


def firebase_token_verifier(token: str, check_revoked: bool = True) -> dict:
    from firebase_admin import auth

    initialize_firebase()
    return auth.verify_id_token(token, check_revoked=check_revoked)


def verify_bearer_token(
    authorization: str | None,
    verifier: Callable[..., dict] | None = None,
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Google 로그인이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Google 로그인이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        decoded = (verifier or firebase_token_verifier)(
            token,
            check_revoked=True,
        )
        uid = decoded.get("uid") or decoded.get("sub")
        email = decoded.get("email") or ""
        auth_time = int(decoded.get("auth_time") or 0)
        provider = (decoded.get("firebase") or {}).get("sign_in_provider")
        if not uid or provider != "google.com":
            raise ValueError("invalid identity provider")
        return AuthUser(uid=uid, email=email, auth_time=auth_time)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=401,
            detail="로그인 정보가 만료됐습니다. 다시 로그인해 주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def require_recent_auth(user: AuthUser, now: float | None = None) -> None:
    if (now or time.time()) - user.auth_time > RECENT_AUTH_SECONDS:
        raise HTTPException(
            status_code=401,
            detail="계정 삭제 전에 Google 로그인을 다시 확인해 주세요.",
            headers={"X-Reauth-Required": "true"},
        )


def ensure_meeting_capacity(store: MeetingStore, uid: str) -> None:
    if store.count(uid) >= MAX_MEETINGS_PER_USER:
        raise HTTPException(
            status_code=409,
            detail=(
                f"회의는 계정당 {MAX_MEETINGS_PER_USER}개까지 저장할 수 있습니다. "
                "기존 회의를 삭제한 뒤 다시 시도해 주세요."
            ),
        )


def get_owned_meeting(
    store: MeetingStore,
    uid: str,
    meeting_id: str,
) -> dict:
    meeting = store.get(uid, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="회의를 찾을 수 없습니다.")
    return meeting


def delete_account(
    user: AuthUser,
    store: MeetingStore,
    delete_auth_user: Callable[[str], None],
) -> None:
    require_recent_auth(user)
    store.delete_all(user.uid)
    delete_auth_user(user.uid)


def delete_firebase_user(uid: str) -> None:
    from firebase_admin import auth

    initialize_firebase()
    auth.delete_user(uid)


def meeting_title(value: str) -> str:
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", value.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return (cleaned or "새 회의")[:80]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as audio_file:
        for chunk in iter(lambda: audio_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def new_meeting_id() -> str:
    return uuid.uuid4().hex


def _iso(value) -> str | None:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str):
        return value
    return None


def _summary(data: dict) -> dict:
    analysis = data.get("analysis") or {}
    extraction = analysis.get("extraction") or {}
    return {
        "id": data["id"],
        "title": data["title"],
        "created_at": _iso(data.get("created_at")),
        "audio_duration_seconds": analysis.get("audio_duration_seconds", 0),
        "decision_count": len(extraction.get("decisions") or []),
        "action_count": len(extraction.get("action_items") or []),
    }


class FirebaseMeetingStore:
    def __init__(self) -> None:
        import google.auth
        from google.cloud import firestore, storage

        initialize_firebase()
        self._firestore = firestore.Client(project=FIREBASE_PROJECT_ID)
        self._storage = storage.Client(project=FIREBASE_PROJECT_ID)
        self._bucket = self._storage.bucket(MEETING_AUDIO_BUCKET)
        self._credentials, _ = google.auth.default()

    def _collection(self, uid: str):
        return (
            self._firestore.collection("users")
            .document(uid)
            .collection("meetings")
        )

    def _document(self, uid: str, meeting_id: str):
        return self._collection(uid).document(meeting_id)

    def count(self, uid: str) -> int:
        return sum(
            1
            for _ in self._collection(uid).limit(MAX_MEETINGS_PER_USER).stream()
        )

    def ensure_total_audio_capacity(self, incoming_bytes: int) -> None:
        stored_bytes = 0
        for blob in self._bucket.list_blobs(prefix="users/"):
            stored_bytes += int(blob.size or 0)
            if stored_bytes + incoming_bytes > MAX_TOTAL_AUDIO_BYTES:
                raise HTTPException(
                    status_code=507,
                    detail=(
                        "현재 데모의 전체 저장 공간이 가득 찼습니다. "
                        "잠시 후 다시 시도해 주세요."
                    ),
                )

    def list(self, uid: str) -> list[dict]:
        query = self._collection(uid).order_by(
            "created_at",
            direction="DESCENDING",
        )
        return [_summary(snapshot.to_dict()) for snapshot in query.stream()]

    def get(self, uid: str, meeting_id: str) -> dict | None:
        snapshot = self._document(uid, meeting_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        audio = data.get("audio") or {}
        blob_path = audio.get("object_path")
        generation = audio.get("generation")
        if not blob_path or not generation:
            return None
        blob = self._bucket.blob(blob_path, generation=int(generation))
        if not blob.exists():
            return None
        return {
            "id": data["id"],
            "title": data["title"],
            "created_at": _iso(data.get("created_at")),
            "analysis": data.get("analysis") or {},
            "audio_url": self._signed_audio_url(
                blob_path,
                generation=int(generation),
            ),
            "audio_url_expires_in_seconds": SIGNED_URL_MINUTES * 60,
        }

    def create(
        self,
        uid: str,
        meeting_id: str,
        title: str,
        audio_path: Path,
        content_type: str,
        size_bytes: int,
        sha256: str,
        analysis: dict,
    ) -> dict:
        created_at = datetime.now(timezone.utc)
        object_path = f"users/{uid}/meetings/{meeting_id}/audio"
        data = {
            "id": meeting_id,
            "owner_uid": uid,
            "title": title,
            "created_at": created_at,
            "schema_version": 1,
            "audio": {
                "object_path": object_path,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "sha256": sha256,
                "generation": 99999999999999999999,
            },
            "analysis": analysis,
        }
        serialized_data = {**data, "created_at": created_at.isoformat()}
        document_size = len(
            json.dumps(
                serialized_data,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if document_size > MAX_FIRESTORE_DOCUMENT_BYTES:
            raise HTTPException(
                status_code=413,
                detail="분석 결과가 저장 가능한 크기를 초과했습니다.",
            )

        blob = self._bucket.blob(object_path)
        self._signed_audio_url(object_path)
        blob.cache_control = "private, no-store, max-age=0"
        blob.upload_from_filename(audio_path, content_type=content_type)
        generation = int(blob.generation or 0)
        if not generation:
            blob.delete()
            raise RuntimeError("uploaded object generation missing")
        data["audio"]["generation"] = generation
        try:
            audio_url = self._signed_audio_url(
                object_path,
                generation=generation,
            )
            self._document(uid, meeting_id).create(data)
        except Exception:
            blob.delete(if_generation_match=generation)
            raise
        return {
            "id": meeting_id,
            "title": title,
            "created_at": created_at.isoformat(),
            "analysis": analysis,
            "audio_url": audio_url,
            "audio_url_expires_in_seconds": SIGNED_URL_MINUTES * 60,
        }

    def delete(self, uid: str, meeting_id: str) -> bool:
        reference = self._document(uid, meeting_id)
        snapshot = reference.get()
        if not snapshot.exists:
            return False
        data = snapshot.to_dict()
        audio = data.get("audio") or {}
        object_path = audio.get("object_path")
        generation = audio.get("generation")
        if object_path and generation:
            blob = self._bucket.blob(
                object_path,
                generation=int(generation),
            )
            if blob.exists():
                blob.delete(if_generation_match=int(generation))
        reference.delete()
        return True

    def delete_all(self, uid: str) -> None:
        meeting_ids = [snapshot.id for snapshot in self._collection(uid).stream()]
        for meeting_id in meeting_ids:
            self.delete(uid, meeting_id)
        for blob in self._bucket.list_blobs(prefix=f"users/{uid}/"):
            blob.delete(if_generation_match=int(blob.generation))
        has_documents = any(self._collection(uid).limit(1).stream())
        has_audio = any(self._bucket.list_blobs(prefix=f"users/{uid}/"))
        if has_documents or has_audio:
            raise RuntimeError("account content deletion incomplete")

    def _signed_audio_url(
        self,
        object_path: str,
        generation: int | None = None,
    ) -> str:
        from google.auth.transport.requests import Request

        self._credentials.refresh(Request())
        return self._bucket.blob(
            object_path,
            generation=generation,
        ).generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=SIGNED_URL_MINUTES),
            method="GET",
            service_account_email=RUNTIME_SERVICE_ACCOUNT,
            access_token=self._credentials.token,
        )


class FirebaseSampleCache:
    def __init__(self) -> None:
        from google.cloud import storage

        initialize_firebase()
        storage_client = storage.Client(project=FIREBASE_PROJECT_ID)
        self._bucket = storage_client.bucket(MEETING_AUDIO_BUCKET)

    def get(self, cache_key: str) -> dict | None:
        blob = self._bucket.blob(f"system/sample-cache/{cache_key}.json")
        if not blob.exists():
            return None
        payload = json.loads(blob.download_as_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None

    def put(self, cache_key: str, result: dict) -> None:
        blob = self._bucket.blob(f"system/sample-cache/{cache_key}.json")
        blob.cache_control = "private, no-store, max-age=0"
        blob.upload_from_string(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")),
            content_type="application/json; charset=utf-8",
        )
