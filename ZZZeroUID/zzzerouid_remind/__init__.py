import re
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.subscribe import gs_subscribe
from gsuid_core.utils.database.models import GsBind

from ..utils.hint import BIND_UID_HINT, error_reply
from ..utils.zzzero_api import zzz_api
from ..utils.challenge_remind_store import (
    get_global_config,
    get_effective_config,
    get_user_config,
    reset_user_remind_time,
    set_global_enable,
    set_global_remind_time,
    set_global_threshold,
    set_user_remind_time,
    set_user_threshold,
)

sv_zzz_remind = SV("绝区零挑战提醒")
sv_zzz_remind_admin = SV("绝区零挑战提醒配置", pm=1)

REMIND_TASK_NAME = "[绝区零] 挑战提醒"


def _parse_remind_time(message: str) -> Tuple[Optional[str], Optional[str]]:
    pattern = r"(每日\d+时(?:(\d+)分)?|每周[日天一二三四五六]\d+时(?:(\d+)分)?)"
    match = re.search(pattern, message)
    if not match:
        return None, "时间格式错误，请使用例如：每日20时 / 每周六20时10分"
    remind_time = match.group(1)
    minute = int(match.group(2) or match.group(3) or 0)
    if minute < 0 or minute >= 60 or minute % 10 != 0:
        return None, "分钟必须是 0~59 的整十分钟"
    return remind_time, None


