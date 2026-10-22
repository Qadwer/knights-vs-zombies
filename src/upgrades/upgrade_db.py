"""
База данных улучшений и система прокачки при повышении уровня (Level-Up).
Особенности:
- 5 общих улучшений, доступных всем классам
- 10 уникальных улучшений для каждого из 4 классов (Воин, Лучник, Маг, Призыватель)
- 5 уровней у каждого улучшения с прогрессивным масштабированием бонусов
- Редкость улучшений и фильтрация строго под текущий класс героя
"""

from dataclasses import dataclass
import random
from typing import Callable, Dict, List, Optional, Any, Tuple
from ..config import settings, UpgradeBalance, MinionBalance


@dataclass
class UpgradeCard:
    id: str                     # Уникальный идентификатор карты, напр. "common_dmg_sharp_lvl1"
    base_id: str                # Базовый идентификатор улучшения, напр. "common_dmg_sharp"
    title: str                  # Отображаемое название, напр. "Заточка оружия"
    desc: str                   # Описание бонуса текущего уровня
    tier: str                   # Редкость: "common", "rare", "epic"
    icon: str                   # Ключ иконки для IconEngine
    level: int                  # Уровень от 1 до 5
    max_level: int              # Максимальный уровень (5)
    class_req: Optional[str]    # None для общих, либо "warrior"/"ranger"/"mage"/"summoner"
    apply_fn: Callable[[Any], None]

    def apply(self, player: Any) -> None:
        if not hasattr(player, "upgrade_levels"):
            player.upgrade_levels = {}
        old_lvl = player.upgrade_levels.get(self.base_id, 0)
        if self.apply_fn:
            try:
                self.apply_fn(player, old_lvl, self.level)
            except TypeError:
                self.apply_fn(player)
        player.upgrade_levels[self.base_id] = self.level


def _calc_delta(table: List[float], old_lvl: int, new_lvl: int) -> float:
    new_idx = max(0, min(len(table) - 1, new_lvl - 1))
    new_val = table[new_idx]
    old_val = table[old_lvl - 1] if 1 <= old_lvl <= len(table) else 0.0
    return new_val - old_val


def _resolve_levels(p: Any, base_id: str, old_lvl: Any, new_lvl: Optional[int]) -> Tuple[int, int]:
    if new_lvl is None:
        target = int(old_lvl)
        current = getattr(p, "upgrade_levels", {}).get(base_id, 0)
        return current, target
    return int(old_lvl), int(new_lvl)


class UpgradeBase:
    def __init__(
        self,
        base_id: str,
        title: str,
        tier: str,
        icon: str,
        class_req: Optional[str],
        level_descs: List[str],
        apply_per_level: Callable[..., None]
    ):
        self.base_id = base_id
        self.title = title
        self.tier = tier
        self.icon = icon
        self.class_req = class_req
        self.level_descs = level_descs
        self.apply_per_level = apply_per_level
        self.max_level = 5

    def get_card(self, level: int) -> UpgradeCard:
        clamped_lvl = max(1, min(5, level))
        desc_idx = clamped_lvl - 1
        desc = self.level_descs[desc_idx] if desc_idx < len(self.level_descs) else self.level_descs[-1]

        def _apply(player: Any, old_lvl: Optional[int] = None, new_lvl: Optional[int] = None):
            if old_lvl is None:
                old_lvl = getattr(player, "upgrade_levels", {}).get(self.base_id, 0)
            if new_lvl is None:
                new_lvl = clamped_lvl
            self.apply_per_level(player, old_lvl, new_lvl)

        return UpgradeCard(
            id=f"{self.base_id}_lvl{clamped_lvl}",
            base_id=self.base_id,
            title=self.title,
            desc=desc,
            tier=self.tier,
            icon=self.icon,
            level=clamped_lvl,
            max_level=self.max_level,
            class_req=self.class_req,
            apply_fn=_apply
        )


# ===========================================================================
# 1. FIVE COMMON UPGRADES (Available to ALL classes)
# ===========================================================================

def _apply_common_dmg(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "common_dmg_sharp", old_lvl, new_lvl)
    p.damage_multi += _calc_delta(UpgradeBalance.COMMON_DMG_SHARP, cur, nxt)

def _apply_common_hp(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "common_vitality", old_lvl, new_lvl)
    delta = _calc_delta(UpgradeBalance.COMMON_VITALITY_HP, cur, nxt)
    p.max_hp += delta
    if nxt >= 5:
        p.hp = p.max_hp
    else:
        p.hp = min(p.max_hp, p.hp + delta)

def _apply_common_spd(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "common_swiftness", old_lvl, new_lvl)
    delta = _calc_delta(UpgradeBalance.COMMON_SWIFTNESS_SPD, cur, nxt)
    base_s = getattr(p, "base_speed", 195.0)
    p.speed += base_s * delta

def _apply_common_mag(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "common_magnet", old_lvl, new_lvl)
    p.magnet_range += _calc_delta(UpgradeBalance.COMMON_MAGNET_RANGE, cur, nxt)

def _apply_common_haste(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "common_haste", old_lvl, new_lvl)
    delta = _calc_delta(UpgradeBalance.COMMON_HASTE_CDR, cur, nxt)
    p.cooldown_multi = max(0.40, p.cooldown_multi - delta)

