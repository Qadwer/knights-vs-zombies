import unittest
import os
import sys
import math

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from src.entities.player import Warrior, Ranger, Mage, Summoner, create_player
from src.entities.zombie import Zombie
from src.entities.minion import Minion
from src.entities.projectile import AcidSpitProjectile
from src.save_manager import SaveManager
from src.ui.hud import HUD
from src.game import Game


class TestInconsistenciesFixes(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))
        self.hud = HUD()

    def test_dash_cooldown_with_reduction(self):
        warrior = Warrior(200, 200)
        sound_engine = type("DummySound", (), {"play_dash": lambda self: None})()

        # Without reduction
        warrior.trigger_dash(1.0, 0.0, sound_engine)
        self.assertAlmostEqual(warrior.dash_timer, warrior.dash_cooldown, places=2)

        # With 40% reduction
        warrior.dash_timer = 0.0
        warrior.dash_cooldown_reduction = 0.40
        warrior.trigger_dash(1.0, 0.0, sound_engine)
        expected_cd = warrior.dash_cooldown * 0.60
        self.assertAlmostEqual(warrior.dash_timer, expected_cd, places=2)

        # Render HUD to ensure no crash with dash cooldown reduction
        self.hud.draw(self.screen, warrior, 1, 5, False, 0.0, 100, 10, False)

    def test_mage_mana_shield_absorption_and_hud(self):
        mage = Mage(300, 300)
        mage.mana_shield = 40.0
        mage.mana_shield_max = 60.0

        # Draw HUD with shield
        self.hud.draw(self.screen, mage, 2, 8, False, 0.0, 200, 15, False)

        # Damage absorption: shield absorbs before HP
        sound_engine = type("DummySound", (), {"play_hit_zombie": lambda self: None, "play_player_hurt": lambda self: None})()
        initial_hp = mage.hp
        mage.take_damage(25.0, sound_engine, None)
        self.assertEqual(mage.hp, initial_hp)
        self.assertAlmostEqual(mage.mana_shield, 15.0, places=1)

    def test_save_manager_syncs_base_speed(self):
        save_mgr = SaveManager(filepath="test_temp_save.json")
        try:
            save_mgr.data["permanent_upgrades"]["speed_boost"] = 3
            warrior = Warrior(100, 100)
            orig_speed = warrior.speed
            save_mgr.apply_permanent_upgrades_to_knight(warrior)
            self.assertGreater(warrior.speed, orig_speed)
            self.assertEqual(warrior.base_speed, warrior.speed)
        finally:
            if os.path.exists("test_temp_save.json"):
                os.remove("test_temp_save.json")

    def test_minion_damage_and_acid_spit_interception(self):
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="summoner")
        summoner = game.player
        self.assertGreaterEqual(len(summoner.minions), 2)
        minion = summoner.minions[0]

        # 1. Minion takes damage
        orig_hp = minion.hp
        minion.take_damage(30.0)
        self.assertEqual(minion.hp, orig_hp - 30.0)

        # 2. Zombie contacts minion and deals damage to minion
        zombie = Zombie(minion.x, minion.y, "walker")
        zombie.attack_cooldown = 0.0
        minion_prev_hp = minion.hp
        zombie.update(0.016, summoner, game.zombies, game.projectiles, game.particles, game.damage_numbers, game.sound_engine, game.camera)
        self.assertLess(minion.hp, minion_prev_hp)

        # 3. Acid spit intercepted by minion
        acid = AcidSpitProjectile(minion.x, minion.y, minion.x, minion.y, damage=15)
        game.projectiles.append(acid)
        minion_hp_before_acid = minion.hp
        game.update_playing(0.016)
        self.assertTrue(acid.dead)
        self.assertLess(minion.hp, minion_hp_before_acid)

    def test_frost_and_poison_slow_precedence(self):
        z = Zombie(300.0, 300.0, "walker")
        base_speed = z.speed
        z.slow_timer = 2.0
        z.poison_timer = 2.0
        z.poison_slow = True

        player = Warrior(500.0, 300.0)
        # When both frost (0.40) and poison (0.70) are active:
        # Strongest slow takes precedence (0.40), avoiding double-slow 0.28
        z.update(0.016, player, [], [], [], [], type("DummySound", (), {"play_hit_zombie": lambda s: None})(), None)
        self.assertTrue(z.frozen)
        # Speed factor was min(0.40, 0.70) = 0.40
        self.assertAlmostEqual(z.x, 300.0 + (base_speed * 0.40) * 0.016, places=2)

        # When frost expires, secondary poison slow (0.70) takes over smoothly
        z.slow_timer = 0.0
        z.x = 300.0
        z.y = 300.0
        z.update(0.016, player, [], [], [], [], type("DummySound", (), {"play_hit_zombie": lambda s: None})(), None)
        self.assertFalse(z.frozen)
        self.assertAlmostEqual(z.x, 300.0 + (base_speed * 0.70) * 0.016, places=2)

    def test_multilevel_xp_progression(self):
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="warrior")
        p = game.player

        # Grant XP enough for 2 levels
        xp_needed = p.xp_to_next_level + int(round(p.xp_to_next_level * 1.35)) + 10
        p.gain_xp(xp_needed)
        self.assertGreater(p.xp, p.xp_to_next_level)

        # Trigger upgrade modal
        game.show_level_up()
        self.assertEqual(game.state, "UPGRADE")

        # Select choice 0
        game.input_handler.upgrade_choice = 0
        game.update_upgrade()
        # Should remain/re-enter in UPGRADE for the second pending level
        self.assertEqual(game.state, "UPGRADE")

    def test_dead_player_no_regeneration(self):
        # Warrior with HP regen
        warrior = Warrior(200, 200)
        warrior.regen_rate = 15.0
        warrior.hp = 0.0
        warrior.dead = True
        sound_engine = type("DummySound", (), {"play_player_walk": lambda s: None})()
        warrior.update(0.5, 0.0, 0.0, 0.0, sound_engine)
        self.assertEqual(warrior.hp, 0.0)
        self.assertTrue(warrior.dead)

        # Mage with Mana Shield regen
        mage = Mage(200, 200)
        mage.mana_shield_max = 50.0
        mage.mana_shield = 0.0
        mage.hp = 0.0
        mage.dead = True
        mage.update(0.5, 0.0, 0.0, 0.0, sound_engine)
        self.assertEqual(mage.mana_shield, 0.0)

    def test_arrow_ricochet_keeps_arrow_alive(self):
        from src.entities.projectile import ArrowProjectile
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="ranger")
        z1 = Zombie(300, 300, "walker")
        z2 = Zombie(380, 300, "walker")
        game.zombies = [z1, z2]

        arrow = ArrowProjectile(290, 300, 0.0, damage=50, pierce=1, ricochet_count=1)
        game.projectiles = [arrow]

        # Update frame: arrow collides with z1, ricochets to z2
        game.update_playing(0.016)
        self.assertIn(z1, arrow.hit_zombies)
        self.assertFalse(arrow.dead)
        self.assertEqual(arrow.ricochet_count, 0)
        self.assertGreaterEqual(arrow.pierce_count, 1)

    def test_explosive_arrow_radius_scaling(self):
        ranger = Ranger(100, 100)
        ranger.explosive_arrow_bonus = 1.0  # +40% blast radius: 80 * 1.4 = 112.0
        projs = []
        ranger.atk3_timer = 0.0
        ranger.perform_attack_3(type("DummySound", (), {"play_bow_shoot": lambda s: None})(), projs)
        self.assertEqual(len(projs), 1)
        exp_proj = projs[0]
        self.assertAlmostEqual(getattr(exp_proj, "blast_radius", 80.0), 112.0, places=1)

    def test_minion_clamped_to_arena(self):
        from src.config import settings
        summoner = Summoner(200, 200)
        minion = Minion(settings.ARENA_MAX_X + 400, settings.ARENA_MAX_Y + 400, summoner)
        minion.update(0.016, [], [], [], None)
        self.assertLessEqual(minion.x, settings.ARENA_MAX_X)
        self.assertLessEqual(minion.y, settings.ARENA_MAX_Y)

    def test_dead_player_no_vampirism_revive(self):
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="warrior")
        game.player.hp = 0.0
        game.player.dead = True
        game.player.vampirism = 10.0

        z = Zombie(200, 200, "walker")
        game.on_zombie_killed(z)
        self.assertEqual(game.player.hp, 0.0)
        self.assertEqual(game.player.hp, 0.0)
        self.assertTrue(game.player.dead)

    def test_minions_die_on_summoner_death(self):
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="summoner")
        summoner = game.player
        self.assertGreaterEqual(len(summoner.minions), 2)
        minions = list(summoner.minions)

        # Trigger player death
        summoner.hp = 0.0
        summoner.take_damage(50.0, game.sound_engine, game.camera)
        self.assertTrue(summoner.dead)
        # All minions must die and be cleared
        for m in minions:
            self.assertTrue(m.dead)
        self.assertEqual(len(summoner.minions), 0)

    def test_zombie_targets_and_kills_minion(self):
        summoner = Summoner(800, 800)
        minion = Minion(250, 250, summoner)
        summoner.minions = [minion]
        zombie = Zombie(270, 250, "walker")
        zombie.attack_cooldown = 0.0

        # Zombie should target nearby minion (270, 250 vs player at 800, 800)
        damage_numbers = []
        particles = []
        sound_engine = type("DummySound", (), {"play_hit_zombie": lambda s: None, "play_player_hurt": lambda s: None})()

        # Update zombie: strikes minion
        zombie.update(0.016, summoner, [zombie], [], particles, damage_numbers, sound_engine, None)
        self.assertLess(minion.hp, minion.max_hp)
        self.assertGreaterEqual(len(damage_numbers), 1)

        # Lethal hit kills minion
        minion.take_damage(200.0, damage_numbers, sound_engine, particles)
        self.assertTrue(minion.dead)
        self.assertEqual(minion.hp, 0.0)

    def test_minion_whip_target_focus_preserved(self):
        summoner = Summoner(200, 200)
        minion = Minion(200, 200, summoner)
        summoner.minions = [minion]

        z_marked = Zombie(350, 200, "brute")
        z_closer = Zombie(230, 200, "walker")
        zombies = [z_marked, z_closer]

        # Designate target via whip command
        minion.target = z_marked

        # Run minion update - should preserve focused target even though z_closer is closer
        sound_engine = type("DummySound", (), {"play_sword_swing": lambda s: None, "play_hit_zombie": lambda s: None})()
        minion.update(0.016, zombies, [], [], sound_engine)
        self.assertEqual(minion.target, z_marked)

        # Once z_marked dies, minion falls back to closest living zombie
        z_marked.dead = True
        minion.update(0.016, zombies, [], [], sound_engine)
        self.assertEqual(minion.target, z_closer)

    def test_mage_teleport_blast_radius_scales_with_area_multi(self):
        mage = Mage(300, 300)
        mage.teleport_blast_damage = 50.0
        mage.area_multi = 1.50  # +50% AOE: 85 * 1.5 = 127.5
        # Place zombie at distance 115px (within 127.5, but outside baseline 85.0)
        z = Zombie(300 + 115, 300, "walker")
        sound_engine = type("DummySound", (), {"play_teleport": lambda s: None, "play_hit_zombie": lambda s: None})()
        damage_numbers = []

        mage.dash_timer = 0.0
        mage.trigger_dash(0.0, 0.0, sound_engine, zombies=[z], damage_numbers=damage_numbers)
        self.assertLess(z.hp, z.max_hp)
        self.assertGreaterEqual(len(damage_numbers), 1)

    def test_zombie_defends_against_attacking_minion(self):
        # Player is at 100px from zombie, but minion is right in melee combat at 30px
        summoner = Summoner(400, 300)
        zombie = Zombie(300, 300, "walker")
        minion = Minion(328, 300, summoner)
        summoner.minions = [minion]
        zombie.attack_cooldown = 0.0

        damage_numbers = []
        sound_engine = type("DummySound", (), {"play_hit_zombie": lambda s: None, "play_player_hurt": lambda s: None})()

        # Zombie should prioritize defending itself against engaging minion at 28px
        zombie.update(0.016, summoner, [zombie], [], [], damage_numbers, sound_engine, None)
        self.assertLess(minion.hp, minion.max_hp)
        self.assertEqual(len(damage_numbers), 1)
        self.assertTrue(damage_numbers[0].text.startswith("-"))

    def test_summon_skill_heals_injured_minions_and_replaces_dead(self):
        summoner = Summoner(200, 200)
        self.assertEqual(len(summoner.minions), 2)
        m1 = summoner.minions[0]
        m2 = summoner.minions[1]

        # Injure m1, kill m2
        m1.hp = 20.0
        m2.hp = 0.0
        m2.dead = True

        sound_engine = type("DummySound", (), {"play_summon": lambda s: None})()
        summoner.atk2_timer = 0.0
        summoner.perform_attack_2(sound_engine)

        # m2 was dead and replaced; army has up to max_minions (4)
        self.assertNotIn(m2, summoner.minions)
        self.assertGreaterEqual(len(summoner.minions), 3)
        # m1 was healed by soul infusion
        self.assertGreater(m1.hp, 20.0)


    def test_summon_skill_does_not_overheal_fresh_spawns(self):
        """Fresh minions summoned this cast must NOT receive soul-infusion heal (they start at 100% HP)."""
        summoner = Summoner(200, 200)
        # Kill all existing minions so the summon will create fresh ones
        for m in summoner.minions:
            m.dead = True
        summoner.minions = []

        sound_engine = type("DummySound", (), {"play_summon": lambda s: None})()
        summoner.atk2_timer = 0.0
        summoner.perform_attack_2(sound_engine)

        # All spawned minions should be at full HP (not above max_hp due to spurious heal)
        for m in summoner.minions:
            self.assertLessEqual(m.hp, m.max_hp)
            self.assertAlmostEqual(m.hp, m.max_hp, places=1,
                                   msg="Fresh minion HP should equal max_hp, not exceed it")

    def test_army_upgrade_spawns_all_new_slots(self):
        """Army upgrade level 1 raises max_minions from 4 to 5; exactly 1 new minion should be spawned."""
        from src.upgrades.upgrade_db import _apply_sum_army
        summoner = Summoner(200, 200)
        # Fill the army to base cap of 4
        while len(summoner.minions) < 4:
            summoner._spawn_minion()
        self.assertEqual(len(summoner.minions), 4)
        self.assertEqual(summoner.max_minions, 4)

        _apply_sum_army(summoner, 0, 1)  # lvl 0 → 1: +1 slot (max_minions=5)
        self.assertEqual(summoner.max_minions, 5)
        self.assertEqual(len(summoner.minions), 5, "One new minion should be spawned to fill the new slot")

    def test_zombie_contact_check_uses_postmovement_distance(self):
        """After movement a zombie that reaches the player must register the melee hit in the same frame."""
        from src.entities.zombie import Zombie
        from src.entities.player import Warrior

        warrior = Warrior(300, 300)
        warrior.invulnerable_timer = 0.0
        warrior.is_dashing = False

        # Actual radii: warrior=18, walker=17 → contact at 35px
        contact_range = 18.0 + 17.0  # warrior.radius + walker.radius
        zombie = Zombie(300 + contact_range + 1.0, 300, "walker")  # 1px outside contact
        zombie.attack_cooldown = 0.0

        sound_engine = type("DummySound", (), {"play_hit_zombie": lambda s: None, "play_player_hurt": lambda s: None})()
        camera = type("Cam", (), {"shake": lambda s, *a, **kw: None})()

        initial_hp = warrior.hp
        # Use dt=0.50 so walker (speed=95) moves 47.5px in one step — well into contact range
        zombie.update(0.50, warrior, [zombie], [], [], [], sound_engine, camera)
        # HP must decrease — zombie landed a melee hit after movement
        self.assertLess(warrior.hp, initial_hp, "Zombie should deal damage in same frame it enters contact range")

    def test_pause_save_during_wave_transition(self):
        """Saving via pause menu while is_wave_transitioning is True must persist wave + 1."""
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="warrior")
        game.wave = 3
        game.is_wave_transitioning = True

        save_file = "test_pause_transition_save.json"
        game.save_mgr = SaveManager(filepath=save_file)
        try:
            save_wave = game.wave + 1 if game.is_wave_transitioning else game.wave
            game.save_mgr.save_active_run(
                save_wave,
                game.score,
                game.kills,
                game.souls_collected_this_run,
                game.player,
                game.applied_upgrade_ids
            )
            saved_run = game.save_mgr.get_active_run()
            self.assertEqual(saved_run["wave"], 4)
        finally:
            if os.path.exists(save_file):
                os.remove(save_file)


    def test_upgrade_card_levels_never_exceed_max(self):
        """Card offered levels must never exceed max_level (5)."""
        from src.upgrades.upgrade_db import get_available_upgrades, ALL_UPGRADES
        warrior = Warrior(200, 200)
        # Set all warrior upgrades to level 4 or 5
        for u in ALL_UPGRADES:
            warrior.upgrade_levels[u.base_id] = 4

        cards = get_available_upgrades(warrior, wave=8, count=3)
        for c in cards:
            self.assertLessEqual(c.level, 5)

        # Even if all are at 5 (fallback mode)
        for u in ALL_UPGRADES:
            warrior.upgrade_levels[u.base_id] = 5
        cards_fallback = get_available_upgrades(warrior, wave=10, count=3)
        for c in cards_fallback:
            self.assertLessEqual(c.level, 5)

    def test_sound_engine_volume_control(self):
        """SoundEngine set_volume clamps between 0.0 and 1.0 and applies volume."""
        from src.audio.sound_engine import SoundEngine
        se = SoundEngine()
        se.set_volume(0.65)
        self.assertAlmostEqual(se.volume, 0.65, places=2)
        se.set_volume(-0.5)
        self.assertEqual(se.volume, 0.0)
        se.set_volume(1.8)
    def test_orbs_loop_breaks_on_level_up(self):
        """When an orb triggers a level up, the state changes to UPGRADE immediately."""
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="warrior")
        from src.entities.orb import ExperienceOrb
        # Add 2 orbs right on top of player with enough XP to level up
        o1 = ExperienceOrb(game.player.x, game.player.y, value=150)
        o2 = ExperienceOrb(game.player.x, game.player.y, value=150)
        game.orbs = [o1, o2]
        game.update_playing(0.016)
        self.assertEqual(game.state, "UPGRADE")


    def test_r_key_state_awareness(self):
        """Pressing R in PLAYING should trigger atk3 without wants_restart. In GAMEOVER, it should set wants_restart."""
        from src.input.input_handler import InputHandler
        ih = InputHandler()
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
        
        # When in PLAYING:
        ih.process_events([event], (0, 0), game_state="PLAYING")
        self.assertTrue(ih.wants_atk3)
        self.assertFalse(ih.wants_restart)

        # When in GAMEOVER:
        ih.process_events([event], (0, 0), game_state="GAMEOVER")
        self.assertTrue(ih.wants_restart)

    def test_zombie_souls_value_from_config(self):
        """Zombies must have souls_value set from their archetype config."""
        from src.config import ZOMBIE_ARCHETYPES
        for z_type, cfg in ZOMBIE_ARCHETYPES.items():
            z = Zombie(100, 100, zombie_type=z_type)
            self.assertEqual(z.souls_value, cfg["souls_value"])

    def test_minion_colossus_balance_multipliers(self):
        """Minion colossus attributes must scale according to MinionBalance constants."""
        from src.config import MinionBalance
        summoner = Summoner(100, 100)
        colossus = Minion(100, 100, summoner, is_colossus=True)
        normal = Minion(100, 100, summoner, is_colossus=False)
        self.assertAlmostEqual(colossus.max_hp / normal.max_hp, MinionBalance.COLOSSUS_HP_MULTI, places=2)
        self.assertAlmostEqual(colossus.base_damage / normal.base_damage, MinionBalance.COLOSSUS_DMG_MULTI, places=2)
        self.assertEqual(colossus.radius, MinionBalance.COLOSSUS_RADIUS)
        self.assertEqual(normal.radius, MinionBalance.ATTACK_RADIUS)

    def test_wind_blade_deflection(self):
        """Warrior's WindBlade projectile should destroy AcidSpit if can_deflect_projectiles is True."""
        from src.entities.projectile import WindBladeProjectile, AcidSpitProjectile
        game = Game(self.screen)
        game.start_new_game(from_saved_run=False, class_type="warrior")
        game.player.can_deflect_projectiles = True

        blade = WindBladeProjectile(100, 100, angle=0.0, damage=50)
        spit = AcidSpitProjectile(105, 100, 0, 100)
        game.projectiles = [blade, spit]

        game.update_playing(0.016)
        self.assertTrue(spit.dead)


if __name__ == "__main__":
    unittest.main()

