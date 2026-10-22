"""
Полиморфные классы игровых персонажей:
1. Warrior (Воин / Рыцарь) - Ближнебойный танк, удары мечом, круговой вихрь, клинок ветра
2. Ranger (Стрелок / Лучник) - Высокая мобильность, одиночный выстрел, веер стрел, разрывная стрела
3. Mage (Маг / Архимаг) - Стеклянная пушка, чародейская стрела, огненный шар, кольцо мороза, телепортация
4. Summoner (Призыватель / Некромант) - Хлыст душ, активные миньоны-скелеты, взрыв душ, бесплотный шаг
"""

import math
import random
from typing import List, Tuple, Dict, Any, Optional
import pygame
from .base import Entity
from .projectile import (
    WindBladeProjectile,
    ArrowProjectile,
    ExplosiveArrowProjectile,
    ArcaneBoltProjectile,
    FireballProjectile,
    SoulWaveProjectile,
)
from .minion import Minion
from ..config import (
    settings,
    PlayerBaseBalance,
    WarriorBalance,
    RangerBalance,
    MageBalance,
    SummonerBalance,
    EconomyBalance,
)


# XP Progression Defaults
XP_BASE_FIRST_LEVEL: int = EconomyBalance.XP_BASE_FIRST_LEVEL
XP_SCALE_PER_LEVEL: float = EconomyBalance.XP_SCALE_PER_LEVEL


class GhostAfterimage:
    def __init__(self, x: float, y: float, angle: float, life: float = 0.18, color: Tuple[int, int, int] = (72, 202, 228)):
        self.x = x
        self.y = y
        self.angle = angle
        self.max_life = life
        self.life = life
        self.color = color