COMMON_BASES: List[UpgradeBase] = [
    UpgradeBase(
        base_id="common_dmg_sharp",
        title="Заточка оружия",
        tier="common",
        icon="upg_dmg",
        class_req=None,
        level_descs=[
            "+8% к урону всех атак и способностей",
            "+16% к урону всех атак и способностей",
            "+24% к урону всех атак и способностей",
            "+32% к урону всех атак и способностей",
            "+45% к урону и мастерство оружия"
        ],
        apply_per_level=_apply_common_dmg
    ),
    UpgradeBase(
        base_id="common_vitality",
        title="Титановое сердце",
        tier="common",
        icon="upg_vitality",
        class_req=None,
        level_descs=[
            "+35 к макс. HP и лечение на 35 HP",
            "+70 к макс. HP и лечение на 70 HP",
            "+105 к макс. HP и лечение на 105 HP",
            "+140 к макс. HP и лечение на 140 HP",
            "+180 к макс. HP и полное исцеление до 100%"
        ],
        apply_per_level=_apply_common_hp
    ),
    UpgradeBase(
        base_id="common_swiftness",
        title="Сапоги следопыта",
        tier="common",
        icon="upg_speed",
        class_req=None,
        level_descs=[
            "+7% к скорости передвижения героя",
            "+14% к скорости передвижения героя",
            "+21% к скорости передвижения героя",
            "+28% к скорости передвижения героя",
            "+38% к скорости бега и легкий шаг"
        ],
        apply_per_level=_apply_common_spd
    ),
    UpgradeBase(
        base_id="common_magnet",
        title="Магнит душ",
        tier="common",
        icon="upg_magnet",
        class_req=None,
        level_descs=[
            "+45 к радиусу притягивания сфер опыта",
            "+90 к радиусу притягивания сфер опыта",
            "+135 к радиусу притягивания сфер опыта",
            "+180 к радиусу притягивания сфер опыта",
            "+240 к радиусу (сбор сфер по всей арене)"
        ],
        apply_per_level=_apply_common_mag
    ),
    UpgradeBase(
        base_id="common_haste",
        title="Ускорение навыков",
        tier="rare",
        icon="upg_haste",
        class_req=None,
        level_descs=[
            "-8% ко времени перезарядки способностей",
            "-16% ко времени перезарядки способностей",
            "-24% ко времени перезарядки способностей",
            "-32% ко времени перезарядки способностей",
            "-42% ко времени перезарядки (ураганный темп)"
        ],
        apply_per_level=_apply_common_haste
    ),
]


# ===========================================================================
# 2. TEN WARRIOR UPGRADES (Воин / Рыцарь)
# ===========================================================================

