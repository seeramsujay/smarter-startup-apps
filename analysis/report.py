import os
import sqlite3
from datetime import date

from core.paths import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def daily_summary(day=None):
    day = day or date.today().isoformat()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT app_name, SUM(duration) AS total, COUNT(*) AS sessions
            FROM activity
            WHERE date(start_time) = ?
            AND app_name != 'Idle'
            GROUP BY app_name
            ORDER BY total DESC
            """,
            (day,),
        ).fetchall()
    finally:
        conn.close()
    return rows


def peak_hours(day=None):
    day = day or date.today().isoformat()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT strftime('%H', start_time) AS hour, SUM(duration) AS total
            FROM activity
            WHERE date(start_time) = ?
            AND app_name != 'Idle'
            GROUP BY hour
            ORDER BY total DESC
            LIMIT 3
            """,
            (day,),
        ).fetchall()
    finally:
        conn.close()
    return rows


def focus_score(day=None):
    day = day or date.today().isoformat()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_sessions,
                AVG(duration) AS avg_duration,
                MAX(duration) AS longest_session
            FROM activity
            WHERE date(start_time) = ?
            AND app_name != 'Idle'
            """,
            (day,),
        ).fetchone()
    finally:
        conn.close()
    return row


def fmt_time(seconds):
    if seconds >= 3600:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 60:.1f}m"


def main(day=None):
    day = day or date.today().isoformat()

    if not os.path.exists(DB_PATH):
        print("No data available")
        return

    apps = daily_summary(day)
    if not apps:
        print(f"No data for {day}")
        return

    total_time = sum(t for _, t, _ in apps)
    total_sessions = sum(s for _, _, s in apps)

    print("╔══════════════════════════════════════╗")
    print("║       GHOST OS X — DAILY REPORT      ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  Date: {day}                   ║")
    print("╚══════════════════════════════════════╝")

    print("\n=== Overview ===")
    print(f"Total tracked: {fmt_time(total_time)}")
    print(f"Total sessions: {total_sessions}")
    print(f"Apps used: {len(apps)}")

    stats = focus_score(day)
    if stats and stats[0]:
        avg_dur = stats[1] or 0
        longest = stats[2] or 0
        print(f"Avg session: {fmt_time(avg_dur)}")
        print(f"Longest session: {fmt_time(longest)}")

        score = min(100, int((avg_dur / 60) * 10))
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        print(f"Focus score: [{bar}] {score}/100")

    print("\n=== App Breakdown ===")
    for name, total, sessions in apps:
        pct = (total / total_time) * 100 if total_time > 0 else 0
        bar_len = int(pct / 5)
        bar = "▓" * bar_len + "░" * (20 - bar_len)
        print(
            f"  {name:<15} {fmt_time(total):>7}  {bar}  {pct:.0f}%  ({sessions} sessions)"
        )

    hours = peak_hours(day)
    if hours:
        print("\n=== Peak Hours ===")
        for hour, total in hours:
            print(f"  {hour}:00  {fmt_time(total)}")

    print()


if __name__ == "__main__":
    import sys

    day_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(day_arg)
