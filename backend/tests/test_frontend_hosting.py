import unittest

from app.main import app


class FrontendHostingTests(unittest.TestCase):
    def test_serves_vite_asset_bundle_at_assets_path(self):
        route_paths = {route.path for route in app.routes}

        self.assertIn("/assets", route_paths)


if __name__ == "__main__":
    unittest.main()
