import os
import sqlite3

from core.paths import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def time_prediction():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT hour, app_name FROM (
                SELECT
                    strftime('%H', start_time) AS hour,
                    app_name,
                    SUM(duration) AS total,
                    RANK() OVER (PARTITION BY strftime('%H', start_time) ORDER BY SUM(duration) DESC) AS rnk
                FROM activity
                WHERE app_name != 'Idle'
                GROUP BY hour, app_name
            )
            WHERE rnk = 1
            ORDER BY hour
            """).fetchall()
    finally:
        conn.close()
    return rows


def next_app_prediction():
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

    predictions = {}
    for src, targets in trans.items():
        best = max(targets, key=targets.get)
        predictions[src] = best
    return predictions


def main():
    if not os.path.exists(DB_PATH):
        print("No data available")
        return

    time_preds = time_prediction()
    if not time_preds:
        print("No data available")
        return

    try:
        from core.feedback import (
            adaptive_predict_for_hour,
            get_feedback_stats,
            init_feedback_table,
        )

        init_feedback_table()
        has_feedback = True
    except Exception:
        has_feedback = False

    print("=== Time Prediction ===")
    for hour, app in time_preds:
        extra = ""
        if has_feedback:
            try:
                result = adaptive_predict_for_hour(hour)
                if result and result[0]:
                    _, conf, trend = result
                    extra = f"  ({conf}%, {trend})"
            except Exception:
                pass
        print(f"{hour}:00 → {app}{extra}")

    print()

    next_preds = next_app_prediction()
    if not next_preds:
        print("No transition data available")
        return

    print("=== Next App Prediction ===")
    for src, dst in next_preds.items():
        print(f"{src} → {dst}")

    if has_feedback:
        print()
        stats = get_feedback_stats()
        if stats:
            print("=== Feedback Stats ===")
            for app, total, hits in stats:
                rate = int(hits / total * 100) if total > 0 else 0
                print(f"{app}: {hits}/{total} ({rate}% accuracy)")


if __name__ == "__main__":
    main()
