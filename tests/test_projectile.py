import unittest
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
pygame.init()

from src.entities.projectile import WindBladeProjectile, AcidSpitProjectile


class TestProjectile(unittest.TestCase):
    def test_wind_blade_movement_and_range(self):
        blade = WindBladeProjectile(100.0, 100.0, angle=0.0, damage=110, max_range=300.0, speed=200.0)
        self.assertEqual(blade.traveled, 0.0)
        self.assertFalse(blade.dead)

        # Update 1 second -> traveled 200 px
        blade.update(1.0)
        self.assertAlmostEqual(blade.x, 300.0, places=1)
        self.assertAlmostEqual(blade.y, 100.0, places=1)
        self.assertFalse(blade.dead)

        # Update another 1 second -> total 400 px >= 300 max_range -> dead
        blade.update(1.0)
        self.assertTrue(blade.dead)

    def test_wind_blade_pierce(self):
        blade = WindBladeProjectile(100.0, 100.0, angle=0.0, damage=110)
        self.assertEqual(blade.pierce_count, 8)
        blade.pierce_count = 0
        blade.update(0.01)
        self.assertTrue(blade.dead)

    def test_acid_spit_movement(self):
        spit = AcidSpitProjectile(100.0, 100.0, target_x=200.0, target_y=100.0, damage=18, speed=100.0)
        self.assertFalse(spit.dead)
        spit.update(0.5)
        self.assertGreater(spit.x, 100.0)


if __name__ == "__main__":
    unittest.main()

