"""
Main entry point for Knight vs Zombies (Рыцарь против Зомби).
"""

import sys
import os
import pygame

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.config import settings, get_resource_path
from src.game import Game
from src.rendering.icons import IconEngine


def main():
    pygame.init()
    pygame.display.set_caption(settings.TITLE)

    # Set application icon (try procedural warrior crest first, then banner)
    try:
        icon_surf = IconEngine.get_icon("class_warrior", 64)
        pygame.display.set_icon(icon_surf)
    except Exception:
        banner_path = get_resource_path(os.path.join("assets", "sprites", "knight_banner.png"))
        if os.path.exists(banner_path):
            try:
                icon_surf = pygame.image.load(banner_path)
                pygame.display.set_icon(icon_surf)
            except Exception:
                pass

    from src.save_manager import SaveManager
    save_mgr = SaveManager()
    is_fullscreen = save_mgr.get_setting("fullscreen", False)

    if is_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    else:
        screen = pygame.display.set_mode(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT),
            pygame.RESIZABLE | pygame.DOUBLEBUF
        )

    game = Game(screen)
    game.run()


if __name__ == "__main__":
    main()

