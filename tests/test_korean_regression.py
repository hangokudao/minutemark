import importlib.util
import json
import math
import tempfile
import unittest
import wave
from array import array
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "download-korean-regression.py"
SPEC = importlib.util.spec_from_file_location("download_korean_regression", SCRIPT)
assert SPEC and SPEC.loader
downloader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(downloader)


class KoreanRegressionValidationTests(unittest.TestCase):
    def test_manifest_has_exact_allowlist_and_reproducible_windows(self):
        payload = json.loads((ROOT / "korean-sample-manifest.json").read_text(encoding="utf-8"))
        entries = downloader.validate_manifest(payload)

        self.assertEqual(
            {entry["video_id"] for entry in entries}, downloader.ALLOWED_VIDEO_IDS
        )
        self.assertEqual(len({entry["filename"] for entry in entries}), 10)
        for entry in entries:
            self.assertEqual(entry["source_url"], downloader.canonical_source_url(entry["video_id"]))
            self.assertEqual(entry["duration"], 60)
            self.assertEqual(entry["original_license"], downloader.REQUIRED_SOURCE_LICENSE)

    def test_rejects_malicious_id_and_source_url(self):
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_video_id("../../etc/passwd")
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_video_id("Aaaaaaaaaaa")
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_source_url(
                "https://evil.example/watch?v=07zhNSvDR0A", "07zhNSvDR0A"
            )
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_source_url(
                "http://www.youtube.com/watch?v=07zhNSvDR0A", "07zhNSvDR0A"
            )
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_source_url(
                "https://www.youtube.com/watch?v=07zhNSvDR0A&redirect=https://evil.example",
                "07zhNSvDR0A",
            )

    def test_rejects_path_traversal_and_invalid_clip_numbers(self):
        with tempfile.TemporaryDirectory() as temporary:
            corpus_dir = Path(temporary)
            with self.assertRaises(downloader.ValidationError):
                downloader.resolve_output_path(corpus_dir, "../outside.wav")
            with self.assertRaises(downloader.ValidationError):
                downloader.resolve_output_path(corpus_dir, "/tmp/out.wav")

        invalid_windows = [
            (-1, 60, 120),
            (0, 44, 120),
            (0, 76, 120),
            (0, math.nan, 120),
            (0, 60, 50),
            (True, 60, 120),
        ]
        for start, duration, source_duration in invalid_windows:
            with self.subTest(start=start, duration=duration):
                with self.assertRaises(downloader.ValidationError):
                    downloader.validate_clip_window(start, duration, source_duration)

        payload = json.loads((ROOT / "korean-sample-manifest.json").read_text(encoding="utf-8"))
        payload["samples"][0]["start"] = -1
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_manifest(payload)

    def test_rejects_redirected_metadata_and_non_korean_license(self):
        entry = json.loads((ROOT / "korean-sample-manifest.json").read_text(encoding="utf-8"))["samples"][0]
        metadata = {
            "id": entry["video_id"],
            "webpage_url": entry["source_url"],
            "availability": "public",
            "license": downloader.REQUIRED_SOURCE_LICENSE,
            "language": "ko",
            "duration": 482,
            "title": entry["title"],
            "uploader": entry["uploader"],
        }
        self.assertEqual(downloader.validate_source_metadata(metadata, entry)["language"], "ko")

        metadata["webpage_url"] = "https://r.example/redirect"
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_source_metadata(metadata, entry)
        metadata["webpage_url"] = entry["source_url"]
        metadata["license"] = "Creative Commons Attribution-NonCommercial"
        with self.assertRaises(downloader.ValidationError):
            downloader.validate_source_metadata(metadata, entry)

    @staticmethod
    def _write_wave(path: Path, amplitude: int) -> None:
        sample_rate = 16000
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            for offset in range(0, sample_rate * 60, sample_rate):
                samples = array(
                    "h",
                    (
                        int(amplitude * math.sin(2 * math.pi * 440 * (offset + index) / sample_rate))
                        for index in range(sample_rate)
                    ),
                )
                handle.writeframes(samples.tobytes())

    def test_ffprobe_signal_gate_accepts_audio_and_rejects_silence_invalid_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audible = root / "audible.wav"
            silent = root / "silent.wav"
            invalid = root / "invalid.wav"
            self._write_wave(audible, 12000)
            self._write_wave(silent, 0)
            invalid.write_bytes(b"not a wav")

            downloader.validate_wave_file(audible, expected_duration=60)
            with self.assertRaises(downloader.ValidationError):
                downloader.validate_wave_file(silent, expected_duration=60)
            with self.assertRaises(downloader.ValidationError):
                downloader.validate_wave_file(invalid, expected_duration=60)

    def test_existing_file_requires_validation_and_hash_mismatch_fails(self):
        entry = json.loads((ROOT / "korean-sample-manifest.json").read_text(encoding="utf-8"))["samples"][0]
        entry["sha256"] = ""
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / entry["filename"]
            self._write_wave(output, 12000)

            digest = downloader._check_existing(output, entry)
            self.assertEqual(len(digest), 64)

            entry["sha256"] = "0" * 64
            with self.assertRaises(downloader.ValidationError):
                downloader._check_existing(output, entry)

    def test_check_only_requires_every_manifest_hash(self):
        payload = json.loads(
            (ROOT / "korean-sample-manifest.json").read_text(encoding="utf-8")
        )
        payload["samples"][0]["sha256"] = ""
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                downloader.ValidationError,
                "requires every sample to have a SHA-256",
            ):
                downloader.run(manifest, check_only=True)

    def test_output_byte_cap_is_enforced(self):
        entry = json.loads((ROOT / "korean-sample-manifest.json").read_text(encoding="utf-8"))["samples"][0]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / entry["filename"]
            self._write_wave(output, 12000)
            with patch.object(downloader, "MAX_OUTPUT_BYTES", 1):
                with self.assertRaises(downloader.ValidationError):
                    downloader.validate_wave_file(output, expected_duration=60)


if __name__ == "__main__":
    unittest.main()
