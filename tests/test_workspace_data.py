import os
import json
import tempfile
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from app import app
from tools import accounts
from tools.encrypted_json import load_json, save_json
from tools.paths import (
    get_profile_storage_path,
    reset_profile_storage_path,
    set_profile_storage_path,
    storage_file,
)
from tools.workspace_data import load_workspace, save_workspace


class WorkspaceDataTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.environment = patch.dict(
            os.environ,
            {
                "SHOPMANAGER_DATA_DIR": self.temp_dir.name,
                "SHOPMANAGER_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii"),
                "SHOPMANAGER_DESKTOP": "1",
            },
        )
        self.environment.start()
        self.account = accounts.create_account("Owner", "Corner Shop")
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["account_id"] = self.account["id"]

    def tearDown(self):
        self.environment.stop()
        self.temp_dir.cleanup()

    def test_legacy_products_customers_and_sales_migrate_to_encrypted_workspace(self):
        token = set_profile_storage_path(
            get_profile_storage_path(self.account["id"])
        )
        try:
            save_json(
                storage_file("ProductList.json"),
                {
                    "P-1": {
                        "Name": "Notebook",
                        "Price": 25,
                        "Quantity": 4,
                        "MinStockLevel": 2,
                        "Category": "Stationery",
                    }
                },
            )
            save_json(
                storage_file("CustomerList.json"),
                {
                    "9000": {
                        "Name": "Asha",
                        "Phone": "9000",
                        "Balance": 30,
                        "Transactions": [
                            {
                                "Timestamp": "2025-01-02 10:30:00",
                                "Type": "GAVE",
                                "Amount": 30,
                                "Note": "Credit sale",
                                "NewBalance": 30,
                            }
                        ],
                    }
                },
            )
            save_json(
                storage_file("SalesLog.json"),
                {
                    "INV-1": {
                        "Timestamp": "2025-01-02 10:30:00",
                        "Items": [
                            {
                                "ProductCode": "P-1",
                                "ProductName": "Notebook",
                                "Quantity": 2,
                                "SellingPrice": 25,
                            }
                        ],
                        "PaymentType": "split",
                        "PaymentSplit": {"cash": 20, "online": 10, "udhari": 20},
                        "CustomerPhone": "9000",
                        "TotalAmount": 50,
                        "Note": "Split payment",
                    }
                },
            )

            migrated = load_workspace()
            saved_path = storage_file("DukaanDeskWorkspace.json")
            with open(saved_path, "rb") as saved_file:
                self.assertTrue(
                    saved_file.read().startswith(b"SHOPMANAGER-ENCRYPTED-JSON-V1\n")
                )
        finally:
            reset_profile_storage_path(token)

        self.assertEqual(migrated["products"][0]["id"], "P-1")
        self.assertEqual(migrated["products"][0]["cost"], 0)
        self.assertEqual(migrated["customers"][0]["balance"], 30)
        self.assertEqual(migrated["customers"][0]["transactions"][0]["type"], "GAVE")
        self.assertEqual(migrated["sales"][0]["credit"], 20)
        self.assertEqual(migrated["sales"][0]["items"][0]["qty"], 2)

    def test_workspace_api_saves_profile_data_and_rejects_bad_imports(self):
        data = {
            "products": [],
            "customers": [],
            "suppliers": [],
            "staff": [],
            "sales": [],
        }
        response = self.client.put("/api/workspace/data", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

        legacy_product = {
            "id": "p1",
            "code": "P-1",
            "name": "Notebook",
            "category": "Stationery",
            "price": 25,
            "quantity": 3,
            "minimum": 1,
        }
        response = self.client.put(
            "/api/workspace/data",
            json={**data, "products": [legacy_product]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["products"][0]["cost"], 0)

        invalid = {**data, "products": [{"id": "p1"}, {"id": "p1"}]}
        response = self.client.put("/api/workspace/data", json=invalid)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

        response = self.client.put(
            "/api/workspace/data",
            json={
                **data,
                "products": [{**legacy_product, "cost": -1}],
            },
        )
        self.assertEqual(response.status_code, 400)

        invalid_attendance = {
            **data,
            "staff": [
                {
                    "id": "staff-1",
                    "name": "Worker",
                    "phone": "",
                    "role": "Helper",
                    "salary": 100,
                    "joinDate": "2025-01-01",
                    "attendance": {"2025-01-01": []},
                }
            ],
        }
        response = self.client.put("/api/workspace/data", json=invalid_attendance)
        self.assertEqual(response.status_code, 400)

        response = self.client.put(
            "/api/workspace/settings",
            json={"theme": []},
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.put("/api/workspace/data", json=data)
        self.assertEqual(response.status_code, 200)

        token = set_profile_storage_path(
            get_profile_storage_path(self.account["id"])
        )
        try:
            self.assertEqual(load_workspace(), data)
            self.assertEqual(
                load_json(storage_file("DukaanDeskWorkspace.json"), None),
                data,
            )
        finally:
            reset_profile_storage_path(token)

    def test_dashboard_uses_workspace_and_legacy_pages_redirect(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Corner Shop", response.data)
        self.assertNotIn(b"Demo Shop", response.data)
        self.assertNotIn(b"Reset demo data", response.data)
        self.assertIn(b"Reset appearance", response.data)
        self.assertIn(b'id="pCost"', response.data)
        self.assertIn(b'href="#i-export"', response.data)
        self.assertIn(b'href="#i-import"', response.data)
        self.assertEqual(self.client.get("/inventory").status_code, 302)
        self.assertEqual(self.client.get("/customers").status_code, 302)
        self.assertEqual(self.client.get("/sales").status_code, 302)
        self.assertEqual(self.client.get("/reports").status_code, 302)

    def test_account_pages_use_the_saved_theme_and_workspace_shell(self):
        response = self.client.put(
            "/api/workspace/settings",
            json={
                "theme": "dark",
                "accent": "#2563eb",
                "layout": "topnav",
                "density": "comfortable",
                "shopName": "Corner Shop",
                "currency": "₹",
            },
        )
        self.assertEqual(response.status_code, 200)

        for path, page_name in (("/account", b"Account settings"), ("/accounts", b"Manage accounts")):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'data-theme="dark"', response.data)
            self.assertIn(b'class="account-app"', response.data)
            self.assertIn(b'class="app-sidebar"', response.data)
            self.assertIn(page_name, response.data)
            self.assertNotIn(b'class="top-header"', response.data)

    def test_appearance_settings_are_encrypted_and_saved_per_profile(self):
        response = self.client.put(
            "/api/workspace/settings",
            json={
                "theme": "dark",
                "accent": "#2563eb",
                "layout": "compact",
                "density": "compact",
                "shopName": "Corner Shop",
                "currency": "$",
            },
        )
        self.assertEqual(response.status_code, 200)

        token = set_profile_storage_path(
            get_profile_storage_path(self.account["id"])
        )
        try:
            path = storage_file("DukaanDeskSettings.json")
            with open(path, "rb") as saved_file:
                self.assertTrue(
                    saved_file.read().startswith(b"SHOPMANAGER-ENCRYPTED-JSON-V1\n")
                )
            self.assertEqual(load_json(path, {})["theme"], "dark")
        finally:
            reset_profile_storage_path(token)

    def test_passwordless_account_requires_and_downloads_export_before_removal(self):
        profile_path = get_profile_storage_path(self.account["id"])
        response = self.client.post(
            "/account/delete",
            data={"confirm_export": "on", "confirm_phrase": "DELETE"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(accounts.get_account(self.account["id"]))

        response = self.client.get("/account/export")
        self.assertEqual(response.status_code, 200)
        exported = json.loads(response.data.decode("utf-8"))
        self.assertTrue(all(key in exported for key in ("products", "customers", "sales", "settings")))

        response = self.client.post(
            "/account/delete",
            data={"confirm_export": "on", "confirm_phrase": "DELETE"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/setup"))
        self.assertIsNone(accounts.get_account(self.account["id"]))
        self.assertFalse(os.path.exists(profile_path))

    def test_password_protected_account_removal_checks_password(self):
        protected = accounts.create_account("Protected", "Protected Shop", "safePass123")
        client = app.test_client()
        with client.session_transaction() as session:
            session["account_id"] = protected["id"]

        response = client.post(
            "/account/delete",
            data={"current_password": "wrong-pass"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(accounts.get_account(protected["id"]))

        response = client.post(
            "/account/delete",
            data={"current_password": "safePass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))
        self.assertIsNone(accounts.get_account(protected["id"]))

    def test_owner_can_export_and_remove_a_passwordless_managed_account(self):
        target = accounts.create_account("Staff", "Staff Shop")
        response = self.client.get(f"/accounts/{target['id']}/export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode("utf-8"))["products"], [])

        response = self.client.post(
            f"/accounts/{target['id']}/delete",
            data={"confirm_export": "on", "confirm_phrase": "DELETE"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/accounts"))
        self.assertIsNone(accounts.get_account(target["id"]))
        self.assertTrue(accounts.get_account(self.account["id"])["is_owner"])


if __name__ == "__main__":
    unittest.main()
