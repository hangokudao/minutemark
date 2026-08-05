import io
import json
import math
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import app
from pipeline import (
    normalize_segment_ids,
    open_a6_request,
    parse_extraction,
    request_a6_json,
)


class HealthTest(unittest.TestCase):
    def test_reports_deployed_commit(self):
        self.assertEqual(
            app.health(),
            {"status": "ok", "commit": app.APP_COMMIT_SHA},
        )


class MonthlyBudgetTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db = app.BUDGET_DB
        self.original_limit = app.A6_RUN_BUDGET_USD
        self.original_reserve = app.A6_REQUEST_RESERVE_USD
        app.BUDGET_DB = Path(self.temp_dir.name) / "budget.sqlite3"
        app.A6_RUN_BUDGET_USD = 1.0
        app.A6_REQUEST_RESERVE_USD = 0.01

    def tearDown(self):
        app.BUDGET_DB = self.original_db
        app.A6_RUN_BUDGET_USD = self.original_limit
        app.A6_REQUEST_RESERVE_USD = self.original_reserve
        self.temp_dir.cleanup()

    def test_records_cumulative_monthly_cost(self):
        app.record_budget(0.00004)
        budget = app.record_budget(0.00003)

        self.assertEqual(budget["month"], app.current_month())
        self.assertAlmostEqual(budget["spent_usd"], 0.00007)
        self.assertAlmostEqual(budget["remaining_usd"], 0.99993)

    def test_rejects_before_reserve_would_cross_limit(self):
        app.record_budget(0.995)

        with self.assertRaises(app.BudgetExceeded):
            app.ensure_budget_room(0.01)


