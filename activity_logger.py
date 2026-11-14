import os
import shutil
import sqlite3

from core.paths import DATA_DIR, DB_PATH


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name   TEXT    NOT NULL,
                start_time TEXT    NOT NULL,
                end_time   TEXT    NOT NULL,
                duration   REAL    NOT NULL
            )
            """)
        conn.execute("SELECT COUNT(*) FROM activity")
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError:
        _backup_db(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name   TEXT    NOT NULL,
                start_time TEXT    NOT NULL,
                end_time   TEXT    NOT NULL,
                duration   REAL    NOT NULL
            )
            """)
        conn.commit()
        conn.close()


def _backup_db(path):
    if os.path.exists(path):
        bak = path + ".bak"
        try:
            shutil.copy2(path, bak)
            os.remove(path)
        except Exception:
            pass


def insert_activity(app_name, start_time, end_time, duration):
    if not app_name or app_name == "Idle":
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                "INSERT INTO activity (app_name, start_time, end_time, duration) VALUES (?, ?, ?, ?)",
                (app_name, start_time, end_time, duration),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        _backup_db(DB_PATH)
        init_db()
    except Exception:
        pass
