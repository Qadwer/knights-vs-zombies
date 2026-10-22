"""
Сущность сферы опыта (ExperienceOrb), выпадающей из поверженных зомби.
"""

import math
import pygame
from .base import Entity
from ..config import EconomyBalance


# Значения по умолчанию для сфер опыта
EXP_ORB_RADIUS: float = EconomyBalance.EXP_ORB_RADIUS
EXP_ORB_BASE_SPEED: float = EconomyBalance.EXP_ORB_BASE_SPEED
EXP_ORB_DEFAULT_VALUE: int = EconomyBalance.EXP_ORB_DEFAULT_VALUE


class ExperienceOrb(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        value: int = EXP_ORB_DEFAULT_VALUE,
        radius: float = EXP_ORB_RADIUS,
        base_speed: float = EXP_ORB_BASE_SPEED,
    ):
        super().__init__(x, y, radius=radius)
        self.value = value
        self.collected = False
        self.bob = 0.0
        self.base_speed = float(base_speed)

    def update(self, dt: float, player) -> bool:
        self.bob += dt * 5.0
        dist = math.hypot(player.x - self.x, player.y - self.y)
        magnet_range = player.magnet_range

        if dist < magnet_range:
            angle = math.atan2(player.y - self.y, player.x - self.x)
            step = self.base_speed * dt
            self.x += math.cos(angle) * step
            self.y += math.sin(angle) * step

            if dist < player.radius + self.radius + 4:
                self.collected = True
                self.dead = True
                return player.gain_xp(self.value)  # Возвращает True, если уровень повышен!
        return False

    def draw(self, screen: pygame.Surface, camera) -> None:
        if self.dead:
            return
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y + math.sin(self.bob) * 3)

        # Внешнее свечение
        pygame.draw.circle(screen, (82, 183, 136), (sx, sy), int(self.radius + 2))
        # Яркое ядро сферы
        pygame.draw.circle(screen, (116, 198, 157), (sx, sy), int(self.radius))
        pygame.draw.circle(screen, (255, 255, 255), (sx - 1, sy - 1), 2)
