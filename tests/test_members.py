import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import HTTPException
from starlette.requests import Request

import app
import members


class AuthenticationBoundaryTest(unittest.TestCase):
    def test_requires_bearer_token(self):
        with self.assertRaises(HTTPException) as raised:
            members.verify_bearer_token(None, verifier=Mock())

        self.assertEqual(raised.exception.status_code, 401)

    def test_verifies_signature_expiry_and_revocation(self):
        verifier = Mock(
            return_value={
                "uid": "user-a",
                "email": "person@example.com",
                "auth_time": 100,
                "firebase": {"sign_in_provider": "google.com"},
            }
        )

        user = members.verify_bearer_token(
            "Bearer signed-token",
            verifier=verifier,
        )

        verifier.assert_called_once_with("signed-token", check_revoked=True)
        self.assertEqual(user.uid, "user-a")
        self.assertEqual(user.email, "person@example.com")

    def test_rejects_non_google_firebase_provider(self):
        verifier = Mock(
            return_value={
                "uid": "user-a",
                "email": "person@example.com",
                "auth_time": 100,
                "firebase": {"sign_in_provider": "password"},
            }
        )

        with self.assertRaises(HTTPException) as raised:
            members.verify_bearer_token(
                "Bearer signed-token",
                verifier=verifier,
            )

        self.assertEqual(raised.exception.status_code, 401)

    def test_hides_token_verification_details(self):
        verifier = Mock(side_effect=ValueError("decoded token leaked"))

        with self.assertLogs("minutemark.members", level="WARNING") as logs:
            with self.assertRaises(HTTPException) as raised:
                members.verify_bearer_token(
                    "Bearer private-token",
                    verifier=verifier,
                )

        self.assertEqual(raised.exception.status_code, 401)
        self.assertNotIn("private-token", raised.exception.detail)
        self.assertNotIn("decoded", raised.exception.detail)
        self.assertNotIn("private-token", " ".join(logs.output))
        self.assertNotIn("decoded token leaked", " ".join(logs.output))

    def test_account_deletion_requires_recent_google_login(self):
        user = members.AuthUser(
            uid="user-a",
            email="person@example.com",
            auth_time=100,
        )

        with self.assertRaises(HTTPException) as raised:
            members.require_recent_auth(user, now=500)

        self.assertEqual(raised.exception.status_code, 401)
        self.assertEqual(raised.exception.headers["X-Reauth-Required"], "true")