class AudioInputTest(unittest.IsolatedAsyncioTestCase):
    def test_public_korean_sample_is_within_duration_limit(self):
        sample_path = Path(app.KOREAN_SAMPLE_DIR) / "ko-01-action.wav"
        duration = app.audio_duration_seconds(sample_path)

        self.assertAlmostEqual(duration, 34.0, delta=0.2)
        self.assertLessEqual(duration, app.MAX_AUDIO_DURATION_SECONDS)

        for sample in app.SAMPLES.values():
            path = Path(app.KOREAN_SAMPLE_DIR) / sample["filename"]
            sample_duration = app.audio_duration_seconds(path)
            self.assertIsNotNone(sample_duration)
            self.assertGreater(sample_duration, 0)
            self.assertLessEqual(sample_duration, app.MAX_AUDIO_DURATION_SECONDS)
            self.assertAlmostEqual(
                sample_duration, float(sample["duration_seconds"]), delta=1.0
            )

    async def test_invalid_audio_hides_decoder_details(self):
        audio = app.UploadFile(
            filename="invalid.wav",
            file=io.BytesIO(b"not an audio file"),
        )

        with self.assertRaises(app.HTTPException) as raised:
            await app.analyze_upload(audio)

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(
            raised.exception.detail,
            "오디오 파일을 읽을 수 없습니다. "
            "올바른 오디오 파일인지 확인해 주세요.",
        )

    def test_unknown_audio_duration_is_reported_as_unknown(self):
        with patch("app.av.open") as av_open:
            container = av_open.return_value.__enter__.return_value
            container.duration = None
            container.streams = []

            self.assertIsNone(app.audio_duration_seconds(Path("unknown.wav")))

    def test_invalid_audio_duration_is_rejected_before_analysis(self):
        invalid_durations = (None, 0.0, -1.0, math.nan, math.inf)

        for duration in invalid_durations:
            with self.subTest(duration=duration):
                with (
                    patch("app.audio_duration_seconds", return_value=duration),
                    patch("app.reserve_analysis_slot") as reserve_slot,
                    patch("app.ensure_budget_room") as ensure_budget,
                    patch("app.get_model") as get_model,
                    patch("app.transcribe") as transcribe,
                    patch("app.a6_chat") as a6_chat,
                ):
                    with self.assertRaises(ValueError):
                        app.analyze_audio(Path("invalid.wav"), "invalid.wav")

                reserve_slot.assert_not_called()
                ensure_budget.assert_not_called()
                get_model.assert_not_called()
                transcribe.assert_not_called()
                a6_chat.assert_not_called()

    @patch("app.run_in_threadpool", new_callable=AsyncMock)
    async def test_unexpected_value_error_hides_internal_details(
        self, run_in_threadpool
    ):
        run_in_threadpool.side_effect = ValueError(
            "decoder failed at /tmp/private-audio.wav"
        )
        audio = app.UploadFile(
            filename="valid-name.wav",
            file=io.BytesIO(b"RIFF"),
        )

        with self.assertRaises(app.HTTPException) as raised:
            await app.analyze_upload(audio)

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(
            raised.exception.detail,
            "오디오 파일을 처리할 수 없습니다. "
            "올바른 오디오 파일인지 확인해 주세요.",
        )
        self.assertNotIn("/tmp", raised.exception.detail)

    def test_public_samples_include_complete_attribution(self):
        for sample_id, sample in app.SAMPLES.items():
            self.assertTrue(sample["author"])
            self.assertTrue(sample["license_url"].startswith("https://"))
            self.assertIn("WAV 변환", sample["modification"])
            self.assertIn("duration_seconds", sample)
            self.assertGreater(sample["duration_seconds"], 0)
            if sample_id in {"action", "decision"}:
                self.assertEqual(
                    sample["license"],
                    "Creative Commons Attribution (CC BY)",
                )

    def test_kmsav_public_samples_expose_both_license_conditions(self):
        kmsav_ids = {
            "kmsav-01",
            "kmsav-03",
            "kmsav-04",
            "kmsav-05",
            "kmsav-06",
            "kmsav-07",
            "kmsav-08",
            "kmsav-10",
        }
        for sample_id in kmsav_ids:
            sample = app.SAMPLES[sample_id]
            self.assertIn("CC BY-NC-SA 4.0", sample["license"])
            self.assertIn("CC BY", sample["license"])
            self.assertEqual(sample["license_url"], "https://github.com/etri/kmsav")

    def test_public_samples_are_exactly_ten_selected_files(self):
        expected_ids = {
            "action",
            "decision",
            "kmsav-01",
            "kmsav-03",
            "kmsav-04",
            "kmsav-05",
            "kmsav-06",
            "kmsav-07",
            "kmsav-08",
            "kmsav-10",
        }
        expected_files = {
            "ko-01-action.wav",
            "ko-02-decision.wav",
            "kmsav-01-07zhNSvDR0A.wav",
            "kmsav-03-9g6USDTbGhg.wav",
            "kmsav-04-0e76Mv3YWso.wav",
            "kmsav-05-3uuLmiV-HNI.wav",
            "kmsav-06-0FzNHep2onE.wav",
            "kmsav-07-9h7CCmpcirA.wav",
            "kmsav-08-9vY0YzdjoMU.wav",
            "kmsav-10-9bTYC7hkWAI.wav",
        }
        forbidden_files = {
            "kmsav-02-ySffCRdGl8.wav",
            "kmsav-09-0rj144h8MeE.wav",
        }

        self.assertEqual(set(app.SAMPLES), expected_ids)
        self.assertEqual(len(app.SAMPLES), 10)
        filenames = {sample["filename"] for sample in app.SAMPLES.values()}
        self.assertEqual(filenames, expected_files)
        self.assertTrue(filenames.isdisjoint(forbidden_files))

        sample_dir = Path(app.KOREAN_SAMPLE_DIR)
        if sample_dir.is_dir():
            on_disk = {path.name for path in sample_dir.glob("*.wav")}
            self.assertEqual(on_disk, expected_files)
            self.assertTrue(on_disk.isdisjoint(forbidden_files))


class PublicSampleCacheTest(unittest.TestCase):
    def setUp(self):
        app._sample_result_cache.clear()

    def tearDown(self):
        app._sample_result_cache.clear()

    @patch("app.analyze_audio")
    @patch("app.get_sample_cache_store")
    def test_reuses_persistent_sample_result_without_analysis(
        self, get_cache, analyze_audio
    ):
        cached = {
            "audio": "ko-01-action.wav",
            "segments": [],
            "extraction": {"decisions": [], "action_items": []},
        }
        get_cache.return_value.get.return_value = cached

        with (
            patch("app.PERSISTENT_SAMPLE_CACHE_ENABLED", True),
            patch("app.sample_cache_key", return_value="sample-key"),
        ):
            result = app.analyze_sample("action")

        analyze_audio.assert_not_called()
        self.assertEqual(result["sample"]["id"], "action")
        self.assertEqual(result["audio_url"], "/audio/action")

    @patch("app.analyze_audio")
    @patch("app.get_sample_cache_store")
    def test_persists_successful_sample_result(self, get_cache, analyze_audio):
        generated = {
            "audio": "ko-01-action.wav",
            "segments": [],
            "extraction": {"decisions": [], "action_items": []},
        }
        cache = get_cache.return_value
        cache.get.return_value = None
        analyze_audio.return_value = generated

        with (
            patch("app.PERSISTENT_SAMPLE_CACHE_ENABLED", True),
            patch("app.sample_cache_key", return_value="sample-key"),
        ):
            result = app.analyze_sample("action")

        cache.put.assert_called_once_with("sample-key", generated)
        self.assertEqual(result["sample"]["id"], "action")


