import unittest
import os
import sys
import math

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pygame
pygame.init()

from src.entities.player import (
    BasePlayer,
    Warrior,
    Ranger,
    Mage,
    Summoner,
    create_player,
)
from src.entities.projectile import (
    ArrowProjectile,
    ExplosiveArrowProjectile,
    ArcaneBoltProjectile,
    FireballProjectile,
    SoulWaveProjectile,
)
from src.entities.minion import Minion
from src.entities.zombie import Zombie
from src.save_manager import SaveManager
import tempfile


class DummySoundEngine:
    def play_sword_swing(self): pass
    def play_spin_attack(self): pass
    def play_wind_blade(self): pass
    def play_dash(self): pass
    def play_player_hurt(self): pass
    def play_bow_shoot(self): pass
    def play_explosion(self): pass
    def play_freeze(self): pass
    def play_teleport(self): pass
    def play_summon(self): pass
    def play_hit_zombie(self): pass
    def play_zombie_hurt(self): pass
    def play_zombie_death(self): pass


class DummyCamera:
    def shake(self, intensity, duration): pass


class TestPlayerClasses(unittest.TestCase):
    def setUp(self):
        self.sounds = DummySoundEngine()
        self.camera = DummyCamera()

    def test_factory_create_player(self):
        w = create_player("warrior", 100, 100)
        self.assertIsInstance(w, Warrior)
        self.assertEqual(w.class_type, "warrior")

        r = create_player("ranger", 100, 100)
        self.assertIsInstance(r, Ranger)
        self.assertEqual(r.class_type, "ranger")

        m = create_player("mage", 100, 100)
        self.assertIsInstance(m, Mage)
        self.assertEqual(m.class_type, "mage")

        s = create_player("summoner", 100, 100)
        self.assertIsInstance(s, Summoner)
        self.assertEqual(s.class_type, "summoner")

        # Unknown fallback
        fallback = create_player("paladin_unknown", 100, 100)
        self.assertIsInstance(fallback, Warrior)

    def test_warrior_skills(self):
        w = Warrior(500, 500)
        self.assertEqual(w.hp, 300.0)
        self.assertEqual(w.speed, 195.0)

        # Attack 1: Melee slash
        self.assertTrue(w.perform_attack_1(self.sounds))
        self.assertGreater(w.atk1_timer, 0)
        # Cannot attack while on cooldown
        self.assertFalse(w.perform_attack_1(self.sounds))

        # Attack 2: Spin attack
        self.assertTrue(w.perform_attack_2(self.sounds))
        self.assertGreater(w.atk2_timer, 0)

        # Attack 3: Wind blade projectile
        proj_list = []
        self.assertTrue(w.perform_attack_3(self.sounds, proj_list))
        self.assertEqual(len(proj_list), 1)

        # Dash
        self.assertTrue(w.perform_dash(self.sounds))
        self.assertTrue(w.is_dashing)

        # Berserk mechanic: bonus damage when health is below 50%
        w.berserk_bonus = 0.50
        self.assertEqual(w.get_damage_multiplier(), 1.0)
        w.hp = w.max_hp * 0.40  # Under 50%
        self.assertEqual(w.get_damage_multiplier(), 1.50)

    def test_ranger_skills(self):
        r = Ranger(500, 500)
        self.assertEqual(r.hp, 230.0)
        self.assertEqual(r.speed, 218.0)

        # Attack 1: Single arrow
        proj_list = []
        self.assertTrue(r.perform_attack_1(self.sounds, proj_list))
        self.assertEqual(len(proj_list), 1)
        self.assertIsInstance(proj_list[0], ArrowProjectile)

        # Attack 2: Multishot (5 arrows)
        proj_list = []
        self.assertTrue(r.perform_attack_2(self.sounds, proj_list))
        self.assertEqual(len(proj_list), 5)
        for p in proj_list:
            self.assertIsInstance(p, ArrowProjectile)

        # Attack 3: Explosive arrow
        proj_list = []
        self.assertTrue(r.perform_attack_3(self.sounds, proj_list))
        self.assertEqual(len(proj_list), 1)
        self.assertIsInstance(proj_list[0], ExplosiveArrowProjectile)

        # Dash: Tumble roll
        self.assertTrue(r.perform_dash(self.sounds))
        self.assertTrue(r.is_dashing)

    def test_mage_skills(self):
        m = Mage(500, 500)
        self.assertEqual(m.hp, 205.0)
        self.assertEqual(m.speed, 190.0)

        # Attack 1: Arcane bolt
        proj_list = []
        self.assertTrue(m.perform_attack_1(self.sounds, proj_list))
        self.assertEqual(len(proj_list), 1)
        self.assertIsInstance(proj_list[0], ArcaneBoltProjectile)

        # Attack 2: Fireball
        proj_list = []
        self.assertTrue(m.perform_attack_2(self.sounds, proj_list))
        self.assertEqual(len(proj_list), 1)
        self.assertIsInstance(proj_list[0], FireballProjectile)

        # Attack 3: Frost nova AoE
        zombie = Zombie(530, 500, "walker")
        zombies = [zombie]
        particles = []
        dmg_nums = []
        self.assertTrue(m.perform_attack_3(self.sounds, zombies=zombies, particles=particles, damage_numbers=dmg_nums, camera=self.camera))
        self.assertLess(zombie.hp, zombie.max_hp)
        self.assertTrue(zombie.frozen)

        # Dash: Blink teleport
        init_x, init_y = m.x, m.y
        m.facing_angle = 0.0  # Face right
        self.assertTrue(m.perform_dash(self.sounds))
        self.assertGreater(m.x, init_x + 80)  # Teleported forward

        # Mana shield: absorbs damage before HP
        m.invulnerable_timer = 0.0
        m.mana_shield_max = 50.0
        m.mana_shield = 50.0
        m.take_damage(20.0, self.sounds, self.camera)
        self.assertEqual(m.hp, 205.0)
        self.assertEqual(m.mana_shield, 30.0)

    def test_summoner_skills_and_minions(self):
        s = Summoner(500, 500)
        self.assertEqual(s.hp, 245.0)
        self.assertEqual(s.speed, 195.0)
        # Starts with 2 companion minions
        self.assertEqual(len(s.minions), 2)

        # Attack 1: Spirit whip
        zombie = Zombie(550, 500, "walker")
        s.facing_angle = 0.0
        self.assertTrue(s.perform_attack_1(self.sounds, zombies=[zombie]))
        self.assertLess(zombie.hp, zombie.max_hp)
        # Minions should now target this zombie
        for m in s.minions:
            self.assertEqual(m.target, zombie)

        # Attack 2: Summon minions up to cap of 4
        self.assertTrue(s.perform_attack_2(self.sounds))
        self.assertEqual(len(s.minions), 4)
        # Further summon when already at cap does not exceed max_minions
        s.atk2_timer = 0.0
        s.perform_attack_2(self.sounds)
        self.assertEqual(len(s.minions), 4)

        # Attack 3: Soul wave (fires 3 waves)
        proj_list = []
        self.assertTrue(s.perform_attack_3(self.sounds, proj_list))
        self.assertEqual(len(proj_list), 3)
        for p in proj_list:
            self.assertIsInstance(p, SoulWaveProjectile)

        # Dash: Ghost walk
        self.assertTrue(s.perform_dash(self.sounds))
        self.assertTrue(s.is_dashing)

        # Damage reduction per minion
        s.is_dashing = False
        s.invulnerable_timer = 0.0
        s.damage_reduction_per_minion = 0.05
        # 4 minions = 20% damage reduction
        s.take_damage(50.0, self.sounds, self.camera)
        # 50 * (1 - 0.20) = 40 damage taken
        self.assertEqual(s.hp, 245.0 - 40.0)


