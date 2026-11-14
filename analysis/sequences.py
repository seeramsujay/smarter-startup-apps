import os
import sqlite3

from core.paths import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def transition_sequences():
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

    return trans


def main():
    if not os.path.exists(DB_PATH):
        print("No data available")
        return

    trans = transition_sequences()
    if not trans:
        print("No transition data available")
        return

    print("=== App Transition Sequences ===")
    for src in sorted(trans):
        print(f"\nFrom {src}:")
        targets = trans[src]
        for dst, count in sorted(targets.items(), key=lambda x: x[1], reverse=True):
            print(f"  → {dst:<15} {count} times")


if __name__ == "__main__":
    main()
