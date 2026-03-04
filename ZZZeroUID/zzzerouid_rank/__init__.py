from typing import Any, Dict, List, Optional

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.database.models import GsBind

from ..utils.hint import BIND_UID_HINT, prefix
from ..utils.rank_store import (
    get_records,
    is_group_enable,
    reset_records,
    set_group_enable,
    set_user_visible,
)
from .draw_rank import draw_rank_img

sv_zzz_rank = SV("zzz群排名")
sv_zzz_rank_admin = SV("zzz群排名管理", pm=1)

RANK_LIMIT = 15
RANK_INFO: Dict[str, Dict[str, str]] = {
    "ABYSS": {
        "display": "式舆防卫战",
        "short": "深渊",
        "query_hint": "深渊",
    },
    "DEADLY": {
        "display": "危局强袭战",
        "short": "危局",
        "query_hint": "危局",
    },
    "VOID": {
        "display": "临界推演",
        "short": "临界",
        "query_hint": "临界推演",
    },
    "ALL": {
        "display": "式舆防卫战、危局强袭战和临界推演",
        "short": "全部",
        "query_hint": "深渊/危局/临界推演",
    },
}
RATING_ORDER = {"S+": 5, "S": 4, "A": 3, "B": 2, "C": 1}


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _get_group_id(ev: Event) -> Optional[str]:
    group_id = getattr(ev, "group_id", None)
    if not group_id:
        return None
    return str(group_id)


def _parse_rank_type(text: str, default: Optional[str] = None) -> Optional[str]:
    if any(k in text for k in ("式舆防卫战", "式舆", "深渊", "防卫战", "防卫")):
        return "ABYSS"
    if any(k in text for k in ("危局强袭战", "危局", "强袭战", "强袭")):
        return "DEADLY"
    if any(k in text for k in ("临界推演", "临界", "推演")):
        return "VOID"
    return default


def _parse_switch_action(text: str) -> Optional[bool]:
    if any(k in text for k in ("显示", "展示", "开启", "打开", "on", "启用", "启动")):
        return True
    if any(k in text for k in ("隐藏", "取消显示", "关闭", "关掉", "off", "禁用", "停止")):
        return False
    return None


def _sort_records(rank_type: str, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if rank_type == "ABYSS":
        return sorted(
            records,
            key=lambda x: (
                -_safe_int(x.get("score")),
                -RATING_ORDER.get(str(x.get("rating", "C")).upper(), 0),
                _safe_int(x.get("update_ts")),
            ),
        )
    if rank_type == "DEADLY":
        return sorted(
            records,
            key=lambda x: (
                -_safe_int(x.get("total_star")),
                -_safe_int(x.get("total_score")),
                _safe_int(x.get("update_ts")),
            ),
        )
    return sorted(
        records,
        key=lambda x: (
            -_safe_int(x.get("total_score")),
            _safe_int(x.get("update_ts")),
        ),
    )


async def _send_group_rank(bot: Bot, ev: Event, rank_type: str):
    group_id = _get_group_id(ev)
    if not group_id:
        return await bot.send("请在群聊中使用该命令！")

    if not is_group_enable(group_id, rank_type):
        return await bot.send(f"当前群{RANK_INFO[rank_type]['display']}排名功能已关闭！")

    records = _sort_records(rank_type, get_records(group_id, rank_type))
    if not records:
        return await bot.send(
            f"没有{RANK_INFO[rank_type]['display']}排名，请先 "
            f"{prefix}显示{RANK_INFO[rank_type]['short']}排名，并且用 "
            f"{prefix}{RANK_INFO[rank_type]['query_hint']} 查询战绩"
        )

    records = records[:RANK_LIMIT]
    img = await draw_rank_img(rank_type, RANK_INFO[rank_type]["display"], records)
    await bot.send(img)


@sv_zzz_rank.on_fullmatch(
    (
        "式舆防卫战排名",
        "式舆排名",
        "深渊排名",
        "防卫战排名",
        "防卫排名",
    ),
    block=True,
)
async def send_abyss_rank(bot: Bot, ev: Event):
    await _send_group_rank(bot, ev, "ABYSS")


@sv_zzz_rank.on_fullmatch(
    (
        "危局强袭战排名",
        "危局排名",
        "强袭战排名",
        "强袭排名",
    ),
    block=True,
)
async def send_deadly_rank(bot: Bot, ev: Event):
    await _send_group_rank(bot, ev, "DEADLY")


@sv_zzz_rank.on_fullmatch(
    (
        "临界推演排名",
        "临界排名",
        "推演排名",
    ),
    block=True,
)
async def send_void_rank(bot: Bot, ev: Event):
    await _send_group_rank(bot, ev, "VOID")


@sv_zzz_rank.on_prefix(
    (
        "显示",
        "展示",
        "开启",
        "打开",
        "on",
        "启用",
        "启动",
        "隐藏",
        "取消显示",
        "关闭",
        "关掉",
        "off",
        "禁用",
        "停止",
    ),
)
async def switch_user_rank(bot: Bot, ev: Event):
    msg = f"{ev.command}{ev.text}".strip()
    if "排名" not in msg:
        return
    if msg.startswith(("开启群", "开启群内", "关闭群", "关闭群内")):
        return

    group_id = _get_group_id(ev)
    if not group_id:
        return await bot.send("请在群聊中使用该命令！")

    action = _parse_switch_action(msg)
    if action is None:
        return await bot.send('请输入"显示"或"隐藏"来设置是否显示个人排名')

    rank_type = _parse_rank_type(msg, default="ALL")
    if rank_type is None:
        return

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id, "zzz")
    if not uid:
        return await bot.send(BIND_UID_HINT)

    set_user_visible(group_id, uid, rank_type, action)
    action_name = "显示" if action else "隐藏"
    await bot.send(
        f"绝区零 UID: {uid}，{RANK_INFO[rank_type]['display']}排名功能已设置为: {action_name}"
    )


@sv_zzz_rank_admin.on_prefix(("开启群", "开启群内", "关闭群", "关闭群内"))
async def switch_group_rank(bot: Bot, ev: Event):
    msg = f"{ev.command}{ev.text}".strip()
    if "排名" not in msg:
        return

    group_id = _get_group_id(ev)
    if not group_id:
        return await bot.send("请在群聊中使用该命令！")

    action = _parse_switch_action(msg)
    if action is None:
        return await bot.send('请输入"开启"或"关闭"来设置群内排名功能')

    rank_type = _parse_rank_type(msg, default="ALL")
    if rank_type is None:
        return

    set_group_enable(group_id, rank_type, action)
    action_name = "开启" if action else "关闭"
    await bot.send(
        f"当前群{RANK_INFO[rank_type]['display']}排名功能已设置为: {action_name}"
    )


@sv_zzz_rank_admin.on_prefix(("重置", "清空"))
async def reset_group_rank(bot: Bot, ev: Event):
    msg = f"{ev.command}{ev.text}".strip()
    if "排名" not in msg:
        return

    group_id = _get_group_id(ev)
    if not group_id:
        return await bot.send("请在群聊中使用该命令！")

    rank_type = _parse_rank_type(msg, default="ALL")
    if rank_type is None:
        return

    reset_records(group_id, rank_type)
    await bot.send(f"清除{RANK_INFO[rank_type]['display']}排名成功！")
