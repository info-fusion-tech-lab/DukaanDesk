import json
import os
import tempfile

from cryptography.fernet import Fernet, InvalidToken


_HEADER = b"SHOPMANAGER-ENCRYPTED-JSON-V1\n"
_BINARY_HEADER = b"SHOPMANAGER-ENCRYPTED-BINARY-V1\n"


def _cipher():
    key = os.environ.get("SHOPMANAGER_ENCRYPTION_KEY")
    if not key:
        if os.environ.get("SHOPMANAGER_DESKTOP") == "1":
            raise RuntimeError("The desktop encryption key is unavailable.")
        return None
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise RuntimeError("The desktop encryption key is invalid.") from error


def load_json(path, default):
    try:
        with open(path, "rb") as file:
            contents = file.read()
    except FileNotFoundError:
        return default

    if not contents:
        return default

    cipher = _cipher()
    is_encrypted = contents.startswith(_HEADER)
    if is_encrypted:
        if cipher is None:
            raise RuntimeError(f"Encrypted data requires the desktop encryption key: {path}")
        try:
            contents = cipher.decrypt(contents[len(_HEADER):])
        except InvalidToken as error:
            raise RuntimeError(f"Could not decrypt local data: {path}") from error

    try:
        value = json.loads(contents.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Local JSON data is invalid: {path}") from error

    if cipher is not None and not is_encrypted:
        save_json(path, value)
    return value


def _write_file(path, payload):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as file:
            temporary_path = file.name
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
        raise


def save_json(path, value):
    payload = json.dumps(value, indent=4, ensure_ascii=False).encode("utf-8")
    cipher = _cipher()
    if cipher is not None:
        payload = _HEADER + cipher.encrypt(payload)
    _write_file(path, payload)


def load_bytes(path):
    with open(path, "rb") as file:
        contents = file.read()

    cipher = _cipher()
    is_encrypted = contents.startswith(_BINARY_HEADER)
    if is_encrypted:
        if cipher is None:
            raise RuntimeError(f"Encrypted data requires the desktop encryption key: {path}")
        try:
            return cipher.decrypt(contents[len(_BINARY_HEADER):])
        except InvalidToken as error:
            raise RuntimeError(f"Could not decrypt local data: {path}") from error

    if cipher is not None:
        save_bytes(path, contents)
    return contents


def save_bytes(path, value):
    cipher = _cipher()
    if cipher is not None:
        value = _BINARY_HEADER + cipher.encrypt(value)
    _write_file(path, value)
