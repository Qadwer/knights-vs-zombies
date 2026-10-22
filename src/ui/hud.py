"""
HUD (интерфейс в игре): отображение здоровья, волн, счета, навыков и перезарядки.
"""

import math
from typing import Tuple
import pygame
from ..entities.player import BasePlayer
from ..config import settings


class HUD:
    def __init__(self):
        pygame.font.init()
        self.font_small = pygame.font.SysFont("Arial", 12, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_banner = pygame.font.SysFont("Arial", 36, bold=True)

        self.banner_title = ""
        self.banner_subtitle = ""
        self.banner_timer = 0.0

    def show_banner(self, title: str, subtitle: str, duration: float = 2.4) -> None:
        self.banner_title = title
        self.banner_subtitle = subtitle
        self.banner_timer = duration

    def update(self, dt: float) -> None:
        if self.banner_timer > 0:
            self.banner_timer -= dt

    def draw(
        self,
        screen: pygame.Surface,
        player: BasePlayer,
        wave: int,
        zombies_remaining: int,
        is_transitioning: bool,
        transition_timer: float,
        score: int,
        kills: int,
        muted: bool
    ) -> None:
        w, h = screen.get_size()

        # 1. Top-Left: Player Stats Bars
        self._draw_player_bars(screen, player)

        # 2. Top-Center: Wave Badge
        self._draw_wave_center(screen, wave, zombies_remaining, is_transitioning, transition_timer, w)

        # 3. Top-Right: Score, Kills, Sound Status
        self._draw_top_right(screen, score, kills, muted, w)

        # 4. Bottom-Center: Skill Cooldown Bar
        self._draw_skills_bar(screen, player, w, h)

        # 5. Wave Banner Popup
        if self.banner_timer > 0:
            self._draw_banner(screen, w, h)

    def _draw_player_bars(self, screen: pygame.Surface, player) -> None:
        from ..rendering.icons import IconEngine
        box_x, box_y = 16, 16
        bar_w, bar_h = 220, 16

        # Dark panel background
        panel_rect = pygame.Rect(box_x - 6, box_y - 6, bar_w + 64, 72)
        pygame.draw.rect(screen, (15, 18, 25, 235), panel_rect, border_radius=8)
        pygame.draw.rect(screen, (35, 45, 62), panel_rect, width=2, border_radius=8)

        # Class avatar icon box
        c_type = getattr(player, "class_type", "warrior")
        icon_rect = pygame.Rect(box_x, box_y + 3, 44, 52)
        pygame.draw.rect(screen, (24, 30, 42), icon_rect, border_radius=6)
        pygame.draw.rect(screen, (245, 166, 35), icon_rect, width=1, border_radius=6)
        class_icon_surf = IconEngine.get_icon(f"class_{c_type}", 40)
        screen.blit(class_icon_surf, (box_x + 2, box_y + 9))

        bars_start_x = box_x + 50

        # --- HP Bar ---
        hp_pct = max(0.0, min(1.0, player.hp / player.max_hp))
        hp_rect = pygame.Rect(bars_start_x, box_y + 2, bar_w, bar_h)
        pygame.draw.rect(screen, (35, 15, 20), hp_rect, border_radius=3)
        pygame.draw.rect(screen, (230, 57, 70), (bars_start_x, box_y + 2, int(bar_w * hp_pct), bar_h), border_radius=3)
        pygame.draw.line(screen, (255, 160, 170), (bars_start_x, box_y + 3), (bars_start_x + int(bar_w * hp_pct), box_y + 3), 1)

        mana_shield = getattr(player, "mana_shield", 0.0)
        mana_shield_max = getattr(player, "mana_shield_max", 0.0)
        if mana_shield_max > 0:
            if mana_shield > 0:
                s_pct = max(0.0, min(1.0, mana_shield / mana_shield_max))
                # Arcane shield top highlight strip & cyan outline
                pygame.draw.rect(screen, (0, 245, 212), (bars_start_x, box_y + 2, int(bar_w * s_pct), 3), border_radius=2)
                pygame.draw.rect(screen, (0, 245, 212), hp_rect, 1, border_radius=3)
            else:
                pygame.draw.rect(screen, (60, 20, 30), hp_rect, 1, border_radius=3)
            hp_str = f"{int(math.ceil(player.hp))} / {int(player.max_hp)} HP  [ЩИТ: {int(math.ceil(mana_shield))}]"
        else:
            pygame.draw.rect(screen, (60, 20, 30), hp_rect, 1, border_radius=3)
            hp_str = f"{int(math.ceil(player.hp))} / {int(player.max_hp)} HP"

        hp_text = self.font_small.render(hp_str, True, (255, 255, 255))
        screen.blit(hp_text, (bars_start_x + (bar_w - hp_text.get_width()) // 2, box_y + 3))

        # --- Dash / Stamina Bar ---
        dash_cd_reduction = getattr(player, "dash_cooldown_reduction", 0.0)
        dash_total = max(0.30, player.dash_cooldown * max(0.30, 1.0 - dash_cd_reduction) * player.cooldown_multi)
        dash_rem = max(0.0, player.dash_timer)
        dash_pct = max(0.0, min(1.0, (dash_total - dash_rem) / dash_total))
        dash_rect = pygame.Rect(bars_start_x, box_y + 22, bar_w, bar_h)
        pygame.draw.rect(screen, (15, 30, 40), dash_rect, border_radius=3)
        pygame.draw.rect(screen, (0, 180, 216), (bars_start_x, box_y + 22, int(bar_w * dash_pct), bar_h), border_radius=3)
        pygame.draw.line(screen, (180, 245, 255), (bars_start_x, box_y + 23), (bars_start_x + int(bar_w * dash_pct), box_y + 23), 1)
        pygame.draw.rect(screen, (20, 45, 60), dash_rect, 1, border_radius=3)
        dash_raw = player.skill_descriptions[3][0] if getattr(player, "skill_descriptions", None) else "РЫВОК"
        dash_name = dash_raw.split(". ", 1)[-1] if ". " in dash_raw else dash_raw
        dash_str = f"{dash_name.upper()} ГОТОВ" if dash_rem <= 0 else f"{dash_name.upper()}: {dash_rem:.1f}с"
        dash_text = self.font_small.render(dash_str, True, (255, 255, 255))
        screen.blit(dash_text, (bars_start_x + (bar_w - dash_text.get_width()) // 2, box_y + 23))

        # --- XP Bar ---
        xp_pct = max(0.0, min(1.0, player.xp / player.xp_to_next_level))
        xp_rect = pygame.Rect(bars_start_x, box_y + 42, bar_w, bar_h)
        pygame.draw.rect(screen, (15, 35, 25), xp_rect, border_radius=3)
        pygame.draw.rect(screen, (82, 183, 136), (bars_start_x, box_y + 42, int(bar_w * xp_pct), bar_h), border_radius=3)
        pygame.draw.line(screen, (190, 250, 220), (bars_start_x, box_y + 43), (bars_start_x + int(bar_w * xp_pct), box_y + 43), 1)
        pygame.draw.rect(screen, (25, 55, 35), xp_rect, 1, border_radius=3)
        xp_str = f"Ур. {player.level} [{player.xp} / {player.xp_to_next_level} XP]"
        xp_text = self.font_small.render(xp_str, True, (255, 255, 255))
        screen.blit(xp_text, (bars_start_x + (bar_w - xp_text.get_width()) // 2, box_y + 43))

    def _draw_wave_center(
        self,
        screen: pygame.Surface,
        wave: int,
        zombies_rem: int,
        is_trans: bool,
        trans_timer: float,
        w: int
    ) -> None:
        panel_w = 260
        panel_h = 56
        px = (w - panel_w) // 2
        py = 16

        pygame.draw.rect(screen, (15, 18, 25, 235), (px, py, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(screen, (245, 166, 35), (px, py, panel_w, panel_h), width=2, border_radius=8)

        wave_str = f"ВОЛНА {wave}"
        w_surf = self.font_large.render(wave_str, True, (245, 166, 35))
        screen.blit(w_surf, (px + (panel_w - w_surf.get_width()) // 2, py + 6))

        if is_trans:
            sub_str = f"Волна пройдена! След: {int(math.ceil(trans_timer))}с"
            s_col = (82, 183, 136)
        else:
            sub_str = f"Врагов осталось: {zombies_rem}"
            s_col = (200, 210, 225)

        s_surf = self.font_small.render(sub_str, True, s_col)
        screen.blit(s_surf, (px + (panel_w - s_surf.get_width()) // 2, py + 32))

    def _draw_top_right(self, screen: pygame.Surface, score: int, kills: int, muted: bool, w: int) -> None:
        from ..rendering.icons import IconEngine
        panel_w = 210
        panel_h = 72
        px = w - panel_w - 16
        py = 16

        pygame.draw.rect(screen, (15, 18, 25, 235), (px, py, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(screen, (35, 45, 62), (px, py, panel_w, panel_h), width=2, border_radius=8)

        # Trophy & Score
        screen.blit(IconEngine.get_icon("trophy", 18), (px + 12, py + 7))
        sc_txt = self.font_medium.render(f"СЧЁТ: {score}", True, (255, 255, 255))
        screen.blit(sc_txt, (px + 36, py + 8))

        # Skull & Kills
        screen.blit(IconEngine.get_icon("skull", 18), (px + 12, py + 27))
        kl_txt = self.font_medium.render(f"ЧЕРЕПА: {kills}", True, (230, 57, 70))
        screen.blit(kl_txt, (px + 36, py + 28))

        # Sound setting
        screen.blit(IconEngine.get_icon("sound_off" if muted else "sound_on", 16), (px + 13, py + 49))
        snd_status = "ЗВУК: ВЫКЛ [M]" if muted else "ЗВУК: ВКЛ [M]"
        snd_col = (140, 145, 155) if muted else (82, 183, 136)
        snd_txt = self.font_small.render(snd_status, True, snd_col)
        screen.blit(snd_txt, (px + 36, py + 49))

    def _draw_skills_bar(self, screen: pygame.Surface, player, w: int, h: int) -> None:
        from ..rendering.icons import IconEngine
        slot_w = 145
        slot_h = 58
        spacing = 10
        total_w = slot_w * 4 + spacing * 3
        start_x = (w - total_w) // 2
        start_y = h - slot_h - 14

        skills_meta = getattr(player, "skill_descriptions", None)
        if not skills_meta or len(skills_meta) < 4:
            skills_meta = [
                ("1. Атака 1", "ЛКМ / 1", "⚔️", ""),
                ("2. Атака 2", "ПКМ / 2", "🌪️", ""),
                ("3. Атака 3", "ПРОБЕЛ / 3", "⚡", ""),
                ("4. Рывок", "SHIFT / F", "💨", ""),
            ]

        c_type = getattr(player, "class_type", "warrior")
        skill_icon_map = {
            "warrior": ["skill_slash", "skill_whirlwind", "skill_wind_blade", "skill_dash"],
            "ranger": ["skill_arrow_shot", "skill_multishot", "skill_explosive_arrow", "skill_roll"],
            "mage": ["skill_arcane_bolt", "skill_fireball", "skill_frost_nova", "skill_teleport"],
            "summoner": ["skill_spirit_whip", "skill_summon", "skill_soul_burst", "skill_ghost_step"],
        }
        icon_keys = skill_icon_map.get(c_type, ["skill_slash", "skill_whirlwind", "skill_wind_blade", "skill_dash"])

        dash_cd_reduction = getattr(player, "dash_cooldown_reduction", 0.0)
        dash_cd_max = max(0.30, player.dash_cooldown * max(0.30, 1.0 - dash_cd_reduction) * player.cooldown_multi)

        skills = [
            (skills_meta[0][0], skills_meta[0][1], player.atk1_timer, max(0.01, player.atk1_cooldown * player.cooldown_multi), (72, 202, 228), icon_keys[0]),
            (skills_meta[1][0], skills_meta[1][1], player.atk2_timer, max(0.01, player.atk2_cooldown * player.cooldown_multi), (245, 166, 35), icon_keys[1]),
            (skills_meta[2][0], skills_meta[2][1], player.atk3_timer, max(0.01, player.atk3_cooldown * player.cooldown_multi), (0, 245, 212), icon_keys[2]),
            (skills_meta[3][0], skills_meta[3][1], player.dash_timer, dash_cd_max, (82, 183, 136), icon_keys[3]),
        ]

        for i, (name, hotkey, cd_cur, cd_max, color, icon_name) in enumerate(skills):
            sx = start_x + i * (slot_w + spacing)
            sy = start_y

            # Base slot background
            pygame.draw.rect(screen, (15, 18, 25, 240), (sx, sy, slot_w, slot_h), border_radius=6)
            pygame.draw.rect(screen, color, (sx, sy, slot_w, slot_h), width=2, border_radius=6)

            # Draw procedural skill icon
            ic_surf = IconEngine.get_icon(icon_name, 36)
            screen.blit(ic_surf, (sx + 7, sy + (slot_h - 36) // 2))

            # Strip leading number if present for neat fit
            clean_name = name.split(". ", 1)[-1] if ". " in name else name
            max_label_w = slot_w - 50
            f_name = self.font_small
            if f_name.size(clean_name)[0] > max_label_w:
                while len(clean_name) > 3 and f_name.size(clean_name + "...")[0] > max_label_w:
                    clean_name = clean_name[:-1]
                clean_name += "..."

            n_surf = f_name.render(clean_name, True, color)
            if c_type == "summoner" and i == 1 and hasattr(player, "minions"):
                alive_count = len([m for m in player.minions if not m.dead])
                hk_str = f"ПКМ ({alive_count}/{getattr(player, 'max_minions', 4)})"
                hk_surf = self.font_small.render(hk_str, True, (160, 245, 205))
            else:
                hk_surf = self.font_small.render(hotkey, True, (180, 190, 205))
            screen.blit(n_surf, (sx + 46, sy + 10))
            screen.blit(hk_surf, (sx + 46, sy + 28))

            # Cooldown progress overlay
            cd_pct = max(0.0, min(1.0, cd_cur / cd_max)) if cd_max > 0 else 0.0
            if cd_pct > 0.0:
                cd_h = int(slot_h * cd_pct)
                cd_rect = pygame.Rect(sx, sy + (slot_h - cd_h), slot_w, cd_h)
                cd_surf = pygame.Surface((slot_w, cd_h), pygame.SRCALPHA)
                cd_surf.fill((0, 0, 0, 185))
                screen.blit(cd_surf, cd_rect.topleft)

                cd_text = self.font_medium.render(f"{cd_cur:.1f}с", True, (255, 255, 255))
                screen.blit(cd_text, (sx + (slot_w - cd_text.get_width()) // 2, sy + (slot_h - cd_text.get_height()) // 2))

    def _draw_banner(self, screen: pygame.Surface, w: int, h: int) -> None:
        t_surf = self.font_banner.render(self.banner_title, True, (245, 166, 35))
        sub_surf = self.font_medium.render(self.banner_subtitle, True, (240, 240, 240))

        banner_w = max(460, t_surf.get_width() + 60, sub_surf.get_width() + 60)
        banner_h = 90
        bx = (w - banner_w) // 2
        by = h // 4

        b_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        pygame.draw.rect(b_surf, (15, 18, 25, 240), (0, 0, banner_w, banner_h), border_radius=8)
        pygame.draw.rect(b_surf, (245, 166, 35), (0, 0, banner_w, banner_h), width=3, border_radius=8)

        b_surf.blit(t_surf, ((banner_w - t_surf.get_width()) // 2, 10))
        b_surf.blit(sub_surf, ((banner_w - sub_surf.get_width()) // 2, 54))

        screen.blit(b_surf, (bx, by))