class BasePlayer(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        class_type: str,
        class_name: str,
        class_icon: str,
        base_hp: float,
        base_speed: float,
        radius: float = PlayerBaseBalance.RADIUS,
        regen_rate: float = PlayerBaseBalance.REGEN_RATE,
        magnet_range: float = PlayerBaseBalance.MAGNET_RANGE,
        dash_cooldown: float = PlayerBaseBalance.DASH_COOLDOWN,
        dash_duration: float = PlayerBaseBalance.DASH_DURATION,
        dash_speed: float = PlayerBaseBalance.DASH_SPEED,
    ):
        super().__init__(x, y, radius=radius)
        self.class_type = class_type
        self.class_name = class_name
        self.class_icon = class_icon
        self.facing_angle = 0.0

        # Характеристики
        self.base_speed = float(base_speed)
        self.max_hp = float(base_hp)
        self.hp = float(self.max_hp)
        self.speed = float(base_speed)
        self.regen_rate = float(regen_rate)
        self.regen_timer = 0.0
        self.magnet_range = float(magnet_range)
        self.vampirism = 0.0
        self.thorns = 0.0
        self.crit_chance_bonus = 0.0
        self.damage_reduction = 0.0
        self.dash_damage = 0.0
        self.dash_cooldown_reduction = 0.0
        self.mana_shield_max = 0.0
        self.mana_shield = 0.0
        self.dash_hit_zombies = set()

        # Баффы мастерства классов
        self.can_deflect_projectiles = False
        self.barrier_orbs_active = False
        self.barrier_orbs = 0
        self.barrier_respawn_timer = 0.0
        self.barrier_orbit_angle = 0.0

        # Множители характеристик (от улучшений)
        self.cooldown_multi = 1.0
        self.damage_multi = 1.0
        self.area_multi = 1.0

        # Уровень и опыт
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = XP_BASE_FIRST_LEVEL
        self.upgrade_levels: Dict[str, int] = {}

        # Базовые таймеры и длительности способностей
        self.atk1_cooldown = 0.0
        self.atk1_timer = 0.0
        self.atk1_anim_timer = 0.0
        self.atk1_anim_duration = 0.16

        self.atk2_cooldown = 0.0
        self.atk2_timer = 0.0
        self.atk2_anim_timer = 0.0
        self.atk2_anim_duration = 0.28

        self.atk3_cooldown = 0.0
        self.atk3_timer = 0.0
        self.atk3_anim_timer = 0.0
        self.atk3_anim_duration = 0.20

        # Рывок / Перекат / Телепорт
        self.dash_cooldown = float(dash_cooldown)
        self.dash_duration = float(dash_duration)
        self.dash_speed = float(dash_speed)
        self.dash_timer = 0.0
        self.is_dashing = False
        self.dash_current_time = 0.0
        self.dash_vx = 0.0
        self.dash_vy = 0.0
        self.ghost_trail: List[GhostAfterimage] = []

        # Неуязвимость и анимация шага
        self.invulnerable_timer = 0.0
        self.walk_cycle = 0.0

        # Описания слотов навыков для UI (название, хоткей, иконка, описание)
        self.skill_descriptions: List[Tuple[str, str, str, str]] = []

    def get_crit_chance(self, base_chance: float = 0.20) -> float:
        return min(0.85, base_chance + getattr(self, "crit_chance_bonus", 0.0))

    def get_damage_multiplier(self) -> float:
        multi = self.damage_multi
        # Берсерк воина: дополнительный урон при здоровье ниже 50%
        if getattr(self, "berserk_bonus", 0.0) > 0 and self.hp < (self.max_hp * 0.5):
            multi += self.berserk_bonus
        return multi

    def update(self, dt: float, move_x: float, move_y: float, aim_angle: float, sound_engine, particles: list = None) -> None:
        if self.dead:
            return

        self.regen_timer += dt
        if self.regen_timer >= 1.0:
            self.regen_timer = 0.0
            if self.hp < self.max_hp:
                self.hp = min(self.max_hp, self.hp + self.regen_rate)

        # Пассивная регенерация щита маны (Маг)
        if getattr(self, "mana_shield_max", 0.0) > 0 and getattr(self, "mana_shield", 0.0) < self.mana_shield_max:
            self.mana_shield = min(self.mana_shield_max, self.mana_shield + 8.0 * dt)

        if self.atk1_timer > 0: self.atk1_timer -= dt
        if self.atk2_timer > 0: self.atk2_timer -= dt
        if self.atk3_timer > 0: self.atk3_timer -= dt
        if self.dash_timer > 0: self.dash_timer -= dt
        if self.invulnerable_timer > 0: self.invulnerable_timer -= dt

        # Обновление защитных сфер (Мастерство мага: 3 вращающиеся сферы)
        if getattr(self, "barrier_orbs_active", False):
            self.barrier_orbit_angle = (getattr(self, "barrier_orbit_angle", 0.0) + dt * 2.8) % (math.pi * 2)
            if getattr(self, "barrier_orbs", 0) <= 0:
                self.barrier_respawn_timer = getattr(self, "barrier_respawn_timer", 0.0) - dt
                if self.barrier_respawn_timer <= 0:
                    self.barrier_orbs = 3
                    self.barrier_respawn_timer = 0.0

        if self.atk1_anim_timer > 0: self.atk1_anim_timer -= dt
        if self.atk2_anim_timer > 0: self.atk2_anim_timer -= dt
        if self.atk3_anim_timer > 0: self.atk3_anim_timer -= dt

        self.facing_angle = aim_angle

        if self.is_dashing:
            self.dash_current_time -= dt
            self.x += self.dash_vx * dt
            self.y += self.dash_vy * dt

            trail_col = (180, 100, 255) if self.class_type == "mage" else (
                (80, 240, 180) if self.class_type == "summoner" else (
                    (116, 198, 157) if self.class_type == "ranger" else (72, 202, 228)
                )
            )
            self.ghost_trail.append(GhostAfterimage(self.x, self.y, self.facing_angle, 0.18, color=trail_col))

            if self.dash_current_time <= 0:
                self.is_dashing = False
                self.dash_hit_zombies.clear()
        else:
            if move_x != 0 or move_y != 0:
                length = math.hypot(move_x, move_y)
                if length > 0.001:
                    norm_x = move_x / length
                    norm_y = move_y / length
                else:
                    norm_x, norm_y = 0.0, 0.0

                self.x += norm_x * self.speed * dt
                self.y += norm_y * self.speed * dt
                self.walk_cycle += dt * 14.0

                if particles is not None and random.random() < 0.25 and len(particles) < 300:
                    from ..rendering.effects import Particle
                    particles.append(Particle(
                        self.x, self.y + 12,
                        -norm_x * 20 + random.uniform(-10, 10),
                        -norm_y * 20 + random.uniform(-10, 10),
                        (85, 91, 110), 3.0, 0.25
                    ))

        # Clamp arena bounds
        min_x = settings.ARENA_MIN_X + self.radius
        max_x = settings.ARENA_MAX_X - self.radius
        min_y = settings.ARENA_MIN_Y + self.radius
        max_y = settings.ARENA_MAX_Y - self.radius
        self.x = max(min_x, min(max_x, self.x))
        self.y = max(min_y, min(max_y, self.y))

        for g in list(self.ghost_trail):
            g.life -= dt
            if g.life <= 0:
                self.ghost_trail.remove(g)

    def trigger_dash(self, move_x: float, move_y: float, sound_engine, *args, **kwargs) -> bool:
        if self.dash_timer > 0:
            return False

        if move_x == 0 and move_y == 0:
            dx = math.cos(self.facing_angle)
            dy = math.sin(self.facing_angle)
        else:
            length = math.hypot(move_x, move_y)
            dx = move_x / length
            dy = move_y / length

        self.is_dashing = True
        self.dash_current_time = self.dash_duration
        dash_speed = self.dash_speed * (1.1 if self.class_type == "ranger" else 1.0)
        self.dash_vx = dx * dash_speed
        self.dash_vy = dy * dash_speed
        effective_cd = self.dash_cooldown * max(0.30, 1.0 - getattr(self, "dash_cooldown_reduction", 0.0)) * self.cooldown_multi
        self.dash_timer = max(0.30, effective_cd)
        self.invulnerable_timer = self.dash_duration
        self.dash_hit_zombies.clear()
        sound_engine.play_dash()
        return True

    def perform_dash(self, sound_engine, move_x: float = 0.0, move_y: float = 0.0, *args, **kwargs) -> bool:
        """Alias for trigger_dash for unified ability interface."""
        return self.trigger_dash(move_x, move_y, sound_engine, *args, **kwargs)

    def take_damage(self, amount: float, sound_engine, camera, damage_numbers: list = None, particles: list = None) -> None:
        if self.invulnerable_timer > 0 or self.is_dashing or self.dead:
            return

        # Поглощение урона сферами эгиды (Мастерство мага: поглощает одну атаку целиком, кд 15 сек)
        if getattr(self, "barrier_orbs_active", False) and getattr(self, "barrier_orbs", 0) > 0:
            self.barrier_orbs = 0
            self.barrier_respawn_timer = 15.0
            self.invulnerable_timer = 0.40
            if camera: camera.shake(6.0, 0.16)
            if sound_engine and hasattr(sound_engine, "play_teleport"):
                sound_engine.play_teleport()
            if damage_numbers is not None:
                from ..rendering.effects import DamageNumber
                damage_numbers.append(DamageNumber(self.x, self.y - 18, "ПОГЛОЩЕНО!", is_crit=True))
            if particles is not None and len(particles) < 300:
                from ..rendering.effects import Particle
                for _ in range(16):
                    pa = random.uniform(0, math.pi * 2)
                    ps = random.uniform(50, 150)
                    particles.append(Particle(
                        self.x, self.y,
                        math.cos(pa) * ps, math.sin(pa) * ps,
                        (72, 202, 228), 3.5, 0.30, "circle"
                    ))
            return

        # Поглощение урона щитом маны (Маг)
        if getattr(self, "mana_shield", 0.0) > 0:
            absorbed = min(self.mana_shield, amount)
            self.mana_shield -= absorbed
            amount -= absorbed
            if camera: camera.shake(5.0, 0.15)
            sound_engine.play_hit_zombie()
            if amount <= 0:
                self.invulnerable_timer = 0.25
                return

        reduction = getattr(self, "damage_reduction", 0.0)
        if hasattr(self, "minions") and hasattr(self, "damage_reduction_per_minion"):
            reduction += len(self.minions) * getattr(self, "damage_reduction_per_minion", 0.0)
        reduction = min(0.70, reduction)
        amount = max(1.0, amount * (1.0 - reduction))
        self.hp -= amount
        self.invulnerable_timer = 0.40
        camera.shake(12.0, 0.25)
        sound_engine.play_player_hurt()
        if self.hp <= 0:
            self.hp = 0.0
            self.dead = True
            if hasattr(self, "minions"):
                for m in self.minions:
                    m.dead = True
                self.minions.clear()

    def gain_xp(self, amount: int) -> bool:
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(round(self.xp_to_next_level * XP_SCALE_PER_LEVEL))
            return True
        return False

    def draw(self, screen: pygame.Surface, camera) -> None:
        pass


