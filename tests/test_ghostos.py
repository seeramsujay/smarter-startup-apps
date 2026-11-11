import pytest
from core.config import DEFAULTS, _validate, VALID_KEYS
from core.paths import OLD_DB, OLD_CONFIG

def test_config_defaults():
    assert DEFAULTS["overlay"] is True
    assert DEFAULTS["daemon_interval"] == 300
    assert "VSCode" in DEFAULTS["launch_map"]

def test_validate_config_bounds():
    cfg = {"daemon_interval": 2, "cooldown": 5, "confidence_threshold": 150}
    validated = _validate(cfg)
    assert validated["daemon_interval"] == 10
    assert validated["cooldown"] == 10
    assert validated["confidence_threshold"] == 100

    cfg_neg = {"confidence_threshold": -20}
    validated_neg = _validate(cfg_neg)
    assert validated_neg["confidence_threshold"] == 0

def test_paths():
    assert OLD_DB.endswith("activity.db")
    assert OLD_CONFIG.endswith("config.json")
