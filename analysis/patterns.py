import os
import sqlite3

from core.paths import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def top_apps():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT app_name, SUM(duration) as total
            FROM activity
            GROUP BY app_name
            ORDER BY total DESC
            """).fetchall()
    finally:
        conn.close()
    return rows


def hourly_pattern():
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
                GROUP BY hour, app_name
            )
            WHERE rnk = 1
            ORDER BY hour
            """).fetchall()
    finally:
        conn.close()
    return {hour: app for hour, app in rows}


def main():
    if not os.path.exists(DB_PATH):
        print("No data available")
        return

    apps = top_apps()
    if not apps:
        print("No data available")
        return

    print("=== Top Apps ===")
    for name, total in apps:
        print(f"{name} - {total / 60:.1f} min")

    print()

    hours = hourly_pattern()
    print("=== Hourly Pattern ===")
    for hour in sorted(hours):
        print(f"{hour}:00 → {hours[hour]}")


if __name__ == "__main__":
    main()
