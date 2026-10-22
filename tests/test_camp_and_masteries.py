"""
Tests for Camp Redesign, Per-Class Upgrades, and Hero Masteries:
- Warrior: Projectile deflection (Sword / Whirlwind destroys AcidSpit)
- Ranger: +50% projectile speed
- Mage: 3 orbiting barrier orbs absorb 1 attack, 15s cooldown, respawn
- Summoner: Every 10th minion is a Colossus (increased HP, damage, scale)
- Camp UI: 4 hero selection cards, shifted hero view, 3 upgrades, mastery card
"""

import math
import os
import tempfile
import pygame
import pytest

from src.save_manager import SaveManager, HERO_CLASSES, HERO_META
from src.entities.player import Warrior, Ranger, Mage, Summoner
from src.entities.projectile import AcidSpitProjectile, ArrowProjectile, ExplosiveArrowProjectile
from src.entities.minion import Minion
from src.ui.menus import Menus
from src.game import Game


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    if not pygame.get_init():
        pygame.init()
    yield


def get_temp_save_mgr():
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tf.close()
    return SaveManager(filepath=tf.name)


def test_per_class_camp_upgrades():
    save_mgr = get_temp_save_mgr()
    save_mgr.add_souls(5000)

    for cid in HERO_CLASSES:
        # Initial levels are 0
        assert save_mgr.get_upgrade_level(f"{cid}_speed") == 0
        assert save_mgr.get_upgrade_level(f"{cid}_hp") == 0
        assert save_mgr.get_upgrade_level(f"{cid}_damage") == 0
        assert not save_mgr.is_mastery_unlocked(cid)
        assert save_mgr.get_class_total_levels(cid) == 0

        # Buy 5 levels for each stat
        for _ in range(5):
            assert save_mgr.buy_upgrade(f"{cid}_speed")
            assert save_mgr.buy_upgrade(f"{cid}_hp")
            assert save_mgr.buy_upgrade(f"{cid}_damage")

        # Now all are at max level (5)
        assert save_mgr.get_upgrade_level(f"{cid}_speed") == 5
        assert save_mgr.get_upgrade_level(f"{cid}_hp") == 5
        assert save_mgr.get_upgrade_level(f"{cid}_damage") == 5
        assert save_mgr.get_class_total_levels(cid) == 15
        assert save_mgr.is_mastery_unlocked(cid)

        # Cannot buy beyond max level
        assert not save_mgr.can_buy_upgrade(f"{cid}_speed")
        assert not save_mgr.buy_upgrade(f"{cid}_speed")

    if os.path.exists(save_mgr.filepath):
        os.remove(save_mgr.filepath)


def test_warrior_mastery_deflect_projectiles():
    save_mgr = get_temp_save_mgr()
    save_mgr.add_souls(3000)
    for _ in range(5):
        save_mgr.buy_upgrade("warrior_speed")
        save_mgr.buy_upgrade("warrior_hp")
        save_mgr.buy_upgrade("warrior_damage")
    assert save_mgr.is_mastery_unlocked("warrior")

    screen = pygame.Surface((1280, 720))
    game = Game(screen)
    game.save_mgr = save_mgr
    game.start_new_game(from_saved_run=False, class_type="warrior")
    assert game.player.can_deflect_projectiles is True

    # Spawn an incoming AcidSpitProjectile directly in front of warrior
    spit = AcidSpitProjectile(game.player.x + 60.0, game.player.y, game.player.x, game.player.y)
    game.projectiles.append(spit)

    # Face the projectile and perform attack 1
    game.player.facing_angle = 0.0
    game.player.atk1_timer = 0.0
    assert game.trigger_attack_1() is True

    # Spit projectile should be destroyed by deflect
    assert spit.dead is True

    # Test attack 2 (whirlwind) deflection
    spit2 = AcidSpitProjectile(game.player.x - 70.0, game.player.y, game.player.x, game.player.y)
    game.projectiles.append(spit2)
    game.player.atk2_timer = 0.0
    assert game.trigger_attack_2() is True
    assert spit2.dead is True

    if os.path.exists(save_mgr.filepath):
        os.remove(save_mgr.filepath)


def test_ranger_mastery_projectile_speed():
    save_mgr = get_temp_save_mgr()
    save_mgr.add_souls(3000)
    for _ in range(5):
        save_mgr.buy_upgrade("ranger_speed")
        save_mgr.buy_upgrade("ranger_hp")
        save_mgr.buy_upgrade("ranger_damage")
    assert save_mgr.is_mastery_unlocked("ranger")

    ranger = Ranger(500.0, 500.0)
    initial_multi = getattr(ranger, "projectile_speed_multi", 1.0)
    save_mgr.apply_permanent_upgrades_to_knight(ranger)
    assert ranger.projectile_speed_multi == pytest.approx(initial_multi * 1.50)

    # Spawn arrows and verify speed is increased by 50%
    projs = []
    class DummySound:
        def play_bow_shoot(self): pass
    ranger.perform_attack_1(DummySound(), projs)
    assert len(projs) == 1
    assert projs[0].speed == pytest.approx(660.0 * 1.50)

    if os.path.exists(save_mgr.filepath):
        os.remove(save_mgr.filepath)


