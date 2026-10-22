"""
Сущности снарядов игры:
- WindBladeProjectile (Клинок ветра - Воин)
- ArrowProjectile & ExplosiveArrowProjectile (Стрела и Разрывная стрела - Лучник)
- ArcaneBoltProjectile & FireballProjectile (Стрела чар и Огненный шар - Маг)
- SoulWaveProjectile (Волна душ - Призыватель)
- AcidSpitProjectile (Плевок кислоты - Плюющийся зомби)
"""

import math
import random
from typing import Set, List
import pygame
from .base import Entity
from ..config import ProjectileBalance


class WindBladeProjectile(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        max_range: float = ProjectileBalance.WINDBLADE_RANGE,
        speed: float = ProjectileBalance.WINDBLADE_SPEED,
        radius: float = ProjectileBalance.WINDBLADE_RADIUS,
        pierce: int = ProjectileBalance.WINDBLADE_PIERCE,
        width: float = 40.0,
        height: float = 14.0,
    ):
        super().__init__(x, y, radius=radius)
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.traveled = 0.0
        self.width = width
        self.height = height
        self.hit_zombies: Set[Entity] = set()
        self.pierce_count = pierce

    def update(self, dt: float, particles: list = None) -> None:
        step = self.speed * dt
        self.x += math.cos(self.angle) * step
        self.y += math.sin(self.angle) * step
        self.traveled += step

        if particles is not None and len(particles) < 300 and random.random() < 0.5:
            from ..rendering.effects import Particle
            px = self.x - math.cos(self.angle) * 10
            py = self.y - math.sin(self.angle) * 10
            vx = -math.cos(self.angle) * 60 + random.uniform(-20, 20)
            vy = -math.sin(self.angle) * 60 + random.uniform(-20, 20)
            particles.append(Particle(px, py, vx, vy, (72, 202, 228), 3.0, 0.22, "circle"))

        if self.traveled >= self.max_range or self.pierce_count <= 0:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)

        surf_w = int(self.width + 16)
        surf_h = int(self.height + 16)
        blade_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        center = (surf_w // 2, surf_h // 2)

        glow_rect = pygame.Rect(center[0] - int(self.width // 2) - 4, center[1] - int(self.height // 2) - 4, int(self.width) + 8, int(self.height) + 8)
        pygame.draw.ellipse(blade_surf, (0, 245, 212, 100), glow_rect)

        inner_rect = pygame.Rect(center[0] - int(self.width // 2), center[1] - int(self.height // 2), int(self.width), int(self.height))
        pygame.draw.ellipse(blade_surf, (255, 255, 255, 240), inner_rect)
        pygame.draw.ellipse(blade_surf, (0, 187, 203, 255), inner_rect, 2)

        deg = -math.degrees(self.angle)
        rotated_surf = pygame.transform.rotate(blade_surf, deg)
        new_rect = rotated_surf.get_rect(center=(sx, sy))
        screen.blit(rotated_surf, new_rect.topleft)


class ArrowProjectile(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        pierce: int = 1,
        speed: float = ProjectileBalance.ARROW_SPEED,
        max_range: float = ProjectileBalance.ARROW_RANGE,
        poison_damage: float = 0.0,
        ricochet_count: int = 0,
        radius: float = ProjectileBalance.ARROW_RADIUS,
    ):
        super().__init__(x, y, radius=radius)
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.traveled = 0.0
        self.pierce_count = pierce
        self.poison_damage = poison_damage
        self.ricochet_count = ricochet_count
        self.hit_zombies: Set[Entity] = set()

    def update(self, dt: float, particles: list = None) -> None:
        step = self.speed * dt
        self.x += math.cos(self.angle) * step
        self.y += math.sin(self.angle) * step
        self.traveled += step

        if particles is not None and random.random() < 0.25 and len(particles) < 300:
            from ..rendering.effects import Particle
            p_color = (80, 240, 80) if self.poison_damage > 0 else (200, 215, 180)
            particles.append(Particle(self.x, self.y, 0, 0, p_color, 2.0, 0.15, "circle"))

        if self.traveled >= self.max_range or (self.pierce_count <= 0 and self.ricochet_count <= 0):
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)

        surf = pygame.Surface((32, 12), pygame.SRCALPHA)
        # Деревянное древко стрелы
        pygame.draw.line(surf, (160, 120, 80), (4, 6), (26, 6), 2)
        # Стальной / ядовитый наконечник
        tip_color = (80, 240, 80) if self.poison_damage > 0 else (230, 235, 240)
        pygame.draw.polygon(surf, tip_color, [(26, 3), (31, 6), (26, 9)])
        # Оперение стрелы
        pygame.draw.line(surf, (82, 183, 136), (4, 3), (9, 6), 2)
        pygame.draw.line(surf, (82, 183, 136), (4, 9), (9, 6), 2)

        rot_surf = pygame.transform.rotate(surf, -math.degrees(self.angle))
        screen.blit(rot_surf, rot_surf.get_rect(center=(sx, sy)).topleft)


class ExplosiveArrowProjectile(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        speed: float = ProjectileBalance.EXPLOSIVE_ARROW_SPEED,
        max_range: float = ProjectileBalance.EXPLOSIVE_ARROW_RANGE,
        blast_radius: float = ProjectileBalance.EXPLOSIVE_ARROW_BLAST_RADIUS,
        radius: float = ProjectileBalance.EXPLOSIVE_ARROW_RADIUS,
    ):
        super().__init__(x, y, radius=radius)
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.blast_radius = blast_radius
        self.traveled = 0.0
        self.hit_zombies: Set[Entity] = set()

    def update(self, dt: float, particles: list = None) -> None:
        step = self.speed * dt
        self.x += math.cos(self.angle) * step
        self.y += math.sin(self.angle) * step
        self.traveled += step

        # Искры огненного шлейфа
        if particles is not None and len(particles) < 300:
            from ..rendering.effects import Particle
            particles.append(Particle(
                self.x, self.y,
                random.uniform(-20, 20), random.uniform(-20, 20),
                random.choice([(255, 100, 20), (245, 166, 35), (255, 220, 50)]),
                random.uniform(2.5, 4.5), 0.2, "circle"
            ))

        if self.traveled >= self.max_range:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)

        surf = pygame.Surface((34, 14), pygame.SRCALPHA)
        pygame.draw.line(surf, (140, 80, 50), (4, 7), (24, 7), 3)
        # Огненный наконечник боеголовки
        pygame.draw.circle(surf, (245, 166, 35), (27, 7), 5)
        pygame.draw.circle(surf, (255, 230, 80), (27, 7), 3)

        rot_surf = pygame.transform.rotate(surf, -math.degrees(self.angle))
        screen.blit(rot_surf, rot_surf.get_rect(center=(sx, sy)).topleft)


class ArcaneBoltProjectile(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        speed: float = ProjectileBalance.ARCANE_BOLT_SPEED,
        max_range: float = ProjectileBalance.ARCANE_BOLT_RANGE,
        chain_lightning: int = 0,
        radius: float = ProjectileBalance.ARCANE_BOLT_RADIUS,
        pierce: int = ProjectileBalance.ARCANE_BOLT_PIERCE,
    ):
        super().__init__(x, y, radius=radius)
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.traveled = 0.0
        self.chain_lightning = chain_lightning
        self.hit_zombies: Set[Entity] = set()
        self.pierce_count = pierce

    def update(self, dt: float, particles: list = None) -> None:
        step = self.speed * dt
        self.x += math.cos(self.angle) * step
        self.y += math.sin(self.angle) * step
        self.traveled += step

        if particles is not None and len(particles) < 300:
            from ..rendering.effects import Particle
            particles.append(Particle(
                self.x, self.y,
                random.uniform(-15, 15), random.uniform(-15, 15),
                (180, 110, 255), 3.0, 0.18, "circle"
            ))

        if self.traveled >= self.max_range or self.pierce_count <= 0:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)
        # Пульсирующая чародейская сфера
        pygame.draw.circle(screen, (160, 90, 240, 120), (sx, sy), int(self.radius + 3))
        pygame.draw.circle(screen, (220, 160, 255), (sx, sy), int(self.radius))
        pygame.draw.circle(screen, (255, 255, 255), (sx, sy), int(self.radius - 4))


class FireballProjectile(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        speed: float = ProjectileBalance.FIREBALL_SPEED,
        max_range: float = ProjectileBalance.FIREBALL_RANGE,
        blast_radius: float = ProjectileBalance.FIREBALL_BLAST_RADIUS,
        radius: float = ProjectileBalance.FIREBALL_RADIUS,
    ):
        super().__init__(x, y, radius=radius)
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.blast_radius = blast_radius
        self.traveled = 0.0
        self.hit_zombies: Set[Entity] = set()

    def update(self, dt: float, particles: list = None) -> None:
        step = self.speed * dt
        self.x += math.cos(self.angle) * step
        self.y += math.sin(self.angle) * step
        self.traveled += step

        # Шлейф языков пламени
        if particles is not None and len(particles) < 300:
            from ..rendering.effects import Particle
            for _ in range(2):
                particles.append(Particle(
                    self.x + random.uniform(-4, 4), self.y + random.uniform(-4, 4),
                    -math.cos(self.angle) * 50 + random.uniform(-20, 20),
                    -math.sin(self.angle) * 50 + random.uniform(-20, 20),
                    random.choice([(255, 77, 0), (255, 160, 0), (255, 220, 50)]),
                    random.uniform(4.0, 7.0), 0.25, "circle"
                ))

        if self.traveled >= self.max_range:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)
        # Ядро и ореол огненного шара
        pygame.draw.circle(screen, (255, 80, 0, 130), (sx, sy), int(self.radius + 5))
        pygame.draw.circle(screen, (255, 140, 20), (sx, sy), int(self.radius))
        pygame.draw.circle(screen, (255, 240, 120), (sx, sy), int(self.radius - 5))


class SoulWaveProjectile(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        speed: float = ProjectileBalance.SOUL_WAVE_SPEED,
        max_range: float = ProjectileBalance.SOUL_WAVE_RANGE,
        radius: float = ProjectileBalance.SOUL_WAVE_RADIUS,
        pierce: int = ProjectileBalance.SOUL_WAVE_PIERCE,
    ):
        super().__init__(x, y, radius=radius)
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.traveled = 0.0
        self.hit_zombies: Set[Entity] = set()
        self.pierce_count = pierce

    def update(self, dt: float, particles: list = None) -> None:
        step = self.speed * dt
        self.x += math.cos(self.angle) * step
        self.y += math.sin(self.angle) * step
        self.traveled += step

        if particles is not None and len(particles) < 300:
            from ..rendering.effects import Particle
            particles.append(Particle(
                self.x, self.y,
                random.uniform(-20, 20), random.uniform(-20, 20),
                (80, 245, 180), 3.5, 0.25, "circle"
            ))

        if self.traveled >= self.max_range or self.pierce_count <= 0:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)
        # Призрачный некротический сгусток
        pygame.draw.circle(screen, (40, 200, 140, 110), (sx, sy), int(self.radius + 4))
        pygame.draw.circle(screen, (80, 245, 180), (sx, sy), int(self.radius))
        pygame.draw.circle(screen, (220, 255, 240), (sx, sy), int(self.radius - 5))


class AcidSpitProjectile(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        target_x: float,
        target_y: float,
        damage: int = ProjectileBalance.ACID_SPIT_DAMAGE,
        speed: float = ProjectileBalance.ACID_SPIT_SPEED,
        radius: float = ProjectileBalance.ACID_SPIT_RADIUS,
        max_range: float = ProjectileBalance.ACID_SPIT_RANGE,
    ):
        super().__init__(x, y, radius=radius)
        self.angle = math.atan2(target_y - y, target_x - x)
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.traveled = 0.0

    def update(self, dt: float, *args, **kwargs) -> None:
        step = self.speed * dt
        self.x += math.cos(self.angle) * step
        self.y += math.sin(self.angle) * step
        self.traveled += step
        if self.traveled >= self.max_range:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)
        pygame.draw.circle(screen, (112, 224, 0, 120), (sx, sy), int(self.radius + 3))
        pygame.draw.circle(screen, (158, 240, 26), (sx, sy), int(self.radius))
        pygame.draw.circle(screen, (220, 255, 120), (sx - 2, sy - 2), 2)