# ==============================================================
# 1. ВОИН / РЫЦАРЬ (WARRIOR)
# ==============================================================
class Warrior(BasePlayer):
    def __init__(
        self,
        x: float,
        y: float,
        hp: float = WarriorBalance.HP,
        speed: float = WarriorBalance.SPEED,
        radius: float = PlayerBaseBalance.RADIUS,
        regen_rate: float = PlayerBaseBalance.REGEN_RATE,
        magnet_range: float = PlayerBaseBalance.MAGNET_RANGE,
        dash_cooldown: float = WarriorBalance.DASH_COOLDOWN,
        dash_duration: float = PlayerBaseBalance.DASH_DURATION,
        dash_speed: float = PlayerBaseBalance.DASH_SPEED,
        atk1_cooldown: float = WarriorBalance.ATK1_COOLDOWN,
        atk1_damage: int = WarriorBalance.ATK1_DAMAGE,
        atk1_range: float = WarriorBalance.ATK1_RANGE,
        atk1_arc: float = WarriorBalance.ATK1_ARC,
        atk2_cooldown: float = WarriorBalance.ATK2_COOLDOWN,
        atk2_damage: int = WarriorBalance.ATK2_DAMAGE,
        atk2_range: float = WarriorBalance.ATK2_RANGE,
        atk3_cooldown: float = WarriorBalance.ATK3_COOLDOWN,
        atk3_damage: int = WarriorBalance.ATK3_DAMAGE,
        atk3_range: float = WarriorBalance.ATK3_RANGE,
        atk3_speed: float = WarriorBalance.ATK3_SPEED,
    ):
        super().__init__(
            x, y,
            class_type="warrior",
            class_name="Воин (Рыцарь)",
            class_icon="🛡️",
            base_hp=hp,
            base_speed=speed,
            radius=radius,
            regen_rate=regen_rate,
            magnet_range=magnet_range,
            dash_cooldown=dash_cooldown,
            dash_duration=dash_duration,
            dash_speed=dash_speed,
        )
        self.atk1_cooldown = float(atk1_cooldown)
        self.atk1_damage = int(atk1_damage)
        self.atk1_range = float(atk1_range)
        self.atk1_arc = float(atk1_arc)

        self.atk2_cooldown = float(atk2_cooldown)
        self.atk2_damage = int(atk2_damage)
        self.atk2_range = float(atk2_range)

        self.atk3_cooldown = float(atk3_cooldown)
        self.atk3_damage = int(atk3_damage)
        self.atk3_range = float(atk3_range)
        self.atk3_speed = float(atk3_speed)

        self.skill_descriptions = [
            ("1. Взмах", "ЛКМ / 1 / Q", "⚔️", f"Быстрый рубящий взмах мечом (урон {self.atk1_damage})"),
            ("2. Вихрь", "ПКМ / 2 / E", "🌪️", f"Круговой удар на 360° с отталкиванием (урон {self.atk2_damage})"),
            ("3. Клинок", "ПРОБЕЛ / 3 / R", "⚡", f"Летящий клинок ветра, пронзает врагов (урон {self.atk3_damage})"),
            ("4. Рывок", "SHIFT / F", "💨", "Рывок сквозь врагов с неуязвимостью"),
        ]

    def perform_attack_1(self, sound_engine) -> bool:
        if self.atk1_timer > 0: return False
        self.atk1_timer = self.atk1_cooldown * self.cooldown_multi
        self.atk1_anim_timer = self.atk1_anim_duration
        sound_engine.play_sword_swing()
        return True

    def perform_attack_2(self, sound_engine) -> bool:
        if self.atk2_timer > 0: return False
        self.atk2_timer = self.atk2_cooldown * self.cooldown_multi
        self.atk2_anim_timer = self.atk2_anim_duration
        sound_engine.play_spin_attack()
        return True

    def perform_attack_3(self, sound_engine, projectiles: list) -> bool:
        if self.atk3_timer > 0: return False
        self.atk3_timer = self.atk3_cooldown * self.cooldown_multi
        self.atk3_anim_timer = self.atk3_anim_duration
        sound_engine.play_wind_blade()

        blade_damage = int(round(self.atk3_damage * self.get_damage_multiplier() * (1.0 + getattr(self, "atk3_damage_bonus", 0.0))))
        speed = self.atk3_speed * (1.35 if getattr(self, "atk3_damage_bonus", 0.0) >= 1.0 else 1.0)
        spawn_x = self.x + math.cos(self.facing_angle) * 22.0
        spawn_y = self.y + math.sin(self.facing_angle) * 22.0

        proj = WindBladeProjectile(
            spawn_x, spawn_y,
            self.facing_angle,
            damage=blade_damage,
            max_range=self.atk3_range * self.area_multi,
            speed=speed
        )
        projectiles.append(proj)
        return True


