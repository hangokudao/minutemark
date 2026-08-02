import hashlib
import io
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

import app
import members


class FrontendContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (app.STATIC_DIR / "index.html").read_text(encoding="utf-8")
        cls.javascript = (app.STATIC_DIR / "app.js").read_text(encoding="utf-8")
        cls.styles = (app.STATIC_DIR / "styles.css").read_text(encoding="utf-8")
        cls.backend = Path(app.__file__).read_text(encoding="utf-8")

    def test_client_routes_are_refreshable(self):
        paths = {route.path for route in app.app.routes}
        self.assertTrue(
            {
                "/samples",
                "/auth",
                "/meetings",
                "/meetings/new",
                "/meetings/{meeting_id}",
                "/account",
                "/privacy",
            }.issubset(paths)
        )

    def test_new_meeting_requires_title_and_participant_notice_controls(self):
        self.assertIn('id="meeting-title"', self.html)
        self.assertIn('maxlength="80"', self.html)
        self.assertIn('id="participant-notice"', self.html)
        self.assertIn('id="analyze-save-button"', self.html)

    def test_mobile_navigation_exposes_required_destinations(self):
        self.assertIn('id="mobile-menu-button"', self.html)
        self.assertIn('id="mobile-menu-dialog"', self.html)
        for path in (
            "/meetings/new",
            "/meetings",
            "/samples",
            "/account",
            "/privacy",
        ):
            self.assertIn(f'href="{path}"', self.html)
        self.assertIn("@media (max-width: 560px)", self.styles)
        self.assertIn(
            "body.is-member .meeting-nav.member-only {\n    display: none !important;",
            self.styles,
        )

    def test_history_and_unsaved_draft_guards_are_registered(self):
        self.assertIn('window.addEventListener("popstate"', self.javascript)
        self.assertIn('window.addEventListener("beforeunload"', self.javascript)
        self.assertIn("history.pushState", self.javascript)
        self.assertIn("history.replaceState", self.javascript)
        self.assertIn('await navigate("/privacy");', self.javascript)
        self.assertNotIn(
            'navigate("/privacy", { skipDraftGuard: true })', self.javascript
        )

    def test_guest_ui_hides_member_history_and_internal_budget(self):
        self.assertIn(
            '<section class="meeting-nav member-only"', self.html
        )
        self.assertNotIn('id="budget-status"', self.html)
        self.assertNotIn("/api/budget", self.javascript)
        self.assertNotIn("/api/budget", {route.path for route in app.app.routes})

    def test_private_requests_are_invalidated_at_auth_boundaries(self):
        self.assertIn("let privateRequestGeneration = 0;", self.javascript)
        self.assertIn("new AbortController()", self.javascript)
        self.assertIn("invalidatePrivateRequests();\n  await signOut(auth);", self.javascript)
        self.assertIn("isPrivateSessionCurrent(session)", self.javascript)
        self.assertIn("clearPrivateResult();\n    await navigate(\"/meetings\"", self.javascript)

    def test_csp_allows_only_required_google_login_script_origin(self):
        self.assertIn(
            "script-src 'self' https://www.gstatic.com https://apis.google.com",
            self.backend,
        )
        self.assertIn(
            'response.headers["Cross-Origin-Opener-Policy"]',
            self.backend,
        )
        self.assertIn('"same-origin-allow-popups"', self.backend)

    def test_google_login_uses_patched_pinned_firebase_auth(self):
        vendor = app.STATIC_DIR / "vendor" / "firebase-auth-12.16.0-patched.js"
        source = vendor.read_text(encoding="utf-8")
        self.assertIn('import("/static/vendor/firebase-auth-12.16.0-patched.js")', self.javascript)
        self.assertEqual(
            hashlib.sha256(vendor.read_bytes()).hexdigest(),
            "902cd602e8a78b19f49b5eeea05fcc9313d5b65b2d1ac7bfdb6e27a628960261",
        )
        self.assertIn("Modified by MinuteMark on 2026-08-02", source)
        self.assertIn('void 0!==n?t(!!n):_fail(e,"internal-error")', source)
        self.assertNotIn('void 0!==n&&t(!!n),_fail(e,"internal-error")', source)

    def test_google_only_auth_and_privacy_contact_are_explicit(self):
        self.assertIn("첫 로그인은 회원가입으로 처리됩니다.", self.html)
        self.assertIn("Google로 계속하기", self.html)
        self.assertNotIn('type="password"', self.html)
        self.assertIn("MinuteMark 개인정보 보호 담당", self.html)
        self.assertIn("mailto:hangokudao@gmail.com", self.html)

    def test_auth_route_renders_before_persisted_auth_resolution(self):
        self.assertIn(
            'if (location.pathname === "/auth") await renderRoute(currentPath);\n'
            '    const [appModule, authModule] = await Promise.all([',
            self.javascript,
        )
        self.assertIn('id="google-signin" type="button" disabled', self.html)
        self.assertIn("elements.googleSignin.disabled = false;", self.javascript)

    def test_portfolio_limit_is_visible_and_repeated_in_privacy_notice(self):
        self.assertIn('class="portfolio-notice"', self.html)
        self.assertIn('id="auth-portfolio-note"', self.html)
        self.assertIn('id="mobile-portfolio-note"', self.html)
        self.assertGreaterEqual(self.html.count("정식 서비스가 아닙니다."), 4)
        self.assertGreaterEqual(
            self.html.count("민감하거나 실제 업무용인 파일은 업로드하지 마세요."),
            2,
        )

    def test_destructive_actions_use_explicit_confirmation_controls(self):
        self.assertIn('id="delete-meeting-dialog"', self.html)
        self.assertIn('id="confirm-delete-meeting"', self.html)
        self.assertIn('id="delete-account-confirm"', self.html)
        self.assertIn('value.trim() !== "탈퇴"', self.javascript)
        self.assertNotIn("이 회의의 원본 오디오와 분석 결과를 삭제할까요?", self.javascript)


