import json
import re
from typing import Dict, Optional, Tuple

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.database.models import GsBind

from ..utils.hint import BIND_UID_HINT
from ..utils.device_store import clear_user_device, set_default_device, set_user_device

sv_zzz_device = SV("绝区零设备绑定")
sv_zzz_device_admin = SV("绝区零默认设备设置", pm=1)


def _is_os_uid(uid: str) -> bool:
    return bool(re.match(r"^(1[0-9])[0-9]{8}$", uid))


def _parse_device_payload(payload: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    text = payload.strip()
    if not text:
        return None, "请在命令后粘贴设备信息 JSON"

    try:
        info = json.loads(text)
    except Exception:
        return None, "设备信息格式错误，请检查 JSON 格式"

    if not isinstance(info, dict):
        return None, "设备信息格式错误，请检查 JSON 格式"

    device_id = str(
        info.get("device_id") or info.get("x-rpc-device_id") or ""
    ).strip()
    device_fp = str(
        info.get("device_fp") or info.get("x-rpc-device_fp") or ""
    ).strip()

    if not device_id or not device_fp:
        return None, "设备信息缺少 device_id 或 device_fp"

    return {"device_id": device_id, "device_fp": device_fp}, None


async def _get_uid(ev: Event) -> Optional[str]:
    return await GsBind.get_uid_by_game(ev.user_id, ev.bot_id, "zzz")


@sv_zzz_device.on_fullmatch("绑定设备帮助", block=True)
async def bind_device_help(bot: Bot, ev: Event):
    msg = [
        "[绑定设备]",
        "方法一（通用，抓包）：",
        "1. 使用抓包工具抓取米游社 APP 的请求",
        "2. 在请求头里找到 x-rpc-device_id 与 x-rpc-device_fp",
        "3. 按下述格式构造 JSON：",
        "   {\"device_id\":\"x-rpc-device_id的值\",\"device_fp\":\"x-rpc-device_fp的值\"}",
        "4. 发送：绑定设备 {\"device_id\":\"...\",\"device_fp\":\"...\"}",
        "5. 提示“绑定设备成功”即完成",
        "",
        "方法二（仅安卓）：",
        "1. 安装设备信息提取 APK：",
        "   https://ghproxy.mihomo.me/https://raw.githubusercontent.com/forchannot/get_device_info/main/app/build/outputs/apk/debug/app-debug.apk",
        "2. 打开后复制设备信息 JSON",
        "3. 发送：绑定设备 {粘贴完整JSON}",
        "",
        "注意：",
        "1. 推荐私聊发送，避免泄露设备信息",
        "2. 绑定成功后会优先使用该设备参数请求米游社接口",
        "3. 如需解绑，发送：解绑设备",
        "",
        "[示例]",
        "绑定设备 {\"device_id\":\"xxxx\",\"device_fp\":\"yyyy\"}",
    ]
    await bot.send("\n".join(msg))


@sv_zzz_device.on_command(("绑定设备",), block=True)
async def bind_device(bot: Bot, ev: Event):
    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)
    if _is_os_uid(uid):
        return await bot.send("国际服不需要绑定设备")

    if not ev.text.strip():
        return await bot.send(
            "为当前 UID 绑定设备，请在命令后粘贴 JSON 设备信息。\n"
            "示例：绑定设备 {\"device_id\":\"...\",\"device_fp\":\"...\"}\n"
            "可发送“绑定设备帮助”查看说明。"
        )

    payload, error = _parse_device_payload(ev.text)
    if not payload:
        return await bot.send(error or "设备信息格式错误")

    set_user_device(uid, payload["device_id"], payload["device_fp"])
    msg = "绑定设备成功"
    if getattr(ev, "group_id", None):
        msg += "\n请尽快撤回包含设备信息的消息"
    await bot.send(msg)


@sv_zzz_device.on_fullmatch("解绑设备", block=True)
async def unbind_device(bot: Bot, ev: Event):
    uid = await _get_uid(ev)
    if not uid:
        return await bot.send(BIND_UID_HINT)
    if _is_os_uid(uid):
        return await bot.send("国际服不需要绑定设备")

    if clear_user_device(uid):
        return await bot.send("解绑设备成功")
    await bot.send("当前 UID 未绑定设备")


@sv_zzz_device_admin.on_command(("设置默认设备",), block=True)
async def set_default_device_cmd(bot: Bot, ev: Event):
    if not ev.text.strip():
        return await bot.send(
            "请在命令后粘贴默认设备 JSON。\n"
            "示例：设置默认设备 {\"device_id\":\"...\",\"device_fp\":\"...\"}"
        )

    payload, error = _parse_device_payload(ev.text)
    if not payload:
        return await bot.send(error or "设备信息格式错误")

    set_default_device(payload["device_id"], payload["device_fp"])
    await bot.send("默认设备设置成功")
