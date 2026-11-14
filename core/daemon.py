import os
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core.autopilot import is_app_running, launch_app, predict_for_hour
from core.checks import preflight
from core.config import get_config
from core.feedback import init_feedback_table
from core.logger import log
from core.paths import DB_PATH
from core.voice import speak

last_launched = {}
_miss_count = {}


def should_launch(app_name, cooldown):
    extra = _miss_count.get(app_name, 0) * 300
    effective_cooldown = cooldown + extra

    if app_name in last_launched:
        elapsed = (datetime.now() - last_launched[app_name]).total_seconds()
        if elapsed < effective_cooldown:
            return False, effective_cooldown - elapsed
    return True, 0


def run_cycle(cooldown):
    now = datetime.now()
    hour = now.strftime("%H")

    if not get_config("autopilot"):
        print(f"[GhostOS] [{now.strftime('%H:%M:%S')}] Autopilot disabled.")
        return

    print(f"[GhostOS] [{now.strftime('%H:%M:%S')}] Checking predictions...")

    try:
        result = predict_for_hour(hour)
    except Exception as e:
        print(f"[GhostOS] Prediction error: {e}")
        log(f"Prediction error: {e}", "ERROR")
        return

    if not result or not result[0]:
        print(f"[GhostOS] No prediction for {hour}:00")
        return

    app, confidence, trend = result
    threshold = get_config("confidence_threshold")

    print(f"[GhostOS] Predicted: {app} ({confidence}%, {trend})")
    log(f"Predicted: {app} ({confidence}%, {trend}) for {hour}:00")

    if confidence < threshold:
        print(f"[GhostOS] Below threshold ({threshold}%). Skipping.")
        return

    if is_app_running(app):
        print(f"[GhostOS] {app} already running.")
        return

    can_launch, remaining = should_launch(app, cooldown)
    if not can_launch:
        print(f"[GhostOS] {app} on cooldown ({int(remaining)}s remaining)")
        return

    launch_app(app)
    last_launched[app] = now


def main():
    if not preflight(require_xdotool=False):
        print("[GhostOS] Preflight checks failed. Continuing anyway...")
        log("Preflight checks had warnings", "WARN")

    if not os.path.exists(DB_PATH):
        print("[GhostOS] No data available. Run tracker first.")
        return

    cycle_interval = get_config("daemon_interval")
    cooldown = get_config("cooldown")
    init_feedback_table()

    print("[GhostOS] Running background daemon...")
    print(f"[GhostOS] Cycle: every {cycle_interval}s | Cooldown: {cooldown}s")
    print(f"[GhostOS] Data: {DB_PATH}")
    log(f"Daemon started — interval={cycle_interval}s cooldown={cooldown}s")
    speak("Ghost OS daemon started")

    try:
        while True:
            try:
                run_cycle(cooldown)
            except Exception as e:
                print(f"[GhostOS] Error: {e}")
                log(f"Cycle error: {e}", "ERROR")
            time.sleep(cycle_interval)
    except KeyboardInterrupt:
        log("Daemon stopped by user")
        speak("Daemon stopped")
        print("\n[GhostOS] Daemon stopped.")


if __name__ == "__main__":
    main()