# ==============================================================
# 2. СТРЕЛОК / ЛУЧНИК (RANGER)
# ==============================================================
class Ranger(BasePlayer):
    def __init__(
        self,
        x: float,
        y: float,
        hp: float = RangerBalance.HP,
        speed: float = RangerBalance.SPEED,
        radius: float = PlayerBaseBalance.RADIUS,
        regen_rate: float = PlayerBaseBalance.REGEN_RATE,
        magnet_range: float = PlayerBaseBalance.MAGNET_RANGE,
        dash_cooldown: float = RangerBalance.DASH_COOLDOWN,
        dash_duration: float = PlayerBaseBalance.DASH_DURATION,
        dash_speed: float = PlayerBaseBalance.DASH_SPEED,
        atk1_cooldown: float = RangerBalance.ATK1_COOLDOWN,
        atk1_damage: int = RangerBalance.ATK1_DAMAGE,
        atk1_speed: float = RangerBalance.ATK1_SPEED,
        atk1_range: float = RangerBalance.ATK1_RANGE,
        atk2_cooldown: float = RangerBalance.ATK2_COOLDOWN,
        atk2_damage: int = RangerBalance.ATK2_DAMAGE,
        atk2_speed: float = RangerBalance.ATK2_SPEED,
        atk2_range: float = RangerBalance.ATK2_RANGE,
        atk2_arrows: int = RangerBalance.ATK2_ARROWS,
        atk3_cooldown: float = RangerBalance.ATK3_COOLDOWN,
        atk3_damage: int = RangerBalance.ATK3_DAMAGE,
        atk3_speed: float = RangerBalance.ATK3_SPEED,
        atk3_range: float = RangerBalance.ATK3_RANGE,
        atk3_blast_radius: float = RangerBalance.ATK3_BLAST_RADIUS,
    ):
        super().__init__(
            x, y,
            class_type="ranger",
            class_name="Стрелок (Лучник)",
            class_icon="🏹",
            base_hp=hp,
            base_speed=speed,
            radius=radius,
            regen_rate=regen_rate,
            magnet_range=magnet_range,
            dash_cooldown=dash_cooldown,
            dash_duration=dash_duration,
            dash_speed=dash_speed,
        )
        self.atk1_cooldown = float(atk1_cooldown)
        self.atk1_damage = int(atk1_damage)
        self.atk1_speed = float(atk1_speed)
        self.atk1_range = float(atk1_range)

        self.atk2_cooldown = float(atk2_cooldown)
        self.atk2_damage = int(atk2_damage)
        self.atk2_speed = float(atk2_speed)
        self.atk2_range = float(atk2_range)
        self.atk2_arrows = int(atk2_arrows)

        self.atk3_cooldown = float(atk3_cooldown)
        self.atk3_damage = int(atk3_damage)
        self.atk3_speed = float(atk3_speed)
        self.atk3_range = float(atk3_range)
        self.atk3_blast_radius = float(atk3_blast_radius)

        self.skill_descriptions = [
            ("1. Выстрел", "ЛКМ / 1 / Q", "🏹", f"Стремительный выстрел стрелой (урон {self.atk1_damage})"),
            ("2. Веер стрел", "ПКМ / 2 / E", "🎯", f"Веер из {self.atk2_arrows} пробивающих стрел конусом (урон {self.atk2_damage})"),
            ("3. Разрывная", "ПРОБЕЛ / 3 / R", "💣", f"Взрывная стрела с мощным огненным взрывом (урон {self.atk3_damage})"),
            ("4. Перекат", "SHIFT / F", "🏃", "Быстрый перекат с уворотом от ударов"),
        ]

    def perform_attack_1(self, sound_engine, projectiles: list = None) -> bool:
        if self.atk1_timer > 0 or projectiles is None: return False
        self.atk1_timer = self.atk1_cooldown * self.cooldown_multi
        self.atk1_anim_timer = 0.14
        sound_engine.play_bow_shoot()

        dmg = int(round(self.atk1_damage * self.get_damage_multiplier()))
        spawn_x = self.x + math.cos(self.facing_angle) * 20.0
        spawn_y = self.y + math.sin(self.facing_angle) * 20.0
        pierce = 1 + getattr(self, "arrow_pierce_bonus", 0)
        speed = self.atk1_speed * getattr(self, "projectile_speed_multi", 1.0)
        poison_dmg = getattr(self, "poison_damage", 0.0)
        ricochet = getattr(self, "ricochet_bonus", 0)
        projectiles.append(ArrowProjectile(
            spawn_x, spawn_y, self.facing_angle, dmg,
            pierce=pierce, speed=speed,
            max_range=self.atk1_range * self.area_multi,
            poison_damage=poison_dmg, ricochet_count=ricochet
        ))
        return True

    def perform_attack_2(self, sound_engine, projectiles: list = None) -> bool:
        if self.atk2_timer > 0 or projectiles is None: return False
        self.atk2_timer = self.atk2_cooldown * self.cooldown_multi
        self.atk2_anim_timer = 0.24
        sound_engine.play_bow_shoot()

        dmg = int(round(self.atk2_damage * self.get_damage_multiplier()))
        extra = getattr(self, "multishot_extra", 0)
        total_arrows = self.atk2_arrows + extra
        half_arc = 0.35 + 0.04 * extra
        angles = [
            -half_arc + (2 * half_arc / max(1, total_arrows - 1)) * idx
            for idx in range(total_arrows)
        ]
        pierce = 2 + getattr(self, "arrow_pierce_bonus", 0)
        speed = self.atk2_speed * getattr(self, "projectile_speed_multi", 1.0)
        poison_dmg = getattr(self, "poison_damage", 0.0)
        ricochet = getattr(self, "ricochet_bonus", 0)
        for a_offset in angles:
            ang = self.facing_angle + a_offset
            spawn_x = self.x + math.cos(ang) * 18.0
            spawn_y = self.y + math.sin(ang) * 18.0
            projectiles.append(ArrowProjectile(
                spawn_x, spawn_y, ang, dmg,
                pierce=pierce, speed=speed,
                max_range=self.atk2_range * self.area_multi,
                poison_damage=poison_dmg, ricochet_count=ricochet
            ))
        return True

    def perform_attack_3(self, sound_engine, projectiles: list = None) -> bool:
        if self.atk3_timer > 0 or projectiles is None: return False
        self.atk3_timer = self.atk3_cooldown * self.cooldown_multi
        self.atk3_anim_timer = 0.22
        sound_engine.play_bow_shoot()

        ex_bonus = getattr(self, "explosive_arrow_bonus", 0.0)
        dmg = int(round(self.atk3_damage * self.get_damage_multiplier() * (1.0 + ex_bonus)))
        blast_rad = self.atk3_blast_radius * (1.0 + ex_bonus * 0.40)
        speed = self.atk3_speed * getattr(self, "projectile_speed_multi", 1.0)
        spawn_x = self.x + math.cos(self.facing_angle) * 22.0
        spawn_y = self.y + math.sin(self.facing_angle) * 22.0
        projectiles.append(ExplosiveArrowProjectile(
            spawn_x, spawn_y, self.facing_angle, dmg,
            speed=speed, max_range=self.atk3_range * self.area_multi,
            blast_radius=blast_rad
        ))
        return True


