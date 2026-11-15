import hashlib
import hmac
import os
import shutil
import uuid

from tools.encrypted_json import load_json, save_bytes, save_json
from tools.paths import get_profile_storage_path, storage_file


_ACCOUNT_FILENAME = "Accounts.json"
_PASSWORD_ITERATIONS = 600_000
_MAX_PASSWORD_LENGTH = 256
_LEGACY_DATA_FILES = ("ProductList.json", "CustomerList.json", "SalesLog.json")


def _accounts_path():
    return storage_file(_ACCOUNT_FILENAME, profile=False)


def _read_accounts():
    data = load_json(_accounts_path(), {"accounts": []})
    if not isinstance(data, dict) or not isinstance(data.get("accounts"), list):
        raise RuntimeError("The local account index has an invalid format.")
    return data["accounts"]


def list_accounts():
    return [
        {
            "id": account["id"],
            "username": account["username"],
            "shop_name": account["shop_name"],
            "has_password": bool(account.get("password_hash")),
            "is_owner": bool(account.get("is_owner")),
        }
        for account in _read_accounts()
    ]


def get_account(account_id):
    return next(
        (account for account in _read_accounts() if account["id"] == account_id),
        None,
    )


def profile_directory(account_id):
    return get_profile_storage_path(account_id)


def _hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS
    )
    return f"{salt.hex()}:{digest.hex()}"


def _validate_password(password):
    if password is not None and not 8 <= len(password) <= _MAX_PASSWORD_LENGTH:
        raise ValueError("Password must contain 8 to 256 characters.")


def verify_password(account, password):
    password_hash = account.get("password_hash")
    if not password_hash:
        return not password
    if not password or len(password) > _MAX_PASSWORD_LENGTH:
        return False
    try:
        salt_hex, digest_hex = password_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        raise RuntimeError("The local account password record is invalid.")

    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS
    )
    return hmac.compare_digest(actual, expected)


def _migrate_legacy_data(profile_path):
    base_path = os.path.dirname(_accounts_path())
    copied_files = []
    for filename in _LEGACY_DATA_FILES:
        source = os.path.join(base_path, filename)
        if not os.path.isfile(source):
            continue
        destination = os.path.join(profile_path, filename)
        if os.path.exists(destination):
            continue
        value = load_json(source, {})
        save_json(destination, value)
        copied_files.append(source)

    source_qr = os.path.join(base_path, "ProductQRs")
    destination_qr = os.path.join(profile_path, "ProductQRs")
    copied_qr = False
    if os.path.isdir(source_qr) and not os.path.exists(destination_qr):
        shutil.copytree(source_qr, destination_qr)
        for filename in os.listdir(destination_qr):
            image_path = os.path.join(destination_qr, filename)
            if os.path.isfile(image_path) and filename.lower().endswith(".png"):
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                save_bytes(image_path, image_data)
        copied_qr = True
    return copied_files, source_qr if copied_qr else None


def _remove_legacy_data(copied_files, copied_qr):
    for path in copied_files:
        os.remove(path)
    if copied_qr:
        shutil.rmtree(copied_qr)


def create_account(username, shop_name, password=None):
    username = (username or "").strip()
    shop_name = (shop_name or "").strip()
    if not username or len(username) > 40:
        raise ValueError("Username must contain 1 to 40 characters.")
    if not shop_name or len(shop_name) > 80:
        raise ValueError("Shop name must contain 1 to 80 characters.")
    _validate_password(password)

    accounts = _read_accounts()
    if any(account["username"].casefold() == username.casefold() for account in accounts):
        raise ValueError("That username is already in use.")

    account = {
        "id": uuid.uuid4().hex,
        "username": username,
        "shop_name": shop_name,
        "password_hash": _hash_password(password) if password else None,
        "is_owner": not accounts,
    }

    profile_path = profile_directory(account["id"])
    os.makedirs(profile_path, exist_ok=True)
    copied_files = []
    copied_qr = None
    if not accounts:
        copied_files, copied_qr = _migrate_legacy_data(profile_path)

    accounts.append(account)
    save_json(_accounts_path(), {"accounts": accounts})
    _remove_legacy_data(copied_files, copied_qr)
    return account


def update_account(account_id, shop_name=None, password=None, remove_password=False):
    accounts = _read_accounts()
    account = next((item for item in accounts if item["id"] == account_id), None)
    if not account:
        raise ValueError("Local account not found.")

    if shop_name is not None:
        shop_name = shop_name.strip()
        if not shop_name or len(shop_name) > 80:
            raise ValueError("Shop name must contain 1 to 80 characters.")
        account["shop_name"] = shop_name
    if remove_password:
        account["password_hash"] = None
    elif password:
        _validate_password(password)
        account["password_hash"] = _hash_password(password)

    save_json(_accounts_path(), {"accounts": accounts})
    return account


def delete_account(account_id, password=None):
    stored_accounts = _read_accounts()
    account = next((item for item in stored_accounts if item["id"] == account_id), None)
    if not account:
        raise ValueError("Local account not found.")
    if account.get("password_hash") and not verify_password(account, password):
        raise ValueError("The account password is incorrect.")

    remaining = [item for item in stored_accounts if item["id"] != account_id]
    if account.get("is_owner") and remaining:
        remaining[0]["is_owner"] = True

    profile_path = profile_directory(account_id)
    archived_path = profile_path + ".deleting-" + uuid.uuid4().hex
    if os.path.exists(profile_path):
        os.replace(profile_path, archived_path)
    try:
        save_json(_accounts_path(), {"accounts": remaining})
    except Exception:
        if os.path.exists(archived_path):
            os.replace(archived_path, profile_path)
        raise

    if os.path.exists(archived_path):
        shutil.rmtree(archived_path)
    return remaining
