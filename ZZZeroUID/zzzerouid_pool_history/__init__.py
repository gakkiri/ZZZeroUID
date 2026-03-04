import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.name_convert import alias_to_char_name
from ..utils.pool_history import (
    get_current_pools,
    get_item_history,
    get_pool_history_data,
    get_rerun_summary,
    get_version_pools,
)
from .draw_pool_history import (
    draw_all_pool_img,
    draw_current_pool_img,
    draw_item_history_img,
    draw_rerun_summary_img,
    draw_version_pool_img,
)

sv_zzz_pool = SV("绝区零卡池历史")

HISTORY_SUFFIX = (
    "复刻记录",
    "复刻历史",
    "复刻统计",
    "卡池记录",
    "卡池历史",
    "卡池统计",
)


def _parse_summary(raw: str):
    raw = raw.strip()
    if re.match(r"^(五星|S级?)?(角色|代理人)$", raw, flags=re.I):
        return "S", "角色"
    if re.match(r"^(四星|A级?)?(角色|代理人)$", raw, flags=re.I):
        return "A", "角色"
    if re.match(r"^(五星|S级?)(武器|音擎)$", raw, flags=re.I):
        return "S", "武器"
    if re.match(r"^(四星|A级?)(武器|音擎)$", raw, flags=re.I):
        return "A", "武器"
    return None


@sv_zzz_pool.on_suffix("卡池", block=True)
async def query_pool_by_suffix(bot: Bot, ev: Event):
    raw = ev.text.strip()
    data = await get_pool_history_data()
    if not data:
        return await bot.send("卡池历史记录数据获取失败")

    if raw in ("", "当前", "本期", "当期"):
        pools = get_current_pools(data)
        if not pools:
            return await bot.send("当前没有正在进行的活动卡池。")
        return await bot.send(await draw_current_pool_img(pools))

    version_match = re.match(r"^v?(\d+\.\d+)(上半|下半)?$", raw)
    if version_match:
        version = version_match.group(1)
        phase = version_match.group(2) or ""
        pools = get_version_pools(data, version, phase)
        if not pools:
            return await bot.send(f"未查询到绝区零 {version}{phase} 版本的卡池数据")
        return await bot.send(await draw_version_pool_img(version, phase, pools))


@sv_zzz_pool.on_suffix(HISTORY_SUFFIX, block=True)
async def query_pool_history(bot: Bot, ev: Event):
    raw = ev.text.strip()
    data = await get_pool_history_data()
    if not data:
        return await bot.send("卡池历史记录数据获取失败")

    if not raw:
        return await bot.send(await draw_all_pool_img(data))

    summary = _parse_summary(raw)
    if summary:
        rarity, target_type = summary
        rows = get_rerun_summary(data, rarity, target_type)
        if not rows:
            return await bot.send("暂无可用统计数据")
        return await bot.send(await draw_rerun_summary_img(rarity, target_type, rows))

    query_name = alias_to_char_name(raw)
    records = get_item_history(data, query_name)
    if not records:
        return await bot.send(f"未找到【{query_name}】卡池记录，请检查名称后重试")

    first = records[0]
    is_s = str(first.get("s", "")) == query_name
    rarity = "S" if is_s else "A"
    pool_type = str(first.get("type", "角色"))
    return await bot.send(await draw_item_history_img(query_name, rarity, pool_type, records))
