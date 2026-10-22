import unittest
import os
import sys
import math

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
pygame.init()

from src.entities.player import Warrior, Ranger, Mage, Summoner
from src.entities.zombie import Zombie
from src.entities.minion import Minion
from src.entities.projectile import (
    ArrowProjectile,
    WindBladeProjectile,
    ArcaneBoltProjectile,
    FireballProjectile,
    SoulWaveProjectile,
)
from src.audio.sound_engine import SoundEngine
from src.rendering.camera import Camera
from src.config import settings
from src.upgrades.upgrade_db import (
    COMMON_BASES,
    WARRIOR_BASES,
    RANGER_BASES,
    MAGE_BASES,
    SUMMONER_BASES,
)
from src.save_manager import SaveManager
from src.game import Game


class MockSoundEngine:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class TestAllUpgradesMechanics(unittest.TestCase):
    def setUp(self):
        self.sound = MockSoundEngine()
        self.camera = Camera(800, 600)

    # -------------------------------------------------------------
    # 1. WARRIOR UPGRADES
    # -------------------------------------------------------------
    def test_warrior_berserk_damage(self):
        w = Warrior(100, 100)
        base_multi = w.get_damage_multiplier()
        self.assertEqual(base_multi, 1.0)

        # Apply Berserk upgrade lvl 2 (+40%)
        berserk_base = next(b for b in WARRIOR_BASES if b.base_id == "war_berserk")
        card = berserk_base.get_card(2)
        card.apply(w)
        self.assertAlmostEqual(w.berserk_bonus, 0.40)

        # When HP is 100%, berserk bonus does not trigger
        self.assertEqual(w.get_damage_multiplier(), 1.0)

        # When HP drops below 50%
        w.hp = w.max_hp * 0.40
        self.assertAlmostEqual(w.get_damage_multiplier(), 1.40)

    def test_warrior_wind_blade_damage_bonus(self):
        w = Warrior(100, 100)
        proj_list = []
        w.perform_attack_3(self.sound, proj_list)
        self.assertEqual(len(proj_list), 1)
        base_blade_dmg = proj_list[0].damage

        # Apply wind blade upgrade lvl 3 (+75%)
        wb_base = next(b for b in WARRIOR_BASES if b.base_id == "war_wind_blade")
        wb_base.get_card(3).apply(w)
        w.atk3_timer = 0.0

        proj_list2 = []
        w.perform_attack_3(self.sound, proj_list2)
        self.assertEqual(len(proj_list2), 1)
        upgraded_dmg = proj_list2[0].damage
        self.assertGreater(upgraded_dmg, base_blade_dmg * 1.6)

    def test_warrior_crit_chance_executioner(self):
        w = Warrior(100, 100)
        self.assertAlmostEqual(w.get_crit_chance(0.20), 0.20)

        exec_base = next(b for b in WARRIOR_BASES if b.base_id == "war_executioner")
        exec_base.get_card(2).apply(w)
        self.assertAlmostEqual(w.crit_chance_bonus, 0.16)
        self.assertAlmostEqual(w.get_crit_chance(0.20), 0.36)

    def test_warrior_iron_skin_damage_reduction(self):
        w = Warrior(100, 100)
        w.hp = 200.0
        w.take_damage(50.0, self.sound, self.camera)
        # Without reduction, HP is 150
        self.assertEqual(w.hp, 150.0)

        # Apply iron skin lvl 3 (+18% reduction, +60 max hp)
        is_base = next(b for b in WARRIOR_BASES if b.base_id == "war_iron_skin")
        is_base.get_card(3).apply(w)
        self.assertAlmostEqual(w.damage_reduction, 0.18)

        w.hp = 200.0
        w.invulnerable_timer = 0.0
        w.take_damage(50.0, self.sound, self.camera)
        # 50 * (1 - 0.18) = 41 dmg taken
        self.assertAlmostEqual(w.hp, 200.0 - 41.0)

    # -------------------------------------------------------------
    # 2. RANGER UPGRADES
    # -------------------------------------------------------------
    def test_ranger_poison_tips_application(self):
        r = Ranger(100, 100)
        poison_base = next(b for b in RANGER_BASES if b.base_id == "rng_poison_tips")
        poison_base.get_card(2).apply(r)
        self.assertAlmostEqual(r.poison_damage, 40.0)

        projectiles = []
        r.perform_attack_1(self.sound, projectiles)
        arrow = projectiles[0]
        self.assertAlmostEqual(arrow.poison_damage, 40.0)

        z = Zombie(200, 200)
        init_hp = z.hp
        # Apply poison from arrow
        z.apply_poison(arrow.poison_damage, 3.0)
        self.assertGreater(z.poison_timer, 0.0)
        self.assertGreater(z.poison_dps, 0.0)

        # Simulate update ticking for 0.6 seconds (should trigger at least 1 tick)
        z.update(0.6, r, [z], [], [], [], self.sound, self.camera)
        self.assertLess(z.hp, init_hp)

    def test_ranger_multishot_extra_arrows(self):
        r = Ranger(100, 100)
        projectiles = []
        r.perform_attack_2(self.sound, projectiles)
        self.assertEqual(len(projectiles), 5)

        ms_base = next(b for b in RANGER_BASES if b.base_id == "rng_multishot")
        ms_base.get_card(2).apply(r)
        self.assertEqual(r.multishot_extra, 2)

        r.atk2_timer = 0.0
        projectiles2 = []
        r.perform_attack_2(self.sound, projectiles2)
        self.assertEqual(len(projectiles2), 7)

    def test_ranger_ricochet_bonus_parameter(self):
        r = Ranger(100, 100)
        rico_base = next(b for b in RANGER_BASES if b.base_id == "rng_ricochet")
        rico_base.get_card(3).apply(r)
        self.assertEqual(r.ricochet_bonus, 3)

        projectiles = []
        r.perform_attack_1(self.sound, projectiles)
        arrow = projectiles[0]
        self.assertEqual(arrow.ricochet_count, 3)

    # -------------------------------------------------------------
    # 3. MAGE UPGRADES
    # -------------------------------------------------------------
    def test_mage_arcane_barrage_multishot(self):
        m = Mage(100, 100)
        projectiles = []
        m.perform_attack_1(self.sound, projectiles)
        self.assertEqual(len(projectiles), 1)

        barrage_base = next(b for b in MAGE_BASES if b.base_id == "mage_arcane_barrage")
        barrage_base.get_card(3).apply(m)
        self.assertEqual(m.arcane_barrage_extra, 3)

        m.atk1_timer = 0.0
        projectiles2 = []
        m.perform_attack_1(self.sound, projectiles2)
        self.assertEqual(len(projectiles2), 4)

    def test_mage_mana_shield_absorption(self):
        m = Mage(100, 100)
        shield_base = next(b for b in MAGE_BASES if b.base_id == "mage_mana_shield")
        shield_base.get_card(1).apply(m)
        self.assertAlmostEqual(m.mana_shield_max, 35.0)
        self.assertAlmostEqual(m.mana_shield, 35.0)

        initial_hp = m.hp
        # Take 20 damage: shield should absorb all of it, leaving HP untouched!
        m.take_damage(20.0, self.sound, self.camera)
        self.assertEqual(m.hp, initial_hp)
        self.assertAlmostEqual(m.mana_shield, 15.0)

        # Take another 25 damage: shield absorbs remaining 15, 10 goes to HP
        m.invulnerable_timer = 0.0
        m.take_damage(25.0, self.sound, self.camera)
        self.assertAlmostEqual(m.mana_shield, 0.0)
        self.assertAlmostEqual(m.hp, initial_hp - 10.0)

    def test_mage_fireball_damage_and_blast(self):
        m = Mage(100, 100)
        fb_base = next(b for b in MAGE_BASES if b.base_id == "mage_fireball_mastery")
        fb_base.get_card(2).apply(m)
        self.assertAlmostEqual(m.fireball_damage_bonus, 0.50)

        projectiles = []
        m.perform_attack_2(self.sound, projectiles)
        fb = projectiles[0]
        # Base damage is 85, with +50% should be ~128
        self.assertGreaterEqual(fb.damage, 127)
        self.assertGreater(fb.blast_radius, 75.0)

    def test_mage_frost_nova_radius_bonus(self):
        m = Mage(100, 100)
        fn_base = next(b for b in MAGE_BASES if b.base_id == "mage_frost_nova")
        fn_base.get_card(2).apply(m)
        self.assertAlmostEqual(m.frost_nova_radius_bonus, 0.36)

    # -------------------------------------------------------------
    # 4. SUMMONER UPGRADES
    # -------------------------------------------------------------
    def test_summoner_minion_multipliers(self):
        s = Summoner(100, 100)
        # Apply minion dmg (+36%), hp (+50%), speed (+30%)
        next(b for b in SUMMONER_BASES if b.base_id == "sum_minion_dmg").get_card(2).apply(s)
        next(b for b in SUMMONER_BASES if b.base_id == "sum_minion_hp").get_card(2).apply(s)
        next(b for b in SUMMONER_BASES if b.base_id == "sum_minion_speed").get_card(2).apply(s)

        self.assertAlmostEqual(s.minion_dmg_multi, 1.36)
        self.assertAlmostEqual(s.minion_hp_multi, 1.50)
        self.assertAlmostEqual(s.minion_speed_multi, 1.30)

        # Newly spawned minion should inherit these scaled stats
        m = Minion(120, 120, s)
        self.assertAlmostEqual(m.max_hp, settings.MINION_BASE_HP * 1.50)
        self.assertAlmostEqual(m.speed, settings.MINION_BASE_SPEED * 1.30)
        self.assertAlmostEqual(m.damage, int(round(settings.MINION_BASE_DAMAGE * 1.36)))

    def test_summoner_soul_burst_extra_waves(self):
        s = Summoner(100, 100)
        burst_base = next(b for b in SUMMONER_BASES if b.base_id == "sum_soul_burst")
        burst_base.get_card(2).apply(s)
        self.assertEqual(s.soul_burst_extra, 2)

        projectiles = []
        s.perform_attack_3(self.sound, projectiles)
        # Base 3 + 2 extra = 5 soul waves
        self.assertEqual(len(projectiles), 5)

    def test_summoner_spectral_shield_reduction(self):
        s = Summoner(100, 100)
        shield_base = next(b for b in SUMMONER_BASES if b.base_id == "sum_spectral_shield")
        shield_base.get_card(2).apply(s)
        self.assertAlmostEqual(s.damage_reduction_per_minion, 0.06)

        # With 2 minions alive, reduction = 2 * 0.06 = 0.12 (12%)
        s.hp = 200.0
        s.take_damage(50.0, self.sound, self.camera)
        # 50 * (1 - 0.12) = 44 dmg
        self.assertAlmostEqual(s.hp, 200.0 - 44.0)

    # -------------------------------------------------------------
    # 5. SAVE & RESUME ACTIVE RUN PERSISTENCE
    # -------------------------------------------------------------
    def test_save_and_resume_all_class_attributes(self):
        test_file = os.path.join(root_dir, "test_upgrade_save.json")
        if os.path.exists(test_file):
            os.remove(test_file)

        try:
            sm = SaveManager(filepath=test_file)
            r = Ranger(150, 150)
            # Apply some upgrades
            next(b for b in RANGER_BASES if b.base_id == "rng_poison_tips").get_card(2).apply(r)
            next(b for b in RANGER_BASES if b.base_id == "rng_ricochet").get_card(3).apply(r)
            next(b for b in RANGER_BASES if b.base_id == "rng_multishot").get_card(1).apply(r)

            applied_ids = ["rng_poison_tips_lvl2", "rng_ricochet_lvl3", "rng_multishot_lvl1"]
            sm.save_active_run(wave=3, score=1200, kills=45, souls_collected_this_run=18, player=r, applied_upgrade_ids=applied_ids)

            # Now test game reconstructs player correctly
            screen = pygame.display.set_mode((800, 600))
            game = Game(screen)
            game.save_mgr = sm
            game.start_new_game(from_saved_run=True)

            self.assertEqual(game.player.class_type, "ranger")
            self.assertAlmostEqual(game.player.poison_damage, 40.0)
            self.assertEqual(game.player.ricochet_bonus, 3)
            self.assertEqual(game.player.multishot_extra, 1)
            self.assertEqual(game.player.upgrade_levels.get("rng_poison_tips"), 2)
            self.assertEqual(game.player.upgrade_levels.get("rng_ricochet"), 3)
            self.assertEqual(game.player.upgrade_levels.get("rng_multishot"), 1)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists(test_file + ".tmp"):
                os.remove(test_file + ".tmp")

    def test_all_45_upgrades_icons_valid(self):
        from src.rendering.icons import IconEngine
        all_bases = COMMON_BASES + WARRIOR_BASES + RANGER_BASES + MAGE_BASES + SUMMONER_BASES
        self.assertEqual(len(all_bases), 45)
        for b in all_bases:
            for lvl in range(1, 6):
                card = b.get_card(lvl)
                icon_surf = IconEngine.get_icon(card.icon, size=48)
                self.assertIsNotNone(icon_surf)
                self.assertEqual(icon_surf.get_width(), 48)
                self.assertEqual(icon_surf.get_height(), 48)


if __name__ == "__main__":
    unittest.main()

