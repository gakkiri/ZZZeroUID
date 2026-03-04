import html
import re
from io import BytesIO
from typing import Optional

import httpx
from PIL import Image, ImageDraw

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img

from ..utils.image import GREY, add_footer, get_zzz_bg
from ..utils.fonts.zzz_fonts import zzz_font_26, zzz_font_44

sv_zzz_calendar = SV("绝区零活动日历")

ANN_LIST_URL = (
    "https://announcement-api.mihoyo.com/common/nap_cn/announcement/api/getAnnList"
    "?game=nap&game_biz=nap_cn&lang=zh-cn&bundle_id=nap_cn&channel_id=1"
    "&level=70&platform=pc&region=prod_gf_cn&uid=12345678"
)
ANN_CONTENT_URL = (
    "https://announcement-static.mihoyo.com/common/nap_cn/announcement/api/getAnnContent"
    "?game=nap&game_biz=nap_cn&lang=zh-cn&bundle_id=nap_cn&platform=pc"
    "&region=prod_gf_cn&level=70&channel_id=1&t={}"
)


async def _fetch_calendar_img_url() -> Optional[str]:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        ann_list_resp = await client.get(ANN_LIST_URL)
        ann_list_resp.raise_for_status()
        ann_list = ann_list_resp.json()
        ann_data = ann_list.get("data", {})
        if not ann_data:
            return None
        t = ann_data.get("t")
        if not t:
            return None

        content_resp = await client.get(ANN_CONTENT_URL.format(t))
        content_resp.raise_for_status()
        content_data = content_resp.json().get("data", {})
        content_list = content_data.get("list", [])
        if not isinstance(content_list, list):
            return None

        target = None
        for item in content_list:
            title = str(item.get("title", ""))
            subtitle = str(item.get("subtitle", ""))
            if "日历" in title and "活动日历" in subtitle:
                target = item
                break
            if "活动日历" in title:
                target = item
                break

        if not target:
            return None

        content = html.unescape(str(target.get("content", "")))
        match = re.search(r'<img[^>]*src="([^"]+)"', content, flags=re.I)
        if not match:
            return None
        return match.group(1)


async def _draw_calendar_img(img_url: str) -> bytes:
    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        resp = await client.get(img_url)
        resp.raise_for_status()
    calendar_raw = Image.open(BytesIO(resp.content)).convert("RGBA")

    target_w = 1020
    ratio = target_w / max(1, calendar_raw.size[0])
    target_h = int(calendar_raw.size[1] * ratio)
    calendar_img = calendar_raw.resize((target_w, target_h)).convert("RGBA")

    bg = get_zzz_bg(1100, target_h + 230, "bg3")
    draw = ImageDraw.Draw(bg)
    draw.text((60, 60), "绝区零活动日历", "white", zzz_font_44, "lm")
    draw.text((60, 114), "数据来源：米游社公告", GREY, zzz_font_26, "lm")

    bg.paste(calendar_img, (40, 170), calendar_img)
    bg = add_footer(bg)
    return await convert_img(bg)


@sv_zzz_calendar.on_fullmatch(("日历", "cal"), block=True)
async def send_calendar(bot: Bot, ev: Event):
    try:
        img_url = await _fetch_calendar_img_url()
        if not img_url:
            return await bot.send("未找到活动日历")
        img = await _draw_calendar_img(img_url)
        await bot.send(img)
    except Exception:
        await bot.send("获取活动日历失败，请稍后重试")