def _is_time_match(remind_time: str, now: datetime) -> bool:
    if "每日" in remind_time:
        match = re.search(r"每日(\d+)时(?:(\d+)分)?", remind_time)
        if not match:
            return False
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        return now.hour == hour and now.minute == minute

    if "每周" in remind_time:
        day_map = {"日": 0, "天": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
        match = re.search(r"每周([日天一二三四五六])(\d+)时(?:(\d+)分)?", remind_time)
        if not match:
            return False
        week_day = day_map[match.group(1)]
        hour = int(match.group(2))
        minute = int(match.group(3) or 0)
        current_day = (now.weekday() + 1) % 7
        return current_day == week_day and now.hour == hour and now.minute == minute

    return False


def _time_to_ts(time_data: Optional[Dict[str, Any]]) -> int:
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


def _format_period_ts(begin_ts: int, end_ts: int) -> str:
    if begin_ts <= 0 or end_ts <= 0:
        return ""
    begin = datetime.fromtimestamp(begin_ts)
    end = datetime.fromtimestamp(end_ts)
    left = end_ts - int(time.time())
    days = max(0, left // 86400)
    hours = max(0, (left % 86400) // 3600)
    return (
        f"统计周期：{begin.year}/{begin.month}/{begin.day}"
        f" - {end.year}/{end.month}/{end.day}\n"
        f"刷新剩余: {days}天{hours}小时"
    )


async def _check_uid_status(
    uid: str,
    abyss_threshold: int,
    deadly_threshold: int,
    show_all: bool = False,
) -> list[str]:
    messages: list[str] = []

    challenge_data = await zzz_api.get_zzz_challenge_info(uid, 1)
    hadal_data = await zzz_api.get_zzz_hadal_info(uid, 1)
    if isinstance(challenge_data, int):
        messages.append(f"式舆防卫战查询失败: {error_reply(challenge_data)}")
    else:
        all_floors = challenge_data.get("all_floor_detail", [])
        s_count = sum(1 for floor in all_floors if str(floor.get("rating", "")).upper().startswith("S"))
        s_count = min(5, s_count)
        challenge_alert_added = False
        fifth_rating = ""
        if isinstance(hadal_data, dict):
            fifth_rating = str(
                hadal_data.get("hadal_info_v2", {}).get("brief", {}).get("rating", "")
            ).upper()

        if abyss_threshold < 6:
            ok = s_count >= abyss_threshold
            if show_all or not ok:
                challenge_alert_added = True
                status = " ✓" if ok else ""
                messages.append(f"式舆防卫战S评级: {s_count}/5{status}")
                if fifth_rating:
                    messages.append(f"第五层评价: {fifth_rating}")
        else:
            ok = s_count >= 5 and fifth_rating == "S+"
            if show_all or not ok:
                challenge_alert_added = True
                status = " ✓" if ok else ""
                messages.append(f"式舆防卫战S评级: {s_count}/5{status}")
                messages.append(f"第五层评价: {fifth_rating or '无'}{' ✓' if fifth_rating == 'S+' else ''}")

        if challenge_alert_added:
            period = _format_period_ts(
                int(challenge_data.get("begin_time", 0)),
                int(challenge_data.get("end_time", 0)),
            )
            if period:
                messages.append(period)

    mem_data = await zzz_api.get_zzz_mem_info(uid, 1)
    if isinstance(mem_data, int):
        messages.append(f"危局强袭战查询失败: {error_reply(mem_data)}")
    else:
        total_star = int(mem_data.get("total_star", 0))
        ok = total_star >= deadly_threshold
        if show_all or not ok:
            status = " ✓" if ok else ""
            messages.append(f"危局强袭战星数: {total_star}/9{status}")

            start_ts = _time_to_ts(mem_data.get("start_time"))
            end_ts = _time_to_ts(mem_data.get("end_time"))
            period = _format_period_ts(start_ts, end_ts)
            if period:
                messages.append(period)

    return messages


async def _get_uid(ev: Event) -> Optional[str]:
    return await GsBind.get_uid_by_game(ev.user_id, ev.bot_id, "zzz")


@sv_zzz_remind.on_fullmatch(("开启挑战提醒", "关闭挑战提醒"), block=True)
async def set_challenge_remind(bot: Bot, ev: Event):
    global_config = get_global_config()
    is_enable = "开启" in ev.command
    if is_enable and not global_config.get("enable", True):
        return await bot.send("当前未启用防卫战/危局挑战提醒功能")

    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)

    if is_enable:
        if await gs_subscribe.get_subscribe(REMIND_TASK_NAME, uid=uid):
            return await bot.send("挑战提醒已开启，请勿重复操作")

        await gs_subscribe.add_subscribe("single", REMIND_TASK_NAME, ev, uid=uid)
        cfg = get_effective_config(uid)
        await bot.send(
            "挑战提醒已开启，"
            f"将在 {cfg['remind_time']} 检查式舆<"
            f"{cfg['abyss_threshold']}层或危局<{cfg['deadly_threshold']}星"
        )
        return

    data = await gs_subscribe.get_subscribe(REMIND_TASK_NAME, uid=uid)
    if data:
        await gs_subscribe.delete_subscribe("single", REMIND_TASK_NAME, ev, uid=uid)
        return await bot.send("挑战提醒已关闭")
    await bot.send("挑战提醒尚未开启")


@sv_zzz_remind_admin.on_fullmatch(("开启全局挑战提醒", "启用全局挑战提醒", "关闭全局挑战提醒", "禁用全局挑战提醒"), block=True)
async def set_global_challenge_remind(bot: Bot, ev: Event):
    enable = ("开启" in ev.command) or ("启用" in ev.command)
    current = bool(get_global_config().get("enable", True))
    if current == enable:
        return await bot.send(
            f"全局防卫战/危局挑战提醒功能已{'启用' if enable else '禁用'}，请勿重复操作"
        )
    set_global_enable(enable)
    await bot.send(f"全局防卫战/危局挑战提醒功能已{'启用' if enable else '禁用'}")


@sv_zzz_remind.on_prefix("设置")
async def set_personal_threshold(bot: Bot, ev: Event):
    msg = f"{ev.command}{ev.text}".strip()
    if "阈值" not in msg or "全局" in msg:
        return

    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)

    abyss_match = re.search(r"(?:式舆防卫战|式舆|深渊|防卫战|防卫)阈值\s*(\d+)", msg)
    if abyss_match:
        value = int(abyss_match.group(1))
        if value < 1 or value > 6:
            return await bot.send("防卫战阈值必须在1到6之间")
        set_user_threshold(uid, "ABYSS", value)
        return await bot.send(
            f"式舆防卫战阈值已设为: S层数<{min(5, value)}层"
            f"{'或第五层<S+评价' if value == 6 else ''}时提醒"
        )

    deadly_match = re.search(r"(?:危局强袭战|危局|强袭|强袭战)阈值\s*(\d+)", msg)
    if deadly_match:
        value = int(deadly_match.group(1))
        if value < 1 or value > 9:
            return await bot.send("危局阈值必须在1到9之间")
        set_user_threshold(uid, "DEADLY", value)
        return await bot.send(f"危局强袭战阈值已设为: <{value}星时提醒")


@sv_zzz_remind_admin.on_prefix("设置全局")
async def set_global_threshold_or_time(bot: Bot, ev: Event):
    msg = f"{ev.command}{ev.text}".strip()

    if "提醒时间" in msg:
        remind_time, error = _parse_remind_time(msg)
        if not remind_time:
            return await bot.send(error or "时间格式错误")
        set_global_remind_time(remind_time)
        return await bot.send(f"全局提醒时间已更新为: {remind_time}")

    abyss_match = re.search(r"(?:式舆防卫战|式舆|深渊|防卫战|防卫)阈值\s*(\d+)", msg)
    if abyss_match:
        value = int(abyss_match.group(1))
        if value < 1 or value > 6:
            return await bot.send("防卫战阈值必须在1到6之间")
        set_global_threshold("ABYSS", value)
        return await bot.send(
            f"全局默认式舆防卫战阈值已设为: S层数<{min(5, value)}层"
            f"{'或第五层<S+评价' if value == 6 else ''}时提醒"
        )

    deadly_match = re.search(r"(?:危局强袭战|危局|强袭|强袭战)阈值\s*(\d+)", msg)
    if deadly_match:
        value = int(deadly_match.group(1))
        if value < 1 or value > 9:
            return await bot.send("危局阈值必须在1到9之间")
        set_global_threshold("DEADLY", value)
        return await bot.send(f"全局默认危局强袭战阈值已设为: <{value}星时提醒")


@sv_zzz_remind.on_prefix("设置个人提醒时间")
async def set_user_remind_time_cmd(bot: Bot, ev: Event):
    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)
    remind_time, error = _parse_remind_time(f"{ev.command}{ev.text}")
    if not remind_time:
        return await bot.send(error or "时间格式错误")
    set_user_remind_time(uid, remind_time)
    await bot.send(f"个人提醒时间已设置为: {remind_time}")


