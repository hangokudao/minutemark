#!/usr/bin/env python3
"""Download and validate the local Korean audio regression corpus.

The manifest is deliberately small and reviewable.  Media stays in the
ignored corpus directory; this script records the source metadata and SHA-256
for each validated WAV without sending audio to a transcription service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT_DIR / "korean-sample-manifest.json"
REQUIRED_SOURCE_LICENSE = "Creative Commons Attribution license (reuse allowed)"
SOURCE_HOST = "www.youtube.com"
SOURCE_PATH = "/watch"
ALLOWED_VIDEO_IDS = frozenset(
    {
        "07zhNSvDR0A",
        "-ySffCRdGl8",
        "9g6USDTbGhg",
        "0e76Mv3YWso",
        "3uuLmiV-HNI",
        "0FzNHep2onE",
        "9h7CCmpcirA",
        "9vY0YzdjoMU",
        "0rj144h8MeE",
        "9bTYC7hkWAI",
    }
)
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*\.wav$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MIN_CLIP_SECONDS = 45.0
MAX_CLIP_SECONDS = 75.0
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
PROCESS_TIMEOUT_SECONDS = 180
METADATA_TIMEOUT_SECONDS = 60
SIGNAL_RMS_DBFS_MIN = -50.0
SIGNAL_ACTIVE_RATIO_MIN = 0.05


class ValidationError(ValueError):
    """Raised when a manifest, source, or local media file is unsafe."""


def canonical_source_url(video_id: str) -> str:
    """Return the only YouTube URL accepted by the downloader."""

    validate_video_id(video_id)
    return f"https://{SOURCE_HOST}{SOURCE_PATH}?v={video_id}"


def validate_video_id(video_id: Any) -> str:
    if not isinstance(video_id, str) or not VIDEO_ID_RE.fullmatch(video_id):
        raise ValidationError("video ID must be an 11-character YouTube ID")
    if video_id not in ALLOWED_VIDEO_IDS:
        raise ValidationError(f"video ID is not in the exact allowlist: {video_id}")
    return video_id


def validate_source_url(source_url: Any, video_id: str) -> str:
    """Reject arbitrary hosts, schemes, paths, query parameters, and fragments."""

    validate_video_id(video_id)
    if not isinstance(source_url, str):
        raise ValidationError("source URL must be a string")
    parsed = urlparse(source_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != SOURCE_HOST
        or parsed.path != SOURCE_PATH
        or parsed.fragment
        or parsed.params
    ):
        raise ValidationError("source URL must be the canonical HTTPS YouTube watch URL")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if set(query) != {"v"} or query["v"] != [video_id]:
        raise ValidationError("source URL query must contain only the allowlisted video ID")
    return canonical_source_url(video_id)


def _finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationError(f"{field_name} must be a finite number")
    return number


def validate_clip_window(
    start: Any, duration: Any, source_duration: Any = None
) -> tuple[float, float]:
    start_seconds = _finite_number(start, "start")
    duration_seconds = _finite_number(duration, "duration")
    if start_seconds < 0:
        raise ValidationError("start must be non-negative")
    if not MIN_CLIP_SECONDS <= duration_seconds <= MAX_CLIP_SECONDS:
        raise ValidationError("duration must be between 45 and 75 seconds")
    if source_duration is not None:
        source_seconds = _finite_number(source_duration, "source duration")
        if source_seconds <= 0 or start_seconds + duration_seconds > source_seconds + 0.25:
            raise ValidationError("clip window must fit within the source duration")
    return start_seconds, duration_seconds


def validate_filename(filename: Any) -> str:
    if not isinstance(filename, str) or not FILENAME_RE.fullmatch(filename):
        raise ValidationError("filename must be a simple .wav filename")
    return filename


def resolve_output_path(corpus_dir: Path, filename: str) -> Path:
    """Resolve one direct child and prove it remains under the corpus directory."""

    validate_filename(filename)
    corpus_root = corpus_dir.resolve()
    output_path = (corpus_root / filename).resolve()
    try:
        relative = output_path.relative_to(corpus_root)
    except ValueError as exc:
        raise ValidationError("output path escapes the corpus directory") from exc
    if len(relative.parts) != 1:
        raise ValidationError("output path must be a direct corpus child")
    return output_path


def _language_values(metadata: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in ("language", "original_language"):
        value = metadata.get(key)
        if isinstance(value, str):
            values.add(value.lower())
    for fmt in metadata.get("formats", []):
        if not isinstance(fmt, dict):
            continue
        value = fmt.get("language")
        if isinstance(value, str):
            values.add(value.lower())
    return values


def has_korean_language_metadata(metadata: dict[str, Any]) -> bool:
    return any(value == "ko" or value.startswith("ko-") for value in _language_values(metadata))


def validate_source_metadata(metadata: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    video_id = validate_video_id(entry.get("video_id"))
    expected_url = validate_source_url(entry.get("source_url"), video_id)
    if metadata.get("id") != video_id:
        raise ValidationError("yt-dlp metadata ID does not match the manifest")
    if metadata.get("webpage_url") != expected_url:
        raise ValidationError("yt-dlp metadata URL crossed the YouTube source boundary")
    if str(metadata.get("availability", "")).lower() != "public":
        raise ValidationError("source video is not public")
    license_text = str(metadata.get("license", ""))
    if license_text != REQUIRED_SOURCE_LICENSE:
        raise ValidationError("source video is not Creative Commons Attribution")
    if not has_korean_language_metadata(metadata):
        raise ValidationError("yt-dlp metadata has no Korean audio-language signal")
    source_duration = metadata.get("duration")
    validate_clip_window(entry.get("start"), entry.get("duration"), source_duration)
    if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
        raise ValidationError("source metadata has no title")
    if not isinstance(metadata.get("uploader"), str) or not metadata["uploader"].strip():
        raise ValidationError("source metadata has no uploader")
    return {
        "title": metadata["title"].strip(),
        "uploader": metadata["uploader"].strip(),
        "license": license_text,
        "source_duration": float(source_duration),
        "language": "ko",
    }


def validate_manifest(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValidationError("manifest must be a JSON object")
    if payload.get("source_license_required") != REQUIRED_SOURCE_LICENSE:
        raise ValidationError("manifest source license requirement is invalid")
    samples = payload.get("samples")
    if not isinstance(samples, list) or len(samples) != len(ALLOWED_VIDEO_IDS):
        raise ValidationError("manifest must contain exactly ten samples")
    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for entry in samples:
        if not isinstance(entry, dict):
            raise ValidationError("every manifest sample must be an object")
        video_id = validate_video_id(entry.get("video_id"))
        if video_id in seen_ids:
            raise ValidationError(f"duplicate video ID: {video_id}")
        seen_ids.add(video_id)
        filename = validate_filename(entry.get("filename"))
        if filename in seen_files:
            raise ValidationError(f"duplicate filename: {filename}")
        seen_files.add(filename)
        validate_source_url(entry.get("source_url"), video_id)
        validate_clip_window(
            entry.get("start"), entry.get("duration"), entry.get("source_duration")
        )
        license_text = entry.get("original_license")
        if license_text != REQUIRED_SOURCE_LICENSE:
            raise ValidationError("manifest source license must be Creative Commons Attribution")
        checksum = entry.get("sha256", "")
        if not isinstance(checksum, str) or (checksum and not SHA256_RE.fullmatch(checksum)):
            raise ValidationError("sha256 must be empty or a lowercase SHA-256 digest")
    if seen_ids != ALLOWED_VIDEO_IDS:
        raise ValidationError("manifest video IDs must equal the exact allowlist")
    return samples


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read manifest: {path}") from exc
    validate_manifest(payload)
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise ValidationError(f"required executable is missing: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValidationError(f"command timed out after {timeout}s: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip().splitlines()
        message = detail[-1] if detail else "no command output"
        raise ValidationError(f"{command[0]} failed: {message}") from exc


def fetch_source_metadata(video_id: str) -> dict[str, Any]:
    validate_video_id(video_id)
    command = [
        "yt-dlp",
        "--skip-download",
        "--dump-single-json",
        "--no-warnings",
        "--no-playlist",
        "--no-cache-dir",
        "--socket-timeout",
        "30",
        "--retries",
        "1",
        canonical_source_url(video_id),
    ]
    result = _run(command, METADATA_TIMEOUT_SECONDS)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("yt-dlp metadata was not valid JSON") from exc


def _source_file(staging_dir: Path) -> Path:
    candidates = [
        path
        for path in staging_dir.glob("source.*")
        if path.is_file() and not path.name.endswith((".part", ".ytdl"))
    ]
    if len(candidates) != 1:
        raise ValidationError("yt-dlp did not produce exactly one source audio file")
    return candidates[0]


def download_source(video_id: str, staging_dir: Path) -> Path:
    validate_video_id(video_id)
    output_template = str(staging_dir / "source.%(ext)s")
    command = [
        "yt-dlp",
        "--no-playlist",
        "--no-cache-dir",
        "--no-warnings",
        "--no-progress",
        "--socket-timeout",
        "30",
        "--retries",
        "1",
        "--fragment-retries",
        "1",
        "--max-filesize",
        str(MAX_SOURCE_BYTES),
        "--format",
        "bestaudio[ext=m4a]/bestaudio",
        "--output",
        output_template,
        canonical_source_url(video_id),
    ]
    _run(command, PROCESS_TIMEOUT_SECONDS)
    source = _source_file(staging_dir)
    if source.stat().st_size <= 0 or source.stat().st_size > MAX_SOURCE_BYTES:
        raise ValidationError("downloaded source exceeds the byte cap or is empty")
    return source


def make_clip(source: Path, start: float, duration: float, destination: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(source),
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        "-f",
        "wav",
        str(destination),
    ]
    _run(command, PROCESS_TIMEOUT_SECONDS)


def validate_signal(path: Path) -> None:
    try:
        handle = wave.open(str(path), "rb")
    except (wave.Error, OSError) as exc:
        raise ValidationError("file is not a readable WAV") from exc
    with handle:
        if handle.getnchannels() != 1 or handle.getsampwidth() != 2:
            raise ValidationError("signal proxy expects mono signed 16-bit PCM")
        total_samples = active_samples = 0
        sum_squares = 0.0
        while raw := handle.readframes(32768):
            values = array("h")
            values.frombytes(raw)
            if sys.byteorder != "little":
                values.byteswap()
            for value in values:
                total_samples += 1
                sum_squares += float(value * value)
                if abs(value) >= 160:
                    active_samples += 1
    if total_samples == 0:
        raise ValidationError("audio has no samples")
    rms_dbfs = 20.0 * math.log10(
        max(math.sqrt(sum_squares / total_samples) / 32768.0, 1e-12)
    )
    if rms_dbfs <= SIGNAL_RMS_DBFS_MIN:
        raise ValidationError("audio is too quiet for the local speech proxy")
    if active_samples / total_samples <= SIGNAL_ACTIVE_RATIO_MIN:
        raise ValidationError("audio has too little active signal for the local speech proxy")


def validate_wave_file(path: Path, expected_duration: float | None = None) -> float:
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValidationError("output audio is missing or empty")
    if path.stat().st_size > MAX_OUTPUT_BYTES:
        raise ValidationError("output audio exceeds the byte cap")
    result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        PROCESS_TIMEOUT_SECONDS,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("ffprobe output was not valid JSON") from exc
    streams = payload.get("streams")
    if not isinstance(streams, list) or len(streams) != 1:
        raise ValidationError("output must contain exactly one audio stream")
    stream = streams[0]
    if stream.get("codec_type") != "audio":
        raise ValidationError("output contains a non-audio stream")
    if stream.get("codec_name") != "pcm_s16le":
        raise ValidationError("output codec must be signed 16-bit PCM")
    if str(stream.get("sample_rate")) != "16000" or stream.get("channels") != 1:
        raise ValidationError("output audio must be 16 kHz mono")
    format_name = str((payload.get("format") or {}).get("format_name", ""))
    if "wav" not in format_name.split(","):
        raise ValidationError("output container must be WAV")
    try:
        duration = float(stream.get("duration") or (payload.get("format") or {}).get("duration"))
    except (TypeError, ValueError) as exc:
        raise ValidationError("ffprobe did not report audio duration") from exc
    if not MIN_CLIP_SECONDS <= duration <= MAX_CLIP_SECONDS:
        raise ValidationError("output duration must be between 45 and 75 seconds")
    if expected_duration is not None and abs(duration - expected_duration) > 1.0:
        raise ValidationError("output duration differs from the requested clip window")
    validate_signal(path)
    return duration


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    temporary_name = temporary.name
    try:
        with temporary:
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _manifest_corpus_dir(payload: dict[str, Any]) -> Path:
    relative_dir = payload.get("corpus_dir")
    if not isinstance(relative_dir, str) or not relative_dir:
        raise ValidationError("manifest corpus_dir is required")
    corpus_dir = (ROOT_DIR / relative_dir).resolve()
    samples_root = (ROOT_DIR / "samples").resolve()
    try:
        corpus_dir.relative_to(samples_root)
    except ValueError as exc:
        raise ValidationError("corpus_dir must remain under samples/") from exc
    if Path(relative_dir).is_absolute() or ".." in Path(relative_dir).parts:
        raise ValidationError("corpus_dir must be a relative samples path")
    return corpus_dir


def _check_existing(path: Path, entry: dict[str, Any]) -> str:
    validate_wave_file(path, expected_duration=float(entry["duration"]))
    digest = sha256_file(path)
    expected = entry.get("sha256", "")
    if expected and digest != expected:
        raise ValidationError(f"existing file SHA-256 mismatch: {path.name}")
    return digest


def process_sample(entry: dict[str, Any], corpus_dir: Path) -> tuple[str, bool]:
    output_path = resolve_output_path(corpus_dir, entry["filename"])
    if output_path.exists():
        return _check_existing(output_path, entry), True
    corpus_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".korean-regression-", dir=corpus_dir) as staging_name:
        staging_dir = Path(staging_name)
        source = download_source(entry["video_id"], staging_dir)
        temporary_clip = staging_dir / "clip.wav"
        make_clip(source, float(entry["start"]), float(entry["duration"]), temporary_clip)
        validate_wave_file(temporary_clip, expected_duration=float(entry["duration"]))
        digest = sha256_file(temporary_clip)
        os.replace(temporary_clip, output_path)
    return digest, False


def run(manifest_path: Path, check_only: bool) -> int:
    payload = load_manifest(manifest_path)
    entries = payload["samples"]
    if check_only and any(not entry.get("sha256") for entry in entries):
        raise ValidationError("--check-only requires every sample to have a SHA-256")
    corpus_dir = _manifest_corpus_dir(payload)
    failures: list[str] = []
    for entry in entries:
        try:
            if check_only:
                digest = _check_existing(resolve_output_path(corpus_dir, entry["filename"]), entry)
                reused = True
            else:
                metadata = fetch_source_metadata(entry["video_id"])
                checked = validate_source_metadata(metadata, entry)
                entry["title"] = checked["title"]
                entry["uploader"] = checked["uploader"]
                entry["original_license"] = checked["license"]
                entry["metadata_language"] = checked["language"]
                entry["source_duration"] = round(checked["source_duration"], 3)
                digest, reused = process_sample(entry, corpus_dir)
            entry["sha256"] = digest
            print(f"{'REUSE' if reused else 'GET'} {entry['id']} {entry['video_id']}")
        except (KeyError, ValidationError, OSError) as exc:
            failures.append(f"{entry.get('id', '<unknown>')}: {exc}")
            print(f"FAIL {failures[-1]}", file=sys.stderr)
    if failures:
        print(f"{len(failures)} sample(s) failed; manifest was not rewritten", file=sys.stderr)
        return 1
    if not check_only:
        write_manifest(manifest_path, payload)
    print(f"PASS {len(entries)} Korean regression samples ({'check-only' if check_only else 'download/validate'})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="JSON manifest (default: korean-sample-manifest.json)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate existing local clips without contacting YouTube",
    )
    args = parser.parse_args(argv)
    try:
        return run(args.manifest, args.check_only)
    except ValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