class MeetingOwnershipTest(unittest.TestCase):
    def test_unknown_or_other_users_meeting_is_not_found(self):
        store = Mock()
        store.get.return_value = None

        with self.assertRaises(HTTPException) as raised:
            members.get_owned_meeting(store, "user-a", "meeting-b")

        store.get.assert_called_once_with("user-a", "meeting-b")
        self.assertEqual(raised.exception.status_code, 404)

    def test_meeting_limit_is_checked_before_analysis(self):
        store = Mock()
        store.count.return_value = members.MAX_MEETINGS_PER_USER

        with self.assertRaises(HTTPException) as raised:
            members.ensure_meeting_capacity(store, "user-a")

        self.assertEqual(raised.exception.status_code, 409)

    def test_total_storage_limit_is_checked_before_analysis(self):
        store = members.FirebaseMeetingStore.__new__(members.FirebaseMeetingStore)
        store._bucket = Mock()
        store._bucket.list_blobs.return_value = [
            Mock(size=members.MAX_TOTAL_AUDIO_BYTES)
        ]

        with self.assertRaises(HTTPException) as raised:
            store.ensure_total_audio_capacity(1)

        self.assertEqual(raised.exception.status_code, 507)

    def test_account_content_is_deleted_before_auth_user(self):
        events = []
        store = Mock()
        store.delete_all.side_effect = lambda uid: events.append(("content", uid))
        delete_auth_user = Mock(
            side_effect=lambda uid: events.append(("auth", uid))
        )
        user = members.AuthUser(
            uid="user-a",
            email="person@example.com",
            auth_time=int(time.time()),
        )

        members.delete_account(user, store, delete_auth_user)

        self.assertEqual(events, [("content", "user-a"), ("auth", "user-a")])

    def test_incomplete_content_cleanup_keeps_auth_user(self):
        store = Mock()
        store.delete_all.side_effect = RuntimeError("cleanup incomplete")
        delete_auth_user = Mock()
        user = members.AuthUser(
            uid="user-a",
            email="person@example.com",
            auth_time=int(time.time()),
        )

        with self.assertRaises(RuntimeError):
            members.delete_account(user, store, delete_auth_user)

        delete_auth_user.assert_not_called()

    def test_storage_object_is_deleted_if_firestore_create_fails(self):
        store = members.FirebaseMeetingStore.__new__(members.FirebaseMeetingStore)
        blob = Mock()
        blob.generation = 123
        store._bucket = Mock()
        store._bucket.blob.return_value = blob
        store._signed_audio_url = Mock(return_value="https://signed.example/audio")
        document = Mock()
        document.create.side_effect = RuntimeError("firestore unavailable")
        store._document = Mock(return_value=document)

        with tempfile.NamedTemporaryFile() as audio:
            with self.assertRaises(RuntimeError):
                store.create(
                    "user-a",
                    "meeting-a",
                    "회의",
                    Path(audio.name),
                    "audio/wav",
                    4,
                    "sha256",
                    {"audio": "회의"},
                )

        blob.delete.assert_called_once_with(if_generation_match=123)
        self.assertEqual(blob.cache_control, "private, no-store, max-age=0")
        self.assertEqual(
            document.create.call_args.args[0]["audio"]["generation"],
            123,
        )

    def test_signed_url_failure_leaves_no_storage_or_firestore_record(self):
        store = members.FirebaseMeetingStore.__new__(members.FirebaseMeetingStore)
        blob = Mock()
        store._bucket = Mock()
        store._bucket.blob.return_value = blob
        document = Mock()
        store._document = Mock(return_value=document)
        store._signed_audio_url = Mock(side_effect=RuntimeError("signer unavailable"))

        with tempfile.NamedTemporaryFile() as audio:
            with self.assertRaises(RuntimeError):
                store.create(
                    "user-a",
                    "meeting-a",
                    "회의",
                    Path(audio.name),
                    "audio/wav",
                    4,
                    "sha256",
                    {"audio": "회의"},
                )

        blob.upload_from_filename.assert_not_called()
        document.create.assert_not_called()

    def test_oversized_firestore_document_is_rejected_before_upload(self):
        store = members.FirebaseMeetingStore.__new__(members.FirebaseMeetingStore)
        blob = Mock()
        store._bucket = Mock()
        store._bucket.blob.return_value = blob
        document = Mock()
        store._document = Mock(return_value=document)
        store._signed_audio_url = Mock(return_value="https://signed.example/audio")

        with tempfile.NamedTemporaryFile() as audio:
            with self.assertRaises(HTTPException) as raised:
                store.create(
                    "user-a",
                    "meeting-a",
                    "회의",
                    Path(audio.name),
                    "audio/wav",
                    4,
                    "sha256",
                    {"transcript": "가" * members.MAX_FIRESTORE_DOCUMENT_BYTES},
                )

        self.assertEqual(raised.exception.status_code, 413)
        blob.upload_from_filename.assert_not_called()
        document.create.assert_not_called()

    def test_meeting_deletes_audio_before_firestore_document(self):
        events = []
        store = members.FirebaseMeetingStore.__new__(members.FirebaseMeetingStore)
        blob = Mock()
        blob.exists.return_value = True
        blob.delete.side_effect = lambda **_kwargs: events.append("audio")
        store._bucket = Mock()
        store._bucket.blob.return_value = blob
        document = Mock()
        document.get.return_value = Mock(
            exists=True,
            to_dict=Mock(
                return_value={
                    "audio": {"object_path": "object", "generation": 123}
                }
            ),
        )
        document.delete.side_effect = lambda: events.append("document")
        store._document = Mock(return_value=document)

        self.assertTrue(store.delete("user-a", "meeting-a"))
        self.assertEqual(events, ["audio", "document"])
        store._bucket.blob.assert_called_once_with("object", generation=123)
        blob.delete.assert_called_once_with(if_generation_match=123)

    def test_account_cleanup_deletes_orphaned_user_audio(self):
        store = members.FirebaseMeetingStore.__new__(members.FirebaseMeetingStore)
        collection = Mock()
        collection.stream.return_value = []
        collection.limit.return_value.stream.return_value = []
        store._collection = Mock(return_value=collection)
        orphan = Mock(generation=456)
        store._bucket = Mock()
        store._bucket.list_blobs.side_effect = [[orphan], []]

        store.delete_all("user-a")

        self.assertEqual(
            store._bucket.list_blobs.call_args_list[0].kwargs,
            {"prefix": "users/user-a/"},
        )
        orphan.delete.assert_called_once_with(if_generation_match=456)


