import unittest
import os
import sys
import tempfile

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
pygame.init()

from src.save_manager import SaveManager
from src.entities.player import Warrior as Knight
from src.config import settings


class TestSaveManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.save_mgr = SaveManager(filepath=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except Exception:
                pass

    def test_default_state(self):
        self.assertEqual(self.save_mgr.high_score, 0)
        self.assertEqual(self.save_mgr.max_wave, 0)
        self.assertEqual(self.save_mgr.total_kills, 0)
        self.assertEqual(self.save_mgr.total_games, 0)
        self.assertEqual(self.save_mgr.souls, 0)
        self.assertFalse(self.save_mgr.has_active_run())

    def test_record_game_end(self):
        self.save_mgr.record_game_end(wave=5, kills=30, score=1200, souls_earned=45)
        self.assertEqual(self.save_mgr.total_games, 1)
        self.assertEqual(self.save_mgr.total_kills, 30)
        self.assertEqual(self.save_mgr.high_score, 1200)
        self.assertEqual(self.save_mgr.max_wave, 5)
        self.assertEqual(self.save_mgr.souls, 45)

        # Another run with lower score and wave
        self.save_mgr.record_game_end(wave=3, kills=15, score=600, souls_earned=20)
        self.assertEqual(self.save_mgr.total_games, 2)
        self.assertEqual(self.save_mgr.total_kills, 45)
        self.assertEqual(self.save_mgr.high_score, 1200)  # High score preserved
        self.assertEqual(self.save_mgr.max_wave, 5)       # Max wave preserved
        self.assertEqual(self.save_mgr.souls, 65)

    def test_buy_permanent_upgrade(self):
        # Cannot buy without souls
        self.assertFalse(self.save_mgr.can_buy_upgrade("hp_boost"))
        self.assertFalse(self.save_mgr.buy_upgrade("hp_boost"))

        # Add souls and buy
        self.save_mgr.add_souls(100)
        self.assertTrue(self.save_mgr.can_buy_upgrade("hp_boost"))
        cost = self.save_mgr.get_upgrade_cost("hp_boost")
        self.assertTrue(self.save_mgr.buy_upgrade("hp_boost"))
        self.assertEqual(self.save_mgr.get_upgrade_level("hp_boost"), 1)
        self.assertEqual(self.save_mgr.souls, 100 - cost)

    def test_apply_permanent_upgrades(self):
        self.save_mgr.add_souls(500)
        self.save_mgr.buy_upgrade("hp_boost")      # +25 HP
        self.save_mgr.buy_upgrade("damage_boost")  # +8% dmg

        knight = Knight(500.0, 500.0)
        base_hp = knight.max_hp
        base_dmg = knight.damage_multi

        self.save_mgr.apply_permanent_upgrades_to_knight(knight)
        self.assertEqual(knight.max_hp, base_hp + 25.0)
        self.assertEqual(knight.hp, knight.max_hp)
        self.assertAlmostEqual(knight.damage_multi, base_dmg + 0.08, places=2)

    def test_active_run_save_and_clear(self):
        knight = Knight(500.0, 500.0)
        knight.hp = 180.0
        knight.level = 3
        knight.xp = 45

        self.save_mgr.save_active_run(
            wave=4,
            score=950,
            kills=25,
            souls_collected_this_run=35,
            player=knight,
            applied_upgrade_ids=["dmg_sharp", "swift_boots"]
        )

        self.assertTrue(self.save_mgr.has_active_run())
        run = self.save_mgr.get_active_run()
        self.assertEqual(run["wave"], 4)
        self.assertEqual(run["score"], 950)
        self.assertEqual(run["player"]["hp"], 180.0)
        self.assertEqual(run["player"]["level"], 3)
        self.assertEqual(run["applied_upgrade_ids"], ["dmg_sharp", "swift_boots"])

        self.save_mgr.clear_active_run()
        self.assertFalse(self.save_mgr.has_active_run())


if __name__ == "__main__":
    unittest.main()

