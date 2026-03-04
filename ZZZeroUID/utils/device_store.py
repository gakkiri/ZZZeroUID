import json
from typing import Any, Dict, Optional

from .resource.RESOURCE_PATH import MAIN_PATH

DEVICE_DATA_PATH = MAIN_PATH / "device_info.json"


def _default_data() -> Dict[str, Any]:
    return {"default": {}, "users": {}}


def _save(data: Dict[str, Any]) -> None:
    DEVICE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEVICE_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def _load() -> Dict[str, Any]:
    if not DEVICE_DATA_PATH.exists():
        data = _default_data()
        _save(data)
        return data
    with open(DEVICE_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("default", {})
    data.setdefault("users", {})
    return data


def _normalize_device(data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    device_id = str(data.get("device_id", "")).strip()
    device_fp = str(data.get("device_fp", "")).strip()
    if not device_id or not device_fp:
        return None
    return {
        "device_id": device_id,
        "device_fp": device_fp,
    }


def set_user_device(uid: str, device_id: str, device_fp: str) -> None:
    data = _load()
    data["users"][str(uid)] = {
        "device_id": str(device_id).strip(),
        "device_fp": str(device_fp).strip(),
    }
    _save(data)


def clear_user_device(uid: str) -> bool:
    data = _load()
    users = data.get("users", {})
    had_value = str(uid) in users
    users.pop(str(uid), None)
    _save(data)
    return had_value


def set_default_device(device_id: str, device_fp: str) -> None:
    data = _load()
    data["default"] = {
        "device_id": str(device_id).strip(),
        "device_fp": str(device_fp).strip(),
    }
    _save(data)


def get_device(uid: str, use_default: bool = True) -> Optional[Dict[str, str]]:
    data = _load()
    users = data.get("users", {})
    user_device = users.get(str(uid))
    normalized = _normalize_device(user_device or {})
    if normalized:
        return normalized

    if use_default:
        return _normalize_device(data.get("default", {}))
    return None