class TestProjectilesAndMinions(unittest.TestCase):
    def setUp(self):
        self.sounds = DummySoundEngine()

    def test_arrow_projectile(self):
        arrow = ArrowProjectile(100, 100, angle=0.0, damage=40, speed=500, max_range=200)
        self.assertFalse(arrow.dead)
        arrow.update(0.1)
        self.assertAlmostEqual(arrow.x, 150.0, delta=1.0)
        # Move past max range
        arrow.update(0.5)
        self.assertTrue(arrow.dead)

    def test_explosive_arrow(self):
        ex_arrow = ExplosiveArrowProjectile(100, 100, angle=0.0, damage=90, speed=400, max_range=200)
        self.assertFalse(ex_arrow.dead)
        # Move forward
        ex_arrow.update(0.2)
        self.assertFalse(ex_arrow.dead)
        # Reach max range
        ex_arrow.update(0.5)
        self.assertTrue(ex_arrow.dead)

    def test_arcane_bolt(self):
        bolt = ArcaneBoltProjectile(100, 100, angle=0.0, damage=35, speed=600, max_range=300)
        bolt.update(0.1)
        self.assertAlmostEqual(bolt.x, 160.0, delta=1.0)
        self.assertFalse(bolt.dead)

    def test_fireball(self):
        fb = FireballProjectile(100, 100, angle=0.0, damage=140, speed=400, max_range=200)
        self.assertFalse(fb.dead)
        fb.update(0.6)
        self.assertTrue(fb.dead)

    def test_soul_wave_pierce(self):
        sw = SoulWaveProjectile(100, 100, angle=0.0, damage=110, speed=400, max_range=500)
        self.assertEqual(sw.pierce_count, 6)
        sw.pierce_count = 0
        sw.update(0.01)
        self.assertTrue(sw.dead)

    def test_minion_ai_and_combat(self):
        summoner = Summoner(500, 500)
        minion = summoner.minions[0]
        minion.x = 500.0
        minion.y = 500.0
        zombie = Zombie(520, 500, "walker")
        minion.target = zombie

        initial_zombie_hp = zombie.hp
        # Update minion for a second to allow it to attack zombie
        minion.update(1.0, all_zombies=[zombie], particles=[], damage_numbers=[], sound_engine=self.sounds)
        self.assertLess(zombie.hp, initial_zombie_hp)

        # Minion takes damage and dies
        minion.take_damage(200.0)
        self.assertTrue(minion.dead)


