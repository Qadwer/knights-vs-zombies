"""
Менеджер сохранений и прогресса: управляет постоянной статистикой карьеры,
мета-прогрессией улучшений лагеря, настройками звука/экрана и чекпоинтами забега.
"""

import json
import os
from typing import Dict, Any, Optional, List


HERO_CLASSES = ["warrior", "ranger", "mage", "summoner"]

HERO_META = {
    "warrior": {
        "id": "warrior",
        "name": "Рыцарь",
        "role": "Воин Света (Ближний бой)",
        "color": (230, 57, 70),
        "mastery_title": "Отбивание пуль",
        "mastery_desc": "Взмахи меча (ЛКМ и ПКМ) разрушают ядовитые снаряды врагов при контакте.",
        "mastery_short": "Отбивание пуль мечом",
    },
    "ranger": {
        "id": "ranger",
        "name": "Лучник",
        "role": "Следопыт Леса (Дальний бой)",
        "color": (82, 183, 136),
        "mastery_title": "Сверхзвуковые стрелы",
        "mastery_desc": "Скорость полета всех типов стрел увеличена на +50%.",
        "mastery_short": "Скорость стрел +50%",
    },
    "mage": {
        "id": "mage",
        "name": "Маг",
        "role": "Архимаг Тайной Магии (AoE заклинания)",
        "color": (160, 110, 240),
        "mastery_title": "Сферы Эгиды",
        "mastery_desc": "3 вращающихся защитных шара поглощают одну атаку и перезаряжаются 15 секунд.",
        "mastery_short": "3 защитные сферы (кд 15 сек)",
    },
    "summoner": {
        "id": "summoner",
        "name": "Призыватель",
        "role": "Повелитель Душ (Армия нежити)",
        "color": (72, 202, 228),
        "mastery_title": "Призыв Исполина",
        "mastery_desc": "Каждый 10-й призванный скелет становится гигантом с увеличенным HP и уроном.",
        "mastery_short": "Каждый 10-й миньон — гигант",
    },
}

from .config import get_save_path, EconomyBalance

CLASS_UPGRADES_META = EconomyBalance.CAMP_UPGRADES

PERMANENT_UPGRADES_META = {
    # Legacy keys for backward compatibility
    "hp_boost": {
        "title": "Закалка ветерана",
        "desc": "+25 к максимальному здоровью рыцаря",
        "max_level": 5,
        "base_cost": 25,
        "cost_multiplier": 1.6,
        "icon": "hp_boost",
    },
    "damage_boost": {
        "title": "Острый клинок",
        "desc": "+8% к урону всех атак рыцаря",
        "max_level": 5,
        "base_cost": 30,
        "cost_multiplier": 1.7,
        "icon": "damage_boost",
    },
    "speed_boost": {
        "title": "Легкие доспехи",
        "desc": "+6% к скорости перемещения",
        "max_level": 5,
        "base_cost": 20,
        "cost_multiplier": 1.5,
        "icon": "speed_boost",
    },
    "magnet_boost": {
        "title": "Магнитное кольцо",
        "desc": "+25 к радиусу сбора сфер опыта",
        "max_level": 5,
        "base_cost": 15,
        "cost_multiplier": 1.5,
        "icon": "magnet_boost",
    },
}

for cid, hmeta in HERO_META.items():
    for stat, umeta in CLASS_UPGRADES_META.items():
        key = f"{cid}_{stat}"
        PERMANENT_UPGRADES_META[key] = {
            "hero_id": cid,
            "stat": stat,
            "title": f"{umeta['title']} ({hmeta['name']})",
            "desc": umeta["desc_template"].format(val=umeta["val_per_lvl"]),
            "max_level": umeta["max_level"],
            "base_cost": umeta["base_cost"],
            "cost_multiplier": umeta["cost_multiplier"],
            "icon": umeta["icon"],
        }



