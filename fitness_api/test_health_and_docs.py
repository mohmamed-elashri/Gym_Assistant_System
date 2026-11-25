from django.test import TestCase


class HealthAndDocsTests(TestCase):
    def test_live(self):
        response = self.client.get("/api/health/live/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready_checks_database(self):
        response = self.client.get("/api/health/ready/")
        self.assertEqual(response.status_code, 200)

    def test_openapi_schema_is_served(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)