class AuthenticatedUploadRouteTest(unittest.IsolatedAsyncioTestCase):
    async def test_chunked_body_within_limit_remains_compatible(self):
        boundary = "boundary"
        body = b"".join(
            [
                (
                    f"--{boundary}\r\n"
                    'Content-Disposition: form-data; name="audio"; filename="meeting.wav"\r\n'
                    "Content-Type: audio/wav\r\n\r\naudio\r\n"
                ).encode(),
                (
                    f"--{boundary}\r\n"
                    'Content-Disposition: form-data; name="title"\r\n\r\n'
                    "제품 회의\r\n"
                ).encode(),
                (
                    f"--{boundary}\r\n"
                    'Content-Disposition: form-data; name="participant_notice_confirmed"\r\n\r\n'
                    "true\r\n"
                ).encode(),
                f"--{boundary}--\r\n".encode(),
            ]
        )
        messages = [{"type": "http.request", "body": body, "more_body": False}]

        async def receive():
            return messages.pop(0)

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/meetings",
                "headers": [
                    (
                        b"content-type",
                        f"multipart/form-data; boundary={boundary}".encode(),
                    )
                ],
            },
            receive,
        )
        store = Mock()
        store.count.return_value = 0
        store.create.return_value = {"id": "meeting-a", "title": "제품 회의"}
        created_files = []
        real_spooled_file = tempfile.SpooledTemporaryFile

        def tracked_spooled_file(*args, **kwargs):
            file = real_spooled_file(*args, **kwargs)
            created_files.append(file)
            return file

        with (
            patch(
                "app.authenticated_user",
                return_value=members.AuthUser("user-a", "", int(time.time())),
            ),
            patch("app.get_meeting_store", return_value=store),
            patch("app.analyze_audio", return_value={"segments": []}),
            patch(
                "starlette.formparsers.SpooledTemporaryFile",
                side_effect=tracked_spooled_file,
            ),
        ):
            result = await app.create_meeting(request)

        self.assertEqual(result, {"id": "meeting-a", "title": "제품 회의"})
        store.create.assert_called_once()
        self.assertTrue(created_files)
        self.assertTrue(all(file.closed for file in created_files))

    async def test_chunked_oversized_body_is_rejected_before_form_completes(self):
        boundary = "boundary"
        first_chunk = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="audio"; filename="meeting.wav"\r\n'
            "Content-Type: audio/wav\r\n\r\n"
        ).encode() + b"x"
        second_chunk = b"x" * 5 + f"\r\n--{boundary}--\r\n".encode()
        messages = [
            {
                "type": "http.request",
                "body": first_chunk,
                "more_body": True,
            },
            {
                "type": "http.request",
                "body": second_chunk,
                "more_body": True,
            },
            {"type": "http.request", "body": b"", "more_body": False},
        ]
        received = []

        async def receive():
            received.append(len(messages))
            return messages.pop(0)

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/meetings",
                "headers": [
                    (
                        b"content-type",
                        f"multipart/form-data; boundary={boundary}".encode(),
                    )
                ],
            },
            receive,
        )
        store = Mock()
        store.count.return_value = 0
        created_files = []
        real_spooled_file = tempfile.SpooledTemporaryFile

        def tracked_spooled_file(*args, **kwargs):
            file = real_spooled_file(*args, **kwargs)
            created_files.append(file)
            return file

        with (
            patch(
                "app.authenticated_user",
                return_value=members.AuthUser("user-a", "", int(time.time())),
            ),
            patch("app.get_meeting_store", return_value=store),
            patch("app.MAX_MULTIPART_BYTES", len(first_chunk) + 4),
            patch(
                "starlette.formparsers.SpooledTemporaryFile",
                side_effect=tracked_spooled_file,
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                await app.create_meeting(request)

        self.assertEqual(raised.exception.status_code, 413)
        self.assertEqual(raised.exception.detail, "파일은 20MB 이하여야 합니다.")
        self.assertEqual(len(received), 2)
        self.assertTrue(created_files)
        self.assertTrue(all(file.closed for file in created_files))

    async def test_rejects_before_reading_multipart_body(self):
        async def receive():
            raise AssertionError("request body must not be read before auth")

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/meetings",
                "headers": [],
            },
            receive,
        )

        with self.assertRaises(HTTPException) as raised:
            await app.create_meeting(request)

        self.assertEqual(raised.exception.status_code, 401)

    def test_anonymous_upload_endpoint_is_not_registered(self):
        paths = {route.path for route in app.app.routes}
        self.assertNotIn("/api/analyze", paths)

    async def test_same_idempotency_key_returns_saved_meeting_without_body(self):
        async def receive():
            raise AssertionError("saved request must not read multipart again")

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/meetings",
                "headers": [(b"idempotency-key", b"a" * 32)],
            },
            receive,
        )
        store = Mock()
        store.get.return_value = {"id": "a" * 32, "title": "saved"}

        with (
            patch(
                "app.authenticated_user",
                return_value=members.AuthUser("user-a", "", int(time.time())),
            ),
            patch("app.get_meeting_store", return_value=store),
        ):
            meeting = await app.create_meeting(request)

        self.assertEqual(meeting["title"], "saved")
        store.count.assert_not_called()

    def test_missing_or_other_users_meeting_delete_returns_404(self):
        request = Mock()
        store = Mock()
        store.delete.return_value = False

        with (
            patch(
                "app.authenticated_user",
                return_value=members.AuthUser("user-a", "", int(time.time())),
            ),
            patch("app.get_meeting_store", return_value=store),
        ):
            with self.assertRaises(HTTPException) as raised:
                app.delete_meeting("missing", request)

        self.assertEqual(raised.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
