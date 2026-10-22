"""
Главный координатор игры: управление игровыми состояниями, игровыми циклами обновления
и отрисовки, прогрессией волн, боем 4 классов (Воин, Лучник, Маг, Призыватель),
миньонами, мета-прогрессией и сохранением/загрузкой.
"""

import math
import random
from typing import List, Optional
import pygame
from .config import settings, EconomyBalance, ZombieWaveBalance, MinionBalance
from .entities.player import BasePlayer, Warrior, Ranger, Mage, Summoner, create_player
from .entities.zombie import Zombie
from .entities.projectile import (
    WindBladeProjectile,
    ArrowProjectile,
    ExplosiveArrowProjectile,
    ArcaneBoltProjectile,
    FireballProjectile,
    SoulWaveProjectile,
    AcidSpitProjectile,
)
from .entities.orb import ExperienceOrb
from .rendering.camera import Camera
from .rendering.renderer import Renderer
from .rendering.effects import Particle, DamageNumber, BloodDecal
from .audio.sound_engine import SoundEngine
from .input.input_handler import InputHandler
from .ui.hud import HUD
from .ui.menus import Menus
from .upgrades.upgrade_db import ALL_UPGRADES, UpgradeCard, get_available_upgrades
from .save_manager import SaveManager


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True

        # Save & Progress Manager
        self.save_mgr = SaveManager()

        # Modules
        w, h = screen.get_size()
        self.camera = Camera(w, h)
        self.renderer = Renderer(screen)
        self.sound_engine = SoundEngine()
        self.input_handler = InputHandler()
        self.hud = HUD()
        self.menus = Menus()

        # Apply saved audio setting
        if self.save_mgr.get_setting("sfx_muted", False):
            self.sound_engine.muted = True
        saved_vol = self.save_mgr.get_setting("sfx_volume", 1.0)
        self.sound_engine.set_volume(saved_vol)

        # Game State: "MENU", "PLAYING", "UPGRADE", "PAUSED", "GAMEOVER"
        self.state = "MENU"

        # Score, Wave & Souls variables
        self.score = 0
        self.kills = 0
        self.wave = 1
        self.souls_collected_this_run = 0
        self.applied_upgrade_ids: List[str] = []

        self.is_wave_active = False
        self.zombies_to_spawn = 0
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        self.is_wave_transitioning = False
        self.wave_transition_timer = 0.0

        # Entities
        self.player: Optional[BasePlayer] = None
        self.zombies: List[Zombie] = []
        self.projectiles: list = []
        self.orbs: List[ExperienceOrb] = []
        self.particles: List[Particle] = []
        self.damage_numbers: List[DamageNumber] = []
        self.blood_decals: List[BloodDecal] = []

        # Current upgrade choices for Level Up
        self.current_upgrade_cards: List[UpgradeCard] = []

    def toggle_fullscreen(self) -> None:
        is_fs = not self.save_mgr.get_setting("fullscreen", False)
        self.save_mgr.set_setting("fullscreen", is_fs)
        if is_fs:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        else:
            self.screen = pygame.display.set_mode(
                (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT),
                pygame.RESIZABLE | pygame.DOUBLEBUF
            )
        w, h = self.screen.get_size()
        self.camera.resize(w, h)
        self.renderer.on_resize(self.screen)

    def start_new_game(self, from_saved_run: bool = False, class_type: str = "warrior") -> None:
        self.zombies.clear()
        self.projectiles.clear()
        self.orbs.clear()
        self.particles.clear()
        self.damage_numbers.clear()
        self.blood_decals.clear()

        center_x = (settings.ARENA_MIN_X + settings.ARENA_MAX_X) / 2.0
        center_y = (settings.ARENA_MIN_Y + settings.ARENA_MAX_Y) / 2.0

        if from_saved_run and self.save_mgr.has_active_run():
            run_data = self.save_mgr.get_active_run()
            self.wave = run_data.get("wave", 1)
            self.score = run_data.get("score", 0)
            self.kills = run_data.get("kills", 0)
            self.souls_collected_this_run = run_data.get("souls_collected", 0)
            self.applied_upgrade_ids = list(run_data.get("applied_upgrade_ids", []))

            # Reconstruct player from saved data
            p_data = run_data.get("player", {})
            saved_class = p_data.get("class_type", "warrior")
            self.player = create_player(saved_class, center_x, center_y)

            # Restore base and extended stats
            for attr, val in p_data.items():
                if attr not in ("class_type", "upgrade_levels", "xp_to_next"):
                    setattr(self.player, attr, val)

            # Ensure xp_to_next_level is properly set even from older saves
            if "xp_to_next" in p_data and "xp_to_next_level" not in p_data:
                self.player.xp_to_next_level = p_data["xp_to_next"]

            # Ensure summoner minions match loaded scaling and are healthy
            if hasattr(self.player, "minions"):
                base_hp = MinionBalance.BASE_HP
                base_spd = MinionBalance.BASE_SPEED
                # Keep active minions or respawn up to initial minimum if empty
                if not self.player.minions and hasattr(self.player, "_spawn_minion"):
                    self.player._spawn_minion()
                    self.player._spawn_minion()
                for m in self.player.minions:
                    m.max_hp = base_hp * getattr(self.player, "minion_hp_multi", 1.0)
                    m.hp = m.max_hp
                    m.speed = base_spd * getattr(self.player, "minion_speed_multi", 1.0)

            # Restore upgrade levels
            self.player.upgrade_levels = dict(p_data.get("upgrade_levels", {}))
            for uid in self.applied_upgrade_ids:
                parts = uid.rsplit("_lvl", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    base_id, lvl = parts[0], int(parts[1])
                    self.player.upgrade_levels[base_id] = max(self.player.upgrade_levels.get(base_id, 0), lvl)
        else:
            # Fresh new run with chosen class
            self.save_mgr.clear_active_run()
            self.score = 0
            self.kills = 0
            self.wave = 1
            self.souls_collected_this_run = 0
            self.applied_upgrade_ids.clear()

            self.player = create_player(class_type, center_x, center_y)
            self.player.upgrade_levels = {}
            # Apply permanent camp upgrades
            self.save_mgr.apply_permanent_upgrades(self.player)

        self.state = "PLAYING"
        self.start_wave(self.wave)

    def start_wave(self, wave_num: int) -> None:
        self.wave = wave_num
        self.is_wave_active = True
        self.is_wave_transitioning = False
        self.wave_transition_timer = 0.0
        self.zombies_to_spawn = 10 + wave_num * 5
        self.spawn_interval = max(
            ZombieWaveBalance.SPAWN_INTERVAL_MIN,
            ZombieWaveBalance.SPAWN_INTERVAL_BASE - wave_num * 0.08
        )
        self.spawn_timer = 0.5
        
        self.sound_engine.play_wave_start()
        
        # Формируем подзаголовок с учетом бонуса здоровья зомби
        hp_bonus_pct = int((self.wave - 1) * ZombieWaveBalance.HP_SCALE_PER_WAVE * 100)
        if wave_num % 5 == 0:
            subtitle = f"БОСС-ВОЛНА: Орда мутантов! (Мощь врагов +{hp_bonus_pct}%)"
        elif hp_bonus_pct > 0:
            subtitle = f"Орда зомби надвигается! (Здоровье врагов +{hp_bonus_pct}%)"
        else:
            subtitle = "Орда зомби надвигается!"
            
        self.hud.show_banner(f"ВОЛНА {wave_num}", subtitle, duration=2.4)

    def spawn_single_zombie(self) -> None:
        side = random.randint(0, 3)
        margin = 70.0
        if side == 0:  # Top
            x = random.uniform(settings.ARENA_MIN_X + margin, settings.ARENA_MAX_X - margin)
            y = settings.ARENA_MIN_Y + margin
        elif side == 1:  # Right
            x = settings.ARENA_MAX_X - margin
            y = random.uniform(settings.ARENA_MIN_Y + margin, settings.ARENA_MAX_Y - margin)
        elif side == 2:  # Bottom
            x = random.uniform(settings.ARENA_MIN_X + margin, settings.ARENA_MAX_X - margin)
            y = settings.ARENA_MAX_Y - margin
        else:  # Left
            x = settings.ARENA_MIN_X + margin
            y = random.uniform(settings.ARENA_MIN_Y + margin, settings.ARENA_MAX_Y - margin)

        rand = random.random()
        z_type = "walker"
        if self.wave >= 2 and rand < 0.28:
            z_type = "runner"
        elif self.wave >= 3 and rand < 0.45:
            z_type = "spitter"
        elif self.wave >= 4 and rand < 0.60:
            z_type = "brute"

        if self.wave % 5 == 0 and random.random() < 0.35:
            z_type = "brute"

        self.zombies.append(Zombie(x, y, z_type, wave=self.wave))

    # ==========================================================
    # COMBAT TRIGGERS (POLYMORPHIC FOR ALL 4 CLASSES)
    # ==========================================================
    def trigger_attack_1(self) -> bool:
        if not self.player: return False

        if self.player.class_type == "warrior":
            if not self.player.perform_attack_1(self.sound_engine):
                return False
            hit_angle = self.player.facing_angle
            hit_range = getattr(self.player, "atk1_range", 85.0) * self.player.area_multi
            damage = int(round(getattr(self.player, "atk1_damage", 35) * self.player.get_damage_multiplier()))
            hit_arc = getattr(self.player, "atk1_arc", 1.15)

            for z in list(self.zombies):
                if z.dead: continue
                dist = math.hypot(z.x - self.player.x, z.y - self.player.y)
                if dist <= hit_range + z.radius:
                    ang = math.atan2(z.y - self.player.y, z.x - self.player.x)
                    diff = abs((ang - hit_angle + math.pi) % (math.pi * 2) - math.pi)
                    if diff < hit_arc:
                        crit_chance = self.player.get_crit_chance(0.20)
                        is_crit = random.random() < crit_chance
                        actual_dmg = int(round(damage * 1.8)) if is_crit else damage
                        z.take_damage(actual_dmg, ang, 260.0, self.particles, self.damage_numbers, self.sound_engine, is_crit)

            # Bullet Deflection Mastery (Warrior): Melee slash destroys incoming enemy projectiles
            if getattr(self.player, "can_deflect_projectiles", False):
                for proj in list(self.projectiles):
                    if proj.dead or not isinstance(proj, AcidSpitProjectile):
                        continue
                    p_dist = math.hypot(proj.x - self.player.x, proj.y - self.player.y)
                    if p_dist <= hit_range + proj.radius + 30.0:
                        p_ang = math.atan2(proj.y - self.player.y, proj.x - self.player.x)
                        p_diff = abs((p_ang - hit_angle + math.pi) % (math.pi * 2) - math.pi)
                        if p_diff < hit_arc + 0.35:
                            proj.dead = True
                            self.sound_engine.play_sword_swing()
                            self.damage_numbers.append(DamageNumber(proj.x, proj.y - 12, "ОТБИТО!", is_crit=True))
                            for _ in range(8):
                                pa = random.uniform(0, math.pi * 2)
                                ps = random.uniform(80, 200)
                                self.particles.append(Particle(
                                    proj.x, proj.y,
                                    math.cos(pa) * ps, math.sin(pa) * ps,
                                    (255, 230, 80), 3.0, 0.22, "spark"
                                ))
            return True

        elif self.player.class_type == "ranger":
            return self.player.perform_attack_1(self.sound_engine, self.projectiles)

        elif self.player.class_type == "mage":
            return self.player.perform_attack_1(self.sound_engine, self.projectiles)

        elif self.player.class_type == "summoner":
            return self.player.perform_attack_1(self.sound_engine, self.zombies, self.particles, self.damage_numbers)

        return False

    def trigger_attack_2(self) -> bool:
        if not self.player: return False

        if self.player.class_type == "warrior":
            if not self.player.perform_attack_2(self.sound_engine):
                return False
            whirlwind_bonus = 1.0 + getattr(self.player, "atk2_damage_bonus", 0.0)
            hit_range = getattr(self.player, "atk2_range", 115.0) * self.player.area_multi
            damage = int(round(getattr(self.player, "atk2_damage", 70) * self.player.get_damage_multiplier() * whirlwind_bonus))
            if self.save_mgr.get_setting("screen_shake", True):
                self.camera.shake(8.0, 0.20)

            for z in list(self.zombies):
                if z.dead: continue
                dist = math.hypot(z.x - self.player.x, z.y - self.player.y)
                if dist <= hit_range + z.radius:
                    push_ang = math.atan2(z.y - self.player.y, z.x - self.player.x)
                    crit_chance = self.player.get_crit_chance(0.30)
                    is_crit = random.random() < crit_chance
                    actual_dmg = int(round(damage * 1.7)) if is_crit else damage
                    z.take_damage(actual_dmg, push_ang, 380.0, self.particles, self.damage_numbers, self.sound_engine, is_crit)

            # Bullet Deflection Mastery (Warrior Whirlwind): 360-degree deflection of projectiles
            if getattr(self.player, "can_deflect_projectiles", False):
                for proj in list(self.projectiles):
                    if proj.dead or not isinstance(proj, AcidSpitProjectile):
                        continue
                    p_dist = math.hypot(proj.x - self.player.x, proj.y - self.player.y)
                    if p_dist <= hit_range + proj.radius + 20.0:
                        proj.dead = True
                        self.sound_engine.play_sword_swing()
                        self.damage_numbers.append(DamageNumber(proj.x, proj.y - 12, "ОТБИТО!", is_crit=True))
                        for _ in range(8):
                            pa = random.uniform(0, math.pi * 2)
                            ps = random.uniform(80, 200)
                            self.particles.append(Particle(
                                proj.x, proj.y,
                                math.cos(pa) * ps, math.sin(pa) * ps,
                                (255, 230, 80), 3.0, 0.22, "spark"
                            ))
            return True

        elif self.player.class_type == "ranger":
            return self.player.perform_attack_2(self.sound_engine, self.projectiles)

        elif self.player.class_type == "mage":
            return self.player.perform_attack_2(self.sound_engine, self.projectiles)

        elif self.player.class_type == "summoner":
            return self.player.perform_attack_2(self.sound_engine)

        return False

    def trigger_attack_3(self) -> bool:
        if not self.player: return False

        if self.player.class_type == "warrior":
            return self.player.perform_attack_3(self.sound_engine, self.projectiles)
        elif self.player.class_type == "ranger":
            return self.player.perform_attack_3(self.sound_engine, self.projectiles)
        elif self.player.class_type == "mage":
            return self.player.perform_attack_3(self.sound_engine, self.zombies, self.particles, self.damage_numbers, self.camera)
        elif self.player.class_type == "summoner":
            return self.player.perform_attack_3(self.sound_engine, self.projectiles)

        return False

    def trigger_dash(self) -> bool:
        if not self.player:
            return False
        return self.player.trigger_dash(
            self.input_handler.move_x,
            self.input_handler.move_y,
            self.sound_engine,
            zombies=self.zombies,
            particles=self.particles,
            damage_numbers=self.damage_numbers
        )

    def _detonate_explosion(self, ex: float, ey: float, radius: float, damage: int) -> None:
        self.sound_engine.play_explosion()
        if self.save_mgr.get_setting("screen_shake", True):
            self.camera.shake(9.0, 0.22)

        for z in list(self.zombies):
            if z.dead: continue
            d = math.hypot(z.x - ex, z.y - ey)
            if d <= radius + z.radius:
                ang = math.atan2(z.y - ey, z.x - ex)
                z.take_damage(damage, ang, 320.0, self.particles, self.damage_numbers, self.sound_engine, is_crit=True)

        # Fire burst particles
        for _ in range(22):
            pa = random.uniform(0, math.pi * 2)
            pd = random.uniform(0, radius)
            self.particles.append(Particle(
                ex + math.cos(pa) * pd,
                ey + math.sin(pa) * pd,
                math.cos(pa) * 60, math.sin(pa) * 60,
                random.choice([(255, 60, 0), (255, 140, 20), (255, 230, 70)]),
                random.uniform(4.0, 7.5), 0.35, "circle"
            ))

    def on_zombie_killed(self, z: Zombie) -> None:
        self.kills += 1
        self.score += z.score_value

        soul_bonus = getattr(self.player, "soul_gain_bonus", 0) if self.player else 0
        base_souls = getattr(z, "souls_value", 5 if z.type == "brute" else (2 if z.type in ("runner", "spitter") else 1))
        souls_gain = base_souls + soul_bonus
        self.souls_collected_this_run += souls_gain

        if self.player and not self.player.dead and self.player.vampirism > 0:
            self.player.hp = min(self.player.max_hp, self.player.hp + self.player.vampirism)

        # Corpse Explosion upgrade (Summoner)
        if self.player and getattr(self.player, "corpse_explosion_damage", 0.0) > 0:
            c_dmg = int(round(self.player.corpse_explosion_damage * self.player.get_damage_multiplier()))
            self._detonate_explosion(z.x, z.y, 85.0 * self.player.area_multi, c_dmg)

        self.orbs.append(ExperienceOrb(z.x, z.y, z.xp_value))

        if len(self.blood_decals) > 250:
            self.blood_decals.pop(0)
        blood_color = random.choice([(60, 9, 25), (84, 11, 14), (63, 0, 8)])
        self.blood_decals.append(BloodDecal(z.x, z.y, random.uniform(z.radius * 0.8, z.radius * 1.4), blood_color))

    def show_level_up(self) -> None:
        self.state = "UPGRADE"
        self.sound_engine.play_level_up()
        self.current_upgrade_cards = get_available_upgrades(self.player, self.wave, count=3)

    def trigger_game_over(self) -> None:
        self.state = "GAMEOVER"
        self.sound_engine.play_game_over()
        bonus_souls = self.wave * EconomyBalance.BONUS_SOULS_PER_WAVE
        total_run_souls = self.souls_collected_this_run + bonus_souls
        self.save_mgr.record_game_end(self.wave, self.kills, self.score, total_run_souls)
        if self.player and hasattr(self.player, "minions"):
            for m in self.player.minions:
                m.dead = True
            self.player.minions.clear()

    def run(self) -> None:
        while self.running:
            dt = min(0.1, self.clock.tick(settings.FPS) / 1000.0)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    is_fs = self.save_mgr.get_setting("fullscreen", False)
                    if not is_fs:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                        self.camera.resize(event.w, event.h)
                        self.renderer.on_resize(self.screen)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()

            player_screen_pos = (
                int(self.player.x - self.camera.x) if self.player else self.screen.get_width() // 2,
                int(self.player.y - self.camera.y) if self.player else self.screen.get_height() // 2
            )
            self.input_handler.process_events(events, player_screen_pos, game_state=self.state)

            if self.input_handler.wants_toggle_sound:
                is_muted = self.sound_engine.toggle_mute()
                self.save_mgr.set_setting("sfx_muted", is_muted)

            # State Machine Routing
            if self.state == "PLAYING":
                self.update_playing(dt)
            elif self.state == "MENU":
                self.update_menu()
            elif self.state == "UPGRADE":
                self.update_upgrade()
            elif self.state == "PAUSED":
                self.update_paused()
            elif self.state == "GAMEOVER":
                self.update_gameover()

            self.render()

        pygame.quit()

    def update_menu(self) -> None:
        mouse_pos = self.input_handler.mouse_pos
        clicked = self.input_handler.mouse_left_clicked

        if self.menus.active_tab == "MAIN":
            if self.input_handler.wants_start:
                self.sound_engine.play_menu_click()
                if self.save_mgr.has_active_run():
                    self.start_new_game(from_saved_run=True)
                else:
                    self.menus.active_tab = "CLASS_SELECT"
                return

            if clicked:
                if self.menus.btn_continue_rect.collidepoint(mouse_pos) and self.save_mgr.has_active_run():
                    self.sound_engine.play_menu_click()
                    self.start_new_game(from_saved_run=True)
                elif self.menus.btn_newgame_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "CLASS_SELECT"
                elif self.menus.btn_camp_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "CAMP"
                elif self.menus.btn_stats_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "STATS"
                elif self.menus.btn_settings_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "SETTINGS"
                elif self.menus.btn_controls_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "CONTROLS"
                elif self.menus.btn_quit_rect.collidepoint(mouse_pos):
                    self.running = False

        elif self.menus.active_tab == "CLASS_SELECT":
            if self.input_handler.wants_start:
                self.sound_engine.play_menu_click()
                self.start_new_game(from_saved_run=False, class_type=self.menus.selected_class_type)
                return
            elif self.input_handler.wants_pause:
                self.sound_engine.play_menu_click()
                self.menus.active_tab = "MAIN"
                return

            if clicked:
                if self.menus.btn_start_class_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.start_new_game(from_saved_run=False, class_type=self.menus.selected_class_type)
                elif self.menus.btn_back_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "MAIN"
                else:
                    for c_id, rect in self.menus.class_card_rects.items():
                        if rect.collidepoint(mouse_pos):
                            self.menus.selected_class_type = c_id
                            self.sound_engine.play_menu_click()

        elif self.menus.active_tab == "CAMP":
            if self.input_handler.wants_pause:  # ESC pressed
                self.sound_engine.play_menu_click()
                if self.menus.camp_selected_hero is not None:
                    self.menus.camp_selected_hero = None
                else:
                    self.menus.active_tab = "MAIN"
                return

            if clicked:
                if self.menus.btn_back_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    if self.menus.camp_selected_hero is not None:
                        self.menus.camp_selected_hero = None
                    else:
                        self.menus.active_tab = "MAIN"
                elif getattr(self.menus, "camp_all_heroes_btn_rect", None) and self.menus.camp_all_heroes_btn_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.camp_selected_hero = None
                else:
                    hero_clicked = False
                    for h_id, rect in getattr(self.menus, "camp_hero_rects", {}).items():
                        if rect.collidepoint(mouse_pos):
                            self.menus.camp_selected_hero = h_id
                            self.sound_engine.play_menu_click()
                            hero_clicked = True
                            break
                    if not hero_clicked:
                        for up_id, rect in self.menus.camp_upgrade_btn_rects.items():
                            if rect.collidepoint(mouse_pos):
                                if self.save_mgr.buy_upgrade(up_id):
                                    self.sound_engine.play_buy_upgrade()
                                else:
                                    self.sound_engine.play_menu_click()

        elif self.menus.active_tab == "STATS":
            if clicked and self.menus.btn_back_rect.collidepoint(mouse_pos):
                self.sound_engine.play_menu_click()
                self.menus.active_tab = "MAIN"

        elif self.menus.active_tab == "SETTINGS":
            if clicked:
                if self.menus.btn_back_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "MAIN"
                else:
                    for key, rect in self.menus.settings_toggle_rects.items():
                        if rect.collidepoint(mouse_pos):
                            self.sound_engine.play_menu_click()
                            if key == "sfx_muted":
                                is_m = not self.save_mgr.get_setting("sfx_muted", False)
                                self.save_mgr.set_setting("sfx_muted", is_m)
                                self.sound_engine.muted = is_m
                            elif key == "screen_shake":
                                ss = not self.save_mgr.get_setting("screen_shake", True)
                                self.save_mgr.set_setting("screen_shake", ss)
                            elif key == "fullscreen":
                                self.toggle_fullscreen()

        elif self.menus.active_tab == "CONTROLS":
            if clicked:
                if self.menus.btn_back_rect.collidepoint(mouse_pos):
                    self.sound_engine.play_menu_click()
                    self.menus.active_tab = "MAIN"
                else:
                    for subtab_name, rect in self.menus.controls_tab_rects.items():
                        if rect.collidepoint(mouse_pos):
                            self.sound_engine.play_menu_click()
                            self.menus.controls_subtab = subtab_name

    def update_upgrade(self) -> None:
        choice = self.input_handler.upgrade_choice
        chosen_card = None
        if 0 <= choice < len(self.current_upgrade_cards):
            chosen_card = self.current_upgrade_cards[choice]
        elif self.input_handler.mouse_left_clicked:
            for idx, rect in enumerate(self.menus.upgrade_card_rects):
                if rect.collidepoint(self.input_handler.mouse_pos):
                    chosen_card = self.current_upgrade_cards[idx]
                    break

        if chosen_card:
            chosen_card.apply(self.player)
            self.applied_upgrade_ids.append(chosen_card.id)
            self.sound_engine.play_menu_click()
            if self.player.xp >= self.player.xp_to_next_level:
                self.player.gain_xp(0)
                self.show_level_up()
            else:
                self.state = "PLAYING"

    def update_paused(self) -> None:
        mouse_pos = self.input_handler.mouse_pos
        clicked = self.input_handler.mouse_left_clicked

        if self.input_handler.wants_pause:
            self.sound_engine.play_menu_click()
            self.state = "PLAYING"
        elif self.input_handler.wants_restart:
            self.sound_engine.play_menu_click()
            self.start_new_game(from_saved_run=False, class_type=self.player.class_type if self.player else "warrior")
        elif clicked:
            if self.menus.resume_btn_rect.collidepoint(mouse_pos):
                self.sound_engine.play_menu_click()
                self.state = "PLAYING"
            elif self.menus.save_quit_btn_rect.collidepoint(mouse_pos):
                self.sound_engine.play_menu_click()
                if self.player:
                    save_wave = self.wave + 1 if self.is_wave_transitioning else self.wave
                    self.save_mgr.save_active_run(
                        save_wave,
                        self.score,
                        self.kills,
                        self.souls_collected_this_run,
                        self.player,
                        self.applied_upgrade_ids
                    )
                self.menus.active_tab = "MAIN"
                self.state = "MENU"
            elif self.menus.pause_restart_btn_rect.collidepoint(mouse_pos):
                self.sound_engine.play_menu_click()
                self.start_new_game(from_saved_run=False, class_type=self.player.class_type if self.player else "warrior")

    def update_gameover(self) -> None:
        mouse_pos = self.input_handler.mouse_pos
        clicked = self.input_handler.mouse_left_clicked

        if self.input_handler.wants_restart or self.input_handler.wants_start:
            self.sound_engine.play_menu_click()
            self.start_new_game(from_saved_run=False, class_type=self.player.class_type if self.player else "warrior")
        elif clicked:
            if self.menus.gameover_restart_btn_rect.collidepoint(mouse_pos):
                self.sound_engine.play_menu_click()
                self.start_new_game(from_saved_run=False, class_type=self.player.class_type if self.player else "warrior")
            elif self.menus.gameover_menu_btn_rect.collidepoint(mouse_pos):
                self.sound_engine.play_menu_click()
                self.menus.active_tab = "MAIN"
                self.state = "MENU"

    def update_playing(self, dt: float) -> None:
        if self.input_handler.wants_pause:
            self.sound_engine.play_menu_click()
            self.state = "PAUSED"
            return

        if self.input_handler.wants_atk1:
            self.trigger_attack_1()
        if self.input_handler.wants_atk2:
            self.trigger_attack_2()
        if self.input_handler.wants_atk3:
            self.trigger_attack_3()
        if self.input_handler.wants_dash:
            self.trigger_dash()

        # Wave Spawning Logic
        if self.is_wave_active:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.zombies_to_spawn > 0:
                self.spawn_timer = self.spawn_interval
                self.spawn_single_zombie()
                self.zombies_to_spawn -= 1

            if self.zombies_to_spawn <= 0 and len(self.zombies) == 0:
                self.is_wave_active = False
                self.score += self.wave * 250
                self.souls_collected_this_run += self.wave * 3

                self.is_wave_transitioning = True
                self.wave_transition_timer = 2.4
                self.hud.show_banner(f"ВОЛНА {self.wave} ПРОЙДЕНА!", "Приготовьтесь к следующей орде...", 2.4)

                if self.player:
                    self.save_mgr.save_active_run(
                        self.wave + 1,
                        self.score,
                        self.kills,
                        self.souls_collected_this_run,
                        self.player,
                        self.applied_upgrade_ids
                    )

        if self.is_wave_transitioning:
            self.wave_transition_timer -= dt
            if self.wave_transition_timer <= 0:
                self.is_wave_transitioning = False
                self.start_wave(self.wave + 1)

        # Update Player
        self.player.update(
            dt,
            self.input_handler.move_x,
            self.input_handler.move_y,
            self.input_handler.aim_angle,
            self.sound_engine,
            self.particles
        )

        if self.player.hp <= 0:
            self.trigger_game_over()
            return

        # Dash Smash collision (Warrior)
        if self.player.is_dashing and getattr(self.player, "dash_damage", 0.0) > 0:
            for z in self.zombies:
                if z.dead or z in self.player.dash_hit_zombies: continue
                d = math.hypot(z.x - self.player.x, z.y - self.player.y)
                if d <= self.player.radius + z.radius + 6.0:
                    self.player.dash_hit_zombies.add(z)
                    push_ang = math.atan2(z.y - self.player.y, z.x - self.player.x)
                    smash_dmg = int(round(self.player.dash_damage * self.player.get_damage_multiplier()))
                    z.take_damage(smash_dmg, push_ang, 340.0, self.particles, self.damage_numbers, self.sound_engine, is_crit=True)

        # Update Summoner Minions
        if hasattr(self.player, "minions"):
            for m in list(self.player.minions):
                m.update(dt, self.zombies, self.particles, self.damage_numbers, self.sound_engine)

        # Update Projectiles & Collisions
        for proj in list(self.projectiles):
            if isinstance(proj, WindBladeProjectile):
                proj.update(dt, self.particles)
                # Bullet Deflection Mastery (Warrior Wind Blade)
                if getattr(self.player, "can_deflect_projectiles", False):
                    for other_p in list(self.projectiles):
                        if other_p.dead or not isinstance(other_p, AcidSpitProjectile):
                            continue
                        if math.hypot(proj.x - other_p.x, proj.y - other_p.y) < (proj.width / 2.0 + other_p.radius + 10.0):
                            other_p.dead = True
                            self.sound_engine.play_sword_swing()
                            self.damage_numbers.append(DamageNumber(other_p.x, other_p.y - 12, "ОТБИТО!", is_crit=True))
                            for _ in range(8):
                                pa = random.uniform(0, math.pi * 2)
                                ps = random.uniform(80, 200)
                                self.particles.append(Particle(
                                    other_p.x, other_p.y,
                                    math.cos(pa) * ps, math.sin(pa) * ps,
                                    (255, 230, 80), 3.0, 0.22, "spark"
                                ))
                for z in self.zombies:
                    if z.dead or z in proj.hit_zombies: continue
                    d = math.hypot(proj.x - z.x, proj.y - z.y)
                    if d < proj.width / 2.0 + z.radius:
                        proj.hit_zombies.add(z)
                        proj.pierce_count -= 1
                        z.take_damage(proj.damage, proj.angle, 280.0, self.particles, self.damage_numbers, self.sound_engine, is_crit=True)
                        if proj.pierce_count <= 0:
                            proj.dead = True
                            break

            elif isinstance(proj, ArrowProjectile):
                proj.update(dt, self.particles)
                for z in self.zombies:
                    if z.dead or z in proj.hit_zombies: continue
                    d = math.hypot(proj.x - z.x, proj.y - z.y)
                    if d < proj.radius + z.radius:
                        proj.hit_zombies.add(z)
                        proj.pierce_count -= 1
                        crit_chance = self.player.get_crit_chance(0.25) if self.player else 0.25
                        is_crit = random.random() < crit_chance
                        actual_dmg = int(round(proj.damage * 1.8)) if is_crit else proj.damage
                        z.take_damage(actual_dmg, proj.angle, 220.0, self.particles, self.damage_numbers, self.sound_engine, is_crit=is_crit)

                        # Poison effect
                        if getattr(proj, "poison_damage", 0.0) > 0:
                            z.apply_poison(proj.poison_damage, 3.0, slow=(proj.poison_damage >= 100.0))

                        # Ricochet effect
                        ricocheted = False
                        if getattr(proj, "ricochet_count", 0) > 0:
                            candidates = [other for other in self.zombies if not other.dead and other not in proj.hit_zombies]
                            if candidates:
                                nearest = min(candidates, key=lambda other: math.hypot(other.x - proj.x, other.y - proj.y))
                                proj.angle = math.atan2(nearest.y - proj.y, nearest.x - proj.x)
                                proj.ricochet_count -= 1
                                proj.traveled = max(0.0, proj.traveled - 150.0)
                                proj.pierce_count = max(proj.pierce_count, 1)
                                ricocheted = True

                        if not ricocheted and proj.pierce_count <= 0:
                            proj.dead = True
                            break
                        if ricocheted:
                            break

            elif isinstance(proj, ExplosiveArrowProjectile):
                proj.update(dt, self.particles)
                hit = False
                for z in self.zombies:
                    if z.dead: continue
                    d = math.hypot(proj.x - z.x, proj.y - z.y)
                    if d < proj.radius + z.radius:
                        hit = True
                        break
                if hit or proj.dead:
                    proj.dead = True
                    area_m = self.player.area_multi if self.player else 1.0
                    blast_rad = getattr(proj, "blast_radius", 80.0) * area_m
                    self._detonate_explosion(proj.x, proj.y, blast_rad, proj.damage)

            elif isinstance(proj, ArcaneBoltProjectile):
                proj.update(dt, self.particles)
                for z in self.zombies:
                    if z.dead or z in proj.hit_zombies: continue
                    d = math.hypot(proj.x - z.x, proj.y - z.y)
                    if d < proj.radius + z.radius:
                        proj.hit_zombies.add(z)
                        proj.pierce_count -= 1
                        crit_chance = self.player.get_crit_chance(0.30) if self.player else 0.30
                        is_crit = random.random() < crit_chance
                        actual_dmg = int(round(proj.damage * 1.7)) if is_crit else proj.damage
                        z.take_damage(actual_dmg, proj.angle, 190.0, self.particles, self.damage_numbers, self.sound_engine, is_crit=is_crit)

                        # Chain Lightning effect
                        chain_k = getattr(proj, "chain_lightning", 0)
                        if chain_k > 0:
                            candidates = [other for other in self.zombies if not other.dead and other is not z]
                            candidates.sort(key=lambda other: math.hypot(other.x - z.x, other.y - z.y))
                            for cz in candidates[:chain_k]:
                                if math.hypot(cz.x - z.x, cz.y - z.y) <= 240.0:
                                    owner_multi = self.player.get_damage_multiplier() if self.player else 1.0
                                    lt_dmg = int(round(35 * owner_multi))
                                    cz.take_damage(lt_dmg, math.atan2(cz.y - z.y, cz.x - z.x), 160.0, self.particles, self.damage_numbers, self.sound_engine, is_crit=True)
                                    if len(self.particles) < 300:
                                        for step in range(5):
                                            t = step / 5.0
                                            lx = z.x + (cz.x - z.x) * t + random.uniform(-5, 5)
                                            ly = z.y + (cz.y - z.y) * t + random.uniform(-5, 5)
                                            self.particles.append(Particle(lx, ly, 0, 0, (140, 220, 255), 2.5, 0.18, "circle"))

                        if proj.pierce_count <= 0:
                            proj.dead = True
                            break

            elif isinstance(proj, FireballProjectile):
                proj.update(dt, self.particles)
                hit = False
                for z in self.zombies:
                    if z.dead: continue
                    d = math.hypot(proj.x - z.x, proj.y - z.y)
                    if d < proj.radius + z.radius:
                        hit = True
                        break
                if hit or proj.dead:
                    proj.dead = True
                    area_m = self.player.area_multi if self.player else 1.0
                    blast_rad = getattr(proj, "blast_radius", 75.0) * area_m
                    self._detonate_explosion(proj.x, proj.y, blast_rad, proj.damage)

            elif isinstance(proj, SoulWaveProjectile):
                proj.update(dt, self.particles)
                for z in self.zombies:
                    if z.dead or z in proj.hit_zombies: continue
                    d = math.hypot(proj.x - z.x, proj.y - z.y)
                    if d < proj.radius + z.radius:
                        proj.hit_zombies.add(z)
                        proj.pierce_count -= 1
                        z.take_damage(proj.damage, proj.angle, 250.0, self.particles, self.damage_numbers, self.sound_engine, is_crit=True)
                        if proj.pierce_count <= 0:
                            proj.dead = True
                            break

            elif isinstance(proj, AcidSpitProjectile):
                proj.update(dt)
                hit_target = False
                if hasattr(self.player, "minions") and self.player.minions:
                    for m in self.player.minions:
                        if m.dead: continue
                        if math.hypot(proj.x - m.x, proj.y - m.y) < proj.radius + m.radius:
                            proj.dead = True
                            m.take_damage(proj.damage, self.damage_numbers, self.sound_engine, self.particles)
                            hit_target = True
                            break
                if not hit_target:
                    d = math.hypot(proj.x - self.player.x, proj.y - self.player.y)
                    if d < proj.radius + self.player.radius:
                        proj.dead = True
                        self.player.take_damage(proj.damage, self.sound_engine, self.camera, self.damage_numbers, self.particles)

            if proj.dead and proj in self.projectiles:
                self.projectiles.remove(proj)

        # Update Zombies
        for z in list(self.zombies):
            z.update(
                dt,
                self.player,
                self.zombies,
                self.projectiles,
                self.particles,
                self.damage_numbers,
                self.sound_engine,
                self.camera
            )
            if z.dead:
                self.on_zombie_killed(z)
                self.zombies.remove(z)

        # Update Experience Orbs
        for orb in list(self.orbs):
            leveled_up = orb.update(dt, self.player)
            if orb.collected or orb.dead:
                if orb in self.orbs:
                    self.orbs.remove(orb)
            if leveled_up:
                self.show_level_up()
                break

        # Update Particles
        for part in list(self.particles):
            part.update(dt)
            if part.life <= 0:
                self.particles.remove(part)

        # Update Damage Numbers
        for dn in list(self.damage_numbers):
            dn.update(dt)
            if dn.life <= 0:
                self.damage_numbers.remove(dn)

        # Update Camera & HUD
        self.camera.update(dt, self.player.x, self.player.y)
        self.hud.update(dt)

    def render(self) -> None:
        if self.state == "MENU":
            self.screen.fill(settings.COLOR_BG)
            self.menus.draw_start_menu(self.screen, self.save_mgr, self.input_handler.mouse_pos)
            pygame.display.flip()
            return

        # Render Main World
        self.renderer.render_world(
            self.camera,
            self.player,
            self.zombies,
            self.projectiles,
            self.orbs,
            self.particles,
            self.damage_numbers,
            self.blood_decals,
            self.input_handler.mouse_pos
        )

        # Render In-Game HUD
        if self.player:
            zombies_rem = len(self.zombies) + self.zombies_to_spawn
            self.hud.draw(
                self.screen,
                self.player,
                self.wave,
                zombies_rem,
                self.is_wave_transitioning,
                self.wave_transition_timer,
                self.score,
                self.kills,
                self.sound_engine.muted
            )

        # Render Modal Overlays
        if self.state == "UPGRADE":
            cards = self.current_upgrade_cards or getattr(self, "offered_upgrades", [])
            self.menus.draw_upgrade_menu(self.screen, cards, self.input_handler.mouse_pos)
        elif self.state == "PAUSED":
            self.menus.draw_pause_menu(self.screen, self.input_handler.mouse_pos)
        elif self.state == "GAMEOVER":
            bonus_souls = self.wave * EconomyBalance.BONUS_SOULS_PER_WAVE
            total_run_souls = self.souls_collected_this_run + bonus_souls
            self.menus.draw_game_over_menu(
                self.screen,
                self.wave,
                self.kills,
                self.score,
                total_run_souls,
                self.save_mgr.high_score,
                self.input_handler.mouse_pos
            )

        pygame.display.flip()
