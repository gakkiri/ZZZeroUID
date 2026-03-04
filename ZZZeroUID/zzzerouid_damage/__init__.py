import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.uid import get_uid
from ..utils.hint import BIND_UID_HINT
from .draw_damage import draw_damage_img

sv_zzz_damage = SV("zzz伤害面板")

DAMAGE_SUFFIXES = tuple(["伤害"] + [f"伤害{i}" for i in range(1, 31)])


@sv_zzz_damage.on_suffix(DAMAGE_SUFFIXES, block=True)
async def send_damage_panel(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)

    char_name = ev.text.strip()
    if not char_name:
        return

    match = re.match(r"伤害(\d+)?$", ev.command.strip())
    if not match:
        return
    skill_index = int(match.group(1)) if match.group(1) else None

    logger.info(f"[绝区零] [伤害面板] CHAR: {char_name}, UID: {uid}, INDEX: {skill_index}")
    im = await draw_damage_img(uid, char_name, skill_index)
    await bot.send(im)
