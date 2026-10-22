"""
Конфигурация, игровой баланс и системные настройки игры «Рыцарь против Зомби».
Все параметры баланса игроков, классов, врагов, снарядов, экономики
и прогрессии централизованы здесь в структурированных секциях.
"""

import os
import sys
from typing import Tuple, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


# =====================================================================
# ПУТИ И СИСТЕМНЫЕ УТИЛИТЫ СРЕДЫ ВЫПОЛНЕНИЯ
# =====================================================================
def get_base_dir() -> str:
    """Возвращает базовую директорию проекта, совместимую с бандлами PyInstaller."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path: str) -> str:
    """Корректно разрешает путь к ресурсам в dev-режиме и в скомпилированном exe."""
    base = get_base_dir()
    return os.path.normpath(os.path.join(base, relative_path))


def get_save_path(filename: str = "save_data.json") -> str:
    """
    Возвращает путь к файлу сохранений. В frozen-режиме пробует записать рядом с exe
    (портативный режим); если запись запрещена, использует %APPDATA%/KnightVsZombies.
    """
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        test_file = os.path.join(exe_dir, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            return os.path.join(exe_dir, filename)
        except Exception:
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            save_dir = os.path.join(appdata, "KnightVsZombies")
            os.makedirs(save_dir, exist_ok=True)
            return os.path.join(save_dir, filename)
    else:
        return os.path.join(get_base_dir(), filename)


# =====================================================================
# 1. ГЕОМЕТРИЯ ЭКРАНА И АРЕНЫ
# =====================================================================
class DisplayConfig:
    WINDOW_WIDTH: int = 1280
    WINDOW_HEIGHT: int = 720
    FPS: int = 60
    TITLE: str = "Рыцарь против Зомби (Knight vs Zombies)"

    # Поле боя и арена (50x50 клеток по 32x32 px = арена 1600x1600 px)
    FIELD_SIZE: Tuple[int, int] = (50, 50)
    TILE_SIZE: int = 32
    ARENA_MIN_X: int = 64
    ARENA_MIN_Y: int = 64
    ARENA_MAX_X: int = 1536
    ARENA_MAX_Y: int = 1536

    # Цветовая палитра арены
    COLOR_BG: Tuple[int, int, int] = (14, 17, 23)
    COLOR_BORDER: Tuple[int, int, int] = (31, 36, 45)
    COLOR_TILE_A: Tuple[int, int, int] = (20, 24, 32)
    COLOR_TILE_B: Tuple[int, int, int] = (24, 29, 38)


# =====================================================================
# 2. БАЛАНС ИГРОКА И КЛАССОВ
# =====================================================================
class PlayerBaseBalance:
    MAX_HP: float = 300.0
    SPEED: float = 195.0
    RADIUS: float = 18.0
    REGEN_RATE: float = 1.0        # Восстановление HP в секунду
    MAGNET_RANGE: float = 100.0    # Радиус притяжения сфер опыта
    DASH_COOLDOWN: float = 1.3
    DASH_DURATION: float = 0.22
    DASH_SPEED: float = 540.0


class WarriorBalance:
    HP: float = 300.0
    SPEED: float = 195.0
    RADIUS: float = 18.0
    DASH_COOLDOWN: float = 1.30

    # Навык 1: Взмах мечом (ближний сектор)
    ATK1_COOLDOWN: float = 0.26
    ATK1_DAMAGE: int = 35
    ATK1_RANGE: float = 85.0
    ATK1_ARC: float = 1.15  # Полуугол сектора в радианах

    # Навык 2: Вихрь (круговой удар на 360°)
    ATK2_COOLDOWN: float = 1.80
    ATK2_DAMAGE: int = 70
    ATK2_RANGE: float = 115.0

    # Навык 3: Клинок ветра (пронзающий снаряд)
    ATK3_COOLDOWN: float = 3.20
    ATK3_DAMAGE: int = 110
    ATK3_RANGE: float = 580.0
    ATK3_SPEED: float = 460.0


class RangerBalance:
    HP: float = 230.0
    SPEED: float = 218.0
    RADIUS: float = 18.0
    DASH_COOLDOWN: float = 1.10

    # Навык 1: Выстрел стрелой
    ATK1_COOLDOWN: float = 0.22
    ATK1_DAMAGE: int = 45
    ATK1_SPEED: float = 660.0
    ATK1_RANGE: float = 680.0

    # Навык 2: Веер стрел (мультивыстрел)
    ATK2_COOLDOWN: float = 1.60
    ATK2_DAMAGE: int = 38
    ATK2_SPEED: float = 600.0
    ATK2_RANGE: float = 540.0
    ATK2_ARROWS: int = 5

    # Навык 3: Разрывная стрела
    ATK3_COOLDOWN: float = 3.00
    ATK3_DAMAGE: int = 120
    ATK3_SPEED: float = 540.0
    ATK3_RANGE: float = 620.0
    ATK3_BLAST_RADIUS: float = 80.0


class MageBalance:
    HP: float = 205.0
    SPEED: float = 190.0
    RADIUS: float = 18.0
    DASH_COOLDOWN: float = 1.35
    BLINK_DISTANCE: float = 190.0

    # Навык 1: Стрела чар
    ATK1_COOLDOWN: float = 0.25
    ATK1_DAMAGE: int = 40
    ATK1_SPEED: float = 530.0

    # Навык 2: Огненный шар
    ATK2_COOLDOWN: float = 1.85
    ATK2_DAMAGE: int = 85
    ATK2_SPEED: float = 420.0
    ATK2_RANGE: float = 580.0
    ATK2_BLAST_RADIUS: float = 75.0

    # Навык 3: Кольцо мороза
    ATK3_COOLDOWN: float = 3.20
    ATK3_DAMAGE: int = 95
    ATK3_RADIUS: float = 135.0


class SummonerBalance:
    HP: float = 245.0
    SPEED: float = 195.0
    RADIUS: float = 18.0
    DASH_COOLDOWN: float = 1.30
    MAX_MINIONS: int = 4

    # Навык 1: Хлыст душ
    ATK1_COOLDOWN: float = 0.28
    ATK1_DAMAGE: int = 35
    ATK1_RANGE: float = 95.0

    # Навык 2: Призыв скелетов
    ATK2_COOLDOWN: float = 2.40

    # Навык 3: Взрыв душ
    ATK3_COOLDOWN: float = 3.30
    ATK3_DAMAGE: int = 110
    ATK3_SPEED: float = 460.0
    ATK3_RANGE: float = 550.0


class MinionBalance:
    BASE_HP: float = 85.0
    BASE_SPEED: float = 210.0
    BASE_DAMAGE: float = 22.0
    ATTACK_RADIUS: float = 12.0
    COLOSSUS_RADIUS: float = 17.0
    COLOSSUS_HP_MULTI: float = 2.2
    COLOSSUS_DMG_MULTI: float = 2.0


# =====================================================================
# 3. БАЛАНС ЗОМБИ И ВОЛН
# =====================================================================
class ZombieWaveBalance:
    SPAWN_INTERVAL_BASE: float = 1.2
    SPAWN_INTERVAL_MIN: float = 0.35
    HP_SCALE_PER_WAVE: float = 0.10     # +10% HP за каждую волну
    DMG_SCALE_PER_WAVE: float = 0.06    # +6% урона за каждую волну
    BOSS_WAVE_HP_MULTI: float = 1.25    # +25% HP на босс-волнах (5, 10, 15...)


ZOMBIE_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "runner": {
        "radius": 15.0,
        "max_hp": 40.0,
        "speed": 165.0,
        "damage": 10.0,
        "color": (193, 18, 31),
        "xp_value": 18,
        "score_value": 70,
        "souls_value": 2,
    },
    "brute": {
        "radius": 28.0,
        "max_hp": 240.0,
        "speed": 70.0,
        "damage": 32.0,
        "color": (45, 106, 79),
        "xp_value": 55,
        "score_value": 150,
        "souls_value": 5,
    },
    "spitter": {
        "radius": 16.0,
        "max_hp": 60.0,
        "speed": 95.0,
        "damage": 14.0,
        "color": (112, 224, 0),
        "xp_value": 28,
        "score_value": 90,
        "souls_value": 2,
        "spit_cooldown": 2.4,
    },
    "walker": {
        "radius": 17.0,
        "max_hp": 65.0,
        "speed": 95.0,
        "damage": 15.0,
        "color": (82, 183, 136),
        "xp_value": 14,
        "score_value": 40,
        "souls_value": 1,
    },
}


# =====================================================================
# 4. БАЛАНС СНАРЯДОВ
# =====================================================================
class ProjectileBalance:
    # Клинок ветра (Воин)
    WINDBLADE_RANGE: float = 580.0
    WINDBLADE_SPEED: float = 460.0
    WINDBLADE_RADIUS: float = 12.0
    WINDBLADE_PIERCE: int = 8

    # Стрела (Лучник)
    ARROW_SPEED: float = 660.0
    ARROW_RANGE: float = 680.0
    ARROW_RADIUS: float = 6.0

    # Разрывная стрела (Лучник)
    EXPLOSIVE_ARROW_SPEED: float = 540.0
    EXPLOSIVE_ARROW_RANGE: float = 620.0
    EXPLOSIVE_ARROW_BLAST_RADIUS: float = 80.0
    EXPLOSIVE_ARROW_RADIUS: float = 8.0

    # Стрела чар (Маг)
    ARCANE_BOLT_SPEED: float = 530.0
    ARCANE_BOLT_RANGE: float = 650.0
    ARCANE_BOLT_RADIUS: float = 10.0
    ARCANE_BOLT_PIERCE: int = 2

    # Огненный шар (Маг)
    FIREBALL_SPEED: float = 420.0
    FIREBALL_RANGE: float = 580.0
    FIREBALL_BLAST_RADIUS: float = 75.0
    FIREBALL_RADIUS: float = 14.0

    # Взрыв душ (Призыватель)
    SOUL_WAVE_SPEED: float = 460.0
    SOUL_WAVE_RANGE: float = 550.0
    SOUL_WAVE_RADIUS: float = 15.0
    SOUL_WAVE_PIERCE: int = 6

    # Плевок кислоты (Плюющийся зомби)
    ACID_SPIT_SPEED: float = 230.0
    ACID_SPIT_RANGE: float = 600.0
    ACID_SPIT_DAMAGE: int = 18
    ACID_SPIT_RADIUS: float = 7.0


# =====================================================================
# 5. ЭКОНОМИКА И ПРОГРЕССИЯ (ДУШИ, ОПЫТ, ПРОКАЧКА ЛАГЕРЯ)
# =====================================================================
class EconomyBalance:
    # Души
    BONUS_SOULS_PER_WAVE: int = 2

    # Сферы опыта
    EXP_ORB_RADIUS: float = 5.0
    EXP_ORB_BASE_SPEED: float = 380.0
    EXP_ORB_DEFAULT_VALUE: int = 15

    # Прогрессия уровней героя в забеге (XP)
    XP_BASE_FIRST_LEVEL: int = 100       # Базовый опыт для перехода на 2-й уровень
    XP_SCALE_PER_LEVEL: float = 1.20     # Множитель увеличения требуемого опыта за каждый уровень (рост на +20%)

    # Мета-улучшения в лагере
    CAMP_UPGRADES = {
        "speed": {
            "stat": "speed",
            "title": "Скорость",
            "desc_template": "+{val}% к скорости перемещения",
            "val_per_lvl": 6,
            "max_level": 5,
            "base_cost": 20,
            "cost_multiplier": 1.55,
            "icon": "speed_boost",
        },
        "hp": {
            "stat": "hp",
            "title": "Здоровье",
            "desc_template": "+{val} к максимальному здоровью",
            "val_per_lvl": 25,
            "max_level": 5,
            "base_cost": 25,
            "cost_multiplier": 1.60,
            "icon": "hp_boost",
        },
        "damage": {
            "stat": "damage",
            "title": "Урон",
            "desc_template": "+{val}% к урону всех атак",
            "val_per_lvl": 8,
            "max_level": 5,
            "base_cost": 30,
            "cost_multiplier": 1.65,
            "icon": "damage_boost",
        },
    }


# =====================================================================
# 6. БАЛАНС ИГРОВЫХ УЛУЧШЕНИЙ (LEVEL-UP UPGRADES)
# =====================================================================
class UpgradeBalance:
    # Веса редкостей по волнам
    TIER_WEIGHTS_WAVE_1_2: Dict[str, int] = {"common": 75, "rare": 23, "epic": 2}
    TIER_WEIGHTS_WAVE_3_4: Dict[str, int] = {"common": 48, "rare": 42, "epic": 10}
    TIER_WEIGHTS_WAVE_5_6: Dict[str, int] = {"common": 28, "rare": 48, "epic": 24}
    TIER_WEIGHTS_WAVE_LATE: Dict[str, int] = {"common": 16, "rare": 44, "epic": 40}

    # Множитель приоритета уже начатых улучшений
    INVESTED_UPGRADE_WEIGHT_MULTI: float = 1.35

    # 1. ОБЩИЕ УЛУЧШЕНИЯ (5 шт.)
    COMMON_DMG_SHARP = [0.08, 0.16, 0.24, 0.32, 0.45]
    COMMON_VITALITY_HP = [35.0, 70.0, 105.0, 140.0, 180.0]
    COMMON_SWIFTNESS_SPD = [0.07, 0.14, 0.21, 0.28, 0.38]
    COMMON_MAGNET_RANGE = [45.0, 90.0, 135.0, 180.0, 240.0]
    COMMON_HASTE_CDR = [0.08, 0.16, 0.24, 0.32, 0.42]

    # 2. УЛУЧШЕНИЯ ВОИНА / РЫЦАРЯ (10 шт.)
    WAR_CLEAVE_AREA = [0.12, 0.24, 0.36, 0.48, 0.65]
    WAR_IRON_SKIN_DMG_RED = [0.06, 0.12, 0.18, 0.24, 0.32]
    WAR_IRON_SKIN_HP = [20.0, 40.0, 60.0, 80.0, 120.0]
    WAR_WHIRLWIND_DMG = [0.20, 0.40, 0.60, 0.80, 1.10]
    WAR_WHIRLWIND_AREA = [0.06, 0.12, 0.18, 0.24, 0.30]
    WAR_WIND_BLADE_DMG = [0.25, 0.50, 0.75, 1.00, 1.40]
    WAR_THORNS = [16.0, 32.0, 48.0, 64.0, 90.0]
    WAR_VAMPIRISM = [1.4, 2.8, 4.2, 5.6, 7.5]
    WAR_BERSERK_DMG = [0.20, 0.40, 0.60, 0.80, 1.20]
    WAR_DASH_SMASH_DMG = [45.0, 90.0, 135.0, 180.0, 240.0]
    WAR_HOLY_REGEN = [1.2, 2.4, 3.6, 4.8, 6.5]
    WAR_EXECUTIONER_CRIT = [0.08, 0.16, 0.24, 0.32, 0.45]

    # 3. УЛУЧШЕНИЯ ЛУЧНИКА / СТРЕЛКА (10 шт.)
    RNG_ARROW_DMG = [0.10, 0.20, 0.30, 0.40, 0.55]
    RNG_ARROW_SPD = [0.15, 0.30, 0.45, 0.60, 0.80]
    RNG_PIERCE = [1, 2, 3, 4, 5]
    RNG_MULTISHOT = [1, 2, 3, 4, 6]
    RNG_EXPLOSIVE_DMG = [0.25, 0.50, 0.75, 1.00, 1.40]
    RNG_EXPLOSIVE_AREA = [0.08, 0.16, 0.24, 0.32, 0.45]
    RNG_EAGLE_EYE_CRIT = [0.09, 0.18, 0.27, 0.36, 0.50]
    RNG_EAGLE_EYE_MAGNET = [25.0, 50.0, 75.0, 100.0, 140.0]
    RNG_ACROBAT_CDR = [0.12, 0.24, 0.36, 0.48, 0.60]
    RNG_ACROBAT_SPD = [0.04, 0.08, 0.12, 0.16, 0.22]
    RNG_POISON_DPS = [20.0, 40.0, 60.0, 80.0, 120.0]
    RNG_RICOCHET = [1, 2, 3, 4, 5]
    RNG_HUNTER_DMG = [0.06, 0.12, 0.18, 0.24, 0.35]
    RNG_HUNTER_CDR = [0.06, 0.12, 0.18, 0.24, 0.35]
    RNG_HUNTER_SPD = [0.03, 0.06, 0.09, 0.12, 0.18]

    # 4. УЛУЧШЕНИЯ МАГА (10 шт.)
    MAGE_ARCANE_DMG = [0.11, 0.22, 0.33, 0.44, 0.60]
    MAGE_FIREBALL_DMG = [0.25, 0.50, 0.75, 1.00, 1.40]
    MAGE_FIREBALL_AREA = [0.07, 0.14, 0.21, 0.28, 0.40]
    MAGE_FROST_NOVA_RADIUS = [0.18, 0.36, 0.54, 0.72, 0.95]
    MAGE_BLINK_BLAST_DMG = [40.0, 80.0, 120.0, 160.0, 220.0]
    MAGE_MANA_SHIELD_AMOUNT = [35.0, 70.0, 105.0, 140.0, 190.0]
    MAGE_MANA_SHIELD_HP = [20.0, 40.0, 60.0, 80.0, 120.0]
    MAGE_ARCANE_BARRAGE_EXTRA = [1, 2, 3, 4, 5]
    MAGE_SPELL_HASTE_CDR = [0.09, 0.18, 0.27, 0.36, 0.48]
    MAGE_LIGHTNING_TARGETS = [1, 2, 3, 4, 6]
    MAGE_SUPERNOVA_AREA = [0.15, 0.30, 0.45, 0.60, 0.85]
    MAGE_SIPHON_VAMPIRISM = [1.5, 3.0, 4.5, 6.0, 8.0]

    # 5. УЛУЧШЕНИЯ ПРИЗЫВАТЕЛЯ (10 шт.)
    SUM_MINION_DMG = [0.18, 0.36, 0.54, 0.72, 0.95]
    SUM_HERO_DMG_BONUS = [0.05, 0.10, 0.15, 0.20, 0.30]
    SUM_ARMY_EXTRA = [1, 2, 3, 4, 5]
    SUM_MINION_HP = [0.25, 0.50, 0.75, 1.00, 1.40]
    SUM_MINION_SPD = [0.15, 0.30, 0.45, 0.60, 0.80]
    SUM_SOUL_BURST_EXTRA = [1, 2, 3, 4, 6]
    SUM_SPIRIT_WHIP_DMG = [0.10, 0.20, 0.30, 0.40, 0.55]
    SUM_SPIRIT_WHIP_AREA = [0.08, 0.16, 0.24, 0.32, 0.45]
    SUM_CORPSE_EXPLOSION_DMG = [45.0, 90.0, 135.0, 180.0, 240.0]
    SUM_SOUL_HARVEST_SOULS = [1, 2, 3, 4, 6]
    SUM_SPECTRAL_SHIELD_DEF = [0.03, 0.06, 0.09, 0.12, 0.15]
    SUM_VAMP_BOND_VAMPIRISM = [1.2, 2.4, 3.6, 4.8, 6.5]


# =====================================================================
# 7. ЕДИНЫЙ ОБЪЕКТ НАСТРОЕК (ДЛЯ ПОЛНОЙ ОБРАТНОЙ СОВМЕСТИМОСТИ)
# =====================================================================
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Экран и арена
    WINDOW_WIDTH: int = DisplayConfig.WINDOW_WIDTH
    WINDOW_HEIGHT: int = DisplayConfig.WINDOW_HEIGHT
    FPS: int = DisplayConfig.FPS
    TITLE: str = DisplayConfig.TITLE

    FIELD_SIZE: Tuple[int, int] = DisplayConfig.FIELD_SIZE
    TILE_SIZE: int = DisplayConfig.TILE_SIZE
    ARENA_MIN_X: int = DisplayConfig.ARENA_MIN_X
    ARENA_MIN_Y: int = DisplayConfig.ARENA_MIN_Y
    ARENA_MAX_X: int = DisplayConfig.ARENA_MAX_X
    ARENA_MAX_Y: int = DisplayConfig.ARENA_MAX_Y

    # Цветовая палитра
    COLOR_BG: Tuple[int, int, int] = DisplayConfig.COLOR_BG
    COLOR_BORDER: Tuple[int, int, int] = DisplayConfig.COLOR_BORDER
    COLOR_TILE_A: Tuple[int, int, int] = DisplayConfig.COLOR_TILE_A
    COLOR_TILE_B: Tuple[int, int, int] = DisplayConfig.COLOR_TILE_B

    # Базовые параметры игрока
    PLAYER_MAX_HP: float = PlayerBaseBalance.MAX_HP
    PLAYER_SPEED: float = PlayerBaseBalance.SPEED
    PLAYER_RADIUS: float = PlayerBaseBalance.RADIUS
    PLAYER_REGEN_RATE: float = PlayerBaseBalance.REGEN_RATE
    PLAYER_MAGNET_RANGE: float = PlayerBaseBalance.MAGNET_RANGE

    DASH_COOLDOWN: float = PlayerBaseBalance.DASH_COOLDOWN
    DASH_DURATION: float = PlayerBaseBalance.DASH_DURATION
    DASH_SPEED: float = PlayerBaseBalance.DASH_SPEED

    # Волны зомби
    ZOMBIE_SPAWN_INTERVAL_BASE: float = ZombieWaveBalance.SPAWN_INTERVAL_BASE
    ZOMBIE_SPAWN_INTERVAL_MIN: float = ZombieWaveBalance.SPAWN_INTERVAL_MIN
    ZOMBIE_HP_SCALE_PER_WAVE: float = ZombieWaveBalance.HP_SCALE_PER_WAVE
    ZOMBIE_DMG_SCALE_PER_WAVE: float = ZombieWaveBalance.DMG_SCALE_PER_WAVE
    ZOMBIE_BOSS_WAVE_HP_MULTI: float = ZombieWaveBalance.BOSS_WAVE_HP_MULTI

    # Миньоны
    MINION_BASE_HP: float = MinionBalance.BASE_HP
    MINION_BASE_SPEED: float = MinionBalance.BASE_SPEED
    MINION_BASE_DAMAGE: float = MinionBalance.BASE_DAMAGE

    # Души
    BONUS_SOULS_PER_WAVE: int = EconomyBalance.BONUS_SOULS_PER_WAVE


# Синглтон настроек
settings = Settings()
