import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .resource.RESOURCE_PATH import MAIN_PATH

RANK_DATA_PATH = MAIN_PATH / "rank_data.json"

RANK_TYPES = ("ABYSS", "DEADLY", "VOID")
DEFAULT_GROUP_ENABLE = {"ABYSS": True, "DEADLY": True, "VOID": True}


def _ensure_file() -> None:
    if not RANK_DATA_PATH.exists():
        _save({"groups": {}})


def _load() -> Dict[str, Any]:
    _ensure_file()
    with open(RANK_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: Dict[str, Any]) -> None:
    RANK_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RANK_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def _ensure_group(data: Dict[str, Any], group_id: str) -> Dict[str, Any]:
    groups = data.setdefault("groups", {})
    group = groups.setdefault(
        group_id,
        {
            "enable": dict(DEFAULT_GROUP_ENABLE),
            "users": {},
            "records": {"ABYSS": {}, "DEADLY": {}, "VOID": {}},
        },
    )
    group.setdefault("enable", dict(DEFAULT_GROUP_ENABLE))
    group.setdefault("users", {})
    group.setdefault("records", {"ABYSS": {}, "DEADLY": {}, "VOID": {}})
    for t in RANK_TYPES:
        group["enable"].setdefault(t, True)
        group["records"].setdefault(t, {})
    return group


def _ensure_user(group: Dict[str, Any], uid: str) -> Dict[str, Any]:
    users = group.setdefault("users", {})
    user = users.setdefault(
        uid,
        {
            "qq_list": [],
            "visible": {"ABYSS": True, "DEADLY": True, "VOID": True},
        },
    )
    user.setdefault("qq_list", [])
    user.setdefault("visible", {"ABYSS": True, "DEADLY": True, "VOID": True})
    for t in RANK_TYPES:
        user["visible"].setdefault(t, True)
    return user


def set_group_enable(group_id: str, rank_type: str, enable: bool) -> None:
    data = _load()
    group = _ensure_group(data, str(group_id))
    if rank_type == "ALL":
        for t in RANK_TYPES:
            group["enable"][t] = bool(enable)
    else:
        group["enable"][rank_type] = bool(enable)
    _save(data)


def is_group_enable(group_id: str, rank_type: str) -> bool:
    data = _load()
    group = _ensure_group(data, str(group_id))
    _save(data)
    return bool(group["enable"].get(rank_type, True))


def set_user_visible(group_id: str, uid: str, rank_type: str, visible: bool) -> None:
    data = _load()
    group = _ensure_group(data, str(group_id))
    user = _ensure_user(group, uid)
    if rank_type == "ALL":
        for t in RANK_TYPES:
            user["visible"][t] = bool(visible)
    else:
        user["visible"][rank_type] = bool(visible)
    _save(data)


def get_user_visible(group_id: str, uid: str, rank_type: str) -> bool:
    data = _load()
    group = _ensure_group(data, str(group_id))
    user = _ensure_user(group, uid)
    _save(data)
    return bool(user["visible"].get(rank_type, True))


def reset_records(group_id: str, rank_type: str) -> None:
    data = _load()
    group = _ensure_group(data, str(group_id))
    if rank_type == "ALL":
        for t in RANK_TYPES:
            group["records"][t] = {}
    else:
        group["records"][rank_type] = {}
    _save(data)


def update_record(
    group_id: str,
    rank_type: str,
    uid: str,
    qq: str,
    name: str,
    record: Dict[str, Any],
) -> None:
    data = _load()
    group = _ensure_group(data, str(group_id))
    user = _ensure_user(group, uid)

    if qq and qq not in user["qq_list"]:
        user["qq_list"].append(qq)

    record.setdefault("uid", uid)
    record.setdefault("name", name or uid)
    record.setdefault("update_ts", int(datetime.now().timestamp()))
    group["records"][rank_type][uid] = record
    _save(data)


def get_records(group_id: str, rank_type: str) -> List[Dict[str, Any]]:
    data = _load()
    group = _ensure_group(data, str(group_id))
    records = group["records"].get(rank_type, {})
    users = group["users"]

    result: List[Dict[str, Any]] = []
    for uid, item in records.items():
        user = users.get(uid, {})
        visible = bool(user.get("visible", {}).get(rank_type, True))
        if not visible:
            continue
        result.append(item)
    return result


def format_ts(ts: Optional[int]) -> str:
    if not ts:
        return "-"
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%m-%d %H:%M")
    except Exception:
        return "-"
