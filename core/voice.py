import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.config import get_config


def _find_tts():
    for cmd in ["espeak", "spd-say"]:
        try:
            subprocess.run(
                ["which", cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return cmd
        except Exception:
            continue
    return None


_TTS_CMD = None


def speak(text):
    global _TTS_CMD

    if not get_config("voice"):
        return

    if _TTS_CMD is None:
        _TTS_CMD = _find_tts() or ""

    if not _TTS_CMD:
        return

    try:
        if _TTS_CMD == "espeak":
            subprocess.Popen(
                ["espeak", "-s", "160", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif _TTS_CMD == "spd-say":
            subprocess.Popen(
                ["spd-say", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass
