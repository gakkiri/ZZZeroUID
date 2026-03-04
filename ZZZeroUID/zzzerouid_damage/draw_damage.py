import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import aiofiles
from PIL import Image, ImageDraw

from gsuid_core.utils.image.convert import convert_img

from ..utils.image import GREY, YELLOW, add_footer, get_zzz_bg, get_mind_role_img
from ..utils.name_convert import char_name_to_char_id
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.fonts.zzz_fonts import zzz_font_22, zzz_font_26, zzz_font_30, zzz_font_44
from ..zzzerouid_char_detail.dmg_cal import get_dmg


def _get_damage_rows(dmg_dict: Dict[str, List[str]]) -> List[Tuple[str, List[str]]]:
    rows: List[Tuple[str, List[str]]] = []
    for name, values in dmg_dict.items():
        if name == "动作名称":
            continue
        if not isinstance(values, list) or len(values) < 3:
            continue
        rows.append((name, values))
    return rows


async def draw_damage_img(
    uid: str,
    char_name: str,
    skill_index: Optional[int] = None,
) -> Union[str, bytes]:
    char_id = char_name_to_char_id(char_name)
    if not char_id:
        return f"[绝区零] 角色名{char_name}无法找到，请检查输入是否正确"

    path = PLAYER_PATH / str(uid) / f"{char_id}.json"
    if not path.exists():
        return "[绝区零] 未找到该角色面板数据，请先使用 刷新面板"

    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        data = json.loads(await f.read())

    dmg_dict = get_dmg(data)
    rows = _get_damage_rows(dmg_dict)
    if not rows:
        return f"[绝区零] 暂无角色 {char_name} 的伤害计算数据"

    if skill_index is None:
        select = 1
    else:
        select = max(1, min(skill_index, len(rows)))
    selected_name, selected_values = rows[select - 1]

    h = 430 + len(rows) * 54 + 90
    img = get_zzz_bg(1100, h, "bg4")
    draw = ImageDraw.Draw(img)

    draw.text((52, 58), f"{data.get('name_mi18n', char_name)} 伤害面板", "white", zzz_font_44, "lm")
    draw.text((52, 112), f"UID {uid}  |  当前技能序号 {select}/{len(rows)}", GREY, zzz_font_26, "lm")
    draw.text((52, 156), f"目标动作：{selected_name}", YELLOW, zzz_font_30, "lm")
    draw.text((52, 196), "可发送 角色名伤害+序号 切换目标动作", GREY, zzz_font_22, "lm")

    role_img = get_mind_role_img(char_id).resize((320, 190)).convert("RGBA")
    img.paste(role_img, (760, 28), role_img)

    summary = Image.new("RGBA", (1020, 90), (17, 22, 33, 220))
    sdraw = ImageDraw.Draw(summary)
    sdraw.rounded_rectangle((0, 0, 1019, 89), 14, outline=(255, 255, 255, 40), width=2)
    sdraw.text((38, 45), "暴击伤害", "white", zzz_font_26, "lm")
    sdraw.text((295, 45), selected_values[0], YELLOW, zzz_font_30, "lm")
    sdraw.text((500, 45), "期望伤害", "white", zzz_font_26, "lm")
    sdraw.text((752, 45), selected_values[1], YELLOW, zzz_font_30, "lm")
    sdraw.text((860, 45), selected_values[2], "white", zzz_font_26, "lm")
    img.paste(summary, (40, 240), summary)

    header_y = 355
    draw.rounded_rectangle((40, header_y, 1060, header_y + 44), 9, fill=(44, 53, 76, 210))
    draw.text((66, header_y + 22), "#", "white", zzz_font_26, "lm")
    draw.text((126, header_y + 22), "动作名称", "white", zzz_font_26, "lm")
    draw.text((670, header_y + 22), "暴击", "white", zzz_font_26, "lm")
    draw.text((815, header_y + 22), "期望", "white", zzz_font_26, "lm")
    draw.text((960, header_y + 22), "普通", "white", zzz_font_26, "lm")

    for idx, (name, values) in enumerate(rows, start=1):
        y = header_y + 52 + (idx - 1) * 54
        is_selected = idx == select
        if is_selected:
            fill = (86, 52, 18, 220)
        elif idx % 2 == 0:
            fill = (20, 24, 36, 165)
        else:
            fill = (28, 34, 48, 120)
        draw.rounded_rectangle((40, y, 1060, y + 46), 8, fill=fill)

        name_show = name[:26] + "..." if len(name) > 29 else name
        color = YELLOW if is_selected else "white"

        draw.text((66, y + 23), str(idx), color, zzz_font_26, "lm")
        draw.text((126, y + 23), name_show, color, zzz_font_22, "lm")
        draw.text((670, y + 23), str(values[0]), color, zzz_font_22, "lm")
        draw.text((815, y + 23), str(values[1]), color, zzz_font_22, "lm")
        draw.text((960, y + 23), str(values[2]), color, zzz_font_22, "lm")

    img = add_footer(img)
    return await convert_img(img)