class TestClassSavePersistence(unittest.TestCase):
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

    def test_save_and_load_ranger(self):
        ranger = Ranger(400, 400)
        ranger.hp = 190.0
        ranger.level = 4
        self.save_mgr.save_active_run(
            wave=3, score=700, kills=22, souls_collected_this_run=15,
            player=ranger, applied_upgrade_ids=["swift_boots"]
        )

        run = self.save_mgr.get_active_run()
        self.assertEqual(run["player"]["class_type"], "ranger")
        loaded_player = create_player(run["player"]["class_type"], 500, 500)
        self.assertIsInstance(loaded_player, Ranger)

    def test_save_and_load_mage(self):
        mage = Mage(300, 300)
        self.save_mgr.save_active_run(
            wave=5, score=1200, kills=40, souls_collected_this_run=30,
            player=mage, applied_upgrade_ids=[]
        )
        run = self.save_mgr.get_active_run()
        self.assertEqual(run["player"]["class_type"], "mage")
        loaded_player = create_player(run["player"]["class_type"], 100, 100)
        self.assertIsInstance(loaded_player, Mage)

    def test_save_and_load_summoner(self):
        summoner = Summoner(200, 200)
        self.save_mgr.save_active_run(
            wave=2, score=400, kills=10, souls_collected_this_run=10,
            player=summoner, applied_upgrade_ids=[]
        )
        run = self.save_mgr.get_active_run()
        self.assertEqual(run["player"]["class_type"], "summoner")
        loaded_player = create_player(run["player"]["class_type"], 100, 100)
        self.assertIsInstance(loaded_player, Summoner)


if __name__ == "__main__":
    unittest.main()
