import math
import sqlite3
import subprocess
from datetime import datetime

from core.logger import log
from core.paths import DB_PATH

FEEDBACK_CHECK_DELAY = 25
DECAY_HALF_LIFE_DAYS = 7


def predict_for_hour_legacy(hour):
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            """
            SELECT app_name FROM (
                SELECT
                    app_name,
                    SUM(duration) AS total,
                    RANK() OVER (ORDER BY SUM(duration) DESC) AS rnk
                FROM activity
                WHERE strftime('%H', start_time) = ?
                AND app_name != 'Idle'
                GROUP BY app_name
            )
            WHERE rnk = 1
            """,
            (hour,),
        ).fetchone()
    except Exception:
        return None
    finally:
        conn.close()
    return row[0] if row else None


def init_feedback_table():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name  TEXT    NOT NULL,
                timestamp TEXT    NOT NULL,
                success   INTEGER NOT NULL
            )
            """)
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def record_feedback(app_name, success):
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                "INSERT INTO feedback (app_name, timestamp, success) VALUES (?, ?, ?)",
                (app_name, datetime.now().isoformat(), 1 if success else 0),
            )
            conn.commit()
        finally:
            conn.close()
        log(f"Feedback: {app_name} → {'success' if success else 'miss'}")
    except Exception:
        pass


def get_active_window_title():
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
        return title.lower() if title else ""
    except Exception:
        return ""


def check_prediction_result(app_name):
    from tracker import normalize_app

    title = get_active_window_title()
    if not title:
        return None
    active = normalize_app(title) if title else "Idle"
    return active == app_name


def collect_feedback(app_name):
    import time

    time.sleep(FEEDBACK_CHECK_DELAY)
    result = check_prediction_result(app_name)
    if result is not None:
        record_feedback(app_name, result)
        return result
    return None


def get_feedback_score(app_name, hour=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT timestamp, success FROM feedback WHERE app_name = ?",
            (app_name,),
        ).fetchall()
    except Exception:
        return 0.5
    finally:
        conn.close()

    if not rows:
        return 0.5

    now = datetime.now()
    weighted_sum = 0.0
    weight_total = 0.0

    for ts_str, success in rows:
        try:
            ts = datetime.fromisoformat(ts_str)
            age_days = max((now - ts).total_seconds() / 86400, 0.01)
            weight = math.exp(-0.693 * age_days / DECAY_HALF_LIFE_DAYS)
            weighted_sum += success * weight
            weight_total += weight
        except Exception:
            continue

    if weight_total == 0:
        return 0.5

    return weighted_sum / weight_total


def adaptive_predict_for_hour(hour):
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT app_name, SUM(duration) AS total
            FROM activity
            WHERE strftime('%H', start_time) = ?
            AND app_name != 'Idle'
            GROUP BY app_name
            """,
            (hour,),
        ).fetchall()
    except Exception:
        return None, 0.0
    finally:
        conn.close()

    if not rows:
        return None, 0.0

    max_usage = max(t for _, t in rows)
    if max_usage == 0:
        return None, 0.0

    scored = []
    for app, usage in rows:
        usage_score = usage / max_usage
        feedback_score = get_feedback_score(app, hour)
        final = 0.6 * usage_score + 0.4 * feedback_score
        scored.append((app, final))

    scored.sort(key=lambda x: x[1], reverse=True)
    best_app, best_score = scored[0]
    confidence = min(99, int(best_score * 100))

    fb = get_feedback_score(best_app, hour)
    if fb > 0.6:
        trend = "improving"
    elif fb < 0.4:
        trend = "declining"
    else:
        trend = "stable"

    return best_app, confidence, trend


def get_feedback_stats():
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("""
            SELECT app_name,
                   COUNT(*) AS total,
                   SUM(success) AS hits
            FROM feedback
            GROUP BY app_name
            """).fetchall()
    except Exception:
        return []
    finally:
        conn.close()
    return rows
