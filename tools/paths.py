import os
import re
from contextvars import ContextVar


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROFILE_STORAGE_PATH = ContextVar("shopmanager_profile_storage_path", default=None)


def get_base_storage_path():
    path = os.path.abspath(
        os.environ.get("SHOPMANAGER_DATA_DIR", os.path.join(BASE_DIR, "storage"))
    )
    os.makedirs(path, exist_ok=True)
    return path


def get_storage_path():
    return _PROFILE_STORAGE_PATH.get() or get_base_storage_path()


def set_profile_storage_path(path):
    profile_path = os.path.abspath(path)
    os.makedirs(profile_path, exist_ok=True)
    return _PROFILE_STORAGE_PATH.set(profile_path)


def reset_profile_storage_path(token):
    _PROFILE_STORAGE_PATH.reset(token)


def get_profile_storage_path(profile_id):
    if not re.fullmatch(r"[a-f0-9]{32}", profile_id or ""):
        raise ValueError("Invalid local account identifier.")
    return os.path.join(get_base_storage_path(), "Profiles", profile_id)


def storage_file(filename, profile=True):
    root = get_storage_path() if profile else get_base_storage_path()
    return os.path.join(root, filename)


STORAGE_PATH = get_base_storage_path()
