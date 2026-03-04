from typing import Any, Dict, List

from PIL import ImageDraw

from gsuid_core.utils.image.convert import convert_img

from ..utils.image import GREY, YELLOW, add_footer, get_zzz_bg
from ..utils.fonts.zzz_fonts import zzz_font_22, zzz_font_26, zzz_font_30, zzz_font_44
from ..utils.rank_store import format_ts


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


async def draw_rank_img(rank_type: str, title: str, records: List[Dict[str, Any]]) -> bytes:
    h = 240 + len(records) * 54 + 90
    img = get_zzz_bg(1100, h, "bg1")
    draw = ImageDraw.Draw(img)

    draw.text((56, 60), f"{title} 群排名", "white", zzz_font_44, "lm")
    draw.text((56, 112), f"统计人数：{len(records)}", GREY, zzz_font_26, "lm")

    head_y = 156
    draw.rounded_rectangle((44, head_y, 1054, head_y + 48), 10, fill=(35, 44, 64, 210))
    draw.text((72, head_y + 24), "#", "white", zzz_font_26, "lm")
    draw.text((128, head_y + 24), "昵称", "white", zzz_font_26, "lm")
    if rank_type == "ABYSS":
        draw.text((620, head_y + 24), "分数", "white", zzz_font_26, "lm")
        draw.text((730, head_y + 24), "评级", "white", zzz_font_26, "lm")
    elif rank_type == "DEADLY":
        draw.text((620, head_y + 24), "星数", "white", zzz_font_26, "lm")
        draw.text((730, head_y + 24), "分数", "white", zzz_font_26, "lm")
    else:
        draw.text((650, head_y + 24), "分数", "white", zzz_font_26, "lm")
    draw.text((840, head_y + 24), "更新时间", "white", zzz_font_26, "lm")

    for idx, record in enumerate(records, start=1):
        y = head_y + 56 + (idx - 1) * 54
        if idx == 1:
            fill = (89, 64, 18, 220)
            color = YELLOW
        elif idx % 2 == 0:
            fill = (22, 26, 38, 170)
            color = "white"
        else:
            fill = (28, 34, 48, 130)
            color = "white"
        draw.rounded_rectangle((44, y, 1054, y + 46), 8, fill=fill)

        name = str(record.get("name") or record.get("uid") or "-").replace("\n", " ").strip()
        uid = str(record.get("uid") or "-")
        name_show = f"{name} (UID{uid})"
        if len(name_show) > 26:
            name_show = name_show[:25] + "..."

        draw.text((72, y + 23), str(idx), color, zzz_font_26, "lm")
        draw.text((128, y + 23), name_show, color, zzz_font_22, "lm")

        if rank_type == "ABYSS":
            draw.text((620, y + 23), f"{_safe_int(record.get('score'))}", color, zzz_font_30, "lm")
            draw.text((730, y + 23), str(record.get("rating", "-")).upper(), color, zzz_font_30, "lm")
        elif rank_type == "DEADLY":
            draw.text((620, y + 23), f"{_safe_int(record.get('total_star'))}", color, zzz_font_30, "lm")
            draw.text((730, y + 23), f"{_safe_int(record.get('total_score'))}", color, zzz_font_30, "lm")
        else:
            draw.text((650, y + 23), f"{_safe_int(record.get('total_score'))}", color, zzz_font_30, "lm")

        draw.text((840, y + 23), format_ts(_safe_int(record.get("update_ts"))), color, zzz_font_22, "lm")

    img = add_footer(img)
    return await convert_img(img)