class GroundingOutputTest(unittest.TestCase):
    def test_normalizes_comma_separated_segment_ids(self):
        self.assertEqual(
            normalize_segment_ids("S5, S6"),
            ["S5", "S6"],
        )

    def test_keeps_valid_segment_id_array(self):
        self.assertEqual(
            normalize_segment_ids(["S5", "S6"]),
            ["S5", "S6"],
        )

    def test_rejects_invalid_fallback_item_shape(self):
        with self.assertRaises(RuntimeError):
            parse_extraction(
                {
                    "items": [
                        {
                            "kind": "action_item",
                            "text": "후속 작업을 수행한다.",
                            "owner": "",
                            "due": "",
                            "segment_ids": [],
                        }
                    ]
                }
            )


class InstanceCapacityTest(unittest.TestCase):
    def setUp(self):
        self.original_limit = app.MAX_ANALYSES_PER_INSTANCE
        self.original_count = app._analysis_count
        app.MAX_ANALYSES_PER_INSTANCE = 2
        app._analysis_count = 0

    def tearDown(self):
        app.MAX_ANALYSES_PER_INSTANCE = self.original_limit
        app._analysis_count = self.original_count

    def test_rejects_after_instance_analysis_limit(self):
        app.reserve_analysis_slot()
        app.reserve_analysis_slot()

        with self.assertRaises(app.CapacityExceeded):
            app.reserve_analysis_slot()


class A6RetryTest(unittest.TestCase):
    @patch("pipeline.time.sleep")
    @patch("pipeline.urllib.request.urlopen")
    def test_retries_one_transient_502(self, urlopen, sleep):
        response = Mock()
        urlopen.side_effect = [
            urllib.error.HTTPError(
                "https://api.a6api.com/v1/chat/completions",
                502,
                "Bad Gateway",
                None,
                None,
            ),
            response,
        ]

        self.assertIs(open_a6_request(Mock()), response)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    @patch("pipeline.time.sleep")
    @patch("pipeline.urllib.request.urlopen")
    def test_retries_one_bare_timeout(self, urlopen, sleep):
        response = Mock()
        urlopen.side_effect = [TimeoutError("read timed out"), response]

        self.assertIs(open_a6_request(Mock()), response)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    @patch("pipeline.time.sleep")
    @patch("pipeline.urllib.request.urlopen")
    def test_propagates_after_two_bare_timeouts(self, urlopen, sleep):
        timeout = TimeoutError("read timed out")
        urlopen.side_effect = [timeout, timeout]

        with self.assertRaises(TimeoutError) as raised:
            open_a6_request(Mock())

        self.assertIs(raised.exception, timeout)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    @patch("pipeline.open_a6_request")
    def test_falls_back_without_json_schema_on_400(self, open_request):
        response = io.BytesIO(json.dumps({"choices": []}).encode())
        open_request.side_effect = [
            urllib.error.HTTPError(
                "https://api.a6api.com/v1/chat/completions",
                400,
                "Bad Request",
                None,
                None,
            ),
            response,
        ]

        payload = request_a6_json(
            {
                "model": "test-model",
                "response_format": {"type": "json_schema"},
                "messages": [],
            }
        )

        self.assertEqual(payload, {"choices": []})
        first_body = json.loads(open_request.call_args_list[0].args[0].data)
        fallback_body = json.loads(open_request.call_args_list[1].args[0].data)
        self.assertIn("response_format", first_body)
        self.assertNotIn("response_format", fallback_body)


if __name__ == "__main__":
    unittest.main()
