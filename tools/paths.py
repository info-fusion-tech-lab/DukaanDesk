import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_storage_path():
    path = os.path.abspath(
        os.environ.get("SHOPMANAGER_DATA_DIR", os.path.join(BASE_DIR, "storage"))
    )
    os.makedirs(path, exist_ok=True)
    return path


STORAGE_PATH = get_storage_path()
