import unittest
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
pygame.init()

from src.entities.player import Warrior, Ranger, Mage, Summoner
from src.upgrades.upgrade_db import (
    COMMON_BASES,
    WARRIOR_BASES,
    RANGER_BASES,
    MAGE_BASES,
    SUMMONER_BASES,
    ALL_BASES,
    ALL_UPGRADES,
    get_available_upgrades,
)
from src.rendering.icons import IconEngine
from src.ui.menus import Menus


class TestUpgradeProgression(unittest.TestCase):
    def setUp(self):
        self.warrior = Warrior(100, 100)
        self.ranger = Ranger(100, 100)
        self.mage = Mage(100, 100)
        self.summoner = Summoner(100, 100)

    def test_upgrade_database_counts(self):
        # 5 common bases
        self.assertEqual(len(COMMON_BASES), 5)
        # 10 bases per class
        self.assertEqual(len(WARRIOR_BASES), 10)
        self.assertEqual(len(RANGER_BASES), 10)
        self.assertEqual(len(MAGE_BASES), 10)
        self.assertEqual(len(SUMMONER_BASES), 10)
        # Total bases = 5 + 40 = 45
        self.assertEqual(len(ALL_BASES), 45)
        # Total leveled cards = 45 * 5 = 225
        self.assertEqual(len(ALL_UPGRADES), 225)

    def test_ranger_filtering_no_summoner_upgrades(self):
        """Crucial user bug fix: Ranger must NEVER get Summoner, Warrior, or Mage upgrades."""
        for _ in range(50):
            cards = get_available_upgrades(self.ranger, wave=1, count=3)
            self.assertEqual(len(cards), 3)
            for card in cards:
                self.assertIn(card.class_req, [None, "ranger"], f"Invalid card {card.id} for Ranger!")

    def test_warrior_filtering(self):
        for _ in range(50):
            cards = get_available_upgrades(self.warrior, wave=1, count=3)
            for card in cards:
                self.assertIn(card.class_req, [None, "warrior"], f"Invalid card {card.id} for Warrior!")

    def test_mage_filtering(self):
        for _ in range(50):
            cards = get_available_upgrades(self.mage, wave=1, count=3)
            for card in cards:
                self.assertIn(card.class_req, [None, "mage"], f"Invalid card {card.id} for Mage!")

    def test_summoner_filtering(self):
        for _ in range(50):
            cards = get_available_upgrades(self.summoner, wave=1, count=3)
            for card in cards:
                self.assertIn(card.class_req, [None, "summoner"], f"Invalid card {card.id} for Summoner!")

    def test_level_progression_sequential(self):
        """Test that upgrades advance sequentially and stop at max level 5."""
        p = Ranger(100, 100)
        p.upgrade_levels = {}

        # Pick a specific card, say rng_arrow_dmg
        arrow_base = next(b for b in RANGER_BASES if b.base_id == "rng_arrow_dmg")
        
        # Level 1
        card1 = arrow_base.get_card(1)
        self.assertEqual(card1.level, 1)
        card1.apply(p)
        self.assertEqual(p.upgrade_levels["rng_arrow_dmg"], 1)

        # Level 2
        card2 = arrow_base.get_card(2)
        self.assertEqual(card2.level, 2)
        card2.apply(p)
        self.assertEqual(p.upgrade_levels["rng_arrow_dmg"], 2)

        # Max out to level 5
        for lvl in range(3, 6):
            arrow_base.get_card(lvl).apply(p)
        self.assertEqual(p.upgrade_levels["rng_arrow_dmg"], 5)

        # Once level 5 is reached, get_available_upgrades should never offer rng_arrow_dmg
        for _ in range(30):
            cards = get_available_upgrades(p, wave=1, count=3)
            for c in cards:
                self.assertNotEqual(c.base_id, "rng_arrow_dmg")

    def test_wave_progression_tiers(self):
        """Early waves have mostly common/rare; wave 8+ offers more epics."""
        p = Warrior(100, 100)
        
        # Test wave 1
        wave1_tiers = []
        for _ in range(40):
            cards = get_available_upgrades(p, wave=1, count=3)
            wave1_tiers.extend(c.tier for c in cards)
        # Wave 1 should have very few or zero epics
        epic_count_w1 = wave1_tiers.count("epic")
        self.assertLess(epic_count_w1, len(wave1_tiers) * 0.15)

        # Test wave 8
        wave8_tiers = []
        for _ in range(40):
            cards = get_available_upgrades(p, wave=8, count=3)
            wave8_tiers.extend(c.tier for c in cards)
        epic_count_w8 = wave8_tiers.count("epic")
        # Wave 8 should have significantly more epics than Wave 1
        self.assertGreater(epic_count_w8, epic_count_w1)

    def test_all_upgrade_icons_valid(self):
        """Ensure all 45 upgrades and their levels have valid procedural icons."""
        for base in ALL_BASES:
            # Test base icon key
            ic = IconEngine.get_icon(base.icon, 48)
            self.assertIsNotNone(ic)
            self.assertEqual(ic.get_size(), (48, 48))

            # Test by base_id
            ic_base = IconEngine.get_icon(base.base_id, 48)
            self.assertIsNotNone(ic_base)
            self.assertEqual(ic_base.get_size(), (48, 48))

            # Test with level suffix (e.g. rng_arrow_dmg_lvl3)
            for lvl in range(1, 6):
                card = base.get_card(lvl)
                ic_card = IconEngine.get_icon(card.id, 48)
                self.assertIsNotNone(ic_card)
                self.assertEqual(ic_card.get_size(), (48, 48))

    def test_render_upgrade_menu(self):
        """Ensure draw_upgrade_menu renders cleanly for all classes without corner bracket levels."""
        screen = pygame.display.set_mode((1280, 720))
        menus = Menus()

        for player in [self.warrior, self.ranger, self.mage, self.summoner]:
            cards = get_available_upgrades(player, wave=3, count=3)
            # Render menu
            menus.draw_upgrade_menu(screen, cards, mouse_pos=(640, 360))
            self.assertEqual(len(menus.upgrade_card_rects), 3)


if __name__ == "__main__":
    unittest.main()

