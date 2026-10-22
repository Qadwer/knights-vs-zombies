"""
Плавная виртуальная камера с интерполяцией (lerp), тряской экрана и ограничением границами арены.
"""

import random
from ..config import settings


class Camera:
    def __init__(self, viewport_width: int, viewport_height: int):
        self.x = 0.0
        self.y = 0.0
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.shake_intensity = 0.0
        self.shake_duration = 0.0

    def resize(self, width: int, height: int) -> None:
        """Обновление размеров области просмотра при изменении окна."""
        self.viewport_width = width
        self.viewport_height = height

    def shake(self, intensity: float, duration: float) -> None:
        """Запуск эффекта тряски экрана заданной силы и продолжительности."""
        self.shake_intensity = intensity
        self.shake_duration = duration

    def update(self, dt: float, target_x: float, target_y: float) -> None:
        """Плавное следование за целевыми координатами (target_x, target_y)."""
        # Плавная интерполяция к центру цели
        target_cam_x = target_x - self.viewport_width / 2.0
        target_cam_y = target_y - self.viewport_height / 2.0

        self.x += (target_cam_x - self.x) * 0.12
        self.y += (target_cam_y - self.y) * 0.12

        # Применение эффекта тряски экрана при активности
        if self.shake_duration > 0:
            self.shake_duration -= dt
            self.x += random.uniform(-self.shake_intensity, self.shake_intensity)
            self.y += random.uniform(-self.shake_intensity, self.shake_intensity)

        # Ограничение границами арены мира
        max_cam_x = max(0.0, float(settings.ARENA_MAX_X + 64 - self.viewport_width))
        max_cam_y = max(0.0, float(settings.ARENA_MAX_Y + 64 - self.viewport_height))

        self.x = max(0.0, min(max_cam_x, self.x))
        self.y = max(0.0, min(max_cam_y, self.y))
