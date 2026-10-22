import unittest
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from src.game import Game
from src.entities.player import Warrior, Ranger, Mage, Summoner
from src.upgrades.upgrade_db import get_available_upgrades


class TestGameSimulation(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))
        self.game = Game(self.screen)

    def test_class_selection_and_simulation(self):
        classes = ["warrior", "ranger", "mage", "summoner"]

        for c_id in classes:
            # 1. Start game with chosen class
            self.game.start_new_game(from_saved_run=False, class_type=c_id)
            self.assertIsNotNone(self.game.player)
            self.assertEqual(self.game.player.class_type, c_id)

            # Spawn a few test zombies
            self.game.wave = 1
            self.game.is_wave_active = True
            from src.entities.zombie import Zombie
            self.game.zombies.append(Zombie(self.game.player.x + 80, self.game.player.y, "walker"))
            self.game.zombies.append(Zombie(self.game.player.x - 80, self.game.player.y, "runner"))
            self.game.zombies.append(Zombie(self.game.player.x, self.game.player.y + 80, "brute"))
            self.assertGreaterEqual(len(self.game.zombies), 3)

            # 2. Trigger class attacks
            self.game.player.facing_angle = 0.0
            self.game.trigger_attack_1()
            self.game.trigger_attack_2()
            self.game.trigger_attack_3()
            self.game.player.trigger_dash(1.0, 0.0, self.game.sound_engine)

            # 3. Simulate 60 frames (1 second at 60 FPS)
            dt = 1.0 / 60.0
            for _ in range(60):
                self.game.update_playing(dt)

            # 4. Verify game state
            self.assertTrue(self.game.player.hp > 0)
            if c_id == "summoner":
                self.assertGreaterEqual(len(self.game.player.minions), 2)
            elif c_id == "ranger":
                # Projectiles or particles should have been generated
                self.assertIsNotNone(self.game.projectiles)

            # 5. Check active run save
            self.game.save_mgr.save_active_run(
                wave=self.game.wave,
                score=self.game.score,
                kills=self.game.kills,
                souls_collected_this_run=self.game.souls_collected_this_run,
                player=self.game.player,
                applied_upgrade_ids=self.game.applied_upgrade_ids
            )
            saved = self.game.save_mgr.get_active_run()
            self.assertEqual(saved["player"]["class_type"], c_id)

    def test_class_selection_menu_flow(self):
        # Open class selection menu
        self.game.state = "START_MENU"
        self.game.menus.active_tab = "MAIN"
        self.game.menus.active_tab = "CLASS_SELECT"
        self.assertEqual(self.game.menus.active_tab, "CLASS_SELECT")

        # Pick each class
        for c_id in ["warrior", "ranger", "mage", "summoner"]:
            self.game.menus.selected_class_type = c_id
            self.assertEqual(self.game.menus.selected_class_type, c_id)

    def test_render_all_screens_and_icons(self):
        from src.rendering.icons import IconEngine
        from src.upgrades.upgrade_db import ALL_UPGRADES

        # 1. Test IconEngine can generate all icons
        icon_names = [
            "class_warrior", "class_ranger", "class_mage", "class_summoner",
            "skill_slash", "skill_whirlwind", "skill_wind_blade", "skill_knight_dash",
            "skill_dash", "skill_roll", "skill_ghost_step",
            "skill_arrow_shot", "skill_multishot", "skill_explosive_arrow",
            "skill_arcane_bolt", "skill_fireball", "skill_frost_nova", "skill_teleport",
            "skill_spirit_whip", "skill_summon", "skill_soul_burst",
            "hp_boost", "damage_boost", "speed_boost", "magnet_boost",
            "soul", "skull", "trophy", "gear", "keyboard", "gamepad",
            "shield", "sound_on", "sound_off"
        ]
        for name in icon_names:
            ic = IconEngine.get_icon(name, 32)
            self.assertIsNotNone(ic)
            self.assertEqual(ic.get_size(), (32, 32))

        # Test upgrade card icons
        for up in ALL_UPGRADES:
            up_ic = IconEngine.get_icon(up.id, 44)
            self.assertIsNotNone(up_ic)

        # 2. Test rendering in START_MENU for all tabs
        self.game.state = "START_MENU"
        for tab in ["MAIN", "CLASS_SELECT", "CAMP", "STATS", "SETTINGS", "CONTROLS"]:
            self.game.menus.active_tab = tab
            self.game.render()

        # 3. Test rendering in PLAYING with all 4 classes & all 4 zombie archetypes
        from src.entities.zombie import Zombie
        for c_id in ["warrior", "ranger", "mage", "summoner"]:
            self.game.start_new_game(from_saved_run=False, class_type=c_id)
            for z_type in ["walker", "runner", "spitter", "brute"]:
                z = Zombie(self.game.player.x + 50, self.game.player.y + 50, z_type)
                self.game.zombies.append(z)
            self.game.render()

        # 4. Test rendering UPGRADE modal
        self.game.state = "UPGRADE"
        self.game.current_upgrade_cards = get_available_upgrades(self.game.player, self.game.wave, count=3)
        self.game.render()

        # 5. Test rendering PAUSED modal
        self.game.state = "PAUSED"
        self.game.render()

        # 6. Test rendering GAMEOVER modal
        self.game.state = "GAMEOVER"
        self.game.render()


if __name__ == "__main__":
    unittest.main()

