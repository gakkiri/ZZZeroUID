import json
import re
from pathlib import Path
from typing import Any, Dict

import yaml

def _read_version() -> str:
    version_file = Path(__file__).resolve().parents[1] / "version.py"
    text = version_file.read_text(encoding="utf-8")
    m = re.search(r'ZZZero_version\s*=\s*"([^"]+)"', text)
    if not m:
        raise RuntimeError("无法从 version.py 读取 ZZZero_version")
    return m.group(1)


ZZZero_version = _read_version()


ROOT = Path(__file__).parents[1]
MAP_PATH = ROOT / "utils" / "map"
ALIAS_PATH = ROOT / "utils" / "alias" / "char_alias.json"

PARTNER_FILE = MAP_PATH / f"PartnerId2Data_{ZZZero_version}.json"
WEAPON_FILE = MAP_PATH / f"WeaponId2Data_{ZZZero_version}.json"
EQUIP_FILE = MAP_PATH / f"EquipId2Data_{ZZZero_version}.json"
BANGBOO_FILE = MAP_PATH / f"BangbooId2Data_{ZZZero_version}.json"


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def _convert_weapon_map(src: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for weapon_id, item in src.items():
        base = item.get("BaseProperty", {}) or {}
        rand = item.get("RandProperty", {}) or {}
        result[str(weapon_id)] = {
            "code_name": item.get("CodeName", ""),
            "name": item.get("Name", ""),
            "talents": item.get("Talents", {}),
            "rarity": item.get("Rarity", "A"),
            "props_name": base.get("Name", ""),
            "props_id": str(base.get("Id", "")),
            "props_value": base.get("Value", 0),
            "rand_props_name": rand.get("Name", ""),
            "rand_props_id": str(rand.get("Id", "")),
            "rand_props_value": rand.get("Value", 0),
            "level": item.get("Level", {}),
            "stars": item.get("Stars", {}),
        }
    return result


def _merge_alias(
    alias_data: Dict[str, Any],
    partner_data: Dict[str, Any],
    zzz_plugin_alias: Dict[str, Any],
) -> int:
    changed = 0

    for name, aliases in zzz_plugin_alias.items():
        if name not in alias_data:
            alias_data[name] = []
            changed += 1
        for alias in aliases or []:
            if alias and alias not in alias_data[name]:
                alias_data[name].append(alias)
                changed += 1

    for partner in partner_data.values():
        name = partner.get("name")
        if not name:
            continue
        if name not in alias_data:
            alias_data[name] = []
            changed += 1
        for alias in [partner.get("full_name"), partner.get("en_name")]:
            if alias and alias not in alias_data[name]:
                alias_data[name].append(alias)
                changed += 1

    return changed


def sync(zzz_plugin_root: Path) -> None:
    zzz_map = zzz_plugin_root / "resources" / "map"
    zzz_alias_file = zzz_plugin_root / "defSet" / "alias.yaml"

    if not zzz_map.exists():
        raise FileNotFoundError(f"未找到 map 目录: {zzz_map}")
    if not zzz_alias_file.exists():
        raise FileNotFoundError(f"未找到 alias 文件: {zzz_alias_file}")

    local_partner = _load_json(PARTNER_FILE)
    local_weapon = _load_json(WEAPON_FILE)
    local_equip = _load_json(EQUIP_FILE)
    local_alias = _load_json(ALIAS_PATH)

    source_partner = _load_json(zzz_map / "PartnerId2Data.json")
    source_weapon = _convert_weapon_map(_load_json(zzz_map / "WeaponId2Data.json"))
    source_suit = _load_json(zzz_map / "SuitData.json")
    source_bangboo = _load_json(zzz_map / "BangbooId2Data.json")
    source_alias = yaml.safe_load(zzz_alias_file.read_text(encoding="utf-8")) or {}

    # 角色与音擎使用“覆盖更新”策略，以保证时效
    local_partner.update(source_partner)
    local_weapon.update(source_weapon)

    # 驱动盘保持原有结构，只更新可见名称与效果描述
    for equip_id, suit in source_suit.items():
        if equip_id in local_equip:
            local_equip[equip_id]["equip_name"] = suit.get("name", local_equip[equip_id].get("equip_name", ""))
            local_equip[equip_id]["desc1"] = suit.get("desc1", local_equip[equip_id].get("desc1", ""))
            local_equip[equip_id]["desc2"] = suit.get("desc2", local_equip[equip_id].get("desc2", ""))

    alias_delta = _merge_alias(local_alias, local_partner, source_alias)

    _save_json(PARTNER_FILE, local_partner)
    _save_json(WEAPON_FILE, local_weapon)
    _save_json(EQUIP_FILE, local_equip)
    _save_json(BANGBOO_FILE, source_bangboo)
    _save_json(ALIAS_PATH, local_alias)

    print(f"[同步完成] 角色数量: {len(local_partner)}")
    print(f"[同步完成] 音擎数量: {len(local_weapon)}")
    print(f"[同步完成] 驱动盘数量: {len(local_equip)}")
    print(f"[同步完成] 邦布数量: {len(source_bangboo)}")
    print(f"[同步完成] 别名变更项: {alias_delta}")


if __name__ == "__main__":
    # 默认读取同目录下兄弟仓库
    default_repo = Path(__file__).resolve().parents[3] / "ZZZ-Plugin"
    sync(default_repo)
