from typing import Any, Dict, List, Union, Optional, Tuple
from pathlib import Path

from msgspec import json as msgjson

from ..tools.data_to_map import (
    EquipId2DataFile,
    WeaponId2DataFile,
    PartnerId2DataFile,
    BangbooId2DataFile,
)

MAP_PATH = Path(__file__).parent / "map"
ALIAS_LIST = Path(__file__).parent / "alias"
CHAR_ALIAS = ALIAS_LIST / "char_alias.json"


with open(CHAR_ALIAS, "r", encoding="UTF-8") as f:
    char_alias_data = msgjson.decode(f.read(), type=Dict[str, List[str]])

with open(MAP_PATH / PartnerId2DataFile, "r", encoding="UTF-8") as f:
    partener_data = msgjson.decode(f.read(), type=Dict[str, Dict[str, Any]])

with open(MAP_PATH / WeaponId2DataFile, "r", encoding="UTF-8") as f:
    weapon_data = msgjson.decode(f.read(), type=Dict[str, Any])

with open(MAP_PATH / EquipId2DataFile, "r", encoding="UTF-8") as f:
    equip_data = msgjson.decode(f.read(), type=Dict[str, Dict])

bangboo_data: Dict[str, Dict[str, Any]] = {}
_bangboo_map = MAP_PATH / BangbooId2DataFile
if _bangboo_map.exists():
    with open(_bangboo_map, "r", encoding="UTF-8") as f:
        bangboo_data = msgjson.decode(f.read(), type=Dict[str, Dict[str, Any]])

CHAR_WEAPON_TYPE = {
    "1": "强攻",
    "2": "击破",
    "3": "异常",
    "4": "支援",
    "5": "防护",
    "6": "命破",
}
CHAR_ELEMENT_TYPE = {
    "200": "物理",
    "201": "火",
    "202": "冰",
    "203": "电",
    "205": "以太",
}
BANGBOO_RARITY = {
    4: "S",
    3: "A",
    2: "B",
    1: "C",
}


def _normalize_text(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fa5")


def _is_match(query: str, *candidates: str) -> bool:
    query_norm = _normalize_text(query)
    if not query_norm:
        return False

    normalized = [_normalize_text(i) for i in candidates if i]
    return any(query_norm == i for i in normalized) or any(query_norm in i for i in normalized)


def char_id_to_sprite(char_id: str) -> str:
    char_id = str(char_id)
    if char_id in partener_data:
        return partener_data[char_id]["sprite_id"]
    else:
        return "28"


def char_id_to_full_name(char_id: str) -> str:
    char_id = str(char_id)
    if char_id in partener_data:
        return partener_data[char_id]["full_name"]
    else:
        return "绳匠"


def equip_id_to_sprite(equip_id: Union[str, int]) -> Optional[str]:
    equip_id = str(equip_id)
    if len(equip_id) == 5:
        suit_id = equip_id[:3] + "00"
        if suit_id in equip_data:
            return equip_data[suit_id]["sprite_file"]


def alias_to_char_name(char_name: str) -> str:
    for i in char_alias_data:
        if (char_name in i) or (char_name in char_alias_data[i]):
            return i
    return char_name


def char_id_to_char_name(char_id: str) -> Optional[str]:
    if char_id in partener_data:
        return partener_data[char_id]["name"]
    else:
        return None


def char_name_to_char_id(char_name: str) -> Optional[str]:
    char_name = alias_to_char_name(char_name)
    for i in partener_data:
        chars = partener_data[i]
        if char_name == chars["name"]:
            return i
    else:
        return None


def find_char_data(char_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    char_name = alias_to_char_name(char_name)
    for _id, chars in partener_data.items():
        if _is_match(char_name, chars.get("name", ""), chars.get("full_name", ""), chars.get("en_name", "")):
            return _id, chars
    return None


def find_weapon_data(weapon_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    for _id, weapon in weapon_data.items():
        if _is_match(weapon_name, weapon.get("name", ""), weapon.get("code_name", "")):
            return _id, weapon
    return None


def find_equip_data(equip_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    for _id, equip in equip_data.items():
        if _is_match(equip_name, equip.get("equip_name", ""), equip.get("sprite_file", "")):
            return _id, equip
    return None


def find_bangboo_data(bangboo_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    for _id, bangboo in bangboo_data.items():
        if _is_match(
            bangboo_name,
            str(bangboo.get("CHS", "")),
            str(bangboo.get("EN", "")),
            str(bangboo.get("codename", "")),
        ):
            return _id, bangboo
    return None


def list_char_names(limit: int = 12) -> List[str]:
    names = sorted({str(v.get("name", "")).strip() for v in partener_data.values() if v.get("name")})
    return names[:limit]


def list_weapon_names(limit: int = 12) -> List[str]:
    names = sorted({str(v.get("name", "")).strip() for v in weapon_data.values() if v.get("name")})
    return names[:limit]


def list_equip_names(limit: int = 12) -> List[str]:
    names = sorted({str(v.get("equip_name", "")).strip() for v in equip_data.values() if v.get("equip_name")})
    return names[:limit]


def list_bangboo_names(limit: int = 12) -> List[str]:
    names = sorted({str(v.get("CHS", "")).strip() for v in bangboo_data.values() if v.get("CHS")})
    return names[:limit]