class MeetingFormBoundaryTest(unittest.IsolatedAsyncioTestCase):
    def request_with_form(self, form):
        request = Mock()
        request.headers = {}
        request.form = AsyncMock(return_value=form)
        return request

    def audio_upload(self):
        return UploadFile(
            io.BytesIO(b"audio"),
            filename="meeting.wav",
            headers=Headers({"content-type": "audio/wav"}),
        )

    async def test_participant_notice_is_required_before_analysis(self):
        request = self.request_with_form(
            {"audio": self.audio_upload(), "title": "제품 회의"}
        )
        store = Mock()
        store.count.return_value = 0

        with (
            patch(
                "app.authenticated_user",
                return_value=members.AuthUser("user-a", "", int(time.time())),
            ),
            patch("app.get_meeting_store", return_value=store),
            patch("app.analyze_audio") as analyze_audio,
        ):
            with self.assertRaises(HTTPException) as raised:
                await app.create_meeting(request)

        self.assertEqual(raised.exception.status_code, 400)
        analyze_audio.assert_not_called()

    async def test_user_title_is_saved_after_notice_confirmation(self):
        request = self.request_with_form(
            {
                "audio": self.audio_upload(),
                "title": "  분기   계획 회의  ",
                "participant_notice_confirmed": "true",
            }
        )
        store = Mock()
        store.count.return_value = 0
        store.create.return_value = {"id": "meeting-a", "title": "분기 계획 회의"}

        with (
            patch(
                "app.authenticated_user",
                return_value=members.AuthUser("user-a", "", int(time.time())),
            ),
            patch("app.get_meeting_store", return_value=store),
            patch("app.analyze_audio", return_value={"segments": []}),
        ):
            result = await app.create_meeting(request)

        self.assertEqual(result["title"], "분기 계획 회의")
        self.assertEqual(store.create.call_args.args[2], "분기 계획 회의")


if __name__ == "__main__":
    unittest.main()
