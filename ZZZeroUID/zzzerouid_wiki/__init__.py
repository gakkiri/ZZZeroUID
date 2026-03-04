import re
from typing import List

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img

from ..utils.name_convert import (
    alias_to_char_name,
    CHAR_WEAPON_TYPE,
    CHAR_ELEMENT_TYPE,
    BANGBOO_RARITY,
    find_char_data,
    find_equip_data,
    find_weapon_data,
    find_bangboo_data,
    list_char_names,
    list_equip_names,
    list_weapon_names,
    list_bangboo_names,
)
from ..utils.resource.RESOURCE_PATH import CAT_GUIDE_PATH, FLOWER_GUIDE_PATH
from ..utils.resource.download_file import get_square_bangboo
from ..zzzerouid_config.zzzero_config import ZZZ_CONFIG

sv_zzz_wiki = SV("绝区零WIKI")
sv_zzz_guide = SV("绝区零攻略")


def _strip_color_tag(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("\\n", "\n").strip()


def _format_usage(title: str, names: List[str], sample_prefix: str) -> str:
    preview = "、".join(names[:8]) if names else "暂无"
    return f"[绝区零] {title}\n示例: {sample_prefix}\n可用条目(部分): {preview}"


@sv_zzz_wiki.on_prefix("角色图鉴")
async def send_role_wiki_pic(bot: Bot, ev: Event):
    name = ev.text.strip()
    if not name:
        return await bot.send(_format_usage("角色图鉴", list_char_names(), "角色图鉴露西"))

    data = find_char_data(name)
    if not data:
        return await bot.send(f"[绝区零] 未找到角色[{name}]，请检查输入。")

    _, role = data
    role_name = role.get("name", name)
    full_name = role.get("full_name", role_name)
    rarity = role.get("Rarity", "?")
    element = CHAR_ELEMENT_TYPE.get(str(role.get("ElementType", "")), str(role.get("ElementType", "未知")))
    weapon_type = CHAR_WEAPON_TYPE.get(str(role.get("WeaponType", "")), str(role.get("WeaponType", "未知")))
    camp = str(role.get("Camp", "未知"))
    hit_type = str(role.get("HitType", "未知"))
    level = role.get("Level", {}).get("6", {})

    msg = [
        f"【角色图鉴】{role_name}",
        f"全名：{full_name}",
        f"稀有度：{rarity}",
        f"属性：{element}",
        f"定位：{weapon_type}",
        f"特性：{hit_type}",
        f"阵营：{camp}",
    ]
    if level:
        msg.append(
            f"60级基础：生命{level.get('HpMax', '?')} / 攻击{level.get('Attack', '?')} / 防御{level.get('Defence', '?')}"
        )

    await bot.send("\n".join(msg))


@sv_zzz_guide.on_prefix("角色攻略")
@sv_zzz_guide.on_suffix("攻略")
async def send_role_guide_pic(bot: Bot, ev: Event):
    name = alias_to_char_name(ev.text.strip())
    logger.info(f"[绝区零] 角色攻略: {name}")
    gp = ZZZ_CONFIG.get_config("ZZZGuideProvide").data
    logger.info(f"[绝区零] 攻略提供方: {gp}")
    if gp == "猫冬":
        path = CAT_GUIDE_PATH / f"{name}.jpg"
    else:
        path1 = FLOWER_GUIDE_PATH / f"{name}.jpg"
        path2 = FLOWER_GUIDE_PATH / f"{name}.png"
        path = path1 if path1.exists() else path2

    if path.exists():
        img = await convert_img(path)
        await bot.send(img)
    else:
        await bot.send("[绝区零] 该角色攻略不存在, 请检查输入角色是否正确！")


@sv_zzz_guide.on_prefix("音擎攻略")
async def send_weapon_guide_pic(bot: Bot, ev: Event):
    name = ev.text.strip()
    if not name:
        return await bot.send(_format_usage("音擎攻略", list_weapon_names(), "音擎攻略硫磺石"))

    data = find_weapon_data(name)
    if not data:
        return await bot.send(f"[绝区零] 未找到音擎[{name}]，请检查输入。")

    _, weapon = data
    weapon_name = str(weapon.get("name", name))
    rarity = str(weapon.get("rarity", "?"))
    main_prop = f"{weapon.get('props_name', '主属性')} +{weapon.get('props_value', '?')}"
    sub_prop = f"{weapon.get('rand_props_name', '副属性')} +{weapon.get('rand_props_value', '?')}"
    talents = weapon.get("talents", {})
    talent1 = talents.get("1") or next(iter(talents.values()), None)
    talent5 = talents.get("5")

    msg = [
        f"【音擎攻略】{weapon_name}",
        f"稀有度：{rarity}",
        f"主属性：{main_prop}",
        f"副属性：{sub_prop}",
    ]

    if talent1:
        msg.append(f"效果（精炼1）：{talent1.get('Name', '未知')}")
        msg.append(_strip_color_tag(str(talent1.get("Desc", "无"))))
    if talent5:
        msg.append(f"效果（精炼5）：{talent5.get('Name', '未知')}")
        msg.append(_strip_color_tag(str(talent5.get("Desc", "无"))))

    await bot.send("\n".join(msg))


@sv_zzz_wiki.on_prefix("驱动盘")
async def send_relic_wiki_pic(bot: Bot, ev: Event):
    name = ev.text.strip()
    if not name:
        return await bot.send(_format_usage("驱动盘图鉴", list_equip_names(), "驱动盘啄木鸟电音"))

    data = find_equip_data(name)
    if not data:
        return await bot.send(f"[绝区零] 未找到驱动盘[{name}]，请检查输入。")

    _, equip = data
    equip_name = str(equip.get("equip_name", name))
    msg = [
        f"【驱动盘图鉴】{equip_name}",
        f"二件套：{_strip_color_tag(str(equip.get('desc1', '未知')))}",
        f"四件套：{_strip_color_tag(str(equip.get('desc2', '未知')))}",
    ]
    await bot.send("\n".join(msg))


@sv_zzz_wiki.on_prefix("突破材料")
async def send_material_for_role_wiki_pic(bot: Bot, ev: Event):
    name = ev.text.strip()
    if not name:
        return await bot.send(_format_usage("突破材料查询", list_char_names(), "突破材料露西"))

    data = find_char_data(name)
    if not data:
        return await bot.send(f"[绝区零] 未找到角色[{name}]，请检查输入。")

    _, role = data
    levels = role.get("Level", {})
    role_name = str(role.get("name", name))

    lines = [f"【突破材料】{role_name}"]
    for key in ["1", "2", "3", "4", "5"]:
        lv = levels.get(key)
        if not lv:
            continue

        level_range = f"{lv.get('LevelMin', 0)}-{lv.get('LevelMax', 0)}级"
        materials = lv.get("Materials", {})
        if not materials:
            continue
        mats = "，".join(f"{mid} x{count}" for mid, count in materials.items())
        lines.append(f"{level_range}: {mats}")

    if len(lines) == 1:
        lines.append("未找到可用突破材料数据。")
    else:
        lines.append("注：当前为材料ID与数量，后续会补材料名称映射。")

    await bot.send("\n".join(lines))


@sv_zzz_wiki.on_prefix("武器")
async def send_light_cone_wiki_pic(bot: Bot, ev: Event):
    # 保持与“音擎攻略”一致的用户体验，支持直接查询音擎数据
    await send_weapon_guide_pic(bot, ev)


@sv_zzz_wiki.on_prefix("邦布")
async def send_bang_boo_wiki_pic(bot: Bot, ev: Event):
    name = ev.text.strip()
    if not name:
        return await bot.send(_format_usage("邦布图鉴", list_bangboo_names(), "邦布招财布"))

    data = find_bangboo_data(name)
    if not data:
        return await bot.send(f"[绝区零] 未找到邦布[{name}]，请检查输入。")

    bangboo_id, bangboo = data
    chs_name = str(bangboo.get("CHS", name))
    rarity = BANGBOO_RARITY.get(int(bangboo.get("rank", 0)), str(bangboo.get("rank", "?")))
    desc = _strip_color_tag(str(bangboo.get("desc", "暂无描述")))
    msg = [
        f"【邦布图鉴】{chs_name}",
        f"编号：{bangboo_id}",
        f"稀有度：{rarity}",
        f"代号：{bangboo.get('codename', '未知')}",
        f"描述：{desc}",
    ]
    await bot.send("\n".join(msg))

    try:
        img = await get_square_bangboo(bangboo_id)
        await bot.send(await convert_img(img))
    except Exception as e:
        logger.warning(f"[绝区零] 邦布图鉴图片发送失败: {e}")
