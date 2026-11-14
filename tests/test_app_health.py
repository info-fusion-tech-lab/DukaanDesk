import unittest

from app import app


class HealthRouteTests(unittest.TestCase):
    def test_health_route_reports_ready(self):
        response = app.test_client().get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
