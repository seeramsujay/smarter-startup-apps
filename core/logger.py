import os
from datetime import datetime

from core.paths import LOG_DIR, LOG_FILE

MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB


def _ensure_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _rotate():
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
            bak = LOG_FILE + ".old"
            if os.path.exists(bak):
                os.remove(bak)
            os.rename(LOG_FILE, bak)
    except Exception:
        pass


def log(message, level="INFO"):
    try:
        _ensure_dir()
        _rotate()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] [{level}] {message}\n")
    except Exception:
        pass
