from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from gsuid_core.utils.image.convert import convert_img

from ..utils.image import GREY, BLUE, YELLOW, add_footer, get_zzz_bg
from ..utils.pool_history import get_pool_banner
from ..utils.fonts.zzz_fonts import (
    zzz_font_22,
    zzz_font_26,
    zzz_font_30,
    zzz_font_38,
    zzz_font_44,
)

CARD_W = 1040
TITLE_Y = 64


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _to_a_text(pool: Dict[str, Any]) -> str:
    a_list = pool.get("a", [])
    if isinstance(a_list, list):
        return "、".join(str(i) for i in a_list)
    return str(a_list)


def _draw_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str = "") -> None:
    draw.text((80, TITLE_Y), title, "white", zzz_font_44, "lm")
    if subtitle:
        draw.text((80, 112), subtitle, GREY, zzz_font_26, "lm")


async def _draw_pool_card(pool: Dict[str, Any], index: int = 0) -> Image.Image:
    card = Image.new("RGBA", (CARD_W, 320), (20, 20, 24, 210))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((0, 0, CARD_W - 1, 319), 26, outline=(255, 255, 255, 40), width=2)

    version = str(pool.get("version", "-"))
    pool_type = "角色调频" if str(pool.get("type", "")) == "角色" else "音擎调频"
    s_name = str(pool.get("s", "-"))
    a_names = _to_a_text(pool)
    timer = str(pool.get("timer", "")).replace(" 00:00:00", "")

    draw.text((42, 42), f"#{index}  v{version}  {pool_type}", "white", zzz_font_30, "lm")
    draw.text((42, 88), f"S级：{s_name}", YELLOW, zzz_font_30, "lm")
    draw.text((42, 132), f"A级：{a_names}", BLUE, zzz_font_26, "lm")
    draw.text((42, 184), "时间", GREY, zzz_font_22, "lm")
    draw.text((42, 216), timer, "white", zzz_font_22, "lm")

    banner = await get_pool_banner(str(pool.get("img", "")))
    if banner:
        banner = banner.resize((430, 242)).convert("RGBA")
        card.paste(banner, (586, 38), banner)
    else:
        draw.rounded_rectangle((586, 38, 1016, 280), 16, fill=(44, 44, 55, 255))
        draw.text((801, 160), "无卡池图片", GREY, zzz_font_30, "mm")

    return card


async def draw_current_pool_img(pools: List[Dict[str, Any]]) -> bytes:
    h = 190 + len(pools) * 340 + 90
    bg = get_zzz_bg(1100, h, "bg2")
    draw = ImageDraw.Draw(bg)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    _draw_title(draw, "绝区零当前卡池", f"生成时间：{now}")

    for idx, pool in enumerate(pools, start=1):
        card = await _draw_pool_card(pool, idx)
        bg.paste(card, (30, 150 + (idx - 1) * 340), card)

    bg = add_footer(bg)
    return await convert_img(bg)


async def draw_version_pool_img(version: str, phase: str, pools: List[Dict[str, Any]]) -> bytes:
    phase_label = phase if phase else "全期"
    h = 210 + len(pools) * 340 + 90
    bg = get_zzz_bg(1100, h, "bg4")
    draw = ImageDraw.Draw(bg)
    _draw_title(draw, f"绝区零 v{version}{phase} 卡池", f"范围：{phase_label}")

    for idx, pool in enumerate(pools, start=1):
        card = await _draw_pool_card(pool, idx)
        bg.paste(card, (30, 170 + (idx - 1) * 340), card)

    bg = add_footer(bg)
    return await convert_img(bg)


async def draw_all_pool_img(data: List[Dict[str, Any]]) -> bytes:
    rows: List[str] = []
    for pool in sorted(data, key=lambda x: _safe_int(x.get("end_ts")), reverse=True):
        pool_type = "角色" if str(pool.get("type", "")) == "角色" else "音擎"
        version = str(pool.get("version", "-"))
        s_name = str(pool.get("s", "-"))
        rows.append(f"v{version} | {pool_type} | S:{s_name}")

    h = 220 + len(rows) * 44 + 90
    bg = get_zzz_bg(1100, h, "bg3")
    draw = ImageDraw.Draw(bg)
    _draw_title(draw, "绝区零全版本卡池记录", f"共 {len(rows)} 条")

    for idx, row in enumerate(rows, start=1):
        y = 170 + (idx - 1) * 44
        if idx % 2 == 1:
            draw.rounded_rectangle((48, y - 18, 1050, y + 24), 8, fill=(20, 24, 35, 170))
        draw.text((72, y), f"{idx:02d}. {row}", "white", zzz_font_26, "lm")

    bg = add_footer(bg)
    return await convert_img(bg)


async def draw_rerun_summary_img(rank: str, target_type: str, rows: Sequence[Tuple[str, int]]) -> bytes:
    type_name = "代理人" if target_type == "角色" else "音擎"
    h = 220 + len(rows) * 48 + 90
    bg = get_zzz_bg(1100, h, "bg1")
    draw = ImageDraw.Draw(bg)
    _draw_title(draw, f"{rank}级{type_name}复刻统计", f"统计数量：{len(rows)}")

    for idx, (name, days) in enumerate(rows, start=1):
        y = 170 + (idx - 1) * 48
        if idx % 2 == 0:
            draw.rounded_rectangle((50, y - 20, 1048, y + 24), 8, fill=(31, 34, 46, 170))
        draw.text((80, y), f"{idx:02d}. {name}", "white", zzz_font_30, "lm")
        draw.text((1020, y), f"{days} 天未复刻", YELLOW, zzz_font_26, "rm")

    bg = add_footer(bg)
    return await convert_img(bg)


async def draw_item_history_img(
    query_name: str,
    rarity: str,
    pool_type: str,
    records: Sequence[Dict[str, Any]],
) -> bytes:
    type_name = "代理人" if pool_type == "角色" else "音擎"
    h = 240 + len(records) * 56 + 90
    bg = get_zzz_bg(1100, h, "bg2")
    draw = ImageDraw.Draw(bg)
    _draw_title(draw, f"{query_name} 卡池记录", f"{rarity}级{type_name}  共 {len(records)} 次")

    for idx, pool in enumerate(records, start=1):
        y = 184 + (idx - 1) * 56
        version = str(pool.get("version", "-"))
        timer = str(pool.get("timer", "")).replace(" 00:00:00", "")
        if idx % 2 == 1:
            draw.rounded_rectangle((46, y - 22, 1052, y + 28), 9, fill=(23, 28, 38, 160))
        draw.text((74, y), f"{idx:02d}. v{version}", "white", zzz_font_30, "lm")
        draw.text((320, y), timer, GREY, zzz_font_22, "lm")

    bg = add_footer(bg)
    return await convert_img(bg)