def test_mage_mastery_barrier_orbs():
    save_mgr = get_temp_save_mgr()
    save_mgr.add_souls(3000)
    for _ in range(5):
        save_mgr.buy_upgrade("mage_speed")
        save_mgr.buy_upgrade("mage_hp")
        save_mgr.buy_upgrade("mage_damage")
    assert save_mgr.is_mastery_unlocked("mage")

    mage = Mage(500.0, 500.0)
    save_mgr.apply_permanent_upgrades_to_knight(mage)
    assert mage.barrier_orbs_active is True
    assert mage.barrier_orbs == 3

    class DummySound:
        def play_teleport(self): pass
        def play_hit_zombie(self): pass
        def play_player_hurt(self): pass

    class DummyCam:
        def shake(self, *args): pass

    initial_hp = mage.hp
    # First hit: absorbed completely by 3 barrier orbs!
    mage.take_damage(50.0, DummySound(), DummyCam())
    assert mage.hp == initial_hp
    assert mage.barrier_orbs == 0
    assert mage.barrier_respawn_timer == pytest.approx(15.0)

    # Next hit during cooldown: takes damage
    mage.invulnerable_timer = 0.0
    mage.take_damage(30.0, DummySound(), DummyCam())
    assert mage.hp < initial_hp

    # Fast-forward 15 seconds: barrier orbs respawn!
    mage.update(15.1, 0.0, 0.0, 0.0, DummySound())
    assert mage.barrier_orbs == 3
    assert mage.barrier_respawn_timer == 0.0

    # Absorbs another hit!
    hp_before = mage.hp
    mage.invulnerable_timer = 0.0
    mage.take_damage(60.0, DummySound(), DummyCam())
    assert mage.hp == hp_before
    assert mage.barrier_orbs == 0

    if os.path.exists(save_mgr.filepath):
        os.remove(save_mgr.filepath)


def test_summoner_mastery_colossus_minion():
    save_mgr = get_temp_save_mgr()
    save_mgr.add_souls(3000)
    for _ in range(5):
        save_mgr.buy_upgrade("summoner_speed")
        save_mgr.buy_upgrade("summoner_hp")
        save_mgr.buy_upgrade("summoner_damage")
    assert save_mgr.is_mastery_unlocked("summoner")

    summoner = Summoner(500.0, 500.0)
    save_mgr.apply_permanent_upgrades_to_knight(summoner)
    assert summoner.colossus_minion_unlocked is True

    # Spawn minions up to 10
    summoner.max_minions = 20
    # Clear initial 2 minions to have clean count
    summoner.minions.clear()
    summoner.summon_counter = 0

    for _ in range(10):
        summoner._spawn_minion()

    assert len(summoner.minions) == 10
    # 10th minion is a Colossus
    colossus = summoner.minions[9]
    assert colossus.is_colossus is True
    assert colossus.scale == pytest.approx(1.45)
    assert colossus.radius == 17.0
    assert colossus.max_hp > 85.0 * 2.0
    assert colossus.base_damage > 22.0 * 1.8

    # Minion 9 is standard
    normal = summoner.minions[8]
    assert normal.is_colossus is False
    assert normal.radius == 12.0
    assert normal.scale == 1.0

    if os.path.exists(save_mgr.filepath):
        os.remove(save_mgr.filepath)


def test_camp_menu_ui_overview_and_shifted_hero():
    menus = Menus()
    save_mgr = get_temp_save_mgr()
    screen = pygame.Surface((1280, 720))

    # 1. Overview state (camp_selected_hero = None)
    menus.active_tab = "CAMP"
    menus.camp_selected_hero = None
    menus.draw_start_menu(screen, save_mgr, (640, 360))

    # All 4 hero cards exist
    for cid in HERO_CLASSES:
        assert cid in menus.camp_hero_rects
        rect = menus.camp_hero_rects[cid]
        assert rect.width > 150
        assert rect.height > 200

    # 2. Shifted state (select a hero)
    menus.camp_selected_hero = "warrior"
    menus.draw_start_menu(screen, save_mgr, (640, 360))

    # Quick switch tabs exist
    for cid in HERO_CLASSES:
        assert cid in menus.camp_hero_rects

    # 3 upgrade buttons exist for the selected hero
    assert "warrior_speed" in menus.camp_upgrade_btn_rects
    assert "warrior_hp" in menus.camp_upgrade_btn_rects
    assert "warrior_damage" in menus.camp_upgrade_btn_rects

    # All heroes button exists
    assert menus.camp_all_heroes_btn_rect.width > 0

    if os.path.exists(save_mgr.filepath):
        os.remove(save_mgr.filepath)
