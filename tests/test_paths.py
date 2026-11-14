import os
import tempfile
import unittest
from unittest.mock import patch

from tools.paths import get_storage_path


class StoragePathTests(unittest.TestCase):
    def test_environment_path_is_used_and_created(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = os.path.join(temp_dir, "shop-data")
            with patch.dict(os.environ, {"SHOPMANAGER_DATA_DIR": data_dir}):
                result = get_storage_path()

            self.assertEqual(result, os.path.abspath(data_dir))
            self.assertTrue(os.path.isdir(data_dir))

    def test_default_path_is_project_storage(self):
        with patch.dict(os.environ):
            os.environ.pop("SHOPMANAGER_DATA_DIR", None)
            result = get_storage_path()

        self.assertEqual(result, os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage"))


if __name__ == "__main__":
    unittest.main()
