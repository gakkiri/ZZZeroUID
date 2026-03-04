import json
import hashlib
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image

from gsuid_core.logger import logger

from .resource.RESOURCE_PATH import MAIN_PATH

DATA_URL = "https://raw.githubusercontent.com/iaoongin/GachaClock/main/spider/data/zzz/history.json"

POOL_CACHE_PATH = MAIN_PATH / "pool_history_cache.json"
POOL_BANNER_PATH = MAIN_PATH / "pool_banner"
POOL_CACHE_EXPIRE_SECONDS = 24 * 60 * 60


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _parse_datetime(raw: str) -> Optional[datetime]:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in (
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            if " " not in raw:
                dt = dt.replace(hour=0, minute=0, second=0)
            return dt
        except Exception:
            continue
    return None


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y/%m/%d %H:%M:%S")


def _load_cache() -> Optional[Dict[str, Any]]:
    if not POOL_CACHE_PATH.exists():
        return None
    try:
        with open(POOL_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(data: List[Dict[str, Any]]) -> None:
    POOL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "update_ts": int(datetime.now().timestamp()),
        "data": data,
    }
    with open(POOL_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _seed_v1_data(data: List[Dict[str, Any]]) -> None:
    if any(i.get("version") == "1.0上半" for i in data):
        return
    data.extend(
        [
            {
                "img": "https://patchwiki.biligame.com/images/zzz/thumb/7/7f/8pesvtvchbs3t2jhqjhckd9k08pe7ui.png/900px-%E7%8B%AC%E5%AE%B6%E9%A2%91%E6%AE%B5001%E6%9C%9F.png",
                "title": "「慵懒逐浪」001期独家频段",
                "type": "角色",
                "version": "1.0上半",
                "timer": "公测开启后 ~ 2024/07/24 11:59:59",
                "s": "艾莲",
                "a": ["安东", "苍角"],
            },
            {
                "img": "https://patchwiki.biligame.com/images/zzz/thumb/3/32/gs2uajlo6v2h6pljzij84wdiwhu9fkj.png/900px-%E9%9F%B3%E6%93%8E%E9%A2%91%E6%AE%B5001%E6%9C%9F.png",
                "title": "「喧哗奏鸣」001期音擎频段",
                "type": "武器",
                "version": "1.0上半",
                "timer": "公测开启后 ~ 2024/07/24 11:59:59",
                "s": "深海访客",
                "a": ["含羞恶面", "旋钻机-赤轴"],
            },
        ]
    )


def _normalize_history(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    _seed_v1_data(data)

    for pool in data:
        timer = str(pool.get("timer", ""))
        parts = [x.strip() for x in timer.split("~")]
        end_ts = 0
        if len(parts) >= 2:
            end_dt = _parse_datetime(parts[1])
            if end_dt:
                end_ts = int(end_dt.timestamp())
        pool["_end_ts"] = end_ts

    data.sort(key=lambda x: _safe_int(x.get("_end_ts")))

    for idx, pool in enumerate(data):
        timer = str(pool.get("timer", ""))
        parts = [x.strip() for x in timer.split("~")]
        end_raw = parts[1] if len(parts) >= 2 else ""

        start_dt: Optional[datetime] = None
        end_dt = _parse_datetime(end_raw) if end_raw else None

        if timer.startswith("公测开启后"):
            start_dt = _parse_datetime("2024/07/04 10:00:00")
        elif "版本更新后" in timer:
            prev_end_dt: Optional[datetime] = None
            for j in range(idx - 1, -1, -1):
                prev_end = _safe_int(data[j].get("end_ts"))
                if prev_end > 0:
                    prev_end_dt = datetime.fromtimestamp(prev_end)
                    break
            if prev_end_dt:
                start_dt = (prev_end_dt + timedelta(days=1)).replace(hour=11, minute=0, second=0)
        elif len(parts) >= 2:
            start_dt = _parse_datetime(parts[0])

        if not start_dt and end_dt:
            start_dt = end_dt - timedelta(days=20)

        start_ts = int(start_dt.timestamp()) if start_dt else 0
        end_ts = int(end_dt.timestamp()) if end_dt else _safe_int(pool.get("_end_ts"))

        if start_dt and end_dt:
            pool["timer"] = f"{_format_dt(start_dt)} ~ {_format_dt(end_dt)}"

        pool["start_ts"] = start_ts
        pool["end_ts"] = end_ts
        pool["start_time"] = _format_dt(start_dt) if start_dt else ""
        pool["end_time"] = _format_dt(end_dt) if end_dt else ""
        pool.pop("_end_ts", None)

    return data


async def get_pool_history_data() -> Optional[List[Dict[str, Any]]]:
    cache = _load_cache()
    now_ts = int(datetime.now().timestamp())

    if cache and now_ts - _safe_int(cache.get("update_ts")) <= POOL_CACHE_EXPIRE_SECONDS:
        data = cache.get("data")
        if isinstance(data, list):
            return data

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.get(DATA_URL, headers={"Cache-Control": "no-cache"})
            resp.raise_for_status()
            raw_data = resp.json()
            if not isinstance(raw_data, list):
                raise ValueError("pool history response is not list")
        data = _normalize_history(raw_data)
        _save_cache(data)
        return data
    except Exception as e:
        logger.error(f"[绝区零卡池历史] 拉取失败: {e}")
        if cache and isinstance(cache.get("data"), list):
            return cache["data"]
        return None


def _banner_file(url: str) -> Path:
    POOL_BANNER_PATH.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()
    return POOL_BANNER_PATH / f"{digest}.img"


async def get_pool_banner(url: str) -> Optional[Image.Image]:
    if not url:
        return None
    banner_path = _banner_file(url)
    if banner_path.exists():
        try:
            return Image.open(banner_path).convert("RGBA")
        except Exception:
            try:
                banner_path.unlink()
            except Exception:
                pass

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content = resp.content
        banner_path.write_bytes(content)
        return Image.open(BytesIO(content)).convert("RGBA")
    except Exception as e:
        logger.warning(f"[绝区零卡池历史] 下载卡池图失败: {e}")
        return None


def get_current_pools(data: List[Dict[str, Any]], now_ts: Optional[int] = None) -> List[Dict[str, Any]]:
    now_ts = now_ts or int(datetime.now().timestamp())
    return [pool for pool in data if _safe_int(pool.get("start_ts")) <= now_ts <= _safe_int(pool.get("end_ts"))]


def get_version_pools(data: List[Dict[str, Any]], version: str, phase: str = "") -> List[Dict[str, Any]]:
    pools = []
    for pool in data:
        pool_version = str(pool.get("version", ""))
        if not pool_version.startswith(version):
            continue
        if phase and phase not in pool_version:
            continue
        pools.append(pool)
    pools.sort(key=lambda x: _safe_int(x.get("end_ts")))
    return pools


def get_rerun_summary(data: List[Dict[str, Any]], rarity: str, target_type: str) -> List[Tuple[str, int]]:
    now = int(datetime.now().timestamp())
    latest: Dict[str, int] = {}

    for pool in data:
        if str(pool.get("type", "")) != target_type:
            continue
        end_ts = _safe_int(pool.get("end_ts"))
        if end_ts <= 0 or end_ts > now:
            continue

        targets: List[str] = []
        if rarity == "S":
            s_name = str(pool.get("s", "")).strip()
            if s_name:
                targets.append(s_name)
        else:
            a_list = pool.get("a", [])
            if isinstance(a_list, list):
                targets.extend(str(i).strip() for i in a_list if str(i).strip())
            elif isinstance(a_list, str) and a_list.strip():
                targets.append(a_list.strip())

        for name in targets:
            latest[name] = max(end_ts, latest.get(name, 0))

    result: List[Tuple[str, int]] = []
    for name, ts in latest.items():
        days = max(0, int((now - ts) // 86400))
        result.append((name, days))
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def get_item_history(data: List[Dict[str, Any]], query_name: str) -> List[Dict[str, Any]]:
    records = []
    for pool in data:
        if str(pool.get("s", "")) == query_name:
            records.append(pool)
            continue
        a_list = pool.get("a", [])
        if isinstance(a_list, list) and query_name in a_list:
            records.append(pool)
            continue
        if isinstance(a_list, str) and query_name == a_list:
            records.append(pool)
            continue
    records.sort(key=lambda x: _safe_int(x.get("end_ts")))
    return records