class SaveManager:
    def __init__(self, filepath: Optional[str] = None):
        if filepath is None:
            self.filepath = get_save_path("save_data.json")
        else:
            self.filepath = filepath

        self.data: Dict[str, Any] = self._get_default_data()
        self.load()

    def _get_default_data(self) -> Dict[str, Any]:
        default_upgrades: Dict[str, int] = {
            "hp_boost": 0,
            "damage_boost": 0,
            "speed_boost": 0,
            "magnet_boost": 0,
        }
        for cid in HERO_CLASSES:
            for stat in CLASS_UPGRADES_META:
                default_upgrades[f"{cid}_{stat}"] = 0

        return {
            "career": {
                "high_score": 0,
                "max_wave": 0,
                "total_kills": 0,
                "total_games": 0,
                "souls": 0,
            },
            "permanent_upgrades": default_upgrades,
            "settings": {
                "sfx_muted": False,
                "sfx_volume": 1.0,
                "screen_shake": True,
                "fullscreen": False,
            },
            "active_run": None,
        }

    def load(self) -> None:
        if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge with default structure to prevent missing keys
                    for section, content in self._get_default_data().items():
                        if section not in loaded:
                            loaded[section] = content
                        elif isinstance(content, dict):
                            for key, val in content.items():
                                if key not in loaded[section]:
                                    loaded[section][key] = val
                    self.data = loaded
            except Exception as e:
                print(f"[SaveManager] Failed to load save file: {e}. Using defaults.")
                self.data = self._get_default_data()
        else:
            self.data = self._get_default_data()
            self.save()

    def save(self) -> None:
        try:
            temp_path = self.filepath + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
            os.rename(temp_path, self.filepath)
        except Exception as e:
            print(f"[SaveManager] Error saving data: {e}")

    # --- Career Stats ---
    @property
    def high_score(self) -> int:
        return self.data["career"].get("high_score", 0)

    @property
    def max_wave(self) -> int:
        return self.data["career"].get("max_wave", 0)

    @property
    def total_kills(self) -> int:
        return self.data["career"].get("total_kills", 0)

    @property
    def total_games(self) -> int:
        return self.data["career"].get("total_games", 0)

    @property
    def souls(self) -> int:
        return self.data["career"].get("souls", 0)

    def add_souls(self, count: int) -> None:
        self.data["career"]["souls"] = max(0, self.souls + count)
        self.save()

    def record_game_end(self, wave: int, kills: int, score: int, souls_earned: int) -> None:
        career = self.data["career"]
        career["total_games"] = career.get("total_games", 0) + 1
        career["total_kills"] = career.get("total_kills", 0) + kills
        career["souls"] = career.get("souls", 0) + souls_earned

        if score > career.get("high_score", 0):
            career["high_score"] = score
        if wave > career.get("max_wave", 0):
            career["max_wave"] = wave

        # Clear any active run since run ended
        self.data["active_run"] = None
        self.save()

    # --- Permanent Upgrades ---
    def get_upgrade_level(self, upgrade_id: str) -> int:
        # Fallback resolution for legacy warrior keys
        if upgrade_id == "warrior_hp":
            v = self.data["permanent_upgrades"].get("warrior_hp", 0)
            return max(v, self.data["permanent_upgrades"].get("hp_boost", 0))
        elif upgrade_id == "warrior_damage":
            v = self.data["permanent_upgrades"].get("warrior_damage", 0)
            return max(v, self.data["permanent_upgrades"].get("damage_boost", 0))
        elif upgrade_id == "warrior_speed":
            v = self.data["permanent_upgrades"].get("warrior_speed", 0)
            return max(v, self.data["permanent_upgrades"].get("speed_boost", 0))
        elif upgrade_id == "hp_boost":
            return self.get_upgrade_level("warrior_hp")
        elif upgrade_id == "damage_boost":
            return self.get_upgrade_level("warrior_damage")
        elif upgrade_id == "speed_boost":
            return self.get_upgrade_level("warrior_speed")

        return self.data["permanent_upgrades"].get(upgrade_id, 0)

    def get_upgrade_cost(self, upgrade_id: str) -> int:
        meta = PERMANENT_UPGRADES_META.get(upgrade_id)
        if not meta:
            return 999999
        lvl = self.get_upgrade_level(upgrade_id)
        if lvl >= meta["max_level"]:
            return 0  # Maxed out
        return int(round(meta["base_cost"] * (meta["cost_multiplier"] ** lvl)))

    def can_buy_upgrade(self, upgrade_id: str) -> bool:
        meta = PERMANENT_UPGRADES_META.get(upgrade_id)
        if not meta:
            return False
        lvl = self.get_upgrade_level(upgrade_id)
        if lvl >= meta["max_level"]:
            return False
        cost = self.get_upgrade_cost(upgrade_id)
        return self.souls >= cost

    def buy_upgrade(self, upgrade_id: str) -> bool:
        if not self.can_buy_upgrade(upgrade_id):
            return False
        cost = self.get_upgrade_cost(upgrade_id)
        self.data["career"]["souls"] -= cost
        new_lvl = self.get_upgrade_level(upgrade_id) + 1
        self.data["permanent_upgrades"][upgrade_id] = new_lvl

        # Keep legacy warrior keys in sync
        if upgrade_id == "warrior_hp":
            self.data["permanent_upgrades"]["hp_boost"] = new_lvl
        elif upgrade_id == "hp_boost":
            self.data["permanent_upgrades"]["warrior_hp"] = new_lvl
        elif upgrade_id == "warrior_damage":
            self.data["permanent_upgrades"]["damage_boost"] = new_lvl
        elif upgrade_id == "damage_boost":
            self.data["permanent_upgrades"]["warrior_damage"] = new_lvl
        elif upgrade_id == "warrior_speed":
            self.data["permanent_upgrades"]["speed_boost"] = new_lvl
        elif upgrade_id == "speed_boost":
            self.data["permanent_upgrades"]["warrior_speed"] = new_lvl

        self.save()
        return True

    def is_mastery_unlocked(self, class_type: str) -> bool:
        cid = class_type.lower()
        spd = self.get_upgrade_level(f"{cid}_speed")
        hp = self.get_upgrade_level(f"{cid}_hp")
        dmg = self.get_upgrade_level(f"{cid}_damage")
        return spd >= 5 and hp >= 5 and dmg >= 5

    def get_class_total_levels(self, class_type: str) -> int:
        cid = class_type.lower()
        spd = self.get_upgrade_level(f"{cid}_speed")
        hp = self.get_upgrade_level(f"{cid}_hp")
        dmg = self.get_upgrade_level(f"{cid}_damage")
        return min(15, spd + hp + dmg)

    def apply_permanent_upgrades(self, player) -> None:
        cid = getattr(player, "class_type", "warrior").lower()
        hp_lvl = self.get_upgrade_level(f"{cid}_hp")
        dmg_lvl = self.get_upgrade_level(f"{cid}_damage")
        spd_lvl = self.get_upgrade_level(f"{cid}_speed")
        mag_lvl = self.get_upgrade_level("magnet_boost")

        player.max_hp += hp_lvl * 25.0
        player.hp = player.max_hp
        player.damage_multi += dmg_lvl * 0.08
        player.speed *= (1.0 + spd_lvl * 0.06)
        if hasattr(player, "base_speed"):
            player.base_speed = player.speed
        player.magnet_range += mag_lvl * 25.0

        # Activate class mastery when all 3 attributes reach max level (5/5/5)
        if self.is_mastery_unlocked(cid):
            if cid == "warrior":
                player.can_deflect_projectiles = True
            elif cid == "ranger":
                player.projectile_speed_multi = getattr(player, "projectile_speed_multi", 1.0) * 1.50
            elif cid == "mage":
                player.barrier_orbs_active = True
                player.barrier_orbs = 3
                player.barrier_respawn_timer = 0.0
                player.barrier_orbit_angle = 0.0
            elif cid == "summoner":
                player.colossus_minion_unlocked = True
                player.summon_counter = 0

    apply_permanent_upgrades_to_knight = apply_permanent_upgrades

    # --- Settings ---
    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.data["settings"].get(key, default)

    def set_setting(self, key: str, val: Any) -> None:
        self.data["settings"][key] = val
        self.save()

    # --- Active Run Save & Checkpoint ---
    def has_active_run(self) -> bool:
        return self.data.get("active_run") is not None

    def get_active_run(self) -> Optional[Dict[str, Any]]:
        return self.data.get("active_run")

    def save_active_run(
        self,
        wave: int,
        score: int,
        kills: int,
        souls_collected_this_run: int,
        player,
        applied_upgrade_ids: List[str]
    ) -> None:
        p_dict = {
            "class_type": getattr(player, "class_type", "warrior"),
            "hp": player.hp,
            "max_hp": player.max_hp,
            "speed": player.speed,
            "base_speed": getattr(player, "base_speed", player.speed),
            "level": player.level,
            "xp": player.xp,
            "xp_to_next": player.xp_to_next_level,
            "xp_to_next_level": player.xp_to_next_level,
            "damage_multi": player.damage_multi,
            "cooldown_multi": player.cooldown_multi,
            "area_multi": player.area_multi,
            "regen_rate": player.regen_rate,
            "magnet_range": player.magnet_range,
            "vampirism": player.vampirism,
            "thorns": player.thorns,
            "crit_chance_bonus": getattr(player, "crit_chance_bonus", 0.0),
            "damage_reduction": getattr(player, "damage_reduction", 0.0),
            "dash_damage": getattr(player, "dash_damage", 0.0),
            "dash_cooldown_reduction": getattr(player, "dash_cooldown_reduction", 0.0),
            "atk2_damage_bonus": getattr(player, "atk2_damage_bonus", 0.0),
            "atk3_damage_bonus": getattr(player, "atk3_damage_bonus", 0.0),
            "berserk_bonus": getattr(player, "berserk_bonus", 0.0),
            "projectile_speed_multi": getattr(player, "projectile_speed_multi", 1.0),
            "arrow_pierce_bonus": getattr(player, "arrow_pierce_bonus", 0),
            "multishot_extra": getattr(player, "multishot_extra", 0),
            "explosive_arrow_bonus": getattr(player, "explosive_arrow_bonus", 0.0),
            "poison_damage": getattr(player, "poison_damage", 0.0),
            "ricochet_bonus": getattr(player, "ricochet_bonus", 0),
            "fireball_damage_bonus": getattr(player, "fireball_damage_bonus", 0.0),
            "frost_nova_radius_bonus": getattr(player, "frost_nova_radius_bonus", 0.0),
            "teleport_blast_damage": getattr(player, "teleport_blast_damage", 0.0),
            "mana_shield_max": getattr(player, "mana_shield_max", 0.0),
            "mana_shield": getattr(player, "mana_shield", 0.0),
            "arcane_barrage_extra": getattr(player, "arcane_barrage_extra", 0),
            "chain_lightning_targets": getattr(player, "chain_lightning_targets", 0),
            "minion_dmg_multi": getattr(player, "minion_dmg_multi", 1.0),
            "minion_hp_multi": getattr(player, "minion_hp_multi", 1.0),
            "minion_speed_multi": getattr(player, "minion_speed_multi", 1.0),
            "max_minions": getattr(player, "max_minions", 4),
            "soul_burst_extra": getattr(player, "soul_burst_extra", 0),
            "corpse_explosion_damage": getattr(player, "corpse_explosion_damage", 0.0),
            "soul_gain_bonus": getattr(player, "soul_gain_bonus", 0),
            "damage_reduction_per_minion": getattr(player, "damage_reduction_per_minion", 0.0),
            "can_deflect_projectiles": getattr(player, "can_deflect_projectiles", False),
            "barrier_orbs_active": getattr(player, "barrier_orbs_active", False),
            "barrier_orbs": getattr(player, "barrier_orbs", 0),
            "colossus_minion_unlocked": getattr(player, "colossus_minion_unlocked", False),
            "summon_counter": getattr(player, "summon_counter", 0),
            "upgrade_levels": getattr(player, "upgrade_levels", {}),
        }
        self.data["active_run"] = {
            "wave": wave,
            "score": score,
            "kills": kills,
            "souls_collected": souls_collected_this_run,
            "player": p_dict,
            "applied_upgrade_ids": applied_upgrade_ids,
        }
        self.save()

    def clear_active_run(self) -> None:
        self.data["active_run"] = None
        self.save()