def _apply_war_cleave(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_cleave", old_lvl, new_lvl)
    p.area_multi += _calc_delta(UpgradeBalance.WAR_CLEAVE_AREA, cur, nxt)

def _apply_war_iron_skin(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_iron_skin", old_lvl, new_lvl)
    p.damage_reduction = getattr(p, "damage_reduction", 0.0) + _calc_delta(UpgradeBalance.WAR_IRON_SKIN_DMG_RED, cur, nxt)
    d_hp = _calc_delta(UpgradeBalance.WAR_IRON_SKIN_HP, cur, nxt)
    p.max_hp += d_hp
    p.hp = min(p.max_hp, p.hp + d_hp)

def _apply_war_whirlwind(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_whirlwind", old_lvl, new_lvl)
    p.atk2_damage_bonus = getattr(p, "atk2_damage_bonus", 0.0) + _calc_delta(UpgradeBalance.WAR_WHIRLWIND_DMG, cur, nxt)
    p.area_multi += _calc_delta(UpgradeBalance.WAR_WHIRLWIND_AREA, cur, nxt)

def _apply_war_wind_blade(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_wind_blade", old_lvl, new_lvl)
    p.atk3_damage_bonus = getattr(p, "atk3_damage_bonus", 0.0) + _calc_delta(UpgradeBalance.WAR_WIND_BLADE_DMG, cur, nxt)

def _apply_war_thorns(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_thorns", old_lvl, new_lvl)
    p.thorns += _calc_delta(UpgradeBalance.WAR_THORNS, cur, nxt)

def _apply_war_vampirism(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_vampirism", old_lvl, new_lvl)
    p.vampirism += _calc_delta(UpgradeBalance.WAR_VAMPIRISM, cur, nxt)

def _apply_war_berserk(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_berserk", old_lvl, new_lvl)
    p.berserk_bonus = getattr(p, "berserk_bonus", 0.0) + _calc_delta(UpgradeBalance.WAR_BERSERK_DMG, cur, nxt)

def _apply_war_dash_smash(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_dash_smash", old_lvl, new_lvl)
    p.dash_damage = getattr(p, "dash_damage", 0.0) + _calc_delta(UpgradeBalance.WAR_DASH_SMASH_DMG, cur, nxt)

def _apply_war_holy_regen(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_holy_regen", old_lvl, new_lvl)
    p.regen_rate += _calc_delta(UpgradeBalance.WAR_HOLY_REGEN, cur, nxt)

def _apply_war_executioner(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "war_executioner", old_lvl, new_lvl)
    p.crit_chance_bonus = getattr(p, "crit_chance_bonus", 0.0) + _calc_delta(UpgradeBalance.WAR_EXECUTIONER_CRIT, cur, nxt)

WARRIOR_BASES: List[UpgradeBase] = [
    UpgradeBase(
        base_id="war_cleave",
        title="Размашистый взмах",
        tier="common",
        icon="upg_cleave",
        class_req="warrior",
        level_descs=[
            "+12% к сектору и радиусу рубящих ударов",
            "+24% к радиусу рубящих ударов",
            "+36% к радиусу рубящих ударов",
            "+48% к радиусу рубящих ударов",
            "+65% к площади удара меча (рубит целые толпы)"
        ],
        apply_per_level=_apply_war_cleave
    ),
    UpgradeBase(
        base_id="war_iron_skin",
        title="Латная броня",
        tier="common",
        icon="upg_iron_skin",
        class_req="warrior",
        level_descs=[
            "Снижает входящий урон на 6% и дает +20 HP",
            "Снижает входящий урон на 12% и дает +40 HP",
            "Снижает входящий урон на 18% и дает +60 HP",
            "Снижает входящий урон на 24% и дает +80 HP",
            "Снижает урон на 32% и дает +120 HP"
        ],
        apply_per_level=_apply_war_iron_skin
    ),
    UpgradeBase(
        base_id="war_whirlwind",
        title="Огненный вихрь",
        tier="rare",
        icon="upg_whirlwind",
        class_req="warrior",
        level_descs=[
            "+20% к урону и радиусу круговой атаки 360°",
            "+40% к урону и радиусу круговой атаки 360°",
            "+60% к урону и радиусу круговой атаки 360°",
            "+80% к урону и радиусу круговой атаки 360°",
            "+110% к урону вихря и мощное отталкивание зомби"
        ],
        apply_per_level=_apply_war_whirlwind
    ),
    UpgradeBase(
        base_id="war_wind_blade",
        title="Клинок бури",
        tier="rare",
        icon="upg_wind_blade",
        class_req="warrior",
        level_descs=[
            "+25% к урону пронзающего клинка ветра",
            "+50% к урону пронзающего клинка ветра",
            "+75% к урону пронзающего клинка ветра",
            "+100% к урону пронзающего клинка ветра",
            "+140% к урону и увеличенная скорость снаряда"
        ],
        apply_per_level=_apply_war_wind_blade
    ),
    UpgradeBase(
        base_id="war_thorns",
        title="Шипастый бастион",
        tier="common",
        icon="upg_thorns",
        class_req="warrior",
        level_descs=[
            "Атакующие зомби получают 16 урона при касании",
            "Атакующие зомби получают 32 урона при касании",
            "Атакующие зомби получают 48 урона при касании",
            "Атакующие зомби получают 64 урона при касании",
            "Атакующие зомби получают 90 урона при касании"
        ],
        apply_per_level=_apply_war_thorns
    ),
    UpgradeBase(
        base_id="war_vampirism",
        title="Кровавая жатва",
        tier="rare",
        icon="upg_vampirism",
        class_req="warrior",
        level_descs=[
            "+1.4 HP вампиризма при каждом убийстве зомби",
            "+2.8 HP вампиризма при каждом убийстве зомби",
            "+4.2 HP вампиризма при каждом убийстве зомби",
            "+5.6 HP вампиризма при каждом убийстве зомби",
            "+7.5 HP вампиризма (неуязвимость в гуще врагов)"
        ],
        apply_per_level=_apply_war_vampirism
    ),
    UpgradeBase(
        base_id="war_berserk",
        title="Ярость берсерка",
        tier="epic",
        icon="upg_berserk",
        class_req="warrior",
        level_descs=[
            "+20% урона когда здоровье падает ниже 50%",
            "+40% урона когда здоровье падает ниже 50%",
            "+60% урона когда здоровье падает ниже 50%",
            "+80% урона когда здоровье падает ниже 50%",
            "+120% к урону и скорость атаки при низком HP"
        ],
        apply_per_level=_apply_war_berserk
    ),
    UpgradeBase(
        base_id="war_dash_smash",
        title="Таранный рывок",
        tier="rare",
        icon="upg_dash_smash",
        class_req="warrior",
        level_descs=[
            "Рывок наносит 45 урона всем зомби на пути",
            "Рывок наносит 90 урона всем зомби на пути",
            "Рывок наносит 135 урона всем зомби на пути",
            "Рывок наносит 180 урона всем зомби на пути",
            "Рывок наносит 240 урона и отбрасывает толпу"
        ],
        apply_per_level=_apply_war_dash_smash
    ),
    UpgradeBase(
        base_id="war_holy_regen",
        title="Благословение ордена",
        tier="common",
        icon="upg_holy_regen",
        class_req="warrior",
        level_descs=[
            "+1.2 HP/сек постоянной регенерации здоровья",
            "+2.4 HP/сек постоянной регенерации здоровья",
            "+3.6 HP/сек постоянной регенерации здоровья",
            "+4.8 HP/сек постоянной регенерации здоровья",
            "+6.5 HP/сек мощной святой регенерации"
        ],
        apply_per_level=_apply_war_holy_regen
    ),
    UpgradeBase(
        base_id="war_executioner",
        title="Палач нежити",
        tier="epic",
        icon="upg_executioner",
        class_req="warrior",
        level_descs=[
            "+8% шанс критического удара x2.0 по зомби",
            "+16% шанс критического удара x2.0 по зомби",
            "+24% шанс критического удара x2.0 по зомби",
            "+32% шанс критического удара x2.0 по зомби",
            "+45% шанс сокрушительного критического удара"
        ],
        apply_per_level=_apply_war_executioner
    ),
]


# ===========================================================================
# 3. TEN RANGER UPGRADES (Стрелок / Лучник)
# ===========================================================================

def _apply_rng_arrow_dmg(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_arrow_dmg", old_lvl, new_lvl)
    p.damage_multi += _calc_delta(UpgradeBalance.RNG_ARROW_DMG, cur, nxt)

def _apply_rng_arrow_spd(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_arrow_speed", old_lvl, new_lvl)
    p.projectile_speed_multi = getattr(p, "projectile_speed_multi", 1.0) + _calc_delta(UpgradeBalance.RNG_ARROW_SPD, cur, nxt)

def _apply_rng_pierce(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_piercing", old_lvl, new_lvl)
    p.arrow_pierce_bonus = getattr(p, "arrow_pierce_bonus", 0) + int(_calc_delta(UpgradeBalance.RNG_PIERCE, cur, nxt))

def _apply_rng_multishot(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_multishot", old_lvl, new_lvl)
    p.multishot_extra = getattr(p, "multishot_extra", 0) + int(_calc_delta(UpgradeBalance.RNG_MULTISHOT, cur, nxt))

def _apply_rng_explosive(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_explosive", old_lvl, new_lvl)
    p.explosive_arrow_bonus = getattr(p, "explosive_arrow_bonus", 0.0) + _calc_delta(UpgradeBalance.RNG_EXPLOSIVE_DMG, cur, nxt)
    p.area_multi += _calc_delta(UpgradeBalance.RNG_EXPLOSIVE_AREA, cur, nxt)

def _apply_rng_eagle_eye(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_eagle_eye", old_lvl, new_lvl)
    p.crit_chance_bonus = getattr(p, "crit_chance_bonus", 0.0) + _calc_delta(UpgradeBalance.RNG_EAGLE_EYE_CRIT, cur, nxt)
    p.magnet_range += _calc_delta(UpgradeBalance.RNG_EAGLE_EYE_MAGNET, cur, nxt)

def _apply_rng_acrobat(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_acrobat", old_lvl, new_lvl)
    p.dash_cooldown_reduction = getattr(p, "dash_cooldown_reduction", 0.0) + _calc_delta(UpgradeBalance.RNG_ACROBAT_CDR, cur, nxt)
    p.speed += getattr(p, "base_speed", 218.0) * _calc_delta(UpgradeBalance.RNG_ACROBAT_SPD, cur, nxt)

def _apply_rng_poison(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_poison_tips", old_lvl, new_lvl)
    p.poison_damage = getattr(p, "poison_damage", 0.0) + _calc_delta(UpgradeBalance.RNG_POISON_DPS, cur, nxt)

def _apply_rng_ricochet(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_ricochet", old_lvl, new_lvl)
    p.ricochet_bonus = getattr(p, "ricochet_bonus", 0) + int(_calc_delta(UpgradeBalance.RNG_RICOCHET, cur, nxt))

def _apply_rng_hunter(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "rng_hunter_instinct", old_lvl, new_lvl)
    p.damage_multi += _calc_delta(UpgradeBalance.RNG_HUNTER_DMG, cur, nxt)
    p.cooldown_multi = max(0.40, p.cooldown_multi - _calc_delta(UpgradeBalance.RNG_HUNTER_CDR, cur, nxt))
    p.speed += getattr(p, "base_speed", 218.0) * _calc_delta(UpgradeBalance.RNG_HUNTER_SPD, cur, nxt)

RANGER_BASES: List[UpgradeBase] = [
    UpgradeBase(
        base_id="rng_arrow_dmg",
        title="Тяжелые наконечники",
        tier="common",
        icon="upg_arrow_dmg",
        class_req="ranger",
        level_descs=[
            "+10% к урону всех стрел и выстрелов",
            "+20% к урону всех стрел и выстрелов",
            "+30% к урону всех стрел и выстрелов",
            "+40% к урону всех стрел и выстрелов",
            "+55% к урону стрел (бронебойная мощь)"
        ],
        apply_per_level=_apply_rng_arrow_dmg
    ),
    UpgradeBase(
        base_id="rng_arrow_speed",
        title="Баллистика",
        tier="common",
        icon="upg_arrow_speed",
        class_req="ranger",
        level_descs=[
            "+15% к скорости полёта и дальности стрел",
            "+30% к скорости полёта и дальности стрел",
            "+45% к скорости полёта и дальности стрел",
            "+60% к скорости полёта и дальности стрел",
            "+80% к скорости стрел (молниеносный полёт)"
        ],
        apply_per_level=_apply_rng_arrow_spd
    ),
    UpgradeBase(
        base_id="rng_piercing",
        title="Сквозной выстрел",
        tier="rare",
        icon="upg_piercing",
        class_req="ranger",
        level_descs=[
            "Стрелы пронзают на 1 дополнительного зомби",
            "Стрелы пронзают на 2 дополнительных зомби",
            "Стрелы пронзают на 3 дополнительных зомби",
            "Стрелы пронзают на 4 дополнительных зомби",
            "Стрелы пронзают на 5 зомби насквозь"
        ],
        apply_per_level=_apply_rng_pierce
    ),
    UpgradeBase(
        base_id="rng_multishot",
        title="Град стрел",
        tier="rare",
        icon="upg_multishot",
        class_req="ranger",
        level_descs=[
            "Веер стрел выпускает +1 дополнительную стрелу",
            "Веер стрел выпускает +2 дополнительные стрелы",
            "Веер стрел выпускает +3 дополнительные стрелы",
            "Веер стрел выпускает +4 дополнительные стрелы",
            "Веер стрел выпускает +6 стрел (сплошная стена)"
        ],
        apply_per_level=_apply_rng_multishot
    ),
    UpgradeBase(
        base_id="rng_explosive",
        title="Огненный порох",
        tier="rare",
        icon="upg_explosive",
        class_req="ranger",
        level_descs=[
            "+25% к урону и радиусу взрыва разрывной стрелы",
            "+50% к урону и радиусу взрыва разрывной стрелы",
            "+75% к урону и радиусу взрыва разрывной стрелы",
            "+100% к урону и радиусу взрыва разрывной стрелы",
            "+140% к взрыву (сметает целые орды)"
        ],
        apply_per_level=_apply_rng_explosive
    ),
    UpgradeBase(
        base_id="rng_eagle_eye",
        title="Орлиный взор",
        tier="common",
        icon="upg_eagle_eye",
        class_req="ranger",
        level_descs=[
            "+9% к шансу критического попадания из лука",
            "+18% к шансу критического попадания из лука",
            "+27% к шансу критического попадания из лука",
            "+36% к шансу критического попадания из лука",
            "+50% к шансу крита и увеличенный сбор сфер"
        ],
        apply_per_level=_apply_rng_eagle_eye
    ),
    UpgradeBase(
        base_id="rng_acrobat",
        title="Акробатический перекат",
        tier="common",
        icon="upg_acrobat",
        class_req="ranger",
        level_descs=[
            "-12% к перезарядке переката и +4% скорости",
            "-24% к перезарядке переката и +8% скорости",
            "-36% к перезарядке переката и +12% скорости",
            "-48% к перезарядке переката и +16% скорости",
            "-60% к перезарядке (неуловимый следопыт)"
        ],
        apply_per_level=_apply_rng_acrobat
    ),
    UpgradeBase(
        base_id="rng_poison_tips",
        title="Змеиный яд",
        tier="epic",
        icon="upg_poison",
        class_req="ranger",
        level_descs=[
            "Стрелы отравляют врагов на 20 ед. урона за 3 сек",
            "Стрелы отравляют врагов на 40 ед. урона за 3 сек",
            "Стрелы отравляют врагов на 60 ед. урона за 3 сек",
            "Стрелы отравляют врагов на 80 ед. урона за 3 сек",
            "Смертельный яд: 120 урона и замедление врагов"
        ],
        apply_per_level=_apply_rng_poison
    ),
    UpgradeBase(
        base_id="rng_ricochet",
        title="Рикошет стрел",
        tier="epic",
        icon="upg_ricochet",
        class_req="ranger",
        level_descs=[
            "Стрелы отскакивают в 1 соседнего зомби",
            "Стрелы отскакивают в 2 соседних зомби",
            "Стрелы отскакивают в 3 соседних зомби",
            "Стрелы отскакивают в 4 соседних зомби",
            "Стрелы отскакивают в 5 соседних зомби"
        ],
        apply_per_level=_apply_rng_ricochet
    ),
    UpgradeBase(
        base_id="rng_hunter_instinct",
        title="Инстинкт охотника",
        tier="rare",
        icon="upg_hunter",
        class_req="ranger",
        level_descs=[
            "+6% к общему урону и -6% ко всем кулдаунам",
            "+12% к общему урону и -12% ко всем кулдаунам",
            "+18% к общему урону и -18% ко всем кулдаунам",
            "+24% к общему урону и -24% ко всем кулдаунам",
            "+35% к урону, ускоренная стрельба и маневренность"
        ],
        apply_per_level=_apply_rng_hunter
    ),
]


# ===========================================================================
# 4. TEN MAGE UPGRADES (Маг / Архимаг)
# ===========================================================================

def _apply_mage_arcane(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_arcane_focus", old_lvl, new_lvl)
    p.damage_multi += _calc_delta(UpgradeBalance.MAGE_ARCANE_DMG, cur, nxt)

def _apply_mage_fireball(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_fireball_mastery", old_lvl, new_lvl)
    p.fireball_damage_bonus = getattr(p, "fireball_damage_bonus", 0.0) + _calc_delta(UpgradeBalance.MAGE_FIREBALL_DMG, cur, nxt)
    p.area_multi += _calc_delta(UpgradeBalance.MAGE_FIREBALL_AREA, cur, nxt)

def _apply_mage_frost(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_frost_nova", old_lvl, new_lvl)
    p.frost_nova_radius_bonus = getattr(p, "frost_nova_radius_bonus", 0.0) + _calc_delta(UpgradeBalance.MAGE_FROST_NOVA_RADIUS, cur, nxt)

def _apply_mage_blink(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_blink_blast", old_lvl, new_lvl)
    p.teleport_blast_damage = getattr(p, "teleport_blast_damage", 0.0) + _calc_delta(UpgradeBalance.MAGE_BLINK_BLAST_DMG, cur, nxt)

def _apply_mage_mana_shield(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_mana_shield", old_lvl, new_lvl)
    d_sh = _calc_delta(UpgradeBalance.MAGE_MANA_SHIELD_AMOUNT, cur, nxt)
    p.mana_shield_max = getattr(p, "mana_shield_max", 0.0) + d_sh
    p.mana_shield = getattr(p, "mana_shield", 0.0) + d_sh
    d_hp = _calc_delta(UpgradeBalance.MAGE_MANA_SHIELD_HP, cur, nxt)
    p.max_hp += d_hp
    p.hp = min(p.max_hp, p.hp + d_hp)

def _apply_mage_barrage(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_arcane_barrage", old_lvl, new_lvl)
    p.arcane_barrage_extra = getattr(p, "arcane_barrage_extra", 0) + int(_calc_delta(UpgradeBalance.MAGE_ARCANE_BARRAGE_EXTRA, cur, nxt))

def _apply_mage_spell_haste(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_spell_haste", old_lvl, new_lvl)
    p.cooldown_multi = max(0.40, p.cooldown_multi - _calc_delta(UpgradeBalance.MAGE_SPELL_HASTE_CDR, cur, nxt))

def _apply_mage_lightning(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_chain_lightning", old_lvl, new_lvl)
    p.chain_lightning_targets = getattr(p, "chain_lightning_targets", 0) + int(_calc_delta(UpgradeBalance.MAGE_LIGHTNING_TARGETS, cur, nxt))

def _apply_mage_supernova(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_supernova", old_lvl, new_lvl)
    p.area_multi += _calc_delta(UpgradeBalance.MAGE_SUPERNOVA_AREA, cur, nxt)

def _apply_mage_siphon(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "mage_soul_siphon", old_lvl, new_lvl)
    p.vampirism += _calc_delta(UpgradeBalance.MAGE_SIPHON_VAMPIRISM, cur, nxt)

MAGE_BASES: List[UpgradeBase] = [
    UpgradeBase(
        base_id="mage_arcane_focus",
        title="Чародейский фокус",
        tier="common",
        icon="upg_arcane",
        class_req="mage",
        level_descs=[
            "+11% к урону всех магических заклинаний",
            "+22% к урону всех магических заклинаний",
            "+33% к урону всех магических заклинаний",
            "+44% к урону всех магических заклинаний",
            "+60% к магическому урону (великий архимаг)"
        ],
        apply_per_level=_apply_mage_arcane
    ),
    UpgradeBase(
        base_id="mage_fireball_mastery",
        title="Пиромантия",
        tier="rare",
        icon="upg_fireball",
        class_req="mage",
        level_descs=[
            "+25% к урону и взрыву огненного шара",
            "+50% к урону и взрыву огненного шара",
            "+75% к урону и взрыву огненного шара",
            "+100% к урону и взрыву огненного шара",
            "+140% к взрыву фаербола (пылающий метеорит)"
        ],
        apply_per_level=_apply_mage_fireball
    ),
    UpgradeBase(
        base_id="mage_frost_nova",
        title="Абсолютный ноль",
        tier="rare",
        icon="upg_frost",
        class_req="mage",
        level_descs=[
            "+18% к радиусу ледяного круга и заморозке",
            "+36% к радиусу ледяного круга и заморозке",
            "+54% к радиусу ледяного круга и заморозке",
            "+72% к радиусу ледяного круга и заморозке",
            "+95% к радиусу (замораживает весь экран)"
        ],
        apply_per_level=_apply_mage_frost
    ),
    UpgradeBase(
        base_id="mage_blink_blast",
        title="Астральный взрыв",
        tier="common",
        icon="upg_blink",
        class_req="mage",
        level_descs=[
            "Телепортация вызывает эфирный взрыв на 40 урона",
            "Телепортация вызывает эфирный взрыв на 80 урона",
            "Телепортация вызывает эфирный взрыв на 120 урона",
            "Телепортация вызывает эфирный взрыв на 160 урона",
            "Вспышка телепорта наносит 220 урона и отбрасывает"
        ],
        apply_per_level=_apply_mage_blink
    ),
    UpgradeBase(
        base_id="mage_mana_shield",
        title="Щит маны",
        tier="common",
        icon="upg_mana_shield",
        class_req="mage",
        level_descs=[
            "Поглощает 35 ед. урона и дает +20 макс. HP",
            "Поглощает 70 ед. урона и дает +40 макс. HP",
            "Поглощает 105 ед. урона и дает +60 макс. HP",
            "Поглощает 140 ед. урона и дает +80 макс. HP",
            "Поглощает 190 ед. урона (непробиваемый барьер)"
        ],
        apply_per_level=_apply_mage_mana_shield
    ),
    UpgradeBase(
        base_id="mage_arcane_barrage",
        title="Чародейский шквал",
        tier="rare",
        icon="upg_barrage",
        class_req="mage",
        level_descs=[
            "Стрела чар выпускает +1 дополнительный снаряд",
            "Стрела чар выпускает +2 дополнительных снаряда",
            "Стрела чар выпускает +3 дополнительных снаряда",
            "Стрела чар выпускает +4 дополнительных снаряда",
            "Стрела чар выпускает +5 самонаводящихся снарядов"
        ],
        apply_per_level=_apply_mage_barrage
    ),
    UpgradeBase(
        base_id="mage_spell_haste",
        title="Поток маны",
        tier="common",
        icon="upg_spell_haste",
        class_req="mage",
        level_descs=[
            "-9% к задержке всех магических атак",
            "-18% к задержке всех магических атак",
            "-27% к задержке всех магических атак",
            "-36% к задержке всех магических атак",
            "-48% к задержке (заклинания без перерыва)"
        ],
        apply_per_level=_apply_mage_spell_haste
    ),
    UpgradeBase(
        base_id="mage_chain_lightning",
        title="Цепная молния",
        tier="epic",
        icon="upg_lightning",
        class_req="mage",
        level_descs=[
            "Заклинания вызывают молнию, бьющую в 1 цель",
            "Заклинания вызывают молнию, бьющую в 2 цели",
            "Заклинания вызывают молнию, бьющую в 3 цели",
            "Заклинания вызывают молнию, бьющую в 4 цели",
            "Электрическая дуга поражает до 6 зомби"
        ],
        apply_per_level=_apply_mage_lightning
    ),
    UpgradeBase(
        base_id="mage_supernova",
        title="Сверхновая звезда",
        tier="epic",
        icon="upg_supernova",
        class_req="mage",
        level_descs=[
            "+15% к радиусу поражения всех заклинаний",
            "+30% к радиусу поражения всех заклинаний",
            "+45% к радиусу поражения всех заклинаний",
            "+60% к радиусу поражения всех заклинаний",
            "+85% к площади поражения (гигантский AOE)"
        ],
        apply_per_level=_apply_mage_supernova
    ),
    UpgradeBase(
        base_id="mage_soul_siphon",
        title="Вытягивание жизни",
        tier="rare",
        icon="upg_siphon",
        class_req="mage",
        level_descs=[
            "+1.5 HP вампиризма при убийстве магией",
            "+3.0 HP вампиризма при убийстве магией",
            "+4.5 HP вампиризма при убийстве магией",
            "+6.0 HP вампиризма при убийстве магией",
            "+8.0 HP вампиризма (вечная подпитка жизни)"
        ],
        apply_per_level=_apply_mage_siphon
    ),
]


# ===========================================================================
# 5. TEN SUMMONER UPGRADES (Призыватель / Некромант)
# ===========================================================================

def _apply_sum_minion_dmg(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_minion_dmg", old_lvl, new_lvl)
    p.minion_dmg_multi = getattr(p, "minion_dmg_multi", 1.0) + _calc_delta(UpgradeBalance.SUM_MINION_DMG, cur, nxt)
    p.damage_multi += _calc_delta(UpgradeBalance.SUM_HERO_DMG_BONUS, cur, nxt)

def _apply_sum_army(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_minion_army", old_lvl, new_lvl)
    table = UpgradeBalance.SUM_ARMY_EXTRA
    old_max = 4 + int(table[cur - 1]) if cur >= 1 else 4
    new_max = 4 + int(table[nxt - 1])
    p.max_minions = new_max
    # Spawn to fill every newly available slot
    if hasattr(p, "_spawn_minion"):
        new_slots = max(0, new_max - old_max)
        for _ in range(new_slots):
            p._spawn_minion()

def _apply_sum_minion_hp(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_minion_hp", old_lvl, new_lvl)
    delta = _calc_delta(UpgradeBalance.SUM_MINION_HP, cur, nxt)
    p.minion_hp_multi = getattr(p, "minion_hp_multi", 1.0) + delta
    base_hp = MinionBalance.BASE_HP
    for m in getattr(p, "minions", []):
        m.max_hp = base_hp * p.minion_hp_multi
        m.hp = min(m.max_hp, m.hp + base_hp * delta)

def _apply_sum_minion_speed(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_minion_speed", old_lvl, new_lvl)
    delta = _calc_delta(UpgradeBalance.SUM_MINION_SPD, cur, nxt)
    p.minion_speed_multi = getattr(p, "minion_speed_multi", 1.0) + delta
    base_spd = MinionBalance.BASE_SPEED
    for m in getattr(p, "minions", []):
        m.speed = base_spd * p.minion_speed_multi

def _apply_sum_soul_burst(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_soul_burst", old_lvl, new_lvl)
    p.soul_burst_extra = getattr(p, "soul_burst_extra", 0) + int(_calc_delta(UpgradeBalance.SUM_SOUL_BURST_EXTRA, cur, nxt))

def _apply_sum_spirit_whip(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_spirit_whip", old_lvl, new_lvl)
    p.damage_multi += _calc_delta(UpgradeBalance.SUM_SPIRIT_WHIP_DMG, cur, nxt)
    p.area_multi += _calc_delta(UpgradeBalance.SUM_SPIRIT_WHIP_AREA, cur, nxt)

def _apply_sum_corpse_explosion(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_corpse_explosion", old_lvl, new_lvl)
    p.corpse_explosion_damage = getattr(p, "corpse_explosion_damage", 0.0) + _calc_delta(UpgradeBalance.SUM_CORPSE_EXPLOSION_DMG, cur, nxt)

def _apply_sum_harvest(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_soul_harvest", old_lvl, new_lvl)
    p.soul_gain_bonus = getattr(p, "soul_gain_bonus", 0) + int(_calc_delta(UpgradeBalance.SUM_SOUL_HARVEST_SOULS, cur, nxt))

def _apply_sum_spectral_shield(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_spectral_shield", old_lvl, new_lvl)
    p.damage_reduction_per_minion = getattr(p, "damage_reduction_per_minion", 0.0) + _calc_delta(UpgradeBalance.SUM_SPECTRAL_SHIELD_DEF, cur, nxt)

def _apply_sum_vamp_bond(p, old_lvl, new_lvl=None):
    cur, nxt = _resolve_levels(p, "sum_vampiric_bond", old_lvl, new_lvl)
    p.vampirism += _calc_delta(UpgradeBalance.SUM_VAMP_BOND_VAMPIRISM, cur, nxt)

SUMMONER_BASES: List[UpgradeBase] = [
    UpgradeBase(
        base_id="sum_minion_dmg",
        title="Костяные клыки",
        tier="common",
        icon="upg_minion_dmg",
        class_req="summoner",
        level_descs=[
            "+18% к урону атак верных скелетов-слуг",
            "+36% к урону атак верных скелетов-слуг",
            "+54% к урону атак верных скелетов-слуг",
            "+72% к урону атак верных скелетов-слуг",
            "+95% к урону миньонов (разрывают зомби)"
        ],
        apply_per_level=_apply_sum_minion_dmg
    ),
    UpgradeBase(
        base_id="sum_minion_army",
        title="Легион нежити",
        tier="rare",
        icon="upg_army",
        class_req="summoner",
        level_descs=[
            "+1 к макс. числу призываемых миньонов",
            "+2 к макс. числу призываемых миньонов",
            "+3 к макс. числу призываемых миньонов",
            "+4 к макс. числу призываемых миньонов",
            "+5 к числу миньонов (целая армия скелетов!)"
        ],
        apply_per_level=_apply_sum_army
    ),
    UpgradeBase(
        base_id="sum_minion_hp",
        title="Костяной панцирь",
        tier="common",
        icon="upg_minion_armor",
        class_req="summoner",
        level_descs=[
            "+25% к здоровью и живучести всех миньонов",
            "+50% к здоровью и живучести всех миньонов",
            "+75% к здоровью и живучести всех миньонов",
            "+100% к здоровью и живучести всех миньонов",
            "+140% к здоровью скелетов (настоящие танки)"
        ],
        apply_per_level=_apply_sum_minion_hp
    ),
    UpgradeBase(
        base_id="sum_minion_speed",
        title="Спешка мертвецов",
        tier="common",
        icon="upg_minion_speed",
        class_req="summoner",
        level_descs=[
            "+15% к скорости бега скелетов-слуг",
            "+30% к скорости бега скелетов-слуг",
            "+45% к скорости бега скелетов-слуг",
            "+60% к скорости бега скелетов-слуг",
            "+80% к скорости (молниеносная стая)"
        ],
        apply_per_level=_apply_sum_minion_speed
    ),
    UpgradeBase(
        base_id="sum_soul_burst",
        title="Шквал черепов",
        tier="rare",
        icon="upg_soul_burst",
        class_req="summoner",
        level_descs=[
            "Взрыв душ выпускает +1 дополнительный череп",
            "Взрыв душ выпускает +2 дополнительных черепа",
            "Взрыв душ выпускает +3 дополнительных черепа",
            "Взрыв душ выпускает +4 дополнительных черепа",
            "Взрыв душ выпускает +6 призрачных черепов"
        ],
        apply_per_level=_apply_sum_soul_burst
    ),
    UpgradeBase(
        base_id="sum_spirit_whip",
        title="Хлыст страданий",
        tier="common",
        icon="upg_whip",
        class_req="summoner",
        level_descs=[
            "+10% к урону и дальности призрачного хлыста",
            "+20% к урону и дальности призрачного хлыста",
            "+30% к урону и дальности призрачного хлыста",
            "+40% к урону и дальности призрачного хлыста",
            "+55% к урону хлыста и увеличенный сектор"
        ],
        apply_per_level=_apply_sum_spirit_whip
    ),
    UpgradeBase(
        base_id="sum_corpse_explosion",
        title="Взрыв трупов",
        tier="epic",
        icon="upg_corpse_exp",
        class_req="summoner",
        level_descs=[
            "Гибель зомби от миньона вызывает взрыв на 45 урона",
            "Гибель зомби от миньона вызывает взрыв на 90 урона",
            "Гибель зомби от миньона вызывает взрыв на 135 урона",
            "Гибель зомби от миньона вызывает взрыв на 180 урона",
            "Взрывы на 240 урона с цепной реакцией"
        ],
        apply_per_level=_apply_sum_corpse_explosion
    ),
    UpgradeBase(
        base_id="sum_soul_harvest",
        title="Жатва душ",
        tier="common",
        icon="upg_harvest",
        class_req="summoner",
        level_descs=[
            "+1 дополнительная душа за убийства миньонами",
            "+2 дополнительные души за убийства миньонами",
            "+3 дополнительные души за убийства миньонами",
            "+4 дополнительные души за убийства миньонами",
            "+6 душ за каждое убийство для лагеря"
        ],
        apply_per_level=_apply_sum_harvest
    ),
    UpgradeBase(
        base_id="sum_spectral_shield",
        title="Загробный щит",
        tier="epic",
        icon="upg_spectral_shield",
        class_req="summoner",
        level_descs=[
            "Каждый живой миньон снижает урон герою на 3%",
            "Каждый живой миньон снижает урон герою на 6%",
            "Каждый живой миньон снижает урон герою на 9%",
            "Каждый живой миньон снижает урон герою на 12%",
            "Каждый миньон снижает урон на 15% (до 60% защиты)"
        ],
        apply_per_level=_apply_sum_spectral_shield
    ),
    UpgradeBase(
        base_id="sum_vampiric_bond",
        title="Кровная связь",
        tier="rare",
        icon="upg_vamp_bond",
        class_req="summoner",
        level_descs=[
            "+1.2 HP вампиризма при гибели каждого врага",
            "+2.4 HP вампиризма при гибели каждого врага",
            "+3.6 HP вампиризма при гибели каждого врага",
            "+4.8 HP вампиризма при гибели каждого врага",
            "+6.5 HP вампиризма за павшего зомби"
        ],
        apply_per_level=_apply_sum_vamp_bond
    ),
]


# ===========================================================================
# Lookup structures and ALL_UPGRADES generator
# ===========================================================================

CLASS_BASES_MAP: Dict[str, List[UpgradeBase]] = {
    "warrior": WARRIOR_BASES,
    "ranger": RANGER_BASES,
    "mage": MAGE_BASES,
    "summoner": SUMMONER_BASES,
}

ALL_BASES: List[UpgradeBase] = COMMON_BASES.copy()
for _b_list in CLASS_BASES_MAP.values():
    ALL_BASES.extend(_b_list)

ALL_UPGRADES: List[UpgradeCard] = []
for _base in ALL_BASES:
    for _lvl in range(1, 6):
        ALL_UPGRADES.append(_base.get_card(_lvl))


# ===========================================================================
# Progression & Wave Selection Algorithm
# ===========================================================================

def get_available_upgrades(player: Any, wave: int, count: int = 3) -> List[UpgradeCard]:
    """
    Selects up to `count` upgrades according to run progression:
    - ONLY offers Common upgrades + Player's specific class upgrades (NO cross-class!)
    - If player hasn't reached max level (5), offers the next level (or rare early jump)
    - Early waves (1-2) offer mostly Common/Rare Level 1 (and rarely Level 2)
    - Later waves offer higher tiers and higher levels
    - Never offers upgrades that are already at Level 5
    """
    player_class = getattr(player, "class_type", "warrior")
    if not hasattr(player, "upgrade_levels"):
        player.upgrade_levels = {}

    # 1. Collect eligible bases (Common + Player's Class)
    eligible_bases: List[UpgradeBase] = list(COMMON_BASES)
    class_bases = CLASS_BASES_MAP.get(player_class, WARRIOR_BASES)
    eligible_bases.extend(class_bases)

    # 2. Filter out maxed out upgrades (level >= 5)
    unmaxed_bases = [b for b in eligible_bases if player.upgrade_levels.get(b.base_id, 0) < 5]
    if not unmaxed_bases:
        # All upgrades maxed out! Fallback to common vitality or damage if available
        unmaxed_bases = eligible_bases

    # 3. Determine tier weights based on wave progression
    if wave <= 2:
        tier_weights = UpgradeBalance.TIER_WEIGHTS_WAVE_1_2
    elif wave <= 4:
        tier_weights = UpgradeBalance.TIER_WEIGHTS_WAVE_3_4
    elif wave <= 6:
        tier_weights = UpgradeBalance.TIER_WEIGHTS_WAVE_5_6
    else:
        tier_weights = UpgradeBalance.TIER_WEIGHTS_WAVE_LATE

    # 4. Weight each base
    def get_base_weight(b: UpgradeBase) -> float:
        w = float(tier_weights.get(b.tier, 30))
        # Slightly prioritize upgrades the player has already invested in to build synergy
        curr_lvl = player.upgrade_levels.get(b.base_id, 0)
        if 1 <= curr_lvl < 5:
            w *= UpgradeBalance.INVESTED_UPGRADE_WEIGHT_MULTI
        return max(1.0, w)

    # 5. Pick up to `count` distinct bases without replacement
    candidates = list(unmaxed_bases)
    picked_bases: List[UpgradeBase] = []

    for _ in range(min(count, len(candidates))):
        weights = [get_base_weight(b) for b in candidates]
        total_w = sum(weights)
        if total_w <= 0:
            picked = random.choice(candidates)
        else:
            picked = random.choices(candidates, weights=weights, k=1)[0]
        picked_bases.append(picked)
        candidates.remove(picked)

    # 6. For each picked base, determine the offered level
    result_cards: List[UpgradeCard] = []
    for b in picked_bases:
        curr_lvl = player.upgrade_levels.get(b.base_id, 0)
        if curr_lvl > 0:
            # Player already owns this upgrade: offer the next level (clamped to max_level)
            offered_lvl = min(b.max_level, curr_lvl + 1)
        else:
            # Fresh new upgrade:
            # Early waves (wave 1-2): 88% chance Level 1, 12% rare chance Level 2
            # Later waves: higher starting level chances for late-game catchup
            roll = random.random()
            if wave <= 2:
                offered_lvl = 2 if roll < 0.12 else 1
            elif wave <= 4:
                offered_lvl = 2 if roll < 0.28 else 1
            else:
                if roll < 0.20:
                    offered_lvl = 3
                elif roll < 0.60:
                    offered_lvl = 2
                else:
                    offered_lvl = 1

        card = b.get_card(offered_lvl)
        result_cards.append(card)

    return result_cards
