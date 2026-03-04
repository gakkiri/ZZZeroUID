import html
import re
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence

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


def _strip_html(raw: str) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(raw)).strip()


def _extract_img_url(content: str) -> Optional[str]:
    if not content:
        return None
    content = html.unescape(content)
    for pattern in (
        r"""<img[^>]*(?:src|data-src)=["']([^"']+)["']""",
        r"""url\((?:["'])?([^"')]+)(?:["'])?\)""",
    ):
        match = re.search(pattern, content, flags=re.I)
        if match:
            return match.group(1)
    return None


def _flatten_entries(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sub = item.get("list")
        if isinstance(sub, list):
            entries.extend(_flatten_entries(sub))
        else:
            entries.append(item)
    return entries


def _normalize_entries(content_data: Dict[str, Any]) -> List[Dict[str, str]]:
    raw_list = content_data.get("list", [])
    raw_pic_list = content_data.get("pic_list", [])
    entries = _flatten_entries(raw_list if isinstance(raw_list, list) else [])
    entries.extend(_flatten_entries(raw_pic_list if isinstance(raw_pic_list, list) else []))

    normalized: List[Dict[str, str]] = []
    for item in entries:
        title = _strip_html(str(item.get("title", "")))
        subtitle = _strip_html(str(item.get("subtitle", "")))
        content = str(item.get("content", ""))
        banner = str(item.get("banner", "")).strip()
        normalized.append(
            {
                "title": title,
                "subtitle": subtitle,
                "content": content,
                "banner": banner,
                "text": f"{title} {subtitle}".strip(),
            }
        )
    return normalized


def _pick_img_from_entries(entries: Sequence[Dict[str, str]], keywords: Sequence[str]) -> Optional[str]:
    for item in entries:
        text = item.get("text", "")
        if not all(k in text for k in keywords):
            continue
        content_img = _extract_img_url(item.get("content", ""))
        if content_img:
            return content_img
        banner = item.get("banner", "").strip()
        if banner:
            return banner
    return None


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
        if not isinstance(content_data, dict):
            return None

        entries = _normalize_entries(content_data)
        if not entries:
            return None

        # 1) 优先活动日历
        for keywords in (("活动日历",), ("日历",)):
            url = _pick_img_from_entries(entries, keywords)
            if url:
                return url

        # 2) 兜底：当期活动公告图
        for keywords in (("活动",), ("版本",), ("限时",)):
            url = _pick_img_from_entries(entries, keywords)
            if url:
                return url

        # 3) 最后兜底：任意含图公告
        for item in entries:
            content_img = _extract_img_url(item.get("content", ""))
            if content_img:
                return content_img
            banner = item.get("banner", "").strip()
            if banner:
                return banner
        return None


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