# ==============================================================
# 3. МАГ / АРХИМАГ (MAGE)
# ==============================================================
class Mage(BasePlayer):
    def __init__(
        self,
        x: float,
        y: float,
        hp: float = MageBalance.HP,
        speed: float = MageBalance.SPEED,
        radius: float = PlayerBaseBalance.RADIUS,
        regen_rate: float = PlayerBaseBalance.REGEN_RATE,
        magnet_range: float = PlayerBaseBalance.MAGNET_RANGE,
        dash_cooldown: float = MageBalance.DASH_COOLDOWN,
        dash_duration: float = PlayerBaseBalance.DASH_DURATION,
        dash_speed: float = PlayerBaseBalance.DASH_SPEED,
        atk1_cooldown: float = MageBalance.ATK1_COOLDOWN,
        atk1_damage: int = MageBalance.ATK1_DAMAGE,
        atk1_speed: float = MageBalance.ATK1_SPEED,
        atk2_cooldown: float = MageBalance.ATK2_COOLDOWN,
        atk2_damage: int = MageBalance.ATK2_DAMAGE,
        atk2_speed: float = MageBalance.ATK2_SPEED,
        atk2_range: float = MageBalance.ATK2_RANGE,
        atk2_blast_radius: float = MageBalance.ATK2_BLAST_RADIUS,
        atk3_cooldown: float = MageBalance.ATK3_COOLDOWN,
        atk3_damage: int = MageBalance.ATK3_DAMAGE,
        atk3_radius: float = MageBalance.ATK3_RADIUS,
        blink_distance: float = MageBalance.BLINK_DISTANCE,
    ):
        super().__init__(
            x, y,
            class_type="mage",
            class_name="Маг (Архимаг)",
            class_icon="🔮",
            base_hp=hp,
            base_speed=speed,
            radius=radius,
            regen_rate=regen_rate,
            magnet_range=magnet_range,
            dash_cooldown=dash_cooldown,
            dash_duration=dash_duration,
            dash_speed=dash_speed,
        )
        self.atk1_cooldown = float(atk1_cooldown)
        self.atk1_damage = int(atk1_damage)
        self.atk1_speed = float(atk1_speed)

        self.atk2_cooldown = float(atk2_cooldown)
        self.atk2_damage = int(atk2_damage)
        self.atk2_speed = float(atk2_speed)
        self.atk2_range = float(atk2_range)
        self.atk2_blast_radius = float(atk2_blast_radius)

        self.atk3_cooldown = float(atk3_cooldown)
        self.atk3_damage = int(atk3_damage)
        self.atk3_radius = float(atk3_radius)
        self.blink_distance = float(blink_distance)

        self.skill_descriptions = [
            ("1. Стрела чар", "ЛКМ / 1 / Q", "✨", f"Магическая чародейская стрела (урон {self.atk1_damage})"),
            ("2. Фаербол", "ПКМ / 2 / E", "🔥", f"Огненный шар с сильным взрывом по площади (урон {self.atk2_damage})"),
            ("3. Ледяной круг", "ПРОБЕЛ / 3 / R", "❄️", f"Ледяное кольцо мороза вокруг мага (урон {self.atk3_damage})"),
            ("4. Телепорт", "SHIFT / F", "🌌", "Мгновенный скачок сквозь пространство"),
        ]

    def perform_attack_1(self, sound_engine, projectiles: list = None) -> bool:
        if self.atk1_timer > 0 or projectiles is None: return False
        self.atk1_timer = self.atk1_cooldown * self.cooldown_multi
        self.atk1_anim_timer = 0.16
        sound_engine.play_wind_blade()

        dmg = int(round(self.atk1_damage * self.get_damage_multiplier()))
        extra_bolts = getattr(self, "arcane_barrage_extra", 0)
        chain_lt = getattr(self, "chain_lightning_targets", 0)

        if extra_bolts <= 0:
            spawn_x = self.x + math.cos(self.facing_angle) * 22.0
            spawn_y = self.y + math.sin(self.facing_angle) * 22.0
            projectiles.append(ArcaneBoltProjectile(spawn_x, spawn_y, self.facing_angle, dmg, speed=self.atk1_speed, chain_lightning=chain_lt))
        else:
            total_bolts = 1 + extra_bolts
            half_spread = min(0.35, 0.08 * extra_bolts)
            for idx in range(total_bolts):
                offset = -half_spread + (2 * half_spread / max(1, total_bolts - 1)) * idx
                ang = self.facing_angle + offset
                spawn_x = self.x + math.cos(ang) * 22.0
                spawn_y = self.y + math.sin(ang) * 22.0
                projectiles.append(ArcaneBoltProjectile(spawn_x, spawn_y, ang, dmg, speed=self.atk1_speed, chain_lightning=chain_lt))
        return True

    def perform_attack_2(self, sound_engine, projectiles: list = None) -> bool:
        if self.atk2_timer > 0 or projectiles is None: return False
        self.atk2_timer = self.atk2_cooldown * self.cooldown_multi
        self.atk2_anim_timer = 0.28
        sound_engine.play_explosion()

        bonus = getattr(self, "fireball_damage_bonus", 0.0)
        dmg = int(round(self.atk2_damage * self.get_damage_multiplier() * (1.0 + bonus)))
        blast_rad = self.atk2_blast_radius * (1.0 + bonus * 0.35)
        spawn_x = self.x + math.cos(self.facing_angle) * 24.0
        spawn_y = self.y + math.sin(self.facing_angle) * 24.0
        projectiles.append(FireballProjectile(
            spawn_x, spawn_y, self.facing_angle, dmg,
            speed=self.atk2_speed, max_range=self.atk2_range * self.area_multi,
            blast_radius=blast_rad
        ))
        return True

    def perform_attack_3(self, sound_engine, zombies: list = None, particles: list = None, damage_numbers: list = None, camera = None) -> bool:
        if self.atk3_timer > 0: return False
        self.atk3_timer = self.atk3_cooldown * self.cooldown_multi
        self.atk3_anim_timer = 0.35
        sound_engine.play_freeze()
        if camera: camera.shake(7.0, 0.20)

        radius_bonus = 1.0 + getattr(self, "frost_nova_radius_bonus", 0.0)
        radius = self.atk3_radius * self.area_multi * radius_bonus
        dmg = int(round(self.atk3_damage * self.get_damage_multiplier()))

        if zombies is not None:
            for z in zombies:
                if z.dead: continue
                d = math.hypot(z.x - self.x, z.y - self.y)
                if d <= radius + z.radius:
                    ang = math.atan2(z.y - self.y, z.x - self.x)
                    z.take_damage(dmg, ang, 300.0, particles, damage_numbers, sound_engine, is_crit=True)
                    z.slow_timer = 3.0
                    z.frozen = True

        # Frost particles
        if particles is not None:
            from ..rendering.effects import Particle
            for _ in range(24):
                pa = random.uniform(0, math.pi * 2)
                pd = random.uniform(radius * 0.4, radius)
                particles.append(Particle(
                    self.x + math.cos(pa) * pd,
                    self.y + math.sin(pa) * pd,
                    math.cos(pa) * 40, math.sin(pa) * 40,
                    random.choice([(180, 240, 255), (0, 245, 212), (255, 255, 255)]),
                    random.uniform(3.0, 6.0), 0.35, "circle"
                ))
        return True

    def trigger_dash(self, move_x: float, move_y: float, sound_engine, zombies: list = None, particles: list = None, damage_numbers: list = None, *args, **kwargs) -> bool:
        # Mage Blink: instantaneous flash teleport
        if self.dash_timer > 0: return False

        if move_x == 0 and move_y == 0:
            dx = math.cos(self.facing_angle)
            dy = math.sin(self.facing_angle)
        else:
            length = math.hypot(move_x, move_y)
            dx = move_x / length
            dy = move_y / length

        effective_cd = self.dash_cooldown * max(0.30, 1.0 - getattr(self, "dash_cooldown_reduction", 0.0)) * self.cooldown_multi
        self.dash_timer = max(0.30, effective_cd)
        self.invulnerable_timer = 0.25
        sound_engine.play_teleport()

        blast_dmg = getattr(self, "teleport_blast_damage", 0.0)
        old_x, old_y = self.x, self.y

        # Teleport jump
        teleport_dist = self.blink_distance
        self.x += dx * teleport_dist
        self.y += dy * teleport_dist

        # Clamp arena bounds
        min_x = settings.ARENA_MIN_X + self.radius
        max_x = settings.ARENA_MAX_X - self.radius
        min_y = settings.ARENA_MIN_Y + self.radius
        max_y = settings.ARENA_MAX_Y - self.radius
        self.x = max(min_x, min(max_x, self.x))
        self.y = max(min_y, min(max_y, self.y))

        # Ghost afterimages
        self.ghost_trail.append(GhostAfterimage(old_x, old_y, self.facing_angle, 0.25, color=(200, 120, 255)))
        self.ghost_trail.append(GhostAfterimage(self.x, self.y, self.facing_angle, 0.25, color=(160, 90, 240)))

        # Teleport Blast at arrival & departure
        if blast_dmg > 0 and zombies is not None:
            actual_blast = int(round(blast_dmg * self.get_damage_multiplier()))
            for z in zombies:
                if z.dead: continue
                for bx, by in [(old_x, old_y), (self.x, self.y)]:
                    d = math.hypot(z.x - bx, z.y - by)
                    if d <= 85.0 * self.area_multi + z.radius:
                        push_a = math.atan2(z.y - by, z.x - bx)
                        z.take_damage(actual_blast, push_a, 260.0, particles, damage_numbers, sound_engine)
                        break
        return True


