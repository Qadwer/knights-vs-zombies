"""
Обработчик ввода: клавиатура, мышь и контроллер / геймпад (Steam Deck).
"""

import math
from typing import Tuple, Dict, Any, Optional
import pygame


class InputHandler:
    def __init__(self):
        self.move_x = 0.0
        self.move_y = 0.0
        self.aim_angle = 0.0

        # Action triggers (reset every frame or on consume)
        self.wants_atk1 = False
        self.wants_atk2 = False
        self.wants_atk3 = False
        self.wants_dash = False
        self.wants_pause = False
        self.wants_toggle_sound = False
        self.wants_restart = False
        self.wants_start = False
        self.upgrade_choice: int = -1  # 0, 1, 2 if pressed 1, 2, 3

        # Mouse
        self.mouse_pos: Tuple[int, int] = (0, 0)
        self.mouse_left_down = False
        self.mouse_left_clicked = False

        # Joystick / Gamepad
        self.joystick = None
        self._init_joystick()

    def _init_joystick(self) -> None:
        try:
            if not pygame.joystick.get_init():
                pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
        except Exception:
            self.joystick = None

    def process_events(
        self,
        events: list,
        player_screen_pos: Tuple[int, int] = (0, 0),
        game_state: str = "PLAYING",
        knight_screen_pos: Optional[Tuple[int, int]] = None
    ) -> None:
        self.wants_atk1 = False
        self.wants_atk2 = False
        self.wants_atk3 = False
        self.wants_dash = False
        self.wants_pause = False
        self.wants_toggle_sound = False
        self.wants_restart = False
        self.wants_start = False
        self.upgrade_choice = -1
        self.mouse_left_clicked = False

        self.mouse_pos = pygame.mouse.get_pos()

        # Calculate mouse aim angle
        px, py = knight_screen_pos if knight_screen_pos is not None else player_screen_pos
        self.aim_angle = math.atan2(self.mouse_pos[1] - py, self.mouse_pos[0] - px)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_left_down = True
                    self.mouse_left_clicked = True
                    self.wants_atk1 = True
                elif event.button == 3:  # Right click
                    self.wants_atk2 = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_left_down = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.wants_pause = True
                elif event.key == pygame.K_m:
                    self.wants_toggle_sound = True
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.wants_start = True
                elif event.key == pygame.K_r:
                    if game_state in ("GAMEOVER", "PAUSED"):
                        self.wants_restart = True
                    self.wants_atk3 = True
                elif event.key in (pygame.K_1, pygame.K_q):
                    self.wants_atk1 = True
                    self.upgrade_choice = 0
                elif event.key in (pygame.K_2, pygame.K_e):
                    self.wants_atk2 = True
                    self.upgrade_choice = 1
                elif event.key in (pygame.K_3, pygame.K_SPACE):
                    self.wants_atk3 = True
                    self.upgrade_choice = 2
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_f):
                    self.wants_dash = True

            elif event.type == pygame.JOYBUTTONDOWN:
                # 0 = A, 1 = B, 2 = X, 3 = Y, 4 = LB, 5 = RB, 7 = Start
                if event.button in (0, 5):  # A or RB
                    self.wants_atk1 = True
                    self.wants_start = True
                elif event.button in (2, 4):  # X or LB
                    self.wants_atk2 = True
                elif event.button == 3:  # Y
                    self.wants_atk3 = True
                elif event.button == 1:  # B
                    self.wants_dash = True
                elif event.button == 7:  # Start
                    self.wants_pause = True
                    self.wants_start = True

        # Continuous keyboard movement
        keys = pygame.key.get_pressed()
        mx, my = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]: my -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: my += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: mx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: mx += 1.0

        # Continuous left click auto-attack
        if self.mouse_left_down:
            self.wants_atk1 = True

        # Joystick axis check
        if self.joystick:
            try:
                jx = self.joystick.get_axis(0)
                jy = self.joystick.get_axis(1)
                if abs(jx) > 0.2: mx = jx
                if abs(jy) > 0.2: my = jy

                # Right stick aiming
                ax = self.joystick.get_axis(2)
                ay = self.joystick.get_axis(3)
                if math.hypot(ax, ay) > 0.3:
                    self.aim_angle = math.atan2(ay, ax)
            except Exception:
                pass

        self.move_x = mx
        self.move_y = my

