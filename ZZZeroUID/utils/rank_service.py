import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from gsuid_core.logger import logger
from gsuid_core.models import Event

from .rank_store import is_group_enable, update_record
from .zzzero_api import zzz_api


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_ts(time_data: Optional[Dict[str, Any]]) -> int:
    if not isinstance(time_data, dict):
        return 0
    try:
        return int(
            datetime(
                int(time_data.get("year", 1970)),
                int(time_data.get("month", 1)),
                int(time_data.get("day", 1)),
                int(time_data.get("hour", 0)),
                int(time_data.get("minute", 0)),
                int(time_data.get("second", 0)),
            ).timestamp()
        )
    except Exception:
        return 0


def _get_group_and_qq(ev: Event) -> Optional[Dict[str, str]]:
    group_id = getattr(ev, "group_id", None)
    if not group_id:
        return None
    qq = ev.at if ev.at else ev.user_id
    return {
        "group_id": str(group_id),
        "qq": str(qq),
    }


def _is_current_period(now_ts: int, begin_ts: int, end_ts: int) -> bool:
    if begin_ts <= 0 or end_ts <= 0:
        return True
    return begin_ts <= now_ts <= end_ts


async def refresh_abyss_rank_cache(uid: str, ev: Event) -> bool:
    ctx = _get_group_and_qq(ev)
    if not ctx:
        return False
    group_id = ctx["group_id"]
    if not is_group_enable(group_id, "ABYSS"):
        return False

    data_raw = await zzz_api.get_zzz_hadal_info(uid, 1)
    if isinstance(data_raw, int):
        return False

    hadal_data = data_raw.get("hadal_info_v2", {})
    if not isinstance(hadal_data, dict):
        return False

    brief = hadal_data.get("brief", {})
    if not isinstance(brief, dict):
        return False

    has_fourth = bool(hadal_data.get("fourth_layer_detail"))
    has_fifth = bool(
        hadal_data.get("fitfh_layer_detail", {}).get("layer_challenge_info_list")
    )
    if not has_fourth and not has_fifth:
        return False

    now_ts = int(time.time())
    begin_ts = _safe_int(hadal_data.get("begin_time"))
    end_ts = _safe_int(hadal_data.get("end_time"))
    if not _is_current_period(now_ts, begin_ts, end_ts):
        return False

    update_ts = _to_ts(brief.get("challenge_time")) or now_ts
    record = {
        "score": _safe_int(brief.get("score")),
        "rating": str(brief.get("rating", "C")).upper(),
        "rank_percent": _safe_int(brief.get("rank_percent")),
        "update_ts": update_ts,
    }

    update_record(
        group_id=group_id,
        rank_type="ABYSS",
        uid=uid,
        qq=ctx["qq"],
        name=str(data_raw.get("nick_name") or uid),
        record=record,
    )
    return True


async def refresh_deadly_rank_cache(uid: str, ev: Event) -> bool:
    ctx = _get_group_and_qq(ev)
    if not ctx:
        return False
    group_id = ctx["group_id"]
    if not is_group_enable(group_id, "DEADLY"):
        return False

    data = await zzz_api.get_zzz_mem_info(uid, 1)
    if isinstance(data, int):
        return False
    if not data.get("has_data") or not data.get("list"):
        return False

    now_ts = int(time.time())
    start_ts = _to_ts(data.get("start_time"))
    end_ts = _to_ts(data.get("end_time"))
    if not _is_current_period(now_ts, start_ts, end_ts):
        return False

    items: List[Dict[str, Any]] = data.get("list", [])
    update_ts = 0
    for item in items:
        update_ts = max(update_ts, _to_ts(item.get("challenge_time")))
    update_ts = update_ts or now_ts

    total_score = _safe_int(data.get("total_score"))
    total_star = _safe_int(data.get("total_star"))
    if not total_score:
        total_score = sum(_safe_int(item.get("score")) for item in items)
    if not total_star:
        total_star = sum(_safe_int(item.get("star")) for item in items)

    record = {
        "total_score": total_score,
        "total_star": total_star,
        "rank_percent": _safe_int(data.get("rank_percent")),
        "update_ts": update_ts,
    }

    update_record(
        group_id=group_id,
        rank_type="DEADLY",
        uid=uid,
        qq=ctx["qq"],
        name=str(data.get("nick_name") or uid),
        record=record,
    )
    return True


async def refresh_void_rank_cache(uid: str, ev: Event) -> bool:
    ctx = _get_group_and_qq(ev)
    if not ctx:
        return False
    group_id = ctx["group_id"]
    if not is_group_enable(group_id, "VOID"):
        return False

    data = await zzz_api.get_zzz_void_info(uid)
    if isinstance(data, int):
        return False

    brief = data.get("void_front_battle_abstract_info_brief", {})
    if not isinstance(brief, dict):
        return False
    if not brief.get("has_ending_record"):
        return False

    now_ts = int(time.time())
    end_ts = _safe_int(brief.get("end_ts"))
    if end_ts and now_ts > end_ts:
        return False

    update_ts = 0
    boss_record = data.get("boss_challenge_record") or {}
    main_record = boss_record.get("main_challenge_record") or {}
    update_ts = max(update_ts, _to_ts(main_record.get("challenge_time")))

    for item in data.get("main_challenge_record_list", []):
        update_ts = max(update_ts, _to_ts(item.get("challenge_time")))
    update_ts = update_ts or now_ts

    role_basic = data.get("role_basic_info") or {}
    record = {
        "total_score": _safe_int(brief.get("total_score")),
        "rank_percent": _safe_int(brief.get("rank_percent")),
        "update_ts": update_ts,
    }

    update_record(
        group_id=group_id,
        rank_type="VOID",
        uid=uid,
        qq=ctx["qq"],
        name=str(role_basic.get("nickname") or uid),
        record=record,
    )
    return True


async def refresh_rank_cache_by_type(rank_type: str, uid: str, ev: Event) -> bool:
    try:
        if rank_type == "ABYSS":
            return await refresh_abyss_rank_cache(uid, ev)
        if rank_type == "DEADLY":
            return await refresh_deadly_rank_cache(uid, ev)
        if rank_type == "VOID":
            return await refresh_void_rank_cache(uid, ev)
    except Exception as e:
        logger.exception(f"[绝区零排名] 刷新缓存失败, type={rank_type}, uid={uid}, err={e}")
    return False
