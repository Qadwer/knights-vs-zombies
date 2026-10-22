"""
Визуальные эффекты: частицы (Particles), всплывающие цифры урона (Damage Numbers) и декали крови (Blood Decals).
"""

import random
from typing import Tuple
import pygame


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: Tuple[int, int, int],
        size: float,
        life: float,
        shape: str = "square"
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.shape = shape

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= dt

    def draw(self, screen: pygame.Surface, camera) -> None:
        if self.life <= 0:
            return
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)
        alpha = max(0, min(255, int((self.life / self.max_life) * 255)))

        dim = max(2, int(self.size))
        part_surf = pygame.Surface((dim * 2, dim * 2), pygame.SRCALPHA)
        col_with_alpha = (*self.color, alpha)

        if self.shape == "circle":
            pygame.draw.circle(part_surf, col_with_alpha, (dim, dim), dim)
        else:
            pygame.draw.rect(part_surf, col_with_alpha, (0, 0, dim * 2, dim * 2))

        screen.blit(part_surf, (sx - dim, sy - dim))


class DamageNumber:
    _font_normal = None
    _font_crit = None

    def __init__(self, x: float, y: float, text: str, is_crit: bool = False):
        self.x = x + random.uniform(-8.0, 8.0)
        self.y = y
        self.text = text
        self.is_crit = is_crit
        self.life = 0.8
        self.max_life = 0.8
        self.vy = -55.0
        self.color = (245, 166, 35) if is_crit else (255, 77, 109)

    @classmethod
    def get_fonts(cls):
        if cls._font_normal is None:
            pygame.font.init()
            cls._font_normal = pygame.font.SysFont("Arial", 14, bold=True)
            cls._font_crit = pygame.font.SysFont("Arial", 18, bold=True)
        return cls._font_normal, cls._font_crit

    def update(self, dt: float) -> None:
        self.y += self.vy * dt
        self.vy *= 0.94
        self.life -= dt

    def draw(self, screen: pygame.Surface, camera) -> None:
        if self.life <= 0:
            return
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)
        alpha = max(0, min(255, int((self.life / self.max_life) * 255)))

        font_norm, font_crit = self.get_fonts()
        font = font_crit if self.is_crit else font_norm

        # Render with black outline for high contrast
        text_surf = font.render(self.text, True, self.color)
        outline_surf = font.render(self.text, True, (0, 0, 0))

        combo = pygame.Surface((text_surf.get_width() + 4, text_surf.get_height() + 4), pygame.SRCALPHA)
        # Outline offsets
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            combo.blit(outline_surf, (ox + 2, oy + 2))
        combo.blit(text_surf, (2, 2))
        combo.set_alpha(alpha)

        screen.blit(combo, (sx - combo.get_width() // 2, sy - combo.get_height() // 2))


class BloodDecal:
    def __init__(self, x: float, y: float, radius: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def draw(self, screen: pygame.Surface, camera) -> None:
        sx = int(self.x - camera.x)
        sy = int(self.y - camera.y)
        r = int(self.radius)
        # Draw soft splat on ground
        decal_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(decal_surf, (*self.color, 180), (0, 0, r * 2, int(r * 1.5)))
        screen.blit(decal_surf, (sx - r, sy - int(r * 0.75)))

