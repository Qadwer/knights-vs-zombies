"""
Полнофункциональные интерактивные меню интерфейса: Главный экран со страницами
(Главная, Улучшения лагеря, Статистика, Настройки, Управление), Меню паузы и Экран окончания игры (Game Over).
"""

import math
import os
import random
from typing import List, Tuple, Optional, Dict
import pygame
from ..upgrades.upgrade_db import UpgradeCard
from ..save_manager import PERMANENT_UPGRADES_META, SaveManager, HERO_META, CLASS_UPGRADES_META, HERO_CLASSES
from ..rendering.icons import IconEngine
from ..rendering.hero_sprites import draw_hero_character


class MenuEmberParticle:
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-15.0, 15.0)
        self.vy = random.uniform(-40.0, -15.0)
        self.size = random.uniform(2.0, 4.0)
        self.color = random.choice([(245, 166, 35), (230, 57, 70), (255, 120, 40)])
        self.alpha = random.randint(80, 200)

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y < -10:
            self.y = self.h + 10
            self.x = random.uniform(0, self.w)
        if self.x < -10: self.x = self.w + 10
        elif self.x > self.w + 10: self.x = -10

    def draw(self, screen: pygame.Surface) -> None:
        surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, self.alpha), (int(self.size), int(self.size)), int(self.size))
        screen.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class Menus:
    def __init__(self):
        pygame.font.init()
        self.font_super = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_subtitle = pygame.font.SysFont("Arial", 15)
        self.font_heading = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_card_title = pygame.font.SysFont("Arial", 17, bold=True)
        self.font_card_desc = pygame.font.SysFont("Arial", 13)
        self.font_btn = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 14)
        self.font_stats_val = pygame.font.SysFont("Arial", 19, bold=True)

        # Sub-page navigation inside Start Menu: "MAIN", "CLASS_SELECT", "CAMP", "STATS", "SETTINGS", "CONTROLS"
        self.active_tab = "MAIN"
        self.selected_class_type = "warrior"
        self.controls_subtab = "KEYBOARD"  # "KEYBOARD" or "GAMEPAD"

        # Background ember particles
        self.embers: List[MenuEmberParticle] = [MenuEmberParticle(1280, 720) for _ in range(45)]

        # Knight Banner
        self.banner_img = None
        self._load_banner()

        # Cache button rects for click detection
        self.btn_continue_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_newgame_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_camp_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_stats_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_settings_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_controls_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_quit_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_back_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_start_class_rect = pygame.Rect(0, 0, 0, 0)
        self.class_card_rects: Dict[str, pygame.Rect] = {}

        # In-game modals
        self.upgrade_card_rects: List[pygame.Rect] = []
        self.resume_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.save_quit_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.pause_restart_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.gameover_restart_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.gameover_menu_btn_rect = pygame.Rect(0, 0, 0, 0)

        # Submenu interactive elements
        self.camp_selected_hero: Optional[str] = None
        self.camp_hero_rects: Dict[str, pygame.Rect] = {}
        self.camp_all_heroes_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.camp_upgrade_btn_rects: Dict[str, pygame.Rect] = {}
        self.settings_toggle_rects: Dict[str, pygame.Rect] = {}
        self.controls_tab_rects: Dict[str, pygame.Rect] = {}

    def _load_banner(self) -> None:
        from ..config import get_resource_path
        banner_path = get_resource_path(os.path.join("assets", "sprites", "knight_banner.png"))
        if os.path.exists(banner_path):
            try:
                raw_img = pygame.image.load(banner_path).convert_alpha()
                # Scale nicely to width ~260 px (height ~145 px) so menus fit on 720p without overflow
                orig_w, orig_h = raw_img.get_size()
                target_w = 260
                target_h = int(orig_h * (target_w / float(orig_w)))
                self.banner_img = pygame.transform.smoothscale(raw_img, (target_w, target_h))
            except Exception as e:
                print(f"[Menus] Banner load warning: {e}")
                self.banner_img = None

    def update_embers(self, dt: float, w: int, h: int) -> None:
        for em in self.embers:
            em.w = w
            em.h = h
            em.update(dt)

    def _render_clipped_text(
        self,
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: Tuple[int, int, int],
        x: int,
        y: int,
        max_w: int
    ) -> int:
        """
        Renders text safely within max_w, abbreviating with an ellipsis (...) if needed.
        Returns the rendered surface width.
        """
        disp_text = text
        if font.size(disp_text)[0] > max_w:
            while len(disp_text) > 3 and font.size(disp_text + "...")[0] > max_w:
                disp_text = disp_text[:-1]
            disp_text += "..."
        surf = font.render(disp_text, True, color)
        screen.blit(surf, (x, y))
        return surf.get_width()

    def _render_wrapped_text(
        self,
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: Tuple[int, int, int],
        x: int,
        y: int,
        max_w: int,
        line_spacing: int = 16,
        max_lines: int = 3
    ) -> int:
        """
        Renders multi-line text wrapped neatly within max_w, respecting max_lines.
        Returns total vertical pixels consumed.
        """
        words = text.split()
        lines = []
        curr_line = ""
        for word in words:
            test_line = f"{curr_line} {word}".strip()
            if font.size(test_line)[0] <= max_w:
                curr_line = test_line
            else:
                if curr_line:
                    lines.append(curr_line)
                curr_line = word
        if curr_line:
            lines.append(curr_line)

        lines = lines[:max_lines]
        for idx, line in enumerate(lines):
            disp_line = line
            if font.size(disp_line)[0] > max_w:
                while len(disp_line) > 3 and font.size(disp_line + "...")[0] > max_w:
                    disp_line = disp_line[:-1]
                disp_line += "..."
            surf = font.render(disp_line, True, color)
            screen.blit(surf, (x, y + idx * line_spacing))
        return len(lines) * line_spacing

    # ==========================================================
    # 1. СТАРТОВОЕ МЕНЮ (ГЛАВНЫЙ ЭКРАН И ВКЛАДКИ)
    # ==========================================================
    def draw_start_menu(
        self,
        screen: pygame.Surface,
        save_mgr: SaveManager,
        mouse_pos: Tuple[int, int]
    ) -> None:
        w, h = screen.get_size()

        # Update and draw ambient background embers
        self.update_embers(0.016, w, h)
        for em in self.embers:
            em.draw(screen)

        if self.active_tab == "MAIN":
            self._draw_main_menu(screen, save_mgr, mouse_pos, w, h)
        elif self.active_tab == "CLASS_SELECT":
            self._draw_class_select_menu(screen, save_mgr, mouse_pos, w, h)
        elif self.active_tab == "CAMP":
            self._draw_camp_menu(screen, save_mgr, mouse_pos, w, h)
        elif self.active_tab == "STATS":
            self._draw_stats_menu(screen, save_mgr, mouse_pos, w, h)
        elif self.active_tab == "SETTINGS":
            self._draw_settings_menu(screen, save_mgr, mouse_pos, w, h)
        elif self.active_tab == "CONTROLS":
            self._draw_controls_menu(screen, mouse_pos, w, h)

    def _draw_class_select_menu(
        self,
        screen: pygame.Surface,
        save_mgr: SaveManager,
        mouse_pos: Tuple[int, int],
        w: int,
        h: int
    ) -> None:
        panel_w = min(1140, w - 40)
        panel_h = min(640, h - 30)
        cx = (w - panel_w) // 2
        cy = (h - panel_h) // 2

        panel_rect = pygame.Rect(cx, cy, panel_w, panel_h)
        pygame.draw.rect(screen, (15, 18, 25, 245), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (245, 166, 35), panel_rect, width=3, border_radius=12)

        # Title
        t_surf = self.font_title.render("ВЫБОР КЛАССА ГЕРОЯ", True, (245, 166, 35))
        sub_surf = self.font_subtitle.render("Выберите класс персонажа с уникальными атаками, снарядами и стилем игры", True, (180, 190, 205))
        screen.blit(t_surf, (cx + (panel_w - t_surf.get_width()) // 2, cy + 18))
        screen.blit(sub_surf, (cx + (panel_w - sub_surf.get_width()) // 2, cy + 58))

        classes_data = [
            {
                "id": "warrior",
                "name": "Воин (Рыцарь)",
                "icon": "🛡️",
                "role": "Танк / Ближний бой",
                "color": (245, 166, 35),
                "hp": "300 HP",
                "spd": "195",
                "diff": "★☆☆",
                "skills": [
                    ("1. Взмах", "Рубящий сектор"),
                    ("2. Вихрь", "Круговая атака 360°"),
                    ("3. Клинок ветра", "Пробивающий луч"),
                    ("4. Рывок", "Рывок (щит)"),
                ]
            },
            {
                "id": "ranger",
                "name": "Стрелок (Лучник)",
                "icon": "🏹",
                "role": "Дальний бой / Ловкость",
                "color": (82, 183, 136),
                "hp": "230 HP",
                "spd": "218",
                "diff": "★★☆",
                "skills": [
                    ("1. Выстрел", "Быстрая стрела"),
                    ("2. Веер стрел", "Залп 5 стрел"),
                    ("3. Разрывная", "Взрывной снаряд"),
                    ("4. Перекат", "Быстрый перекат"),
                ]
            },
            {
                "id": "mage",
                "name": "Маг (Архимаг)",
                "icon": "🔮",
                "role": "Разрушительная магия",
                "color": (160, 110, 240),
                "hp": "205 HP",
                "spd": "190",
                "diff": "★★★",
                "skills": [
                    ("1. Стрела чар", "Самонаводка"),
                    ("2. Фаербол", "Огненный шар"),
                    ("3. Ледяной круг", "Кольцо холода"),
                    ("4. Телепорт", "Мгновенный скачок"),
                ]
            },
            {
                "id": "summoner",
                "name": "Призыватель",
                "icon": "💀",
                "role": "Орда духов и скелетов",
                "color": (72, 202, 228),
                "hp": "245 HP",
                "spd": "195",
                "diff": "★★☆",
                "skills": [
                    ("1. Хлыст душ", "Удар хлыстом"),
                    ("2. Призыв", "Скелеты-миньоны"),
                    ("3. Взрыв душ", "3 волны призраков"),
                    ("4. Шаг духа", "Бесплотный уворот"),
                ]
            },
        ]

        # Draw 4 Class Cards
        card_w = (panel_w - 70 - 3 * 14) // 4
        card_h = 412
        start_x = cx + 35
        card_y = cy + 88

        self.class_card_rects.clear()

        for i, c_data in enumerate(classes_data):
            c_x = start_x + i * (card_w + 14)
            card_rect = pygame.Rect(c_x, card_y, card_w, card_h)
            self.class_card_rects[c_data["id"]] = card_rect

            is_selected = (self.selected_class_type == c_data["id"])
            is_hover = card_rect.collidepoint(mouse_pos)
            c_col = c_data["color"]

            # Background
            bg_col = (28, 35, 48) if is_selected else ((22, 28, 38) if is_hover else (18, 22, 30))
            pygame.draw.rect(screen, bg_col, card_rect, border_radius=10)

            # Border
            border_w = 3 if is_selected else (2 if is_hover else 1)
            border_col = c_col if (is_selected or is_hover) else (40, 50, 68)
            pygame.draw.rect(screen, border_col, card_rect, width=border_w, border_radius=10)

            # Selection Tag / Badge
            if is_selected:
                tag_w = 90
                tag_rect = pygame.Rect(c_x + (card_w - tag_w) // 2, card_y - 12, tag_w, 22)
                pygame.draw.rect(screen, c_col, tag_rect, border_radius=4)
                tag_txt = self.font_label.render("ВЫБРАН", True, (15, 15, 15))
                screen.blit(tag_txt, (tag_rect.x + (tag_w - tag_txt.get_width()) // 2, tag_rect.y + 2))

            # Icon Box with Glowing Aura
            ic_size = 52
            ic_rect = pygame.Rect(c_x + (card_w - ic_size) // 2, card_y + 12, ic_size, ic_size)
            if is_selected or is_hover:
                aura_surf = pygame.Surface((ic_size + 16, ic_size + 16), pygame.SRCALPHA)
                aura_alpha = 90 if is_selected else 50
                pygame.draw.circle(aura_surf, (*c_col, aura_alpha), ((ic_size + 16) // 2, (ic_size + 16) // 2), (ic_size + 16) // 2)
                screen.blit(aura_surf, (ic_rect.x - 8, ic_rect.y - 8))

            pygame.draw.rect(screen, (24, 30, 42), ic_rect, border_radius=10)
            pygame.draw.rect(screen, c_col, ic_rect, width=2, border_radius=10)
            class_icon_surf = IconEngine.get_icon(f"class_{c_data['id']}", 44)
            screen.blit(class_icon_surf, (ic_rect.x + (ic_size - 44) // 2, ic_rect.y + (ic_size - 44) // 2))

            # Class Name
            n_surf = self.font_card_title.render(c_data["name"], True, (255, 255, 255) if is_selected else (230, 235, 245))
            screen.blit(n_surf, (c_x + (card_w - n_surf.get_width()) // 2, card_y + 68))

            # Role Subtitle
            r_surf = self.font_subtitle.render(c_data["role"], True, c_col)
            screen.blit(r_surf, (c_x + (card_w - r_surf.get_width()) // 2, card_y + 90))

            # Divider
            pygame.draw.line(screen, (38, 48, 64), (c_x + 15, card_y + 110), (c_x + card_w - 15, card_y + 110), 1)

            # Stats line with icons
            s_line1 = f"Здоровье: {c_data['hp']}"
            s_line2 = f"Скорость: {c_data['spd']}"
            s_line3 = f"Сложность: {c_data['diff']}"

            s1_surf = self.font_card_desc.render(s_line1, True, (230, 57, 70))
            s2_surf = self.font_card_desc.render(s_line2, True, (72, 202, 228))
            s3_surf = self.font_card_desc.render(s_line3, True, (245, 166, 35))

            screen.blit(s1_surf, (c_x + 18, card_y + 115))
            screen.blit(s2_surf, (c_x + 18, card_y + 133))
            screen.blit(s3_surf, (c_x + 18, card_y + 151))

            pygame.draw.line(screen, (38, 48, 64), (c_x + 15, card_y + 173), (c_x + card_w - 15, card_y + 173), 1)

            # Skills with procedural icons
            sk_title = self.font_btn.render("Способности:", True, (220, 230, 240))
            screen.blit(sk_title, (c_x + 18, card_y + 180))

            skill_icon_map = {
                "warrior": ["skill_slash", "skill_whirlwind", "skill_wind_blade", "skill_dash"],
                "ranger": ["skill_arrow_shot", "skill_multishot", "skill_explosive_arrow", "skill_roll"],
                "mage": ["skill_arcane_bolt", "skill_fireball", "skill_frost_nova", "skill_teleport"],
                "summoner": ["skill_spirit_whip", "skill_summon", "skill_soul_burst", "skill_ghost_step"],
            }
            c_skill_icons = skill_icon_map.get(c_data["id"], ["skill_slash", "skill_whirlwind", "skill_wind_blade", "skill_dash"])

            sk_y = card_y + 204
            max_desc_w = card_w - 44
            for s_idx, (s_name, s_desc) in enumerate(c_data["skills"]):
                # Skill icon
                s_icon_key = c_skill_icons[s_idx]
                s_ic = IconEngine.get_icon(s_icon_key, 20)
                screen.blit(s_ic, (c_x + 14, sk_y + 1))

                sn_surf = self.font_card_desc.render(s_name, True, c_col)

                desc_text = s_desc
                if self.font_card_desc.size(desc_text)[0] > max_desc_w:
                    while len(desc_text) > 3 and self.font_card_desc.size(desc_text + "...")[0] > max_desc_w:
                        desc_text = desc_text[:-1]
                    desc_text += "..."

                sd_surf = self.font_card_desc.render(desc_text, True, (160, 170, 185))
                screen.blit(sn_surf, (c_x + 38, sk_y))
                screen.blit(sd_surf, (c_x + 38, sk_y + 14))
                sk_y += 33

            # Select Prompt Button on Card
            card_btn_rect = pygame.Rect(c_x + 14, card_y + card_h - 42, card_w - 28, 32)
            btn_bg = c_col if is_selected else ((35, 42, 56) if is_hover else (26, 32, 44))
            pygame.draw.rect(screen, btn_bg, card_btn_rect, border_radius=5)
            btn_txt = "ВЫБРАН" if is_selected else "Выбрать класс"
            btn_txt_col = (15, 15, 15) if is_selected else (220, 225, 235)
            b_surf = self.font_btn.render(btn_txt, True, btn_txt_col)
            screen.blit(b_surf, (card_btn_rect.x + (card_btn_rect.width - b_surf.get_width()) // 2, card_btn_rect.y + 7))

        # Bottom Actions Bar
        bot_y = cy + panel_h - 58
        btn_start_w = 320
        btn_back_w = 170
        btn_h = 44
        gap = 20
        tot_btns_w = btn_back_w + gap + btn_start_w
        start_x_btns = cx + (panel_w - tot_btns_w) // 2

        class_acc_names = {
            "warrior": "ВОИНА",
            "ranger": "ЛУЧНИКА",
            "mage": "МАГА",
            "summoner": "ПРИЗЫВАТЕЛЯ"
        }
        acc_name = class_acc_names.get(self.selected_class_type, "ГЕРОЯ")

        self.btn_back_rect = pygame.Rect(start_x_btns, bot_y, btn_back_w, btn_h)
        self._draw_btn(screen, self.btn_back_rect, "НАЗАД [ESC]", mouse_pos, (72, 202, 228), (15, 15, 15))

        self.btn_start_class_rect = pygame.Rect(start_x_btns + btn_back_w + gap, bot_y, btn_start_w, btn_h)
        self._draw_btn(screen, self.btn_start_class_rect, f"В БОЙ ЗА {acc_name}! [ENTER]", mouse_pos, (245, 166, 35), (15, 15, 15))

    def _draw_main_menu(
        self,
        screen: pygame.Surface,
        save_mgr: SaveManager,
        mouse_pos: Tuple[int, int],
        w: int,
        h: int
    ) -> None:
        panel_w = min(640, w - 40)
        panel_h = min(620, h - 30)
        cx = (w - panel_w) // 2
        cy = (h - panel_h) // 2

        panel_rect = pygame.Rect(cx, cy, panel_w, panel_h)
        pygame.draw.rect(screen, (15, 18, 25, 240), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (245, 166, 35), panel_rect, width=3, border_radius=12)

        curr_y = cy + 14

        # Optional Banner Image
        if self.banner_img:
            bw, bh = self.banner_img.get_size()
            bx = cx + (panel_w - bw) // 2
            screen.blit(self.banner_img, (bx, curr_y))
            curr_y += bh + 6
        else:
            # Title text
            t_surf = self.font_super.render("РЫЦАРЬ ПРОТИВ ЗОМБИ", True, (245, 166, 35))
            screen.blit(t_surf, (cx + (panel_w - t_surf.get_width()) // 2, curr_y))
            curr_y += 46

        # Subtitle
        sub_surf = self.font_subtitle.render("8-битная экшен-выживалка против орды нежити", True, (180, 190, 205))
        screen.blit(sub_surf, (cx + (panel_w - sub_surf.get_width()) // 2, curr_y))
        curr_y += 24

        # Career Quick Stats Bar with procedural icons
        stats_bar_w = panel_w - 60
        stats_bar_rect = pygame.Rect(cx + 30, curr_y, stats_bar_w, 32)
        pygame.draw.rect(screen, (24, 29, 40), stats_bar_rect, border_radius=6)
        pygame.draw.rect(screen, (40, 50, 70), stats_bar_rect, width=1, border_radius=6)

        sec_w = stats_bar_w // 3
        # 1. High Score
        screen.blit(IconEngine.get_icon("trophy", 18), (cx + 38, curr_y + 7))
        sc_txt = self.font_label.render(f"Рекорд: {save_mgr.high_score}", True, (245, 166, 35))
        screen.blit(sc_txt, (cx + 62, curr_y + 8))

        # 2. Total Kills
        screen.blit(IconEngine.get_icon("skull", 18), (cx + 30 + sec_w + 8, curr_y + 7))
        kl_txt = self.font_label.render(f"Убийств: {save_mgr.total_kills}", True, (230, 57, 70))
        screen.blit(kl_txt, (cx + 30 + sec_w + 32, curr_y + 8))

        # 3. Souls
        screen.blit(IconEngine.get_icon("soul", 18), (cx + 30 + sec_w * 2 + 8, curr_y + 7))
        sl_txt = self.font_label.render(f"Души: {save_mgr.souls}", True, (72, 202, 228))
        screen.blit(sl_txt, (cx + 30 + sec_w * 2 + 32, curr_y + 8))

        curr_y += 40

        # Menu Action Buttons with icons
        has_run = save_mgr.has_active_run()
        btn_w = min(360, panel_w - 60)
        btn_h = 38 if panel_h >= 580 else 34
        gap = 8 if panel_h >= 580 else 5
        bx = cx + (panel_w - btn_w) // 2

        # 1. Continue Button (if active run saved)
        if has_run:
            active_info = save_mgr.get_active_run()
            wave_num = active_info.get("wave", 1) if active_info else 1
            self.btn_continue_rect = pygame.Rect(bx, curr_y, btn_w, btn_h)
            self._draw_btn(screen, self.btn_continue_rect, f"ПРОДОЛЖИТЬ (ВОЛНА {wave_num})", mouse_pos, (82, 183, 136), (15, 15, 15), icon_name="sword")
            curr_y += btn_h + gap
        else:
            self.btn_continue_rect = pygame.Rect(0, 0, 0, 0)

        # 2. New Game
        self.btn_newgame_rect = pygame.Rect(bx, curr_y, btn_w, btn_h)
        self._draw_btn(screen, self.btn_newgame_rect, "НОВАЯ ИГРА", mouse_pos, (245, 166, 35), (15, 15, 15), icon_name="class_warrior")
        curr_y += btn_h + gap

        # 3. Camp Upgrades (Shop)
        self.btn_camp_rect = pygame.Rect(bx, curr_y, btn_w, btn_h)
        self._draw_btn(screen, self.btn_camp_rect, f"ПРОКАЧКА ЛАГЕРЯ  [{save_mgr.souls}]", mouse_pos, (160, 110, 240), (255, 255, 255), icon_name="hp_boost")
        curr_y += btn_h + gap

        # 4. Statistics & Records
        self.btn_stats_rect = pygame.Rect(bx, curr_y, btn_w, btn_h)
        self._draw_btn(screen, self.btn_stats_rect, "СТАТИСТИКА И РЕКОРДЫ", mouse_pos, (72, 202, 228), (15, 15, 15), icon_name="trophy")
        curr_y += btn_h + gap

        # 5. Settings
        self.btn_settings_rect = pygame.Rect(bx, curr_y, btn_w, btn_h)
        self._draw_btn(screen, self.btn_settings_rect, "НАСТРОЙКИ", mouse_pos, (120, 140, 165), (255, 255, 255), icon_name="gear")
        curr_y += btn_h + gap

        # 6. Controls
        self.btn_controls_rect = pygame.Rect(bx, curr_y, btn_w, btn_h)
        self._draw_btn(screen, self.btn_controls_rect, "УПРАВЛЕНИЕ", mouse_pos, (120, 140, 165), (255, 255, 255), icon_name="gamepad")
        curr_y += btn_h + gap

        # 7. Quit
        self.btn_quit_rect = pygame.Rect(bx, curr_y, btn_w, btn_h)
        self._draw_btn(screen, self.btn_quit_rect, "ВЫХОД", mouse_pos, (230, 57, 70), (255, 255, 255), icon_name="skull")

    # ==========================================================
    # 2. ПРОКАЧКА ЛАГЕРЯ (CAMP UPGRADES / SOUL SHOP)
    # ==========================================================
    def _draw_camp_menu(
        self,
        screen: pygame.Surface,
        save_mgr: SaveManager,
        mouse_pos: Tuple[int, int],
        w: int,
        h: int
    ) -> None:
        panel_w = min(1040, w - 30)
        panel_h = min(620, h - 30)
        cx = (w - panel_w) // 2
        cy = (h - panel_h) // 2

        panel_rect = pygame.Rect(cx, cy, panel_w, panel_h)
        pygame.draw.rect(screen, (15, 18, 25, 245), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (160, 110, 240), panel_rect, width=3, border_radius=12)

        # Header Title & Subtitle
        t_surf = self.font_title.render("ЛАГЕРЬ ГЕРОЕВ — ПОСТОЯННЫЕ УЛУЧШЕНИЯ", True, (160, 110, 240))
        sub_surf = self.font_subtitle.render("Прокачивайте характеристики героев и открывайте легендарное Мастерство каждого класса", True, (180, 190, 205))
        screen.blit(t_surf, (cx + (panel_w - t_surf.get_width()) // 2, cy + 18))
        screen.blit(sub_surf, (cx + (panel_w - sub_surf.get_width()) // 2, cy + 54))

        # Balance Box with soul icon (dynamic width to prevent soul count text overflow)
        bal_txt = self.font_heading.render(f"Души в казне: {save_mgr.souls}", True, (245, 166, 35))
        bal_w = max(260, bal_txt.get_width() + 64)
        bal_rect = pygame.Rect(cx + (panel_w - bal_w) // 2, cy + 80, bal_w, 34)
        pygame.draw.rect(screen, (32, 22, 50), bal_rect, border_radius=8)
        pygame.draw.rect(screen, (160, 110, 240), bal_rect, width=2, border_radius=8)
        screen.blit(IconEngine.get_icon("soul", 20), (bal_rect.x + 18, bal_rect.y + 7))
        screen.blit(bal_txt, (bal_rect.x + 46, bal_rect.y + 5))

        self.camp_hero_rects.clear()
        self.camp_upgrade_btn_rects.clear()
        self.camp_all_heroes_btn_rect = pygame.Rect(0, 0, 0, 0)
        anim_time = pygame.time.get_ticks() / 1000.0

        # -------------------------------------------------------------
        # STATE 1: 4 HEROES OVERVIEW (NO HERO SELECTED YET)
        # -------------------------------------------------------------
        if self.camp_selected_hero is None:
            card_gap = 14
            tot_gaps = card_gap * 3
            card_w = (panel_w - 60 - tot_gaps) // 4
            card_h = panel_h - 188
            start_x = cx + 30
            card_y = cy + 124

            for idx, cid in enumerate(HERO_CLASSES):
                hmeta = HERO_META[cid]
                c_x = start_x + idx * (card_w + card_gap)
                card_rect = pygame.Rect(c_x, card_y, card_w, card_h)
                self.camp_hero_rects[cid] = card_rect

                is_hover = card_rect.collidepoint(mouse_pos)
                c_col = hmeta["color"]

                # Card Body
                bg_col = (26, 33, 46) if is_hover else (18, 22, 30)
                pygame.draw.rect(screen, bg_col, card_rect, border_radius=10)
                border_col = c_col if is_hover else (45, 55, 72)
                pygame.draw.rect(screen, border_col, card_rect, width=2 if is_hover else 1, border_radius=10)

                # Hero Role Badge at top
                tag_rect = pygame.Rect(c_x + 12, card_y + 10, card_w - 24, 20)
                pygame.draw.rect(screen, (30, 38, 52), tag_rect, border_radius=4)
                r_txt = self.font_card_desc.render(hmeta["role"].split("(")[0].strip(), True, c_col)
                screen.blit(r_txt, (tag_rect.x + (tag_rect.width - r_txt.get_width()) // 2, tag_rect.y + 2))

                # Procedural Hero Character Sprite Preview with subtle idle animation
                avatar_box = pygame.Rect(c_x + (card_w - 80) // 2, card_y + 36, 80, 80)
                if is_hover:
                    aura_surf = pygame.Surface((88, 88), pygame.SRCALPHA)
                    pygame.draw.circle(aura_surf, (*c_col, 55), (44, 44), 42)
                    screen.blit(aura_surf, (avatar_box.x - 4, avatar_box.y - 4))
                draw_hero_character(screen, avatar_box.centerx, avatar_box.centery, cid, anim_time=anim_time + idx * 0.7, scale=0.86)

                # Hero Name
                n_surf = self.font_card_title.render(hmeta["name"].upper(), True, (255, 255, 255) if is_hover else (225, 230, 240))
                screen.blit(n_surf, (c_x + (card_w - n_surf.get_width()) // 2, card_y + 120))

                # Divider
                pygame.draw.line(screen, (40, 50, 68), (c_x + 14, card_y + 146), (c_x + card_w - 14, card_y + 146), 1)

                # 3 Stat lines: Speed, Health, Damage
                spd_lvl = save_mgr.get_upgrade_level(f"{cid}_speed")
                hp_lvl = save_mgr.get_upgrade_level(f"{cid}_hp")
                dmg_lvl = save_mgr.get_upgrade_level(f"{cid}_damage")
                tot_lvl = min(15, spd_lvl + hp_lvl + dmg_lvl)

                stat_y = card_y + 154
                for s_name, s_lvl, s_bonus, s_color in [
                    ("Скорость", spd_lvl, f"+{spd_lvl * 6}%", (72, 202, 228)),
                    ("Здоровье", hp_lvl, f"+{hp_lvl * 25}", (230, 57, 70)),
                    ("Урон", dmg_lvl, f"+{dmg_lvl * 8}%", (245, 166, 35)),
                ]:
                    st_txt = self.font_card_desc.render(f"{s_name}:", True, (190, 200, 215))
                    val_txt = self.font_card_desc.render(f"[Ур. {s_lvl}/5] {s_bonus}", True, s_color)
                    screen.blit(st_txt, (c_x + 14, stat_y))
                    screen.blit(val_txt, (c_x + card_w - 14 - val_txt.get_width(), stat_y))
                    stat_y += 24

                # Mastery Status Card / Pill (proper height 72px with strictly clipped text to prevent overflow)
                is_mastered = save_mgr.is_mastery_unlocked(cid)
                pill_h = 72
                mast_pill_rect = pygame.Rect(c_x + 10, stat_y + 10, card_w - 20, pill_h)
                pill_max_w = mast_pill_rect.width - 40

                if is_mastered:
                    pygame.draw.rect(screen, (45, 38, 20), mast_pill_rect, border_radius=6)
                    pygame.draw.rect(screen, (245, 166, 35), mast_pill_rect, width=1, border_radius=6)
                    screen.blit(IconEngine.get_icon("star", 20), (mast_pill_rect.x + 8, mast_pill_rect.y + 8))
                    self._render_clipped_text(screen, "МАСТЕРСТВО [15/15]", self.font_label, (255, 215, 0), mast_pill_rect.x + 34, mast_pill_rect.y + 6, pill_max_w)
                    self._render_clipped_text(screen, hmeta["mastery_title"], self.font_card_desc, (82, 183, 136), mast_pill_rect.x + 10, mast_pill_rect.y + 28, mast_pill_rect.width - 20)
                    self._render_clipped_text(screen, hmeta["mastery_short"], self.font_card_desc, (210, 220, 235), mast_pill_rect.x + 10, mast_pill_rect.y + 48, mast_pill_rect.width - 20)
                else:
                    pygame.draw.rect(screen, (22, 26, 36), mast_pill_rect, border_radius=6)
                    pygame.draw.rect(screen, (45, 55, 75), mast_pill_rect, width=1, border_radius=6)
                    screen.blit(IconEngine.get_icon("lock", 20), (mast_pill_rect.x + 8, mast_pill_rect.y + 8))
                    self._render_clipped_text(screen, f"МАСТЕРСТВО [{tot_lvl}/15]", self.font_label, (170, 180, 195), mast_pill_rect.x + 34, mast_pill_rect.y + 6, pill_max_w)
                    self._render_clipped_text(screen, hmeta["mastery_title"], self.font_card_desc, (245, 166, 35), mast_pill_rect.x + 10, mast_pill_rect.y + 28, mast_pill_rect.width - 20)
                    self._render_clipped_text(screen, hmeta["mastery_short"], self.font_card_desc, (135, 145, 160), mast_pill_rect.x + 10, mast_pill_rect.y + 48, mast_pill_rect.width - 20)

                # Card Bottom Select Prompt Button
                card_btn_rect = pygame.Rect(c_x + 14, card_y + card_h - 42, card_w - 28, 32)
                self._draw_btn(screen, card_btn_rect, "ВЫБРАТЬ ГЕРОЯ", mouse_pos, c_col, (15, 15, 15))

        # -------------------------------------------------------------
        # STATE 2: SELECTED HERO SHIFTED VIEW (HERO ON LEFT, UPGRADES ON RIGHT)
        # -------------------------------------------------------------
        else:
            curr_cid = self.camp_selected_hero
            hmeta = HERO_META[curr_cid]
            c_col = hmeta["color"]

            left_w = 280
            left_x = cx + 30
            left_y = cy + 124
            left_h = panel_h - 188

            # Quick-switch hero tabs at top of left column
            tab_gap = 4
            tab_w = (left_w - tab_gap * 3) // 4
            for t_idx, t_cid in enumerate(HERO_CLASSES):
                t_hmeta = HERO_META[t_cid]
                tab_rect = pygame.Rect(left_x + t_idx * (tab_w + tab_gap), left_y, tab_w, 28)
                self.camp_hero_rects[t_cid] = tab_rect

                is_curr = (t_cid == curr_cid)
                is_tab_hov = tab_rect.collidepoint(mouse_pos)
                tab_bg = t_hmeta["color"] if is_curr else ((38, 46, 62) if is_tab_hov else (22, 28, 38))
                pygame.draw.rect(screen, tab_bg, tab_rect, border_radius=5)
                tab_txt_col = (15, 15, 15) if is_curr else ((240, 245, 250) if is_tab_hov else (170, 180, 195))
                t_surf = self.font_card_desc.render(t_hmeta["name"][:5], True, tab_txt_col)
                screen.blit(t_surf, (tab_rect.x + (tab_w - t_surf.get_width()) // 2, tab_rect.y + 7))

            # Left Hero Showcase Box
            box_y = left_y + 34
            box_h = left_h - 34
            box_rect = pygame.Rect(left_x, box_y, left_w, box_h)
            pygame.draw.rect(screen, (20, 25, 34), box_rect, border_radius=10)
            pygame.draw.rect(screen, c_col, box_rect, width=2, border_radius=10)

            # Large Hero Character Avatar with glowing aura
            avatar_cy = box_y + 68
            aura_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (*c_col, 50), (60, 60), 55)
            screen.blit(aura_surf, (left_x + (left_w - 120) // 2, avatar_cy - 60))
            draw_hero_character(screen, left_x + left_w // 2, avatar_cy, curr_cid, anim_time=anim_time, scale=1.16)

            # Hero Name & Role
            hn_surf = self.font_heading.render(hmeta["name"].upper(), True, (255, 255, 255))
            screen.blit(hn_surf, (left_x + (left_w - hn_surf.get_width()) // 2, box_y + 124))

            hr_surf = self.font_card_desc.render(hmeta["role"], True, c_col)
            screen.blit(hr_surf, (left_x + (left_w - hr_surf.get_width()) // 2, box_y + 150))

            pygame.draw.line(screen, (38, 48, 65), (left_x + 18, box_y + 172), (left_x + left_w - 18, box_y + 172), 1)

            # Hero Training Progress Bar
            tot_lvl = save_mgr.get_class_total_levels(curr_cid)
            p_lbl = self.font_label.render(f"Уровень тренировки: {tot_lvl}/15", True, (220, 225, 235))
            screen.blit(p_lbl, (left_x + (left_w - p_lbl.get_width()) // 2, box_y + 184))

            bar_w = left_w - 44
            bar_h = 10
            bar_x = left_x + 22
            bar_y = box_y + 206
            pygame.draw.rect(screen, (35, 42, 56), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            pct = min(1.0, tot_lvl / 15.0)
            if pct > 0:
                bar_fill_col = (255, 215, 0) if tot_lvl >= 15 else c_col
                pygame.draw.rect(screen, bar_fill_col, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)

            # Mastery Status Card inside Left Box (balanced layout, fills dead space)
            is_mastered = save_mgr.is_mastery_unlocked(curr_cid)
            m_card_rect = pygame.Rect(left_x + 16, box_y + 226, left_w - 32, 114)
            if is_mastered:
                pygame.draw.rect(screen, (42, 34, 18), m_card_rect, border_radius=8)
                pygame.draw.rect(screen, (245, 166, 35), m_card_rect, width=1, border_radius=8)
                screen.blit(IconEngine.get_icon("star", 22), (m_card_rect.x + 10, m_card_rect.y + 10))
                self._render_clipped_text(screen, "МАСТЕРСТВО АКТИВНО", self.font_label, (255, 215, 0), m_card_rect.x + 36, m_card_rect.y + 10, m_card_rect.width - 44)
                pygame.draw.line(screen, (60, 50, 28), (m_card_rect.x + 8, m_card_rect.y + 34), (m_card_rect.right - 8, m_card_rect.y + 34), 1)
                self._render_clipped_text(screen, hmeta["mastery_title"], self.font_card_desc, (82, 183, 136), m_card_rect.x + 10, m_card_rect.y + 40, m_card_rect.width - 20)
                self._render_wrapped_text(screen, hmeta["mastery_short"], self.font_card_desc, (215, 225, 235), m_card_rect.x + 10, m_card_rect.y + 60, max_w=m_card_rect.width - 20, line_spacing=16, max_lines=3)
            else:
                pygame.draw.rect(screen, (22, 26, 36), m_card_rect, border_radius=8)
                pygame.draw.rect(screen, (45, 55, 75), m_card_rect, width=1, border_radius=8)
                screen.blit(IconEngine.get_icon("lock", 22), (m_card_rect.x + 10, m_card_rect.y + 10))
                self._render_clipped_text(screen, f"МАСТЕРСТВО ({tot_lvl}/15)", self.font_label, (170, 180, 195), m_card_rect.x + 36, m_card_rect.y + 10, m_card_rect.width - 44)
                pygame.draw.line(screen, (35, 42, 56), (m_card_rect.x + 8, m_card_rect.y + 34), (m_card_rect.right - 8, m_card_rect.y + 34), 1)
                self._render_clipped_text(screen, f"До открытия: {15 - tot_lvl} ур.", self.font_card_desc, (230, 57, 70), m_card_rect.x + 10, m_card_rect.y + 40, m_card_rect.width - 20)
                self._render_wrapped_text(screen, hmeta["mastery_short"], self.font_card_desc, (135, 145, 160), m_card_rect.x + 10, m_card_rect.y + 60, max_w=m_card_rect.width - 20, line_spacing=16, max_lines=3)

            # Button to go back to 4 heroes overview
            self.camp_all_heroes_btn_rect = pygame.Rect(left_x + 16, box_y + box_h - 44, left_w - 32, 34)
            self._draw_btn(screen, self.camp_all_heroes_btn_rect, "« ВСЕ ГЕРОИ", mouse_pos, (72, 202, 228), (15, 15, 15))

            # ---------------------------------------------------------
            # RIGHT COLUMN: 3 STAT ROWS + HERO MASTERY CARD
            # ---------------------------------------------------------
            right_x = left_x + left_w + 22
            right_w = panel_w - left_w - 82
            right_y = left_y

            stats_order = ["speed", "hp", "damage"]
            row_h = 78
            gap = 10

            for s_idx, stat_key in enumerate(stats_order):
                umeta = CLASS_UPGRADES_META[stat_key]
                up_id = f"{curr_cid}_{stat_key}"
                cur_y = right_y + s_idx * (row_h + gap)
                card_rect = pygame.Rect(right_x, cur_y, right_w, row_h)
                pygame.draw.rect(screen, (22, 26, 36), card_rect, border_radius=8)
                pygame.draw.rect(screen, (45, 55, 75), card_rect, width=1, border_radius=8)

                # Icon Box
                ic_rect = pygame.Rect(card_rect.x + 12, cur_y + (row_h - 54) // 2, 54, 54)
                pygame.draw.rect(screen, (30, 36, 50), ic_rect, border_radius=8)
                pygame.draw.rect(screen, (160, 110, 240), ic_rect, width=1, border_radius=8)
                up_icon = IconEngine.get_icon(up_id, 40)
                screen.blit(up_icon, (ic_rect.x + 7, ic_rect.y + 7))

                # Buy Button
                buy_btn_w = 175
                buy_btn_h = 42
                buy_rect = pygame.Rect(card_rect.right - buy_btn_w - 14, cur_y + (row_h - buy_btn_h) // 2, buy_btn_w, buy_btn_h)
                self.camp_upgrade_btn_rects[up_id] = buy_rect

                cur_lvl = save_mgr.get_upgrade_level(up_id)
                max_lvl = umeta["max_level"]

                # Safe available width for text strictly before buy button
                text_x = card_rect.x + 76
                max_text_w = max(10, (buy_rect.x - 14) - text_x)

                # Line 1: Title & Level text
                t_str = f"{umeta['title']}  •  Уровень {cur_lvl}/{max_lvl}"
                self._render_clipped_text(screen, t_str, self.font_card_title, (255, 255, 255), text_x, cur_y + 11, max_text_w)

                # Line 2: 5 Visual Level Blocks + Current Bonus right beside them
                pips_start_x = text_x
                pips_y = cur_y + 35
                pip_col = (72, 202, 228) if stat_key == "speed" else ((230, 57, 70) if stat_key == "hp" else (245, 166, 35))
                for p_i in range(max_lvl):
                    pip_rect = pygame.Rect(pips_start_x + p_i * 18, pips_y, 14, 7)
                    if p_i < cur_lvl:
                        pygame.draw.rect(screen, pip_col, pip_rect, border_radius=2)
                    else:
                        pygame.draw.rect(screen, (38, 46, 62), pip_rect, border_radius=2)
                        pygame.draw.rect(screen, (55, 65, 85), pip_rect, width=1, border_radius=2)

                unit_str = "%" if stat_key != "hp" else " HP"
                cur_val = cur_lvl * umeta["val_per_lvl"]
                if cur_lvl > 0:
                    cur_bonus_str = f"Текущий бонус: +{cur_val}{unit_str}"
                    cur_bonus_col = pip_col
                else:
                    cur_bonus_str = "Текущий бонус: Базовый (0)"
                    cur_bonus_col = (145, 155, 170)

                pips_end_x = pips_start_x + max_lvl * 18 + 10
                avail_bonus_w = max(10, (buy_rect.x - 14) - pips_end_x)
                self._render_clipped_text(screen, cur_bonus_str, self.font_card_desc, cur_bonus_col, pips_end_x, cur_y + 31, avail_bonus_w)

                # Line 3: Next Level Preview or Max Status
                if cur_lvl < max_lvl:
                    nxt_val = (cur_lvl + 1) * umeta["val_per_lvl"]
                    inc_val = umeta["val_per_lvl"]
                    nxt_str = f"След. уровень: +{nxt_val}{unit_str} (+{inc_val}{unit_str})"
                    nxt_col = (185, 195, 210)
                else:
                    nxt_str = "✦ Максимальный уровень прокачки достигнут ✦"
                    nxt_col = (82, 183, 136)
                self._render_clipped_text(screen, nxt_str, self.font_card_desc, nxt_col, text_x, cur_y + 53, max_text_w)

                # Buy Button Display
                if cur_lvl >= max_lvl:
                    pygame.draw.rect(screen, (35, 52, 40), buy_rect, border_radius=6)
                    m_txt = self.font_btn.render("МАКСИМУМ", True, (82, 183, 136))
                    screen.blit(m_txt, (buy_rect.x + (buy_btn_w - m_txt.get_width()) // 2, buy_rect.y + 11))
                else:
                    cost = save_mgr.get_upgrade_cost(up_id)
                    can_buy = save_mgr.souls >= cost
                    is_hov = buy_rect.collidepoint(mouse_pos)

                    if can_buy:
                        col = (160, 110, 240) if is_hov else (120, 75, 190)
                        txt_col = (255, 255, 255)
                    else:
                        col = (50, 55, 65)
                        txt_col = (140, 145, 155)

                    pygame.draw.rect(screen, col, buy_rect, border_radius=6)
                    pygame.draw.rect(screen, (200, 160, 255) if can_buy else (70, 75, 85), buy_rect, width=1, border_radius=6)

                    btn_lbl = f"Улучшить: {cost}"
                    b_font = self.font_btn
                    s_ic = IconEngine.get_icon("soul", 18)
                    if b_font.size(btn_lbl)[0] + 6 + s_ic.get_width() > buy_btn_w - 14:
                        b_font = self.font_label
                    b_surf = b_font.render(btn_lbl, True, txt_col)
                    tot_w = b_surf.get_width() + 6 + s_ic.get_width()
                    start_bx = max(buy_rect.x + 6, buy_rect.x + (buy_btn_w - tot_w) // 2)
                    screen.blit(b_surf, (start_bx, buy_rect.y + (buy_btn_h - b_surf.get_height()) // 2))
                    screen.blit(s_ic, (start_bx + b_surf.get_width() + 6, buy_rect.y + (buy_btn_h - s_ic.get_height()) // 2))

            # ---------------------------------------------------------
            # ROW 4: HERO MASTERY CARD (UNLOCKED UPON MAXING ALL 3 STATS)
            # ---------------------------------------------------------
            mast_y = right_y + 3 * (row_h + gap)
            mast_h = 108
            mast_rect = pygame.Rect(right_x, mast_y, right_w, mast_h)
            max_mast_w = max(10, mast_rect.right - (mast_rect.x + 84) - 16)
            mast_text_x = mast_rect.x + 84

            if is_mastered:
                # Golden Radiant Unlocked State
                pygame.draw.rect(screen, (38, 30, 18), mast_rect, border_radius=10)
                pygame.draw.rect(screen, (245, 166, 35), mast_rect, width=2, border_radius=10)

                # Icon
                ic_box = pygame.Rect(mast_rect.x + 12, mast_y + 14, 60, 80)
                pygame.draw.rect(screen, (52, 42, 24), ic_box, border_radius=8)
                pygame.draw.rect(screen, (255, 215, 0), ic_box, width=1, border_radius=8)
                star_ic = IconEngine.get_icon("star", 44)
                screen.blit(star_ic, (ic_box.x + (ic_box.width - star_ic.get_width()) // 2, ic_box.y + (ic_box.height - star_ic.get_height()) // 2))

                # Title & Badge & Wrapped Description
                m_title = f"⭐ МАСТЕРСТВО: {hmeta['mastery_title'].upper()}"
                self._render_clipped_text(screen, m_title, self.font_card_title, (255, 215, 0), mast_text_x, mast_y + 11, max_mast_w)
                self._render_clipped_text(screen, "✦ РАЗБЛОКИРОВАНО — УСИЛЕНИЕ АКТИВНО В БОЮ ✦", self.font_label, (82, 183, 136), mast_text_x, mast_y + 33, max_mast_w)
                self._render_wrapped_text(screen, hmeta["mastery_desc"], self.font_card_desc, (240, 245, 250), mast_text_x, mast_y + 55, max_w=max_mast_w, line_spacing=18, max_lines=2)

            else:
                # Steel Locked State
                pygame.draw.rect(screen, (20, 24, 32), mast_rect, border_radius=10)
                pygame.draw.rect(screen, (50, 60, 78), mast_rect, width=1, border_radius=10)

                # Icon
                ic_box = pygame.Rect(mast_rect.x + 12, mast_y + 14, 60, 80)
                pygame.draw.rect(screen, (28, 34, 46), ic_box, border_radius=8)
                pygame.draw.rect(screen, (60, 72, 92), ic_box, width=1, border_radius=8)
                lock_ic = IconEngine.get_icon("lock", 40)
                screen.blit(lock_ic, (ic_box.x + (ic_box.width - lock_ic.get_width()) // 2, ic_box.y + (ic_box.height - lock_ic.get_height()) // 2))

                # Title & Lock details & Wrapped Description
                m_title = f"🔒 Мастерство героя: {hmeta['mastery_title']}"
                req_txt = f"ТРЕБУЕТСЯ 5 УР. ВСЕХ ХАРАКТЕРИСТИК (ПРОКАЧАНО: {tot_lvl}/15)"
                self._render_clipped_text(screen, m_title, self.font_card_title, (185, 195, 210), mast_text_x, mast_y + 11, max_mast_w)
                self._render_clipped_text(screen, req_txt, self.font_label, (230, 70, 80), mast_text_x, mast_y + 33, max_mast_w)
                self._render_wrapped_text(screen, hmeta["mastery_desc"], self.font_card_desc, (145, 155, 170), mast_text_x, mast_y + 55, max_w=max_mast_w, line_spacing=18, max_lines=2)

        # Bottom Back Button
        self.btn_back_rect = pygame.Rect(cx + (panel_w - 220) // 2, cy + panel_h - 48, 220, 36)
        self._draw_btn(screen, self.btn_back_rect, "НАЗАД В МЕНЮ [ESC]", mouse_pos, (72, 202, 228), (15, 15, 15), icon_name="shield")

    # ==========================================================
    # 3. СТАТИСТИКА И РЕКОРДЫ (CAREER STATS)
    # ==========================================================
    def _draw_stats_menu(
        self,
        screen: pygame.Surface,
        save_mgr: SaveManager,
        mouse_pos: Tuple[int, int],
        w: int,
        h: int
    ) -> None:
        panel_w = min(640, w - 40)
        panel_h = min(520, h - 30)
        cx = (w - panel_w) // 2
        cy = (h - panel_h) // 2

        panel_rect = pygame.Rect(cx, cy, panel_w, panel_h)
        pygame.draw.rect(screen, (15, 18, 25, 240), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (72, 202, 228), panel_rect, width=3, border_radius=12)

        t_surf = self.font_title.render("СТАТИСТИКА И РЕКОРДЫ", True, (72, 202, 228))
        sub_surf = self.font_subtitle.render("Общие результаты всех ваших битв с ордой зомби", True, (180, 190, 205))
        screen.blit(t_surf, (cx + (panel_w - t_surf.get_width()) // 2, cy + 28))
        screen.blit(sub_surf, (cx + (panel_w - sub_surf.get_width()) // 2, cy + 72))

        stats_items = [
            ("РЕКОРДНЫЙ СЧЁТ", str(save_mgr.high_score), "trophy", (245, 166, 35)),
            ("МАКСИМАЛЬНАЯ ВОЛНА", str(save_mgr.max_wave), "shield", (72, 202, 228)),
            ("ВСЕГО УНИЧТОЖЕНО ЗОМБИ", f"{save_mgr.total_kills}", "skull", (230, 57, 70)),
            ("СЫГРАНО СРАЖЕНИЙ", str(save_mgr.total_games), "sword", (180, 190, 205)),
            ("НАКОПЛЕНО ДУШ В КАЗНЕ", f"{save_mgr.souls}", "soul", (160, 110, 240)),
        ]

        row_y = cy + 115
        row_h = 50
        row_w = panel_w - 60

        for title, val, icon_key, col in stats_items:
            r_rect = pygame.Rect(cx + 30, row_y, row_w, row_h)
            pygame.draw.rect(screen, (22, 26, 36), r_rect, border_radius=6)
            pygame.draw.rect(screen, (35, 42, 56), r_rect, width=1, border_radius=6)

            ic_surf = IconEngine.get_icon(icon_key, 28)
            v_surf = self.font_stats_val.render(val, True, col)

            screen.blit(ic_surf, (r_rect.x + 16, row_y + 11))
            max_t_w = max(10, r_rect.width - 58 - v_surf.get_width() - 28)
            self._render_clipped_text(screen, title, self.font_label, (200, 210, 225), r_rect.x + 58, row_y + 16, max_t_w)
            screen.blit(v_surf, (r_rect.right - v_surf.get_width() - 18, row_y + 14))

            row_y += row_h + 12

        # Back Button
        self.btn_back_rect = pygame.Rect(cx + (panel_w - 220) // 2, cy + panel_h - 62, 220, 42)
        self._draw_btn(screen, self.btn_back_rect, "НАЗАД В МЕНЮ", mouse_pos, (72, 202, 228), (15, 15, 15), icon_name="shield")

    # ==========================================================
    # 4. НАСТРОЙКИ (SETTINGS)
    # ==========================================================
    def _draw_settings_menu(
        self,
        screen: pygame.Surface,
        save_mgr: SaveManager,
        mouse_pos: Tuple[int, int],
        w: int,
        h: int
    ) -> None:
        panel_w = min(620, w - 40)
        panel_h = min(480, h - 30)
        cx = (w - panel_w) // 2
        cy = (h - panel_h) // 2

        panel_rect = pygame.Rect(cx, cy, panel_w, panel_h)
        pygame.draw.rect(screen, (15, 18, 25, 240), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (245, 166, 35), panel_rect, width=3, border_radius=12)

        t_surf = self.font_title.render("НАСТРОЙКИ ИГРЫ", True, (245, 166, 35))
        sub_surf = self.font_subtitle.render("Параметры звука, визуальных эффектов и экрана", True, (180, 190, 205))
        screen.blit(t_surf, (cx + (panel_w - t_surf.get_width()) // 2, cy + 28))
        screen.blit(sub_surf, (cx + (panel_w - sub_surf.get_width()) // 2, cy + 72))

        self.settings_toggle_rects.clear()

        settings_options = [
            ("sfx_muted", "ЗВУКОВЫЕ ЭФФЕКТЫ (SFX)", "ВЫКЛЮЧЕН" if save_mgr.get_setting("sfx_muted", False) else "ВКЛЮЧЕН", not save_mgr.get_setting("sfx_muted", False)),
            ("screen_shake", "ТРЯСКА ЭКРАНА (SCREEN SHAKE)", "ВКЛЮЧЕНА" if save_mgr.get_setting("screen_shake", True) else "ВЫКЛЮЧЕНА", save_mgr.get_setting("screen_shake", True)),
            ("fullscreen", "ПОЛНОЭКРАННЫЙ РЕЖИМ (F11)", "ВКЛЮЧЕН" if save_mgr.get_setting("fullscreen", False) else "ОКОННЫЙ", save_mgr.get_setting("fullscreen", False)),
        ]

        row_y = cy + 125
        row_w = panel_w - 60
        row_h = 56

        for key, title, val_text, is_enabled in settings_options:
            r_rect = pygame.Rect(cx + 30, row_y, row_w, row_h)
            pygame.draw.rect(screen, (22, 26, 36), r_rect, border_radius=6)
            pygame.draw.rect(screen, (35, 42, 56), r_rect, width=1, border_radius=6)

            toggle_w = 140
            toggle_h = 36
            toggle_rect = pygame.Rect(r_rect.right - toggle_w - 14, row_y + 10, toggle_w, toggle_h)
            self.settings_toggle_rects[key] = toggle_rect

            max_title_w = max(10, toggle_rect.x - (r_rect.x + 18) - 10)
            self._render_clipped_text(screen, title, self.font_card_title, (220, 230, 240), r_rect.x + 18, row_y + 18, max_title_w)

            is_hov = toggle_rect.collidepoint(mouse_pos)
            btn_col = (82, 183, 136) if is_enabled else (70, 75, 85)
            if is_hov:
                btn_col = (116, 198, 157) if is_enabled else (95, 100, 110)

            pygame.draw.rect(screen, btn_col, toggle_rect, border_radius=6)
            v_surf = self.font_btn.render(val_text, True, (15, 15, 15) if is_enabled else (230, 230, 230))
            screen.blit(v_surf, (toggle_rect.x + (toggle_w - v_surf.get_width()) // 2, toggle_rect.y + 8))

            row_y += row_h + 14

        # Back Button
        self.btn_back_rect = pygame.Rect(cx + (panel_w - 220) // 2, cy + panel_h - 62, 220, 42)
        self._draw_btn(screen, self.btn_back_rect, "НАЗАД В МЕНЮ", mouse_pos, (72, 202, 228), (15, 15, 15), icon_name="shield")

    # ==========================================================
    # 5. УПРАВЛЕНИЕ (CONTROLS GUIDE)
    # ==========================================================
    def _draw_controls_menu(
        self,
        screen: pygame.Surface,
        mouse_pos: Tuple[int, int],
        w: int,
        h: int
    ) -> None:
        panel_w = min(740, w - 40)
        panel_h = min(570, h - 30)
        cx = (w - panel_w) // 2
        cy = (h - panel_h) // 2

        panel_rect = pygame.Rect(cx, cy, panel_w, panel_h)
        pygame.draw.rect(screen, (15, 18, 25, 240), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (245, 166, 35), panel_rect, width=3, border_radius=12)

        t_surf = self.font_title.render("РУКОВОДСТВО ПО УПРАВЛЕНИЮ", True, (245, 166, 35))
        screen.blit(t_surf, (cx + (panel_w - t_surf.get_width()) // 2, cy + 22))

        # Subtabs: Keyboard vs Gamepad
        tab_w = 210
        tab_h = 36
        kb_rect = pygame.Rect(cx + (panel_w - tab_w * 2 - 16) // 2, cy + 66, tab_w, tab_h)
        gp_rect = pygame.Rect(kb_rect.right + 16, cy + 66, tab_w, tab_h)
        self.controls_tab_rects["KEYBOARD"] = kb_rect
        self.controls_tab_rects["GAMEPAD"] = gp_rect

        # Draw tabs with procedural icons
        kb_active = (self.controls_subtab == "KEYBOARD")
        pygame.draw.rect(screen, (245, 166, 35) if kb_active else (30, 36, 48), kb_rect, border_radius=6)
        kb_ic = IconEngine.get_icon("keyboard", 20)
        kb_txt = self.font_btn.render("Клавиатура и Мышь", True, (15, 15, 15) if kb_active else (200, 210, 225))
        tot_kb_w = kb_ic.get_width() + 8 + kb_txt.get_width()
        start_kb_x = kb_rect.x + (tab_w - tot_kb_w) // 2
        screen.blit(kb_ic, (start_kb_x, kb_rect.y + (tab_h - kb_ic.get_height()) // 2))
        screen.blit(kb_txt, (start_kb_x + kb_ic.get_width() + 8, kb_rect.y + 8))

        gp_active = (self.controls_subtab == "GAMEPAD")
        pygame.draw.rect(screen, (245, 166, 35) if gp_active else (30, 36, 48), gp_rect, border_radius=6)
        gp_ic = IconEngine.get_icon("gamepad", 20)
        gp_txt = self.font_btn.render("Геймпад / Steam Deck", True, (15, 15, 15) if gp_active else (200, 210, 225))
        tot_gp_w = gp_ic.get_width() + 8 + gp_txt.get_width()
        start_gp_x = gp_rect.x + (tab_w - tot_gp_w) // 2
        screen.blit(gp_ic, (start_gp_x, gp_rect.y + (tab_h - gp_ic.get_height()) // 2))
        screen.blit(gp_txt, (start_gp_x + gp_ic.get_width() + 8, gp_rect.y + 8))

        # Controls rows
        if self.controls_subtab == "KEYBOARD":
            controls = [
                ("[W] [A] [S] [D] / Стрелки", "Движение рыцаря по полю арены"),
                ("Курсор мыши", "Направление взгляда и прицеливание"),
                ("ЛКМ / [1] / [Q]", "Основная атака класса (малый кулдаун)"),
                ("ПКМ / [2] / [E]", "Особый навык 1 (урон по площади / усиленный)"),
                ("Пробел / [3] / [R]", "Мощная способность 2 (снаряд / призыв)"),
                ("Shift / [F]", "Рывок / Телепортация (уворот и неуязвимость)"),
                ("[P] / [Esc]", "Пауза игры"),
                ("[M]", "Быстрое переключение звука"),
            ]
        else:
            controls = [
                ("Левый стик / D-Pad", "Движение героя в любом направлении"),
                ("Правый стик (Twin-Stick)", "Прицеливание в любом направлении 360°"),
                ("[RT] / [RB] / [A]", "Основная атака оружия"),
                ("[LT] / [X]", "Особый навык 1"),
                ("[Y]", "Мощная способность 2"),
                ("[LB] / [B]", "Рывок / Уворот от атак зомби"),
                ("[Start] / [Menu]", "Пауза игры"),
                ("[Select] / [View]", "Вкл / Выкл звук"),
            ]

        row_y = cy + 118
        col1_x = cx + 45
        col2_x = cx + 295
        max_d_w = panel_w - 325

        for k_text, desc_text in controls:
            k_surf = self.font_card_title.render(k_text, True, (72, 202, 228))
            d_font = self.font_label
            if d_font.size(desc_text)[0] > max_d_w:
                d_font = self.font_card_desc
            d_surf = d_font.render(desc_text, True, (220, 225, 235))
            screen.blit(k_surf, (col1_x, row_y))
            screen.blit(d_surf, (col2_x, row_y + 2))
            row_y += 33

        # Back Button
        self.btn_back_rect = pygame.Rect(cx + (panel_w - 220) // 2, cy + panel_h - 58, 220, 42)
        self._draw_btn(screen, self.btn_back_rect, "НАЗАД В МЕНЮ", mouse_pos, (72, 202, 228), (15, 15, 15), icon_name="shield")

    # ==========================================================
    # 6. МОДАЛКИ: АПГРЕЙДЫ (LEVEL UP), ПАУЗА, GAME OVER
    # ==========================================================
    def draw_upgrade_menu(
        self,
        screen: pygame.Surface,
        cards: List[UpgradeCard],
        mouse_pos: Tuple[int, int]
    ) -> None:
        w, h = screen.get_size()

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((5, 7, 12, 215))
        screen.blit(overlay, (0, 0))

        t_surf = self.font_super.render("НОВЫЙ УРОВЕНЬ!", True, (245, 166, 35))
        sub_surf = self.font_heading.render("Выберите улучшение для усиления рыцаря", True, (255, 255, 255))
        screen.blit(t_surf, ((w - t_surf.get_width()) // 2, max(15, h // 6 - 36)))
        screen.blit(sub_surf, ((w - sub_surf.get_width()) // 2, max(55, h // 6 + 22)))

        num_cards = max(1, len(cards))
        card_w = min(270, (w - 60 - (num_cards - 1) * 20) // num_cards)
        card_h = min(340, h - 160)
        spacing = 20 if num_cards > 1 else 0
        total_w = num_cards * card_w + (num_cards - 1) * spacing
        start_x = (w - total_w) // 2
        start_y = (h - card_h) // 2 + 30

        self.upgrade_card_rects = []
        tier_colors = {
            "common": (72, 202, 228),
            "rare": (245, 166, 35),
            "epic": (230, 57, 70),
        }
        tier_names = {
            "common": "ОБЫЧНОЕ",
            "rare": "РЕДКОЕ",
            "epic": "ЭПИЧЕСКОЕ",
        }
        class_colors = {
            "warrior": (245, 166, 35),
            "ranger": (82, 183, 136),
            "mage": (160, 110, 240),
            "summoner": (72, 202, 228),
        }
        class_labels = {
            "warrior": "ВОИН",
            "ranger": "СТРЕЛОК",
            "mage": "МАГ",
            "summoner": "ПРИЗЫВАТЕЛЬ",
        }

        for i, card in enumerate(cards):
            cx = start_x + i * (card_w + spacing)
            cy = start_y
            rect = pygame.Rect(cx, cy, card_w, card_h)
            self.upgrade_card_rects.append(rect)

            is_hover = rect.collidepoint(mouse_pos)
            tier_col = tier_colors.get(card.tier, (200, 200, 200))

            bg_col = (25, 32, 45) if is_hover else (16, 20, 28)
            pygame.draw.rect(screen, bg_col, rect, border_radius=10)
            pygame.draw.rect(screen, tier_col if is_hover else (45, 55, 75), rect, width=3 if is_hover else 2, border_radius=10)

            # TOP-LEFT: Level indicator (NO square brackets!)
            lvl = getattr(card, "level", 1)
            lvl_surf = self.font_label.render(f"УРОВЕНЬ {lvl}/5", True, tier_col)
            screen.blit(lvl_surf, (cx + 14, cy + 12))

            # 5 Level Pips under the level text
            for p_idx in range(5):
                pip_rect = pygame.Rect(cx + 14 + p_idx * 15, cy + 30, 11, 4)
                if p_idx < lvl:
                    pygame.draw.rect(screen, tier_col, pip_rect, border_radius=2)
                else:
                    pygame.draw.rect(screen, (32, 40, 52), pip_rect, border_radius=2)
                    pygame.draw.rect(screen, (50, 60, 75), pip_rect, width=1, border_radius=2)

            # TOP-RIGHT: Tier Pill
            tier_str = tier_names.get(card.tier, card.tier.upper())
            tier_surf = self.font_subtitle.render(tier_str, True, tier_col)
            pill_w = tier_surf.get_width() + 14
            pill_rect = pygame.Rect(cx + card_w - pill_w - 12, cy + 12, pill_w, 22)
            pygame.draw.rect(screen, (22, 28, 38), pill_rect, border_radius=5)
            pygame.draw.rect(screen, tier_col, pill_rect, width=1, border_radius=5)
            screen.blit(tier_surf, (pill_rect.x + 7, pill_rect.y + 3))

            # CENTER ICON BOX
            icon_box = pygame.Rect(cx + (card_w - 70) // 2, cy + 46, 70, 58)
            if is_hover:
                aura_surf = pygame.Surface((86, 74), pygame.SRCALPHA)
                pygame.draw.rect(aura_surf, (*tier_col, 50), (0, 0, 86, 74), border_radius=12)
                screen.blit(aura_surf, (icon_box.x - 8, icon_box.y - 8))
            pygame.draw.rect(screen, (25, 32, 44), icon_box, border_radius=8)
            pygame.draw.rect(screen, tier_col, icon_box, width=2 if is_hover else 1, border_radius=8)

            icon_key = getattr(card, "icon", card.id)
            card_ic = IconEngine.get_icon(icon_key, 44)
            screen.blit(card_ic, (icon_box.x + (70 - card_ic.get_width()) // 2, icon_box.y + (58 - card_ic.get_height()) // 2))

            # CLASS / SCOPE TAG
            class_req = getattr(card, "class_req", None)
            if class_req and class_req in class_labels:
                c_lbl = f"✦ {class_labels[class_req]} ✦"
                c_col = class_colors[class_req]
            else:
                c_lbl = "✦ ОБЩЕЕ ✦"
                c_col = (180, 195, 210)
            tag_surf = self.font_subtitle.render(c_lbl, True, c_col)
            screen.blit(tag_surf, (cx + (card_w - tag_surf.get_width()) // 2, cy + 112))

            # CARD TITLE (safe fitted font)
            title_font = self.font_card_title
            if title_font.size(card.title)[0] > card_w - 20:
                title_font = self.font_btn
            if title_font.size(card.title)[0] > card_w - 20:
                title_font = self.font_label
            title_surf = title_font.render(card.title, True, (255, 255, 255))
            screen.blit(title_surf, (cx + (card_w - title_surf.get_width()) // 2, cy + 132))

            # DIVIDER
            pygame.draw.line(screen, (40, 50, 68), (cx + 16, cy + 156), (cx + card_w - 16, cy + 156), 1)

            # DESCRIPTION (wrapped)
            words = card.desc.split()
            lines = []
            curr_line = ""
            for word in words:
                test_line = f"{curr_line} {word}".strip()
                if self.font_card_desc.size(test_line)[0] < card_w - 28:
                    curr_line = test_line
                else:
                    lines.append(curr_line)
                    curr_line = word
            if curr_line:
                lines.append(curr_line)

            line_y = cy + 166
            for line in lines[:4]:  # limit to max 4 lines
                l_surf = self.font_card_desc.render(line, True, (190, 200, 215))
                screen.blit(l_surf, (cx + (card_w - l_surf.get_width()) // 2, line_y))
                line_y += 18

            # BOTTOM SELECTION BUTTON WITH CLEAR KEYBOARD HOTKEY
            btn_h = 36
            btn_rect = pygame.Rect(cx + 14, cy + card_h - 46, card_w - 28, btn_h)
            btn_bg = tier_col if is_hover else (30, 38, 52)
            pygame.draw.rect(screen, btn_bg, btn_rect, border_radius=6)
            pygame.draw.rect(screen, tier_col, btn_rect, width=1, border_radius=6)

            btn_txt = f">> ВЫБРАТЬ [{i + 1}] <<" if is_hover else f"ВЫБРАТЬ [{i + 1}]"
            btn_col = (15, 15, 15) if is_hover else (225, 235, 245)
            b_font = self.font_btn
            if b_font.size(btn_txt)[0] > card_w - 36:
                b_font = self.font_label
            b_surf = b_font.render(btn_txt, True, btn_col)
            screen.blit(b_surf, (btn_rect.x + (btn_rect.width - b_surf.get_width()) // 2, btn_rect.y + (btn_h - b_surf.get_height()) // 2))

    def draw_pause_menu(self, screen: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        w, h = screen.get_size()

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((8, 10, 15, 220))
        screen.blit(overlay, (0, 0))

        pw, ph = 440, 310
        px = (w - pw) // 2
        py = (h - ph) // 2

        pygame.draw.rect(screen, (16, 20, 28), (px, py, pw, ph), border_radius=10)
        pygame.draw.rect(screen, (72, 202, 228), (px, py, pw, ph), width=3, border_radius=10)

        t_surf = self.font_heading.render("ИГРА ПРИОСТАНОВЛЕНА", True, (245, 166, 35))
        screen.blit(t_surf, (px + (pw - t_surf.get_width()) // 2, py + 22))

        btn_w, btn_h = 300, 44
        bx = px + (pw - btn_w) // 2

        # 1. Resume
        self.resume_btn_rect = pygame.Rect(bx, py + 75, btn_w, btn_h)
        self._draw_btn(screen, self.resume_btn_rect, "Продолжить [ESC]", mouse_pos, (72, 202, 228), (15, 15, 15), icon_name="sword")

        # 2. Save & Exit to Menu
        self.save_quit_btn_rect = pygame.Rect(bx, py + 135, btn_w, btn_h)
        self._draw_btn(screen, self.save_quit_btn_rect, "Сохранить и выйти в меню", mouse_pos, (245, 166, 35), (15, 15, 15), icon_name="shield")

        # 3. Restart
        self.pause_restart_btn_rect = pygame.Rect(bx, py + 195, btn_w, btn_h)
        self._draw_btn(screen, self.pause_restart_btn_rect, "Начать заново [R]", mouse_pos, (230, 57, 70), (255, 255, 255), icon_name="skull")

    def draw_game_over_menu(
        self,
        screen: pygame.Surface,
        wave: int,
        kills: int,
        score: int,
        souls_earned: int,
        high_score: int,
        mouse_pos: Tuple[int, int]
    ) -> None:
        w, h = screen.get_size()

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((15, 5, 8, 235))
        screen.blit(overlay, (0, 0))

        pw, ph = 520, 420
        px = (w - pw) // 2
        py = (h - ph) // 2

        pygame.draw.rect(screen, (22, 16, 20), (px, py, pw, ph), border_radius=12)
        pygame.draw.rect(screen, (230, 57, 70), (px, py, pw, ph), width=3, border_radius=12)

        t_surf = self.font_super.render("ВЫ ПАЛИ В БОЮ", True, (230, 57, 70))
        screen.blit(t_surf, (px + (pw - t_surf.get_width()) // 2, py + 22))

        stats = [
            ("ДОСТИГНУТА ВОЛНА:", str(wave), "shield"),
            ("УНИЧТОЖЕНО ЗОМБИ:", str(kills), "skull"),
            ("ИТОГОВЫЙ СЧЁТ:", str(score), "trophy"),
            ("СОБРАНО ДУШ В ЭТОМ БОЮ:", f"+{souls_earned}", "soul"),
            ("РЕКОРД АРЕНЫ:", str(high_score), "trophy"),
        ]

        sy = py + 92
        for lbl, val, ic_key in stats:
            ic_s = IconEngine.get_icon(ic_key, 20)
            l_surf = self.font_label.render(lbl, True, (180, 190, 205))
            v_surf = self.font_card_title.render(val, True, (245, 166, 35))
            screen.blit(ic_s, (px + 45, sy + 2))
            screen.blit(l_surf, (px + 72, sy + 3))
            screen.blit(v_surf, (px + pw - 45 - v_surf.get_width(), sy - 1))
            sy += 32

        btn_w = 215
        btn_h = 44
        gap = 26
        tot_w = btn_w * 2 + gap
        start_bx = px + (pw - tot_w) // 2

        # Restart
        self.gameover_restart_btn_rect = pygame.Rect(start_bx, py + ph - 68, btn_w, btn_h)
        self._draw_btn(screen, self.gameover_restart_btn_rect, "ИГРАТЬ СНОВА [R]", mouse_pos, (230, 57, 70), (255, 255, 255), icon_name="skull")

        # Main Menu
        self.gameover_menu_btn_rect = pygame.Rect(start_bx + btn_w + gap, py + ph - 68, btn_w, btn_h)
        self._draw_btn(screen, self.gameover_menu_btn_rect, "В ГЛАВНОЕ МЕНЮ", mouse_pos, (72, 202, 228), (15, 15, 15), icon_name="shield")

    def _draw_btn(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        mouse_pos: Tuple[int, int],
        base_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int],
        icon_name: Optional[str] = None
    ) -> None:
        is_hover = rect.collidepoint(mouse_pos)
        fill_col = base_color if is_hover else (max(0, base_color[0] - 50), max(0, base_color[1] - 50), max(0, base_color[2] - 50))
        border_col = (255, 255, 255) if is_hover else base_color

        pygame.draw.rect(screen, fill_col, rect, border_radius=6)
        pygame.draw.rect(screen, border_col, rect, width=2, border_radius=6)

        color = text_color if is_hover else (230, 230, 230)
        ic_surf = IconEngine.get_icon(icon_name, 22) if icon_name else None
        ic_w = ic_surf.get_width() + 8 if ic_surf else 0

        max_txt_w = max(10, rect.width - ic_w - 12)
        font = self.font_btn
        if font.size(text)[0] > max_txt_w:
            font = self.font_label
        if font.size(text)[0] > max_txt_w:
            font = self.font_card_desc

        display_text = text
        if font.size(display_text)[0] > max_txt_w:
            while len(display_text) > 3 and font.size(display_text + "...")[0] > max_txt_w:
                display_text = display_text[:-1]
            display_text += "..."

        t_surf = font.render(display_text, True, color)

        if ic_surf:
            tot_w = ic_surf.get_width() + 8 + t_surf.get_width()
            sx = max(rect.x + 6, rect.x + (rect.width - tot_w) // 2)
            screen.blit(ic_surf, (sx, rect.y + (rect.height - ic_surf.get_height()) // 2))
            screen.blit(t_surf, (sx + ic_surf.get_width() + 8, rect.y + (rect.height - t_surf.get_height()) // 2))
        else:
            sx = max(rect.x + 6, rect.x + (rect.width - t_surf.get_width()) // 2)
            screen.blit(t_surf, (sx, rect.y + (rect.height - t_surf.get_height()) // 2))
