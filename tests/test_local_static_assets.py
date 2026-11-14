import unittest

from app import app


class LocalStaticAssetTests(unittest.TestCase):
    def test_local_fonts_and_icons_are_served(self):
        client = app.test_client()
        asset_paths = (
            "/static/fonts.css",
            "/static/vendor/inter/inter-latin-wght-normal.woff2",
            "/static/vendor/fontawesome/css/all.min.css",
            "/static/vendor/fontawesome/webfonts/fa-solid-900.woff2",
        )

        for asset_path in asset_paths:
            with self.subTest(asset_path=asset_path):
                response = client.get(asset_path)
                try:
                    self.assertEqual(response.status_code, 200)
                    self.assertGreater(len(response.data), 0)
                finally:
                    response.close()


if __name__ == "__main__":
    unittest.main()
