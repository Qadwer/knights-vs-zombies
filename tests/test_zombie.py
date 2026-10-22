import unittest
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
pygame.init()

from src.entities.zombie import Zombie
from src.entities.player import Warrior as Knight


class DummySoundEngine:
    def play_hit_zombie(self): pass
    def play_player_hurt(self): pass


class DummyCamera:
    def shake(self, intensity, duration): pass


class TestZombie(unittest.TestCase):
    def setUp(self):
        self.sounds = DummySoundEngine()
        self.camera = DummyCamera()

    def test_zombie_archetypes(self):
        walker = Zombie(100.0, 100.0, "walker")
        self.assertEqual(walker.max_hp, 65.0)
        self.assertEqual(walker.speed, 95.0)

        runner = Zombie(100.0, 100.0, "runner")
        self.assertEqual(runner.max_hp, 40.0)
        self.assertEqual(runner.speed, 165.0)

        spitter = Zombie(100.0, 100.0, "spitter")
        self.assertEqual(spitter.max_hp, 60.0)
        self.assertTrue(hasattr(spitter, "spit_timer"))

        brute = Zombie(100.0, 100.0, "brute")
        self.assertEqual(brute.max_hp, 240.0)
        self.assertEqual(brute.radius, 28.0)

    def test_take_damage_and_knockback(self):
        zombie = Zombie(200.0, 200.0, "walker")
        particles = []
        damage_numbers = []

        zombie.take_damage(
            amount=20,
            knock_angle=0.0,
            knock_force=100.0,
            particles=particles,
            damage_numbers=damage_numbers,
            sound_engine=self.sounds
        )

        self.assertEqual(zombie.hp, 45.0)
        self.assertGreater(zombie.knockback_vx, 0.0)
        self.assertGreater(len(damage_numbers), 0)
        self.assertGreater(len(particles), 0)
        self.assertFalse(zombie.dead)

    def test_zombie_death(self):
        zombie = Zombie(200.0, 200.0, "walker")
        particles = []
        damage_numbers = []

        zombie.take_damage(
            amount=100,
            knock_angle=0.0,
            knock_force=50.0,
            particles=particles,
            damage_numbers=damage_numbers,
            sound_engine=self.sounds
        )

        self.assertEqual(zombie.hp, 0.0)
        self.assertTrue(zombie.dead)

    def test_zombie_ai_chase(self):
        knight = Knight(500.0, 500.0)
        zombie = Zombie(200.0, 500.0, "walker")
        initial_x = zombie.x

        zombie.update(
            dt=0.1,
            player=knight,
            all_zombies=[zombie],
            projectiles=[],
            particles=[],
            damage_numbers=[],
            sound_engine=self.sounds,
            camera=self.camera
        )

        # Zombie should move towards knight (+x direction)
        self.assertGreater(zombie.x, initial_x)


if __name__ == "__main__":
    unittest.main()

