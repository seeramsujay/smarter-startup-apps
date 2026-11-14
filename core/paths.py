import os
import shutil

PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OLD_DB = os.path.join(PROJECT_DIR, "data", "activity.db")
OLD_CONFIG = os.path.join(PROJECT_DIR, "config", "config.json")
OLD_LOG = os.path.join(PROJECT_DIR, "logs", "ghostos.log")

DATA_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "ghostos")


def _check_writable(path):
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, ".test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except Exception:
        return False


if not _check_writable(DATA_DIR):
    DATA_DIR = os.path.join(PROJECT_DIR, ".ghostos_data")

DB_PATH = os.path.join(DATA_DIR, "activity.db")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
LOG_DIR = os.path.join(DATA_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "ghostos.log")


def ensure_dirs():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        pass


def migrate():
    ensure_dirs()
    _migrate_file(OLD_DB, DB_PATH)
    _migrate_file(OLD_CONFIG, CONFIG_PATH)
    _migrate_file(OLD_LOG, LOG_FILE)


def _migrate_file(src, dst):
    if os.path.exists(src) and not os.path.exists(dst):
        try:
            shutil.copy2(src, dst)
        except Exception:
            pass
