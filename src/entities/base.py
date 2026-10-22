"""
Базовый абстрактный класс сущности (Entity).
"""

from abc import ABC, abstractmethod
from typing import Tuple
import pygame


class Entity(ABC):
    def __init__(self, x: float, y: float, radius: float = 16.0):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.active = True
        self.dead = False

    @abstractmethod
    def update(self, dt: float, *args, **kwargs) -> None:
        """Обновление состояния сущности за шаг времени dt."""
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface, camera) -> None:
        """Отрисовка сущности на экране с учётом смещения камеры."""
        pass

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Возвращает прямоугольник коллизии (left, top, width, height)."""
        r = int(self.radius)
        return int(self.x - r), int(self.y - r), r * 2, r * 2

    @property
    def position(self) -> Tuple[float, float]:
        """Возвращает текущие координаты (x, y)."""
        return self.x, self.y
