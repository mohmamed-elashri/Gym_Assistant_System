"""API endpoints require authentication and enforce CSRF."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

ENDPOINTS = [
    "/api/predict/",
    "/api/chat/",
    "/api/workout-plan/",
    "/api/workout-calories/",
]


class ApiAuthTests(TestCase):
    def test_anonymous_requests_are_rejected(self):
        for url in ENDPOINTS:
            response = self.client.post(
                url, data=json.dumps({}), content_type="application/json"
            )
            self.assertIn(response.status_code, (401, 403), url)

    def test_authenticated_request_reaches_validation(self):
        get_user_model().objects.create_user("u1", password="pw-12345-xyz")
        self.client.login(username="u1", password="pw-12345-xyz")
        response = self.client.post(
            "/api/chat/", data=json.dumps({}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_csrf_enforced_for_session_users(self):
        get_user_model().objects.create_user("u2", password="pw-12345-xyz")
        client = Client(enforce_csrf_checks=True)
        client.login(username="u2", password="pw-12345-xyz")
        response = client.post(
            "/api/chat/",
            data=json.dumps({"message": "hi"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_docs_and_health_stay_public(self):
        for url in ("/api/docs/", "/api/schema/", "/api/health/live/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
