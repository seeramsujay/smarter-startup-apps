import subprocess
import time
from datetime import datetime

from activity_logger import init_db, insert_activity
from core.checks import preflight
from core.logger import log

POLL_INTERVAL = 5
CHECKPOINT_INTERVAL = 30

NORMALIZE_RULES = [
    (["chrome", "chromium"], "Chrome"),
    (["firefox"], "Firefox"),
    (["vs code", "code"], "VSCode"),
    (["terminal", "konsole", "alacritty", "kitty"], "Terminal"),
]


def normalize_app(name):
    lower = name.lower()
    for keywords, label in NORMALIZE_RULES:
        for kw in keywords:
            if kw in lower:
                return label
    return name[:30]


def get_active_window():
    try:
        wid = subprocess.check_output(
            ["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL
        ).strip()
        title = (
            subprocess.check_output(
                ["xdotool", "getwindowname", wid], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        return normalize_app(title) if title else "Idle"
    except Exception:
        return "Idle"


def log_session(app_name, start, end):
    if app_name == "Idle":
        return
    duration = (end - start).total_seconds()
    if duration < 1:
        return
    insert_activity(app_name, start.isoformat(), end.isoformat(), duration)
    print(f"Logged: {app_name} ({duration:.1f}s)")


def main():
    if not preflight(require_xdotool=True):
        print("[GhostOS] Cannot start tracker without xdotool.")
        return

    init_db()
    log("Tracker started")

    current_app = get_active_window()
    start_time = datetime.now()
    last_save = start_time

    print(f"Tracking started — active: {current_app}")

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            now = datetime.now()
            active = get_active_window()

            if active != current_app:
                log_session(current_app, start_time, now)
                current_app = active
                start_time = now
                last_save = now

            elif (now - last_save).total_seconds() >= CHECKPOINT_INTERVAL:
                log_session(current_app, start_time, now)
                start_time = now
                last_save = now

    except KeyboardInterrupt:
        log_session(current_app, start_time, datetime.now())
        log("Tracker stopped by user")
        print("\nFinal session saved. Exiting.")


if __name__ == "__main__":
    main()