@sv_zzz_remind.on_fullmatch("个人提醒时间", block=True)
async def view_user_remind_time(bot: Bot, ev: Event):
    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)
    user_cfg = get_user_config(uid)
    if user_cfg.get("remind_time"):
        return await bot.send(f"当前个人提醒时间: {user_cfg['remind_time']}")
    global_cfg = get_global_config()
    await bot.send(
        f"个人提醒时间未设置，默认使用全局时间: {global_cfg.get('global_remind_time', '每日20时')}"
    )


@sv_zzz_remind.on_fullmatch(("重置个人提醒时间", "删除个人提醒时间", "取消个人提醒时间"), block=True)
async def reset_user_remind_time_cmd(bot: Bot, ev: Event):
    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)
    if reset_user_remind_time(uid):
        return await bot.send("个人提醒时间已重置为全局默认时间")
    await bot.send("个人提醒时间尚未设置")


@sv_zzz_remind.on_fullmatch("全局提醒时间", block=True)
async def view_global_remind_time(bot: Bot, ev: Event):
    global_cfg = get_global_config()
    await bot.send(f"当前全局提醒时间: {global_cfg.get('global_remind_time', '每日20时')}")


@sv_zzz_remind.on_fullmatch("查询挑战状态", block=True)
async def check_challenge_status(bot: Bot, ev: Event):
    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)

    cfg = get_effective_config(uid)
    await bot.send("正在查询，请稍候...")
    messages = await _check_uid_status(
        uid,
        abyss_threshold=cfg["abyss_threshold"],
        deadly_threshold=cfg["deadly_threshold"],
        show_all=True,
    )
    if not messages:
        return await bot.send("查询失败，请稍后再试")
    head = (
        f"提醒时间: {cfg['remind_time']}\n"
        f"式舆阈值: {cfg['abyss_threshold']}\n"
        f"危局阈值: {cfg['deadly_threshold']}"
    )
    await bot.send(head + "\n" + "\n".join(messages))


@scheduler.scheduled_job("cron", minute="*/10")
async def zzz_challenge_remind_job():
    global_cfg = get_global_config()
    if not global_cfg.get("enable", True):
        return

    datas = await gs_subscribe.get_subscribe(REMIND_TASK_NAME)
    if not datas:
        return

    now = datetime.now()
    logger.info("[绝区零挑战提醒] 开始执行定时检查...")

    for sub in datas:
        uid = str(sub.uid) if getattr(sub, "uid", None) else ""
        if not uid:
            continue

        cfg = get_effective_config(uid)
        if not _is_time_match(cfg["remind_time"], now):
            continue

        messages = await _check_uid_status(
            uid,
            abyss_threshold=cfg["abyss_threshold"],
            deadly_threshold=cfg["deadly_threshold"],
            show_all=False,
        )
        if messages:
            try:
                await sub.send("【式舆/危局挑战提醒】\n" + "\n".join(messages))
            except Exception as e:
                logger.error(f"[绝区零挑战提醒] 推送失败 uid={uid}, err={e}")

    logger.info("[绝区零挑战提醒] 定时检查结束")