# ==============================================================
# 4. ПРИЗЫВАТЕЛЬ / НЕКРОМАНТ (SUMMONER)
# ==============================================================
class Summoner(BasePlayer):
    def __init__(
        self,
        x: float,
        y: float,
        hp: float = SummonerBalance.HP,
        speed: float = SummonerBalance.SPEED,
        radius: float = PlayerBaseBalance.RADIUS,
        regen_rate: float = PlayerBaseBalance.REGEN_RATE,
        magnet_range: float = PlayerBaseBalance.MAGNET_RANGE,
        dash_cooldown: float = SummonerBalance.DASH_COOLDOWN,
        dash_duration: float = PlayerBaseBalance.DASH_DURATION,
        dash_speed: float = PlayerBaseBalance.DASH_SPEED,
        max_minions: int = SummonerBalance.MAX_MINIONS,
        atk1_cooldown: float = SummonerBalance.ATK1_COOLDOWN,
        atk1_damage: int = SummonerBalance.ATK1_DAMAGE,
        atk1_range: float = SummonerBalance.ATK1_RANGE,
        atk2_cooldown: float = SummonerBalance.ATK2_COOLDOWN,
        atk3_cooldown: float = SummonerBalance.ATK3_COOLDOWN,
        atk3_damage: int = SummonerBalance.ATK3_DAMAGE,
        atk3_speed: float = SummonerBalance.ATK3_SPEED,
        atk3_range: float = SummonerBalance.ATK3_RANGE,
    ):
        super().__init__(
            x, y,
            class_type="summoner",
            class_name="Призыватель (Некромант)",
            class_icon="💀",
            base_hp=hp,
            base_speed=speed,
            radius=radius,
            regen_rate=regen_rate,
            magnet_range=magnet_range,
            dash_cooldown=dash_cooldown,
            dash_duration=dash_duration,
            dash_speed=dash_speed,
        )
        self.max_minions = int(max_minions)
        self.atk1_cooldown = float(atk1_cooldown)
        self.atk1_damage = int(atk1_damage)
        self.atk1_range = float(atk1_range)

        self.atk2_cooldown = float(atk2_cooldown)
        self.atk3_cooldown = float(atk3_cooldown)
        self.atk3_damage = int(atk3_damage)
        self.atk3_speed = float(atk3_speed)
        self.atk3_range = float(atk3_range)

        self.minions: List[Minion] = []
        self.summon_counter = 0
        self.colossus_minion_unlocked = False

        # Initial summon of 2 companion skeletons
        self._spawn_minion()
        self._spawn_minion()

        self.skill_descriptions = [
            ("1. Хлыст душ", "ЛКМ / 1 / Q", "⛓️", f"Призрачный удар хлыстом, указывает цель миньонам (урон {self.atk1_damage})"),
            ("2. Призыв", "ПКМ / 2 / E", "💀", f"Призывает скелетов-миньонов для помощи в бою (макс {self.max_minions})"),
            ("3. Взрыв душ", "ПРОБЕЛ / 3 / R", "🌀", f"Поток призрачных черепов во все стороны (урон {self.atk3_damage})"),
            ("4. Шаг духа", "SHIFT / F", "👻", "Бесплотный шаг сквозь толпы врагов"),
        ]

    def _spawn_minion(self) -> None:
        self.minions = [m for m in self.minions if not m.dead]
        if len(self.minions) < self.max_minions:
            ox = self.x + random.uniform(-30, 30)
            oy = self.y + random.uniform(-30, 30)
            self.summon_counter = getattr(self, "summon_counter", 0) + 1
            is_colossus = getattr(self, "colossus_minion_unlocked", False) and (self.summon_counter % 10 == 0)
            self.minions.append(Minion(ox, oy, self, is_colossus=is_colossus))

    def update(self, dt: float, move_x: float, move_y: float, aim_angle: float, sound_engine, particles: list = None) -> None:
        super().update(dt, move_x, move_y, aim_angle, sound_engine, particles)
        # Filter dead minions
        self.minions = [m for m in self.minions if not m.dead]

    def perform_attack_1(self, sound_engine, zombies: list = None, particles: list = None, damage_numbers: list = None) -> bool:
        if self.atk1_timer > 0: return False
        self.atk1_timer = self.atk1_cooldown * self.cooldown_multi
        self.atk1_anim_timer = 0.18
        sound_engine.play_sword_swing()

        # Spirit whip hit in front arc
        hit_range = self.atk1_range * self.area_multi
        dmg = int(round(self.atk1_damage * self.get_damage_multiplier()))

        if zombies is not None:
            for z in zombies:
                if z.dead: continue
                d = math.hypot(z.x - self.x, z.y - self.y)
                if d <= hit_range + z.radius:
                    ang = math.atan2(z.y - self.y, z.x - self.x)
                    diff = abs((ang - self.facing_angle + math.pi) % (math.pi * 2) - math.pi)
                    if diff < 1.10:
                        z.take_damage(dmg, ang, 220.0, particles, damage_numbers, sound_engine)
                        # Order minions to rush target
                        for m in self.minions:
                            m.target = z
        return True

    def perform_attack_2(self, sound_engine) -> bool:
        if self.atk2_timer > 0: return False
        self.atk2_timer = self.atk2_cooldown * self.cooldown_multi
        self.atk2_anim_timer = 0.30
        sound_engine.play_summon()

        # Capture alive minions before spawning (to avoid healing fresh spawns)
        self.minions = [m for m in self.minions if not m.dead]
        existing_minions = list(self.minions)

        # Summon up to 2 minions to fill army up to max cap
        self._spawn_minion()
        self._spawn_minion()

        # Infuse pre-existing injured minions with restorative soul essence (+35% HP)
        for m in existing_minions:
            if not m.dead and m.hp < m.max_hp:
                m.hp = min(m.max_hp, m.hp + m.max_hp * 0.35)
        return True

    def perform_attack_3(self, sound_engine, projectiles: list = None) -> bool:
        if self.atk3_timer > 0 or projectiles is None: return False
        self.atk3_timer = self.atk3_cooldown * self.cooldown_multi
        self.atk3_anim_timer = 0.25
        sound_engine.play_freeze()

        # Fires soul waves in a spread
        dmg = int(round(self.atk3_damage * self.get_damage_multiplier()))
        extra_waves = getattr(self, "soul_burst_extra", 0)
        total_waves = 3 + extra_waves
        half_arc = 0.40 + 0.05 * min(4, extra_waves)
        angles = [
            -half_arc + (2 * half_arc / max(1, total_waves - 1)) * idx
            for idx in range(total_waves)
        ]
        for a_off in angles:
            ang = self.facing_angle + a_off
            spawn_x = self.x + math.cos(ang) * 22.0
            spawn_y = self.y + math.sin(ang) * 22.0
            projectiles.append(SoulWaveProjectile(spawn_x, spawn_y, ang, dmg, speed=self.atk3_speed, max_range=self.atk3_range * self.area_multi))
        return True


def create_player(class_type: str, x: float, y: float) -> BasePlayer:
    """Factory helper to instantiate a player subclass by class_type identifier."""
    if class_type == "ranger":
        return Ranger(x, y)
    elif class_type == "mage":
        return Mage(x, y)
    elif class_type == "summoner":
        return Summoner(x, y)
    else:
        return Warrior(x, y)


# Совместимость со старым кодом
Knight = Warrior

