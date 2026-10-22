"""
Сущности врагов-зомби с различными архетипами, поведением ИИ и разделением стаи (флокинг).
"""

import math
import random
from typing import List, Tuple, Optional
import pygame
from .base import Entity
from .projectile import AcidSpitProjectile
from ..config import (
    settings,
    ZombieWaveBalance,
    ZOMBIE_ARCHETYPES,
)


class Zombie(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        zombie_type: str = "walker",
        wave: int = 1,
        radius: Optional[float] = None,
        max_hp: Optional[float] = None,
        speed: Optional[float] = None,
        damage: Optional[float] = None,
        color: Optional[Tuple[int, int, int]] = None,
        xp_value: Optional[int] = None,
        score_value: Optional[int] = None,
        spit_cooldown: Optional[float] = None,
    ):
        self.type = zombie_type
        self.wave = max(1, int(wave))
        self.dead = False
        self.flash_timer = 0.0
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0
        self.walk_cycle = random.uniform(0, 10.0)
        self.attack_cooldown = 0.0
        self.slow_timer = 0.0
        self.frozen = False
        self.facing_angle = 0.0
        self.poison_timer = 0.0
        self.poison_tick_timer = 0.0
        self.poison_dps = 0.0
        self.poison_slow = False

        # Конфигурация по умолчанию из архетипа
        cfg = ZOMBIE_ARCHETYPES.get(zombie_type, ZOMBIE_ARCHETYPES["walker"])
        chosen_radius = float(cfg["radius"]) if radius is None else float(radius)
        self.max_hp = float(cfg["max_hp"]) if max_hp is None else float(max_hp)
        self.speed = float(cfg["speed"]) if speed is None else float(speed)
        self.damage = float(cfg["damage"]) if damage is None else float(damage)
        self.color = cfg["color"] if color is None else color
        self.xp_value = int(cfg["xp_value"]) if xp_value is None else int(xp_value)
        self.score_value = int(cfg["score_value"]) if score_value is None else int(score_value)
        self.souls_value = int(cfg.get("souls_value", 1))

        if zombie_type == "spitter":
            self.spit_cooldown = float(cfg.get("spit_cooldown", 2.4)) if spit_cooldown is None else float(spit_cooldown)
            self.spit_timer = random.uniform(1.0, 2.5)

        # --- ПРОГРЕССИЯ ХАРАКТЕРИСТИК ОТ ВОЛНЫ ---
        if self.wave > 1 and max_hp is None and damage is None:
            waves_passed = self.wave - 1
            hp_scale = ZombieWaveBalance.HP_SCALE_PER_WAVE
            dmg_scale = ZombieWaveBalance.DMG_SCALE_PER_WAVE
            boss_multi = ZombieWaveBalance.BOSS_WAVE_HP_MULTI if (self.wave % 5 == 0) else 1.0

            # Нелинейное ускорение после 10-й волны, чтобы перекачанный герой не скучал
            late_game_boost = 1.0 + max(0, self.wave - 10) * 0.05

            hp_multiplier = (1.0 + waves_passed * hp_scale) * boss_multi * late_game_boost
            dmg_multiplier = 1.0 + waves_passed * dmg_scale

            self.max_hp = float(round(self.max_hp * hp_multiplier))
            self.damage = float(round(self.damage * dmg_multiplier))
            # Увеличение награды за усиленных зомби
            self.score_value = int(round(self.score_value * (1.0 + waves_passed * 0.05)))

        super().__init__(x, y, radius=chosen_radius)
        self.hp = float(self.max_hp)

    def apply_poison(self, total_damage: float, duration: float = 3.0, slow: bool = False) -> None:
        """Наложение эффекта периодического урона ядом и замедления."""
        if self.dead or total_damage <= 0:
            return
        dps = total_damage / max(0.5, duration)
        self.poison_dps = max(self.poison_dps, dps)
        self.poison_timer = max(self.poison_timer, duration)
        if slow:
            self.poison_slow = True

    def update(
        self,
        dt: float,
        player,
        all_zombies: List["Zombie"],
        projectiles: list,
        particles: list,
        damage_numbers: list,
        sound_engine,
        camera
    ) -> None:
        if self.dead:
            return

        self.walk_cycle += dt * (self.speed / 15.0)
        if self.flash_timer > 0:
            self.flash_timer -= dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # Тики урона ядом
        if self.poison_timer > 0:
            self.poison_timer -= dt
            self.poison_tick_timer -= dt
            if self.poison_tick_timer <= 0:
                self.poison_tick_timer = 0.5
                tick_dmg = max(1, int(round(self.poison_dps * 0.5)))
                self.hp -= tick_dmg
                self.flash_timer = 0.08
                if damage_numbers is not None:
                    from ..rendering.effects import DamageNumber
                    damage_numbers.append(DamageNumber(self.x, self.y - self.radius, f"-{tick_dmg}", is_crit=False))
                if particles is not None and len(particles) < 300:
                    from ..rendering.effects import Particle
                    particles.append(Particle(
                        self.x + random.uniform(-6, 6),
                        self.y - self.radius + random.uniform(-4, 4),
                        random.uniform(-10, 10), -random.uniform(20, 40),
                        (80, 230, 80), 2.5, 0.35, "circle"
                    ))
                if self.hp <= 0:
                    self.hp = 0.0
                    self.dead = True
                    return

        # Применение отталкивания
        self.x += self.knockback_vx * dt
        self.y += self.knockback_vy * dt
        self.knockback_vx *= 0.88
        self.knockback_vy *= 0.88

        dist_to_player = math.hypot(player.x - self.x, player.y - self.y)
        angle_to_player = math.atan2(player.y - self.y, player.x - self.x)

        # Выбор цели: переключение на миньонов, если они подошли вплотную
        target_x = player.x
        target_y = player.y
        dist_to_target = dist_to_player
        angle_to_target = angle_to_player

        if hasattr(player, "minions") and player.minions:
            for m in player.minions:
                if m.dead: continue
                dm = math.hypot(m.x - self.x, m.y - self.y)
                is_engaging_melee = dm <= (self.radius + m.radius + 18.0)
                is_closer_threat = (dm < dist_to_target and dm < 220.0)
                if is_engaging_melee or is_closer_threat:
                    dist_to_target = dm
                    angle_to_target = math.atan2(m.y - self.y, m.x - self.x)
                    target_x = m.x
                    target_y = m.y

        self.facing_angle = angle_to_target

        # Модификаторы скорости: наибольшее замедление имеет приоритет
        speed_factor = 1.0
        if self.slow_timer > 0:
            self.slow_timer -= dt
            self.frozen = True
            speed_factor = min(speed_factor, 0.40)
        else:
            self.frozen = False

        if self.poison_timer > 0 and self.poison_slow:
            speed_factor = min(speed_factor, 0.70)

        effective_speed = self.speed * speed_factor

        # Поведение искусственного интеллекта по типам
        if self.type == "spitter":
            self.spit_timer -= dt
            if self.spit_timer <= 0 and dist_to_target < 460:
                self.spit_timer = self.spit_cooldown
                projectiles.append(AcidSpitProjectile(self.x, self.y, target_x, target_y, int(self.damage)))

            # Удержание безопасной дистанции
            if dist_to_target < 240:
                self.x -= math.cos(angle_to_target) * effective_speed * dt
                self.y -= math.sin(angle_to_target) * effective_speed * dt
            elif dist_to_target > 340:
                self.x += math.cos(angle_to_target) * effective_speed * dt
                self.y += math.sin(angle_to_target) * effective_speed * dt
        else:
            current_speed = effective_speed
            if self.type == "runner" and dist_to_target < 120:
                current_speed *= 1.4  # Рывок бегуна при приближении

            self.x += math.cos(angle_to_target) * current_speed * dt
            self.y += math.sin(angle_to_target) * current_speed * dt

        # Разделение зомби в стае (флокинг), чтобы они не накладывались друг на друга
        for other in all_zombies:
            if other is self or other.dead:
                continue
            d = math.hypot(self.x - other.x, self.y - other.y)
            min_dist = self.radius + other.radius
            if 0.001 < d < min_dist:
                overlap = (min_dist - d) * 0.5
                push_angle = math.atan2(self.y - other.y, self.x - other.x)
                self.x += math.cos(push_angle) * overlap * 0.5
                self.y += math.sin(push_angle) * overlap * 0.5

        # Ограничение движения границами арены
        min_x = settings.ARENA_MIN_X + self.radius
        max_x = settings.ARENA_MAX_X - self.radius
        min_y = settings.ARENA_MIN_Y + self.radius
        max_y = settings.ARENA_MAX_Y - self.radius
        self.x = max(min_x, min(max_x, self.x))
        self.y = max(min_y, min(max_y, self.y))

        # Пересчет дистанции до игрока после смещения для точной проверки атаки
        dist_to_player = math.hypot(player.x - self.x, player.y - self.y)

        # Проверка удара по миньонам игрока
        hit_minion = False
        if hasattr(player, "minions") and player.minions:
            for m in player.minions:
                if m.dead: continue
                dm = math.hypot(m.x - self.x, m.y - self.y)
                if dm <= self.radius + m.radius + 6.0:
                    if self.attack_cooldown <= 0:
                        m.take_damage(self.damage, damage_numbers, sound_engine, particles)
                        self.attack_cooldown = 0.85
                        ang_m = math.atan2(self.y - m.y, self.x - m.x)
                        self.knockback_vx = math.cos(ang_m) * 45.0
                        self.knockback_vy = math.sin(ang_m) * 45.0
                        hit_minion = True
                        break

        # Контактный удар в ближнем бою по игроку
        if not hit_minion and dist_to_player < self.radius + player.radius:
            if self.attack_cooldown <= 0:
                player.take_damage(self.damage, sound_engine, camera, damage_numbers=damage_numbers, particles=particles)
                self.attack_cooldown = 0.9
                # Небольшая отдача при ударе
                self.knockback_vx = -math.cos(angle_to_player) * 120.0
                self.knockback_vy = -math.sin(angle_to_player) * 120.0

                # Урон от шипов (если у игрока прокачан навык шипов)
                if player.thorns > 0:
                    self.take_damage(
                        amount=int(player.thorns),
                        knock_angle=angle_to_player + math.pi,
                        knock_force=150.0,
                        particles=particles,
                        damage_numbers=damage_numbers,
                        sound_engine=sound_engine
                    )

    def take_damage(
        self,
        amount: int,
        knock_angle: float,
        knock_force: float,
        particles: list,
        damage_numbers: list,
        sound_engine,
        is_crit: bool = False
    ) -> None:
        """Получение урона, отталкивание и создание эффектов крови и цифр."""
        if self.dead:
            return

        self.hp -= amount
        self.flash_timer = 0.10
        sound_engine.play_hit_zombie()

        # Сопротивление отталкиванию для громилы (brute)
        resist = 0.35 if self.type == "brute" else 1.0
        self.knockback_vx += math.cos(knock_angle) * knock_force * resist
        self.knockback_vy += math.sin(knock_angle) * knock_force * resist

        # Всплывающий текст урона
        if damage_numbers is not None:
            from ..rendering.effects import DamageNumber
            damage_numbers.append(DamageNumber(self.x, self.y - self.radius, f"-{amount}", is_crit=is_crit))

        # Частицы брызг крови
        if particles is not None:
            from ..rendering.effects import Particle
            particle_count = 10 if is_crit else 6
            blood_colors = [(106, 4, 15), (157, 2, 8), (208, 0, 0)]
            for _ in range(particle_count):
                p_angle = knock_angle + random.uniform(-0.8, 0.8)
                p_speed = random.uniform(60.0, 180.0)
                particles.append(Particle(
                    self.x, self.y,
                    math.cos(p_angle) * p_speed,
                    math.sin(p_angle) * p_speed,
                    random.choice(blood_colors),
                    random.uniform(3.0, 5.0),
                    random.uniform(0.35, 0.65)
                ))

        if self.hp <= 0:
            self.hp = 0.0
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        pass  # Детальная отрисовка выполняется в модуле renderer.py
