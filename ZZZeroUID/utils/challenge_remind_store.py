import json
from typing import Any, Dict

from .resource.RESOURCE_PATH import MAIN_PATH

REMIND_DATA_PATH = MAIN_PATH / "challenge_remind.json"

DEFAULT_GLOBAL_CONFIG = {
    "enable": True,
    "global_remind_time": "每日20时",
    "abyss_threshold": 5,
    "deadly_threshold": 6,
}


def _default_data() -> Dict[str, Any]:
    return {
        "global": dict(DEFAULT_GLOBAL_CONFIG),
        "users": {},
    }


def _save(data: Dict[str, Any]) -> None:
    REMIND_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REMIND_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def _load() -> Dict[str, Any]:
    if not REMIND_DATA_PATH.exists():
        data = _default_data()
        _save(data)
        return data
    with open(REMIND_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("global", dict(DEFAULT_GLOBAL_CONFIG))
    data.setdefault("users", {})
    for key, value in DEFAULT_GLOBAL_CONFIG.items():
        data["global"].setdefault(key, value)
    return data


def get_global_config() -> Dict[str, Any]:
    data = _load()
    _save(data)
    return dict(data["global"])


def set_global_enable(enable: bool) -> None:
    data = _load()
    data["global"]["enable"] = bool(enable)
    _save(data)


def set_global_remind_time(remind_time: str) -> None:
    data = _load()
    data["global"]["global_remind_time"] = str(remind_time)
    _save(data)


def set_global_threshold(kind: str, value: int) -> None:
    data = _load()
    if kind == "ABYSS":
        data["global"]["abyss_threshold"] = int(value)
    elif kind == "DEADLY":
        data["global"]["deadly_threshold"] = int(value)
    _save(data)


def _ensure_user(data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    users = data.setdefault("users", {})
    user = users.setdefault(str(uid), {})
    user.setdefault("abyss_threshold", None)
    user.setdefault("deadly_threshold", None)
    user.setdefault("remind_time", None)
    return user


def get_user_config(uid: str) -> Dict[str, Any]:
    data = _load()
    user = _ensure_user(data, uid)
    _save(data)
    return dict(user)


def set_user_threshold(uid: str, kind: str, value: int) -> None:
    data = _load()
    user = _ensure_user(data, uid)
    if kind == "ABYSS":
        user["abyss_threshold"] = int(value)
    elif kind == "DEADLY":
        user["deadly_threshold"] = int(value)
    _save(data)


def set_user_remind_time(uid: str, remind_time: str) -> None:
    data = _load()
    user = _ensure_user(data, uid)
    user["remind_time"] = str(remind_time)
    _save(data)


def reset_user_remind_time(uid: str) -> bool:
    data = _load()
    user = _ensure_user(data, uid)
    had_value = bool(user.get("remind_time"))
    user["remind_time"] = None
    _save(data)
    return had_value


def get_effective_config(uid: str) -> Dict[str, Any]:
    data = _load()
    global_config = data["global"]
    user = _ensure_user(data, uid)
    _save(data)
    return {
        "enable": bool(global_config.get("enable", True)),
        "remind_time": user.get("remind_time") or global_config.get("global_remind_time", "每日20时"),
        "abyss_threshold": int(user.get("abyss_threshold") or global_config.get("abyss_threshold", 5)),
        "deadly_threshold": int(user.get("deadly_threshold") or global_config.get("deadly_threshold", 6)),
    }
