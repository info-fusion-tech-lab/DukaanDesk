import json
import os
import tempfile
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

import tools.StorageManager as storage
from app import app
from tools import accounts
from tools.encrypted_json import load_bytes, load_json, save_json
from tools.GenerateQR import generate_labeled_qrcode
from tools.paths import get_profile_storage_path, reset_profile_storage_path, set_profile_storage_path


class EncryptedAccountTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.key = Fernet.generate_key().decode("ascii")
        self.environment = patch.dict(
            os.environ,
            {
                "SHOPMANAGER_DATA_DIR": self.temp_dir.name,
                "SHOPMANAGER_ENCRYPTION_KEY": self.key,
                "SHOPMANAGER_DESKTOP": "1",
            },
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp_dir.cleanup()

    def test_json_is_encrypted_and_rejects_the_wrong_key(self):
        path = os.path.join(self.temp_dir.name, "records.json")
        value = {"shop": "Private Shop", "sales": [10, 20]}
        save_json(path, value)

        with open(path, "rb") as file:
            encrypted = file.read()
        self.assertTrue(encrypted.startswith(b"SHOPMANAGER-ENCRYPTED-JSON-V1\n"))
        self.assertNotIn(b"Private Shop", encrypted)
        self.assertEqual(load_json(path, {}), value)

        with patch.dict(os.environ, {"SHOPMANAGER_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii")}):
            with self.assertRaisesRegex(RuntimeError, "Could not decrypt local data"):
                load_json(path, {})

    def test_accounts_have_separate_encrypted_profiles_and_password_options(self):
        owner = accounts.create_account("Owner", "Owner Shop", "localpass123")
        second = accounts.create_account("Staff", "Staff Shop")

        self.assertTrue(accounts.verify_password(owner, "localpass123"))
        self.assertFalse(accounts.verify_password(owner, "incorrect"))
        self.assertTrue(accounts.verify_password(second, ""))
        self.assertNotEqual(
            get_profile_storage_path(owner["id"]),
            get_profile_storage_path(second["id"]),
        )

        token = set_profile_storage_path(get_profile_storage_path(owner["id"]))
        try:
            self.assertTrue(storage.save_new_product({"Code": "P-1", "Name": "Owner item"}))
            qr_path = generate_labeled_qrcode("P-1")
        finally:
            reset_profile_storage_path(token)
        with open(qr_path, "rb") as file:
            self.assertTrue(file.read().startswith(b"SHOPMANAGER-ENCRYPTED-BINARY-V1\n"))
        self.assertTrue(load_bytes(qr_path).startswith(b"\x89PNG\r\n\x1a\n"))
        client = app.test_client()
        with client.session_transaction() as session:
            session["account_id"] = owner["id"]
        response = client.get("/storage/qrcodes/P-1.png")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b"\x89PNG\r\n\x1a\n"))

        token = set_profile_storage_path(get_profile_storage_path(second["id"]))
        try:
            self.assertEqual(storage.load_products(), {})
        finally:
            reset_profile_storage_path(token)

        with open(os.path.join(self.temp_dir.name, "Accounts.json"), "rb") as file:
            self.assertTrue(file.read().startswith(b"SHOPMANAGER-ENCRYPTED-JSON-V1\n"))

    def test_first_account_migrates_existing_records_to_its_encrypted_profile(self):
        legacy_path = os.path.join(self.temp_dir.name, "ProductList.json")
        with open(legacy_path, "w", encoding="utf-8") as file:
            json.dump({"OLD-1": {"Name": "Legacy item"}}, file)
        legacy_qr = os.path.join(self.temp_dir.name, "ProductQRs", "OLD-1.png")
        os.makedirs(os.path.dirname(legacy_qr))
        with open(legacy_qr, "wb") as file:
            file.write(b"\x89PNG\r\n\x1a\nlegacy image")

        account = accounts.create_account("Owner", "Migrated Shop")
        profile_path = get_profile_storage_path(account["id"])
        migrated_path = os.path.join(profile_path, "ProductList.json")
        migrated_qr = os.path.join(profile_path, "ProductQRs", "OLD-1.png")

        self.assertFalse(os.path.exists(legacy_path))
        with open(migrated_path, "rb") as file:
            encrypted = file.read()
        self.assertTrue(encrypted.startswith(b"SHOPMANAGER-ENCRYPTED-JSON-V1\n"))
        self.assertNotIn(b"Legacy item", encrypted)
        self.assertEqual(
            load_json(migrated_path, {}),
            {"OLD-1": {"Name": "Legacy item"}},
        )
        with open(migrated_qr, "rb") as file:
            self.assertTrue(file.read().startswith(b"SHOPMANAGER-ENCRYPTED-BINARY-V1\n"))
        self.assertEqual(load_bytes(migrated_qr), b"\x89PNG\r\n\x1a\nlegacy image")

    def test_first_run_login_logout_and_owner_account_creation(self):
        client = app.test_client()
        response = client.post(
            "/setup",
            data={"shop_name": "Corner Shop", "username": "Owner"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Corner Shop", response.data)
        self.assertIn(b"Owner", response.data)

        owner = accounts.list_accounts()[0]
        client.post(
            "/account",
            data={
                "shop_name": "Corner Shop",
                "new_password": "updatedpass123",
                "confirm_password": "updatedpass123",
            },
            follow_redirects=True,
        )
        client.post("/logout")
        response = client.post(f"/login/{owner['id']}", data={}, follow_redirects=True)
        self.assertIn(b"Who's using the app?", response.data)
        response = client.post(
            f"/login/{owner['id']}",
            data={"password": "updatedpass123"},
            follow_redirects=True,
        )
        self.assertIn(b"Corner Shop", response.data)

        response = client.post(
            "/accounts",
            data={"shop_name": "Second Shop", "username": "Staff"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        account_list = accounts.list_accounts()
        staff = next(account for account in account_list if account["username"] == "Staff")
        self.assertTrue(staff["has_password"] is False)

        client.post("/logout")
        response = client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Staff", response.data)

        client.post(f"/login/{staff['id']}", data={})
        self.assertEqual(client.get("/dashboard").status_code, 200)
        self.assertEqual(client.get("/accounts").status_code, 403)


if __name__ == "__main__":
    unittest.main()
