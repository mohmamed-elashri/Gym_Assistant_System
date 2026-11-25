"""Input validation and throttling checks for the chat endpoint."""

from django.contrib.auth import get_user_model
from django.test import TestCase


class ChatValidationTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user("chatuser", password="pw-12345-xyz")
        self.client.login(username="chatuser", password="pw-12345-xyz")

    def test_missing_message_returns_400(self):
        response = self.client.post(
            "/api/chat/", data={}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_non_string_message_returns_400(self):
        response = self.client.post(
            "/api/chat/", data={"message": 123}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_overlong_message_returns_400(self):
        response = self.client.post(
            "/api/chat/", data={"message": "x" * 2001}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
