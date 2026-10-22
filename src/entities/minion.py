"""
Сущность миньона для класса Призыватель: следует за игроком, ищет и атакует зомби.
"""

import math
import random
from typing import List, Optional
import pygame
from .base import Entity
from ..config import (
    settings,
    MinionBalance,
)


class Minion(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        summoner,
        is_colossus: bool = False,
        base_hp: float = MinionBalance.BASE_HP,
        base_speed: float = MinionBalance.BASE_SPEED,
        base_damage: float = MinionBalance.BASE_DAMAGE,
        attack_radius: float = MinionBalance.ATTACK_RADIUS,
        colossus_radius: float = MinionBalance.COLOSSUS_RADIUS,
    ):
        self.is_colossus = is_colossus
        self.scale = 1.45 if is_colossus else 1.0
        rad = colossus_radius if is_colossus else attack_radius
        super().__init__(x, y, radius=rad)
        self.summoner = summoner
        self.base_hp = float(base_hp)
        self.base_speed = float(base_speed)
        hp_multi = getattr(summoner, "minion_hp_multi", 1.0)
        speed_multi = getattr(summoner, "minion_speed_multi", 1.0)
        colossus_hp_mult = MinionBalance.COLOSSUS_HP_MULTI if is_colossus else 1.0
        colossus_dmg_mult = MinionBalance.COLOSSUS_DMG_MULTI if is_colossus else 1.0
        self.max_hp = self.base_hp * hp_multi * colossus_hp_mult
        self.hp = self.max_hp
        self.speed = self.base_speed * speed_multi
        self.base_damage = float(base_damage) * colossus_dmg_mult
        self.attack_cooldown = 0.0
        self.target: Optional[Entity] = None
        self.bob = random.uniform(0, 10.0)

    @property
    def damage(self) -> int:
        dmg_multi = getattr(self.summoner, "minion_dmg_multi", 1.0)
        return int(round(self.base_damage * dmg_multi))

    def update(
        self,
        dt: float,
        all_zombies: List[Entity],
        particles: list,
        damage_numbers: list,
        sound_engine
    ) -> None:
        if self.dead:
            return

        self.bob += dt * 8.0
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # Динамическое обновление скорости и запаса здоровья при получении улучшений
        colossus_hp_mult = MinionBalance.COLOSSUS_HP_MULTI if getattr(self, "is_colossus", False) else 1.0
        if hasattr(self.summoner, "minion_speed_multi"):
            self.speed = self.base_speed * self.summoner.minion_speed_multi
        if hasattr(self.summoner, "minion_hp_multi"):
            self.max_hp = self.base_hp * self.summoner.minion_hp_multi * colossus_hp_mult

        # Выбор цели: держим фокус на текущей цели, если жива и рядом; иначе выбираем ближайшего зомби
        is_current_valid = (
            self.target is not None and
            not self.target.dead and
            self.target in all_zombies and
            math.hypot(self.target.x - self.x, self.target.y - self.y) < 480.0
        )
        if not is_current_valid:
            nearest_z = None
            min_dist = 380.0
            for z in all_zombies:
                if z.dead:
                    continue
                d = math.hypot(z.x - self.x, z.y - self.y)
                if d < min_dist:
                    min_dist = d
                    nearest_z = z
            self.target = nearest_z

        if self.target and not self.target.dead:
            # Преследование и атака зомби
            angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            dist = math.hypot(self.target.x - self.x, self.target.y - self.y)

            if dist > self.radius + self.target.radius - 2:
                self.x += math.cos(angle) * self.speed * dt
                self.y += math.sin(angle) * self.speed * dt
                dist = math.hypot(self.target.x - self.x, self.target.y - self.y)

            # Нанесение удара
            if dist <= self.radius + self.target.radius + 4:
                if self.attack_cooldown <= 0:
                    self.attack_cooldown = 0.70
                    sound_engine.play_sword_swing()
                    owner_dmg_multi = self.summoner.get_damage_multiplier() if hasattr(self.summoner, "get_damage_multiplier") else self.summoner.damage_multi
                    actual_dmg = int(round(self.base_damage * getattr(self.summoner, "minion_dmg_multi", 1.0) * owner_dmg_multi))
                    crit_chance = self.summoner.get_crit_chance(0.20) if hasattr(self.summoner, "get_crit_chance") else 0.20
                    is_crit = random.random() < crit_chance
                    if is_crit:
                        actual_dmg = int(round(actual_dmg * 1.6))
                    self.target.take_damage(
                        actual_dmg,
                        angle,
                        knock_force=35.0,
                        particles=particles,
                        damage_numbers=damage_numbers,
                        sound_engine=sound_engine,
                        is_crit=is_crit
                    )
        else:
            # Следование за призывателем
            d_to_owner = math.hypot(self.summoner.x - self.x, self.summoner.y - self.y)
            if d_to_owner > 50.0:
                angle = math.atan2(self.summoner.y - self.y, self.summoner.x - self.x)
                self.x += math.cos(angle) * (self.speed * 1.1) * dt
                self.y += math.sin(angle) * (self.speed * 1.1) * dt

        # Ограничение движения границами арены
        min_x = settings.ARENA_MIN_X + self.radius
        max_x = settings.ARENA_MAX_X - self.radius
        min_y = settings.ARENA_MIN_Y + self.radius
        max_y = settings.ARENA_MAX_Y - self.radius
        self.x = max(min_x, min(max_x, self.x))
        self.y = max(min_y, min(max_y, self.y))

    def take_damage(
        self,
        amount: float,
        damage_numbers: list = None,
        sound_engine = None,
        particles: list = None
    ) -> None:
        if self.dead:
            return
        self.hp -= amount
        if damage_numbers is not None:
            from ..rendering.effects import DamageNumber
            damage_numbers.append(DamageNumber(self.x, self.y - 14, f"-{int(round(amount))}", is_crit=False))
        if sound_engine and hasattr(sound_engine, "play_hit_zombie"):
            sound_engine.play_hit_zombie()
        if self.hp <= 0:
            self.hp = 0.0
            self.dead = True
            if particles is not None and len(particles) < 300:
                from ..rendering.effects import Particle
                for _ in range(14):
                    pa = random.uniform(0, math.pi * 2)
                    spd = random.uniform(30, 95)
                    particles.append(Particle(
                        self.x, self.y,
                        math.cos(pa) * spd, math.sin(pa) * spd,
                        random.choice([(235, 240, 235), (180, 195, 190), (80, 245, 180)]),
                        random.uniform(2.5, 4.5), 0.35, "circle"
                    ))

    def draw(self, screen: pygame.Surface, camera) -> None:
        if self.dead:
            return
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y + math.sin(self.bob) * 3)

        if getattr(self, "is_colossus", False):
            # Колосс (Гигантский миньон) — увеличенные визуальные элементы и аура души
            # 1. Тень на земле
            sh_surf = pygame.Surface((40, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(sh_surf, (0, 0, 0, 110), (0, 0, 40, 20))
            screen.blit(sh_surf, (sx - 20, sy + 13))

            # 2. Изумрудно-золотое сияние души
            glow_surf = pygame.Surface((56, 56), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (245, 166, 35, 65), (28, 28), 26)
            pygame.draw.circle(glow_surf, (80, 245, 180, 60), (28, 28), 20)
            screen.blit(glow_surf, (sx - 28, sy - 28))

            # 3. Грудная клетка и позвоночник
            pygame.draw.line(screen, (220, 230, 225), (sx, sy + 1), (sx, sy + 14), 3)
            for ry in [4, 8, 12]:
                pygame.draw.line(screen, (200, 215, 210), (sx - 8, sy + ry), (sx + 8, sy + ry), 2)

            # 4. Рогатый череп исполина
            pygame.draw.circle(screen, (245, 250, 245), (sx, sy - 4), 12)
            pygame.draw.rect(screen, (225, 230, 225), (sx - 6, sy + 3, 12, 6), border_radius=2)
            # Рога
            pygame.draw.polygon(screen, (245, 166, 35), [(sx - 11, sy - 12), (sx - 7, sy - 4), (sx - 4, sy - 8)])
            pygame.draw.polygon(screen, (245, 166, 35), [(sx + 11, sy - 12), (sx + 7, sy - 4), (sx + 4, sy - 8)])

            # Горящие глаза
            pygame.draw.circle(screen, (15, 22, 28), (sx - 4, sy - 4), 3)
            pygame.draw.circle(screen, (15, 22, 28), (sx + 4, sy - 4), 3)
            pygame.draw.circle(screen, (255, 200, 40), (sx - 4, sy - 4), 2)
            pygame.draw.circle(screen, (255, 200, 40), (sx + 4, sy - 4), 2)

            # Шипованный щит (слева)
            pygame.draw.circle(screen, (60, 45, 35), (sx - 15, sy + 2), 9)
            pygame.draw.circle(screen, (245, 166, 35), (sx - 15, sy + 2), 9, 2)
            pygame.draw.circle(screen, (245, 200, 50), (sx - 15, sy + 2), 3)

            # Двуручный меч колосса (справа)
            pygame.draw.line(screen, (245, 250, 245), (sx + 9, sy + 6), (sx + 22, sy - 9), 4)
            pygame.draw.line(screen, (80, 245, 180), (sx + 21, sy - 9), (sx + 26, sy - 6), 3)

            # Полоса здоровья с золотой рамкой
            bar_w = 34
            bar_h = 4
            bx = sx - bar_w // 2
            by = sy - 21
            pct = max(0.0, min(1.0, self.hp / self.max_hp))
            pygame.draw.rect(screen, (245, 166, 35), (bx - 2, by - 2, bar_w + 4, bar_h + 4), border_radius=2)
            pygame.draw.rect(screen, (35, 20, 25), (bx, by, bar_w, bar_h))
            bar_col = (80, 245, 180) if pct > 0.50 else ((245, 166, 35) if pct > 0.25 else (230, 57, 70))
            pygame.draw.rect(screen, bar_col, (bx, by, int(bar_w * pct), bar_h))
        else:
            # Стандартный скелет-миньон
            # Мягкая тень на земле
            sh_surf = pygame.Surface((28, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(sh_surf, (0, 0, 0, 90), (0, 0, 28, 14))
            screen.blit(sh_surf, (sx - 14, sy + 10))

            # Аура призрачного сияния
            glow_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (80, 245, 180, 45), (18, 18), 16)
            screen.blit(glow_surf, (sx - 18, sy - 18))

            # Позвоночник и ребра
            pygame.draw.line(screen, (200, 210, 205), (sx, sy + 2), (sx, sy + 10), 2)
            for ry in [4, 7]:
                pygame.draw.line(screen, (180, 195, 190), (sx - 5, sy + ry), (sx + 5, sy + ry), 1)

            # Костяной череп
            pygame.draw.circle(screen, (235, 240, 235), (sx, sy - 3), 8)
            pygame.draw.rect(screen, (215, 220, 215), (sx - 4, sy + 2, 8, 4), border_radius=1)

            # Темные глазницы с бирюзовыми искрами душ
            pygame.draw.circle(screen, (15, 22, 28), (sx - 3, sy - 3), 2)
            pygame.draw.circle(screen, (15, 22, 28), (sx + 3, sy - 3), 2)
            pygame.draw.circle(screen, (80, 245, 180), (sx - 3, sy - 3), 1)
            pygame.draw.circle(screen, (80, 245, 180), (sx + 3, sy - 3), 1)

            # Костяной щит (слева)
            pygame.draw.circle(screen, (60, 45, 35), (sx - 10, sy + 1), 6)
            pygame.draw.circle(screen, (245, 166, 35), (sx - 10, sy + 1), 6, 1)
            pygame.draw.circle(screen, (220, 230, 225), (sx - 10, sy + 1), 2)

            # Зазубренный меч (справа)
            pygame.draw.line(screen, (245, 250, 245), (sx + 6, sy + 4), (sx + 15, sy - 5), 2)
            pygame.draw.line(screen, (80, 245, 180), (sx + 15, sy - 5), (sx + 18, sy - 3), 2)

            # Полоска здоровья над миньоном
            bar_w = 22
            bar_h = 3
            bx = sx - bar_w // 2
            by = sy - 15
            pct = max(0.0, min(1.0, self.hp / self.max_hp))
            pygame.draw.rect(screen, (20, 25, 22), (bx - 1, by - 1, bar_w + 2, bar_h + 2), border_radius=1)
            pygame.draw.rect(screen, (40, 25, 30), (bx, by, bar_w, bar_h))
            bar_col = (80, 245, 180) if pct > 0.50 else ((245, 166, 35) if pct > 0.25 else (230, 57, 70))
            pygame.draw.rect(screen, bar_col, (bx, by, int(bar_w * pct), bar_h))
