"""
Unit tests for UI layout, menus, HUD rendering, and fullscreen toggle.
"""

import os
import pygame
import pytest

from src.save_manager import SaveManager
from src.ui.menus import Menus
from src.ui.hud import HUD
from src.entities.player import Warrior, Ranger, Mage, Summoner
from src.upgrades.upgrade_db import get_available_upgrades


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def test_main_menu_buttons_within_screen_bounds():
    menus = Menus()
    save_mgr = SaveManager(filepath="tests/dummy_save.json")

    for res in [(1280, 720), (1920, 1080), (1024, 768), (800, 600)]:
        screen = pygame.Surface(res)
        w, h = res
        menus.draw_start_menu(screen, save_mgr, (w // 2, h // 2))

        # Check all active main menu buttons are within screen bounds
        buttons = [
            menus.btn_newgame_rect,
            menus.btn_camp_rect,
            menus.btn_stats_rect,
            menus.btn_settings_rect,
            menus.btn_controls_rect,
            menus.btn_quit_rect,
        ]
        if save_mgr.has_active_run():
            buttons.append(menus.btn_continue_rect)

        for btn in buttons:
            assert btn.width > 0, "Button width must be positive"
            assert btn.height > 0, "Button height must be positive"
            assert btn.top >= 0, f"Button top {btn.top} is negative at {res}"
            assert btn.bottom <= h, f"Button bottom {btn.bottom} exceeds screen height {h} at {res}"
            assert btn.left >= 0, f"Button left {btn.left} is negative at {res}"
            assert btn.right <= w, f"Button right {btn.right} exceeds screen width {w} at {res}"


def test_game_over_buttons_do_not_overlap():
    menus = Menus()
    screen = pygame.Surface((1280, 720))
    menus.draw_game_over_menu(screen, wave=5, kills=42, score=1200, souls_earned=10, high_score=2000, mouse_pos=(0, 0))

    restart_rect = menus.gameover_restart_btn_rect
    menu_rect = menus.gameover_menu_btn_rect

    assert not restart_rect.colliderect(menu_rect), (
        f"Game Over buttons overlap! Restart: {restart_rect}, Menu: {menu_rect}"
    )
    assert restart_rect.right < menu_rect.left, "Restart button must be to the left of Main Menu button with a gap"


def test_class_select_menu_layout():
    menus = Menus()
    menus.active_tab = "CLASS_SELECT"
    save_mgr = SaveManager(filepath="tests/dummy_save.json")

    for res in [(1280, 720), (1920, 1080), (1024, 768)]:
        screen = pygame.Surface(res)
        w, h = res
        menus.draw_start_menu(screen, save_mgr, (w // 2, h // 2))

        # Check all 4 class cards exist
        assert len(menus.class_card_rects) == 4
        prev_card = None
        for c_id, rect in menus.class_card_rects.items():
            assert rect.width > 0
            assert rect.height > 0
            assert rect.bottom <= h
            if prev_card is not None:
                assert not rect.colliderect(prev_card), f"Class cards {c_id} overlap at {res}"
            prev_card = rect

        # Check action buttons do not overlap
        assert not menus.btn_back_rect.colliderect(menus.btn_start_class_rect)
        assert menus.btn_start_class_rect.bottom <= h
        assert menus.btn_back_rect.bottom <= h


def test_upgrade_cards_render_cleanly():
    menus = Menus()
    player = Warrior(0, 0)
    cards = get_available_upgrades(player, wave=1, count=3)

    for res in [(1280, 720), (1920, 1080), (1024, 768), (800, 600)]:
        screen = pygame.Surface(res)
        w, h = res
        menus.draw_upgrade_menu(screen, cards, (w // 2, h // 2))

        assert len(menus.upgrade_card_rects) == len(cards)
        prev_r = None
        for r in menus.upgrade_card_rects:
            assert r.width > 0
            assert r.height > 0
            assert r.left >= 0
            assert r.right <= w
            assert r.bottom <= h
            if prev_r is not None:
                assert not r.colliderect(prev_r)
            prev_r = r


def test_hud_rendering_all_classes():
    hud = HUD()
    hud.show_banner("ВОЛНА 10 НАЧАЛАСЬ!", "Приготовьтесь к бою", 2.0)

    for cls in (Warrior, Ranger, Mage, Summoner):
        player = cls(100, 100)
        screen = pygame.Surface((1280, 720))
        hud.draw(
            screen=screen,
            player=player,
            wave=10,
            zombies_remaining=25,
            is_transitioning=False,
            transition_timer=0.0,
            score=5000,
            kills=120,
            muted=False
        )


def test_text_clipping_and_wrapping_helpers():
    menus = Menus()
    surf = pygame.Surface((400, 300))
    long_text = "Очень длинная строка текста для проверки корректности обрезки и переноса"

    # Test clipped text
    rendered_w = menus._render_clipped_text(surf, long_text, menus.font_card_desc, (255, 255, 255), 10, 10, max_w=120)
    assert rendered_w <= 120, f"Rendered width {rendered_w} exceeds max_w 120"

    # Test wrapped text
    h = menus._render_wrapped_text(surf, long_text, menus.font_card_desc, (255, 255, 255), 10, 30, max_w=150, line_spacing=18, max_lines=3)
    assert h > 0, "Wrapped text height must be positive"


def test_camp_menu_layout_overview_and_shifted():
    menus = Menus()
    menus.active_tab = "CAMP"
    save_mgr = SaveManager(filepath="tests/dummy_save.json")
    save_mgr.add_souls(99999)  # Large balance to test balance box stability

    for res in [(1280, 720), (1920, 1080), (1024, 768)]:
        screen = pygame.Surface(res)
        w, h = res

        # 1. Overview state (no hero selected)
        menus.camp_selected_hero = None
        menus.draw_start_menu(screen, save_mgr, (w // 2, h // 2))

        assert len(menus.camp_hero_rects) == 4, "Should have 4 hero card rects in overview"
        for cid, r in menus.camp_hero_rects.items():
            assert r.width > 0
            assert r.height > 0
            assert r.right <= w
            assert r.bottom <= h

        # 2. Shifted state for each hero
        for cid in ["warrior", "ranger", "mage", "summoner"]:
            menus.camp_selected_hero = cid
            menus.draw_start_menu(screen, save_mgr, (w // 2, h // 2))

            # Upgrade buttons should exist for the 3 stats
            for stat in ["speed", "hp", "damage"]:
                up_id = f"{cid}_{stat}"
                assert up_id in menus.camp_upgrade_btn_rects
                btn_r = menus.camp_upgrade_btn_rects[up_id]
                assert btn_r.width > 0
                assert btn_r.right <= w

            # Back to all heroes button should exist
            assert menus.camp_all_heroes_btn_rect.width > 0
            assert menus.camp_all_heroes_btn_rect.bottom <= h

