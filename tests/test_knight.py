import unittest
import os
import sys

# Ensure root dir in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
pygame.init()

from src.entities.player import Warrior as Knight
from src.audio.sound_engine import SoundEngine
from src.config import settings


class DummySoundEngine:
    def play_sword_swing(self): pass
    def play_spin_attack(self): pass
    def play_wind_blade(self): pass
    def play_dash(self): pass
    def play_player_hurt(self): pass


class DummyCamera:
    def shake(self, intensity, duration): pass


class TestKnight(unittest.TestCase):
    def setUp(self):
        self.knight = Knight(500.0, 500.0)
        self.sounds = DummySoundEngine()
        self.camera = DummyCamera()

    def test_initial_state(self):
        self.assertEqual(self.knight.hp, settings.PLAYER_MAX_HP)
        self.assertEqual(self.knight.max_hp, settings.PLAYER_MAX_HP)
        self.assertEqual(self.knight.level, 1)
        self.assertEqual(self.knight.xp, 0)
        self.assertFalse(self.knight.dead)

    def test_movement(self):
        initial_x = self.knight.x
        initial_y = self.knight.y
        # Move right
        self.knight.update(0.1, move_x=1.0, move_y=0.0, aim_angle=0.0, sound_engine=self.sounds)
        self.assertGreater(self.knight.x, initial_x)
        self.assertEqual(self.knight.y, initial_y)

    def test_arena_clamp(self):
        # Try moving far past arena min bounds
        self.knight.x = -100.0
        self.knight.y = -100.0
        self.knight.update(0.1, move_x=0.0, move_y=0.0, aim_angle=0.0, sound_engine=self.sounds)
        min_allowed_x = settings.ARENA_MIN_X + self.knight.radius
        self.assertGreaterEqual(self.knight.x, min_allowed_x)

    def test_attack_1(self):
        self.assertTrue(self.knight.perform_attack_1(self.sounds))
        self.assertGreater(self.knight.atk1_timer, 0.0)
        # Immediate second attack fails due to cooldown
        self.assertFalse(self.knight.perform_attack_1(self.sounds))

    def test_attack_2(self):
        self.assertTrue(self.knight.perform_attack_2(self.sounds))
        self.assertGreater(self.knight.atk2_timer, 0.0)
        self.assertFalse(self.knight.perform_attack_2(self.sounds))

    def test_attack_3(self):
        projectiles = []
        self.assertTrue(self.knight.perform_attack_3(self.sounds, projectiles))
        self.assertEqual(len(projectiles), 1)
        self.assertGreater(self.knight.atk3_timer, 0.0)

    def test_dash(self):
        self.assertTrue(self.knight.trigger_dash(1.0, 0.0, self.sounds))
        self.assertTrue(self.knight.is_dashing)
        self.assertGreater(self.knight.invulnerable_timer, 0.0)
        # Cannot dash while on cooldown
        self.assertFalse(self.knight.trigger_dash(1.0, 0.0, self.sounds))

    def test_take_damage_and_death(self):
        self.knight.take_damage(50.0, self.sounds, self.camera)
        self.assertEqual(self.knight.hp, settings.PLAYER_MAX_HP - 50.0)
        self.assertFalse(self.knight.dead)

        # Fatal damage
        self.knight.invulnerable_timer = 0.0
        self.knight.take_damage(500.0, self.sounds, self.camera)
        self.assertEqual(self.knight.hp, 0.0)
        self.assertTrue(self.knight.dead)

    def test_experience_and_level_up(self):
        leveled = self.knight.gain_xp(50)
        self.assertFalse(leveled)
        self.assertEqual(self.knight.level, 1)

        leveled = self.knight.gain_xp(60)  # Total 110 >= 100
        self.assertTrue(leveled)
        self.assertEqual(self.knight.level, 2)
        self.assertEqual(self.knight.xp, 10)


if __name__ == "__main__":
    unittest.main()

