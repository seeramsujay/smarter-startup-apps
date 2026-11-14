#!/usr/bin/env python3
import os
import sys

USAGE = """
Ghost OS X — Activity Intelligence Engine

Usage:
  ghostos track              Start tracking active window
  ghostos report [DATE]      Daily report (default: today)
  ghostos patterns           Top apps + hourly usage patterns
  ghostos sequences          App transition sequences
  ghostos predict            Time + next-app predictions
  ghostos autopilot          Phantom mode (workflow reconstruction)
  ghostos daemon             Background autopilot daemon
  ghostos dashboard          Launch optional web dashboard
  ghostos config show        Show current config
  ghostos config set K V     Set config value
  ghostos status             Show database stats

DATE format: YYYY-MM-DD

Config keys: overlay, voice, autopilot, suggestions, dashboard, daemon_interval, cooldown, confidence_threshold
"""


def _ensure_migration():
    from core.paths import migrate

    migrate()


def cmd_track():
    _ensure_migration()
    from tracker import main

    main()


def cmd_report():
    _ensure_migration()
    day = sys.argv[2] if len(sys.argv) > 2 else None
    from analysis.report import main

    main(day)


def cmd_patterns():
    _ensure_migration()
    from analysis.patterns import main

    main()


def cmd_sequences():
    _ensure_migration()
    from analysis.sequences import main

    main()


def cmd_predict():
    _ensure_migration()
    from analysis.predict import main

    main()


def cmd_autopilot():
    _ensure_migration()
    from core.autopilot import main

    main()


def cmd_daemon():
    _ensure_migration()
    from core.daemon import main

    main()


def cmd_dashboard():
    _ensure_migration()
    from core.config import get_config

    if not get_config("dashboard"):
        print(
            "[GhostOS] Dashboard disabled in config (run: ghostos config set dashboard true)"
        )
        return
    try:
        import flask
        from ui.dashboard import main

        main()
    except ImportError:
        print("[GhostOS] Flask not installed. Run: pip install flask")


def cmd_config():
    _ensure_migration()
    from core.config import get_config, set_config

    if len(sys.argv) < 3:
        print("Usage: ghostos config show | ghostos config set <key> <value>")
        return

    action = sys.argv[2]

    if action == "show":
        cfg = get_config()
        print("=== Ghost OS X — Config ===")
        for k, v in cfg.items():
            if isinstance(v, bool):
                print(f"  {k:<22} {v} {'✓' if v else '✗'}")
            elif isinstance(v, dict):
                print(f"  {k}:")
                for ak, av in v.items():
                    print(f"    {ak:<15} {', '.join(av)}")
            else:
                print(f"  {k:<22} {v}")

    elif action == "set":
        if len(sys.argv) < 5:
            print("Usage: ghostos config set <key> <value>")
            return
        key, value = sys.argv[3], sys.argv[4]
        try:
            cfg = set_config(key, value)
            print(f"[GhostOS] {key} → {cfg[key]}")
        except KeyError as e:
            print(f"[GhostOS] Error: {e}")
        except ValueError as e:
            print(f"[GhostOS] Invalid value: {e}")

    else:
        print("Usage: ghostos config show | ghostos config set <key> <value>")


def cmd_status():
    _ensure_migration()
    import sqlite3

    from core.paths import DB_PATH

    if not os.path.exists(DB_PATH):
        print("No database found. Run 'ghostos track' first.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        total = conn.execute("SELECT COUNT(*) FROM activity").fetchone()[0]
        apps = conn.execute("SELECT COUNT(DISTINCT app_name) FROM activity").fetchone()[
            0
        ]
        first = conn.execute("SELECT MIN(start_time) FROM activity").fetchone()[0]
        last = conn.execute("SELECT MAX(end_time) FROM activity").fetchone()[0]
        total_dur = (
            conn.execute("SELECT SUM(duration) FROM activity").fetchone()[0] or 0
        )
    finally:
        conn.close()

    print("=== Ghost OS X — Status ===")
    print(f"Database: {DB_PATH}")
    print(f"Total records: {total}")
    print(f"Unique apps: {apps}")
    print(f"First entry: {first or 'N/A'}")
    print(f"Last entry: {last or 'N/A'}")
    hours = total_dur / 3600
    print(f"Total tracked: {hours:.1f}h")


COMMANDS = {
    "track": cmd_track,
    "report": cmd_report,
    "patterns": cmd_patterns,
    "sequences": cmd_sequences,
    "predict": cmd_predict,
    "autopilot": cmd_autopilot,
    "daemon": cmd_daemon,
    "dashboard": cmd_dashboard,
    "config": cmd_config,
    "status": cmd_status,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(USAGE.strip())
        sys.exit(1)
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
