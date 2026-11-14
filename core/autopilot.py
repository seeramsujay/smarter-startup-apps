import os
import sqlite3
import subprocess
import threading
import time
from datetime import datetime

from core.checks import find_available_command
from core.config import get_config
from core.feedback import (
    adaptive_predict_for_hour,
    collect_feedback,
    init_feedback_table,
    predict_for_hour_legacy,
)
from core.logger import log
from core.paths import DB_PATH
from core.voice import speak

MAX_CHAIN = 4
LAUNCH_DELAY = 2.5

_recent_misses = {}


def get_launch_map():
    return get_config("launch_map") or {}


def get_connection():
    return sqlite3.connect(DB_PATH)


def predict_for_hour(hour):
    try:
        result = adaptive_predict_for_hour(hour)
        if result and result[0]:
            return result
    except Exception:
        pass

    app = predict_for_hour_legacy(hour)
    if app:
        return app, 50, "stable"
    return None, 0, ""


def get_transition_map():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT app_name FROM activity
            WHERE app_name != 'Idle'
            ORDER BY start_time ASC
            """).fetchall()
    finally:
        conn.close()

    apps = [r[0] for r in rows]

    compressed = []
    for app in apps:
        if not compressed or app != compressed[-1]:
            compressed.append(app)

    trans = {}
    for i in range(len(compressed) - 1):
        src, dst = compressed[i], compressed[i + 1]
        if src not in trans:
            trans[src] = {}
        trans[src][dst] = trans[src].get(dst, 0) + 1

    best = {}
    for src, targets in trans.items():
        best[src] = max(targets, key=targets.get)
    return best


def build_chain(start_app, transition_map):
    chain = [start_app]
    current = start_app
    for _ in range(MAX_CHAIN - 1):
        nxt = transition_map.get(current)
        if not nxt or nxt in chain:
            break
        chain.append(nxt)
        current = nxt
    return chain


def is_app_running(app_name):
    launch_map = get_launch_map()
    candidates = launch_map.get(app_name, [])
    for cmd in candidates:
        try:
            result = subprocess.run(
                ["pgrep", "-f", cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                return True
        except Exception:
            continue
    return False


def launch_app(app_name):
    launch_map = get_launch_map()
    candidates = launch_map.get(app_name, [])

    if not candidates:
        print(f"[GhostOS] No launch command for: {app_name}")
        log(f"No launch command for: {app_name}", "WARN")
        return False

    if is_app_running(app_name):
        print(f"[GhostOS] {app_name} already running. Skipping.")
        return False

    cmd = find_available_command(candidates)
    if not cmd:
        print(f"[GhostOS] No installed binary for {app_name}: {candidates}")
        log(f"No binary found for {app_name}: {candidates}", "WARN")
        return False

    try:
        subprocess.Popen(
            [cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print(f"[GhostOS] Launching {app_name} ({cmd})")
        speak(f"Opening {app_name}")
        log(f"Launched {app_name} via {cmd}")
        return True
    except Exception as e:
        print(f"[GhostOS] Launch failed: {e}")
        log(f"Launch failed for {app_name}: {e}", "ERROR")
    return False


def _async_feedback(app_name):
    try:
        result = collect_feedback(app_name)
        if result is True:
            log(f"Feedback: {app_name} confirmed")
        elif result is False:
            _recent_misses[app_name] = datetime.now()
            log(f"Feedback: {app_name} missed")
    except Exception:
        pass


def main():
    if not get_config("autopilot"):
        print("[GhostOS] Autopilot disabled in config.")
        return

    if not os.path.exists(DB_PATH):
        print("[GhostOS] No data available. Run tracker first.")
        return

    init_feedback_table()
    threshold = get_config("confidence_threshold")

    hour = datetime.now().strftime("%H")
    result = predict_for_hour(hour)

    if not result or not result[0]:
        print(f"[GhostOS] No prediction for hour {hour}:00")
        return

    start_app, confidence, trend = result

    if confidence < threshold:
        print(f"[GhostOS] Predicted: {start_app} ({confidence}%, {trend})")
        print(f"[GhostOS] Below confidence threshold ({threshold}%). Skipping.")
        log(f"Skipped {start_app}: {confidence}% < {threshold}% threshold")
        return

    transition_map = get_transition_map()
    chain = build_chain(start_app, transition_map)

    print(f"[GhostOS] Hour: {hour}:00")
    print(f"[GhostOS] Predicted: {start_app} ({confidence}%, {trend})")
    print("[GhostOS] Reconstructing workflow...")
    print(f"[GhostOS] Chain: {' → '.join(chain)}")
    speak(f"Reconstructing workflow. Starting with {chain[0]}")
    log(f"Phantom mode: {' → '.join(chain)} [{confidence}% {trend}]")
    print()

    launched = []
    for i, app in enumerate(chain):
        if launch_app(app):
            launched.append(app)
        if i < len(chain) - 1:
            time.sleep(LAUNCH_DELAY)

    if launched:
        t = threading.Thread(target=_async_feedback, args=(launched[0],), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
