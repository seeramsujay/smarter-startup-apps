import json
import os
import shutil

from core.paths import CONFIG_PATH

DEFAULTS = {
    "overlay": True,
    "voice": False,
    "autopilot": True,
    "suggestions": True,
    "dashboard": False,
    "daemon_interval": 300,
    "cooldown": 1800,
    "confidence_threshold": 60,
    "data_dir": "~/.local/share/ghostos",
    "launch_map": {
        "VSCode": ["code", "code-oss", "codium"],
        "Chrome": [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
        ],
        "Firefox": ["firefox", "firefox-esr"],
        "Terminal": [
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "alacritty",
            "kitty",
            "xterm",
        ],
    },
}

VALID_KEYS = set(DEFAULTS.keys())
BOOL_KEYS = {"overlay", "voice", "autopilot", "suggestions", "dashboard"}
INT_KEYS = {"daemon_interval", "cooldown", "confidence_threshold"}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULTS)
        return dict(DEFAULTS)
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        merged = {**DEFAULTS, **cfg}
        return _validate(merged)
    except (json.JSONDecodeError, ValueError):
        _backup_corrupt()
        save_config(DEFAULTS)
        return dict(DEFAULTS)
    except Exception:
        return dict(DEFAULTS)


def _backup_corrupt():
    if os.path.exists(CONFIG_PATH):
        bak = CONFIG_PATH + ".bak"
        try:
            shutil.copy2(CONFIG_PATH, bak)
        except Exception:
            pass


def _validate(cfg):
    if cfg.get("daemon_interval", 300) < 10:
        cfg["daemon_interval"] = 10
    if cfg.get("cooldown", 1800) < 10:
        cfg["cooldown"] = 10
    if cfg.get("confidence_threshold", 60) < 0:
        cfg["confidence_threshold"] = 0
    if cfg.get("confidence_threshold", 60) > 100:
        cfg["confidence_threshold"] = 100
    return cfg


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def get_config(key=None):
    cfg = load_config()
    if key is None:
        return cfg
    return cfg.get(key, DEFAULTS.get(key))


def set_config(key, value):
    if key not in VALID_KEYS:
        raise KeyError(f"Invalid config key: {key}")
    cfg = load_config()
    if key in BOOL_KEYS:
        value = str(value).lower() in ("true", "1", "yes", "on")
    elif key in INT_KEYS:
        value = max(10 if key != "confidence_threshold" else 0, int(value))
    cfg[key] = value
    save_config(cfg)
    return cfg
