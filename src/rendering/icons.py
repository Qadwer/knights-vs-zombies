"""
Процедурный движок иконок и эмблем.
Генерирует высокодетализированные пиксель-арт иконки для:
- Классов (Воин, Лучник, Маг, Призыватель)
- Навыков классов (16 уникальных способностей)
- Улучшений лагеря (Здоровье, Урон, Скорость, Магнит)
- Интерфейса и HUD (Души, Черепа, Кубки, Геймпад, Клавиатура, Настройки, Звук)
"""

import math
import re
from typing import Dict, Tuple
import pygame


class IconEngine:
    _cache: Dict[Tuple[str, int], pygame.Surface] = {}

    @classmethod
    def get_icon(cls, name: str, size: int = 32) -> pygame.Surface:
        clean_name = re.sub(r"_lvl\d+$", "", name.lower().strip())
        key = (clean_name, size)
        if key in cls._cache:
            return cls._cache[key]

        surf = cls._render_icon(clean_name, size)
        cls._cache[key] = surf
        return surf

    @classmethod
    def _render_icon(cls, name: str, size: int) -> pygame.Surface:
        # Render on high-res 64x64 canvas then scale smoothly to requested size
        canvas_size = 64
        canvas = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)
        cx, cy = canvas_size // 2, canvas_size // 2

        # -------------------------------------------------------------------------
        # 1. CLASS ICONS
        # -------------------------------------------------------------------------
        if name in ("class_warrior", "warrior", "knight"):
            # Background circular crest
            pygame.draw.circle(canvas, (35, 42, 58), (cx, cy), 28)
            pygame.draw.circle(canvas, (245, 166, 35), (cx, cy), 28, 2)
            pygame.draw.circle(canvas, (180, 115, 20), (cx, cy), 26, 1)

            # Crossed Swords behind helmet
            for ang in [-0.785, 0.785]:
                sw_surf = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)
                # Blade
                pygame.draw.line(sw_surf, (220, 230, 240), (cx, cy - 24), (cx, cy + 24), 3)
                pygame.draw.line(sw_surf, (255, 255, 255), (cx - 1, cy - 22), (cx - 1, cy + 18), 1)
                # Crossguard
                pygame.draw.line(sw_surf, (245, 166, 35), (cx - 7, cy + 14), (cx + 7, cy + 14), 2)
                # Pommel
                pygame.draw.circle(sw_surf, (245, 166, 35), (cx, cy + 22), 3)
                rot_sw = pygame.transform.rotate(sw_surf, math.degrees(ang))
                canvas.blit(rot_sw, rot_sw.get_rect(center=(cx, cy)).topleft)

            # Great Helm (Center)
            # Neck/collar plate
            pygame.draw.polygon(canvas, (73, 80, 87), [(cx - 12, cy + 14), (cx + 12, cy + 14), (cx + 8, cy + 20), (cx - 8, cy + 20)])
            # Main helmet dome
            pygame.draw.rect(canvas, (173, 181, 189), (cx - 13, cy - 10, 26, 22), border_radius=6)
            pygame.draw.rect(canvas, (108, 117, 125), (cx - 13, cy - 10, 26, 22), width=2, border_radius=6)
            pygame.draw.ellipse(canvas, (206, 212, 218), (cx - 12, cy - 16, 24, 14))
            pygame.draw.ellipse(canvas, (108, 117, 125), (cx - 12, cy - 16, 24, 14), 1)

            # Golden Visor cross
            pygame.draw.rect(canvas, (245, 166, 35), (cx - 10, cy - 2, 20, 4))
            pygame.draw.rect(canvas, (245, 166, 35), (cx - 2, cy - 9, 4, 18))
            # Visor dark eye slits
            pygame.draw.rect(canvas, (15, 15, 20), (cx - 9, cy - 1, 6, 2))
            pygame.draw.rect(canvas, (15, 15, 20), (cx + 3, cy - 1, 6, 2))
            # Glowing golden eye gaze
            pygame.draw.circle(canvas, (72, 202, 228), (cx - 6, cy), 1)
            pygame.draw.circle(canvas, (72, 202, 228), (cx + 6, cy), 1)

            # Red Feathery Knight Plume
            plume_pts = [(cx - 2, cy - 16), (cx - 6, cy - 26), (cx + 3, cy - 28), (cx + 8, cy - 19), (cx + 2, cy - 15)]
            pygame.draw.polygon(canvas, (230, 57, 70), plume_pts)
            pygame.draw.polygon(canvas, (245, 166, 35), plume_pts, 1)

        elif name in ("class_ranger", "ranger", "archer"):
            # Background circular crest
            pygame.draw.circle(canvas, (25, 45, 35), (cx, cy), 28)
            pygame.draw.circle(canvas, (82, 183, 136), (cx, cy), 28, 2)
            pygame.draw.circle(canvas, (45, 106, 79), (cx, cy), 26, 1)

            # Hunter Recurve Bow (Left arc)
            pygame.draw.arc(canvas, (180, 115, 45), (cx - 22, cy - 24, 24, 48), -math.pi / 2, math.pi / 2, 3)
            pygame.draw.arc(canvas, (120, 70, 25), (cx - 23, cy - 24, 24, 48), -math.pi / 2, math.pi / 2, 1)
            # Bow tips with gold bindings
            pygame.draw.circle(canvas, (245, 166, 35), (cx - 10, cy - 23), 2)
            pygame.draw.circle(canvas, (245, 166, 35), (cx - 10, cy + 23), 2)
            # Bowstring
            pygame.draw.line(canvas, (230, 235, 240), (cx - 10, cy - 23), (cx + 4, cy), 1)
            pygame.draw.line(canvas, (230, 235, 240), (cx + 4, cy), (cx - 10, cy + 23), 1)

            # Nocked Arrow
            pygame.draw.line(canvas, (150, 105, 60), (cx + 4, cy), (cx + 24, cy), 2)
            # Steel Arrowhead
            arrow_pts = [(cx + 22, cy - 4), (cx + 28, cy), (cx + 22, cy + 4)]
            pygame.draw.polygon(canvas, (240, 245, 250), arrow_pts)
            pygame.draw.polygon(canvas, (82, 183, 136), arrow_pts, 1)
            # Emerald fletching feathers
            pygame.draw.polygon(canvas, (82, 183, 136), [(cx + 4, cy - 3), (cx + 10, cy - 3), (cx + 6, cy)])
            pygame.draw.polygon(canvas, (82, 183, 136), [(cx + 4, cy + 3), (cx + 10, cy + 3), (cx + 6, cy)])

            # Quiver on Right
            pygame.draw.polygon(canvas, (100, 60, 30), [(cx + 6, cy - 18), (cx + 16, cy - 22), (cx + 18, cy + 14), (cx + 8, cy + 18)])
            pygame.draw.line(canvas, (245, 166, 35), (cx + 7, cy - 10), (cx + 17, cy - 14), 2)
            # Arrow shafts in quiver
            for ox in [9, 12, 15]:
                pygame.draw.line(canvas, (160, 120, 80), (cx + ox, cy - 20), (cx + ox + 3, cy - 27), 2)
                pygame.draw.circle(canvas, (255, 255, 255), (cx + ox + 3, cy - 27), 1)

        elif name in ("class_mage", "mage", "wizard"):
            # Background circular crest
            pygame.draw.circle(canvas, (35, 25, 55), (cx, cy), 28)
            pygame.draw.circle(canvas, (160, 110, 240), (cx, cy), 28, 2)
            pygame.draw.circle(canvas, (100, 50, 180), (cx, cy), 26, 1)

            # Runic Arcane Circle in Background
            for rad in [14, 20]:
                pygame.draw.circle(canvas, (120, 70, 200, 90), (cx, cy), rad, 1)

            # Arcane Staff (Diagonal)
            pygame.draw.line(canvas, (130, 80, 45), (cx - 16, cy + 22), (cx + 16, cy - 18), 4)
            pygame.draw.line(canvas, (200, 150, 90), (cx - 15, cy + 22), (cx + 15, cy - 18), 1)
            # Staff Gold Head Mounting
            pygame.draw.circle(canvas, (245, 166, 35), (cx + 16, cy - 18), 6, 2)

            # Pulsing Mana Crystal on Staff
            cryst_pts = [(cx + 16, cy - 26), (cx + 22, cy - 18), (cx + 16, cy - 10), (cx + 10, cy - 18)]
            pygame.draw.polygon(canvas, (0, 245, 212), cryst_pts)
            pygame.draw.polygon(canvas, (255, 255, 255), cryst_pts, 1)
            pygame.draw.circle(canvas, (255, 255, 255), (cx + 16, cy - 18), 2)

            # Wizard Hat (Front Center)
            # Brim
            pygame.draw.ellipse(canvas, (75, 30, 130), (cx - 20, cy + 4, 34, 12))
            pygame.draw.ellipse(canvas, (245, 166, 35), (cx - 20, cy + 4, 34, 12), 1)
            # Hat Cone
            hat_pts = [(cx - 14, cy + 7), (cx - 5, cy - 18), (cx + 2, cy - 20), (cx + 7, cy + 7)]
            pygame.draw.polygon(canvas, (100, 45, 170), hat_pts)
            pygame.draw.polygon(canvas, (60, 20, 110), hat_pts, 1)
            # Hat Belt & Gold Star Buckle
            pygame.draw.line(canvas, (245, 166, 35), (cx - 13, cy + 5), (cx + 6, cy + 5), 2)
            pygame.draw.circle(canvas, (255, 220, 50), (cx - 3, cy + 5), 2)

        elif name in ("class_summoner", "summoner", "necromancer"):
            # Background circular crest
            pygame.draw.circle(canvas, (20, 35, 35), (cx, cy), 28)
            pygame.draw.circle(canvas, (72, 202, 228), (cx, cy), 28, 2)
            pygame.draw.circle(canvas, (30, 100, 115), (cx, cy), 26, 1)

            # Twin Spectral Scythes / Horns in back
            pygame.draw.arc(canvas, (80, 245, 180), (cx - 24, cy - 26, 22, 34), math.pi * 0.4, math.pi * 1.3, 3)
            pygame.draw.arc(canvas, (80, 245, 180), (cx + 2, cy - 26, 22, 34), -math.pi * 0.3, math.pi * 0.6, 3)

            # Necromancer Hood
            pygame.draw.polygon(canvas, (18, 22, 28), [(cx - 14, cy + 18), (cx - 15, cy - 8), (cx, cy - 20), (cx + 15, cy - 8), (cx + 14, cy + 18)])
            pygame.draw.polygon(canvas, (72, 202, 228), [(cx - 14, cy + 18), (cx - 15, cy - 8), (cx, cy - 20), (cx + 15, cy - 8), (cx + 14, cy + 18)], 1)

            # Bone Skull Faceplate
            pygame.draw.ellipse(canvas, (225, 235, 230), (cx - 9, cy - 9, 18, 18))
            # Dark Eye Sockets
            pygame.draw.circle(canvas, (10, 15, 20), (cx - 4, cy - 2), 3)
            pygame.draw.circle(canvas, (10, 15, 20), (cx + 4, cy - 2), 3)
            # Glowing Green Spectral Eyes
            pygame.draw.circle(canvas, (80, 245, 180), (cx - 4, cy - 2), 1)
            pygame.draw.circle(canvas, (80, 245, 180), (cx + 4, cy - 2), 1)
            # Nasal cavity & teeth
            pygame.draw.line(canvas, (10, 15, 20), (cx, cy + 2), (cx, cy + 4), 1)
            for tox in [-3, 0, 3]:
                pygame.draw.line(canvas, (10, 15, 20), (cx + tox, cy + 6), (cx + tox, cy + 9), 1)

        # -------------------------------------------------------------------------
        # 2. SKILL ICONS (WARRIOR)
        # -------------------------------------------------------------------------
        elif name in ("skill_slash", "slash", "sword_swing"):
            # Slash trail
            pygame.draw.arc(canvas, (72, 202, 228), (cx - 24, cy - 24, 48, 48), -math.pi * 0.2, math.pi * 0.9, 6)
            pygame.draw.arc(canvas, (255, 255, 255), (cx - 24, cy - 24, 48, 48), -math.pi * 0.1, math.pi * 0.8, 2)
            # Steel Broadsword
            pygame.draw.line(canvas, (240, 245, 250), (cx - 18, cy + 18), (cx + 18, cy - 18), 4)
            pygame.draw.line(canvas, (255, 255, 255), (cx - 18, cy + 18), (cx + 18, cy - 18), 2)
            # Crossguard & Hilt
            pygame.draw.line(canvas, (245, 166, 35), (cx - 14, cy + 8), (cx - 8, cy + 14), 3)
            pygame.draw.circle(canvas, (245, 166, 35), (cx - 19, cy + 19), 3)

        elif name in ("skill_whirlwind", "whirlwind", "spin"):
            # Swirling Tornado Blades
            for a_deg in [0, 120, 240]:
                rad = math.radians(a_deg)
                p1 = (cx + int(math.cos(rad) * 6), cy + int(math.sin(rad) * 6))
                p2 = (cx + int(math.cos(rad + 0.6) * 22), cy + int(math.sin(rad + 0.6) * 22))
                p3 = (cx + int(math.cos(rad + 0.9) * 26), cy + int(math.sin(rad + 0.9) * 26))
                pygame.draw.polygon(canvas, (245, 166, 35), [p1, p2, p3])
                pygame.draw.polygon(canvas, (255, 230, 120), [p1, p2, p3], 1)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 5)
            pygame.draw.circle(canvas, (245, 166, 35), (cx, cy), 8, 2)

        elif name in ("skill_wind_blade", "wind_blade"):
            # Triple Energy Crescent Waves
            for roff, col, th in [(0, (0, 245, 212), 4), (-6, (200, 255, 250), 3), (6, (72, 202, 228), 2)]:
                pygame.draw.arc(canvas, col, (cx - 20 + roff, cy - 22, 38, 44), -math.pi * 0.5, math.pi * 0.5, th)
            # Center Energy Spark
            pygame.draw.circle(canvas, (255, 255, 255), (cx + 6, cy), 3)

        elif name in ("skill_knight_dash", "skill_dash", "dash", "skill_roll", "roll"):
            # Winged Boots / Speed Lines
            for ly in [-8, 0, 8]:
                pygame.draw.line(canvas, (82, 183, 136, 160), (cx - 20, cy + ly), (cx - 6, cy + ly), 2)
            # Armored Boot
            boot_pts = [(cx - 4, cy - 10), (cx + 8, cy - 10), (cx + 10, cy + 4), (cx + 18, cy + 6), (cx + 18, cy + 12), (cx - 6, cy + 12)]
            pygame.draw.polygon(canvas, (82, 183, 136), boot_pts)
            pygame.draw.polygon(canvas, (255, 255, 255), boot_pts, 1)
            # Wing feathers
            pygame.draw.polygon(canvas, (255, 255, 255), [(cx - 2, cy - 2), (cx - 12, cy - 14), (cx - 4, cy - 8)])

        # -------------------------------------------------------------------------
        # 3. SKILL ICONS (RANGER)
        # -------------------------------------------------------------------------
        elif name in ("skill_arrow_shot", "arrow_shot", "sniper"):
            # Longbow & Nocked Arrow
            pygame.draw.arc(canvas, (180, 115, 45), (cx - 16, cy - 20, 20, 40), -math.pi / 2, math.pi / 2, 3)
            pygame.draw.line(canvas, (230, 235, 240), (cx - 6, cy - 19), (cx - 6, cy + 19), 1)
            pygame.draw.line(canvas, (240, 245, 250), (cx - 12, cy), (cx + 20, cy), 2)
            pygame.draw.polygon(canvas, (82, 183, 136), [(cx + 18, cy - 4), (cx + 24, cy), (cx + 18, cy + 4)])

        elif name in ("skill_multishot", "multishot", "volley"):
            # Fan of 5 Arrows
            for a_off in [-0.5, -0.25, 0.0, 0.25, 0.5]:
                ex = cx + int(math.cos(a_off) * 22)
                ey = cy + int(math.sin(a_off) * 22)
                pygame.draw.line(canvas, (180, 130, 70), (cx - 8, cy), (ex, ey), 2)
                pygame.draw.circle(canvas, (82, 183, 136), (ex, ey), 2)

        elif name in ("skill_explosive_arrow", "explosive_arrow"):
            # Flaming Arrow with Bomb Head
            pygame.draw.line(canvas, (180, 130, 70), (cx - 18, cy), (cx + 6, cy), 2)
            # Round bomb
            pygame.draw.circle(canvas, (35, 40, 45), (cx + 10, cy), 8)
            pygame.draw.circle(canvas, (230, 57, 70), (cx + 10, cy), 8, 2)
            # Burning Fuse
            pygame.draw.arc(canvas, (245, 166, 35), (cx + 8, cy - 14, 10, 10), 0, math.pi * 0.8, 2)
            pygame.draw.circle(canvas, (255, 230, 50), (cx + 16, cy - 12), 3)

        # -------------------------------------------------------------------------
        # 4. SKILL ICONS (MAGE)
        # -------------------------------------------------------------------------
        elif name in ("skill_arcane_bolt", "arcane_bolt"):
            # Swirling Arcane Nebula
            pygame.draw.circle(canvas, (160, 110, 240, 80), (cx, cy), 18)
            pygame.draw.circle(canvas, (200, 140, 255), (cx, cy), 12, 2)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 5)
            # Four Star Glints
            for ang in [0, 1.57, 3.14, 4.71]:
                p1 = (cx + int(math.cos(ang) * 4), cy + int(math.sin(ang) * 4))
                p2 = (cx + int(math.cos(ang) * 20), cy + int(math.sin(ang) * 20))
                pygame.draw.line(canvas, (220, 180, 255), p1, p2, 2)

        elif name in ("skill_fireball", "fireball"):
            # Layered Raging Fireball
            pygame.draw.circle(canvas, (230, 57, 70), (cx - 2, cy), 14)
            pygame.draw.circle(canvas, (245, 166, 35), (cx - 2, cy), 10)
            pygame.draw.circle(canvas, (255, 240, 120), (cx - 2, cy), 6)
            # Flame trails behind
            flame_pts = [(cx + 4, cy - 10), (cx + 22, cy - 8), (cx + 12, cy), (cx + 24, cy + 6), (cx + 4, cy + 10)]
            pygame.draw.polygon(canvas, (245, 166, 35), flame_pts)
            pygame.draw.polygon(canvas, (255, 220, 50), [(cx + 4, cy - 6), (cx + 16, cy), (cx + 4, cy + 6)])

        elif name in ("skill_frost_nova", "frost_nova"):
            # Intricate Crystalline Snowflake Star
            for a_deg in [0, 60, 120]:
                rad = math.radians(a_deg)
                dx, dy = int(math.cos(rad) * 20), int(math.sin(rad) * 20)
                pygame.draw.line(canvas, (0, 245, 212), (cx - dx, cy - dy), (cx + dx, cy + dy), 3)
                pygame.draw.line(canvas, (255, 255, 255), (cx - dx, cy - dy), (cx + dx, cy + dy), 1)
                # Chevron branches
                for sign in [-1, 1]:
                    bx, by = cx + int(dx * 0.6 * sign), cy + int(dy * 0.6 * sign)
                    pygame.draw.circle(canvas, (180, 245, 255), (bx, by), 2)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 4)

        elif name in ("skill_teleport", "blink"):
            # Twin Spatial Rift Gates
            pygame.draw.ellipse(canvas, (160, 110, 240), (cx - 18, cy - 18, 14, 36), 2)
            pygame.draw.ellipse(canvas, (0, 245, 212), (cx + 4, cy - 18, 14, 36), 2)
            # Warp Streak
            pygame.draw.line(canvas, (255, 255, 255), (cx - 10, cy), (cx + 10, cy), 2)
            pygame.draw.circle(canvas, (255, 255, 255), (cx - 11, cy), 3)
            pygame.draw.circle(canvas, (255, 255, 255), (cx + 11, cy), 3)

        # -------------------------------------------------------------------------
        # 5. SKILL ICONS (SUMMONER)
        # -------------------------------------------------------------------------
        elif name in ("skill_spirit_whip", "spirit_whip"):
            # Sinuous Spectral Barbed Whip
            whip_pts = [(cx - 16, cy + 14), (cx - 8, cy + 4), (cx, cy + 8), (cx + 8, cy - 4), (cx + 18, cy - 14)]
            pygame.draw.lines(canvas, (80, 245, 180), False, whip_pts, 3)
            pygame.draw.lines(canvas, (255, 255, 255), False, whip_pts, 1)
            # Barbs / Souls on whip
            for px, py in whip_pts:
                pygame.draw.circle(canvas, (72, 202, 228), (px, py), 2)

        elif name in ("skill_summon", "summon", "minions"):
            # Undead Skull with Crown of Green Flames
            pygame.draw.circle(canvas, (220, 235, 230), (cx, cy + 2), 11)
            # Jaw
            pygame.draw.rect(canvas, (200, 215, 210), (cx - 6, cy + 9, 12, 7), border_radius=2)
            # Dark Eye Sockets
            pygame.draw.circle(canvas, (15, 20, 25), (cx - 4, cy + 2), 3)
            pygame.draw.circle(canvas, (15, 20, 25), (cx + 4, cy + 2), 3)
            # Glowing green spirit eyes
            pygame.draw.circle(canvas, (80, 245, 180), (cx - 4, cy + 2), 1)
            pygame.draw.circle(canvas, (80, 245, 180), (cx + 4, cy + 2), 1)
            # Flame tips on head
            for fx in [-6, 0, 6]:
                pygame.draw.polygon(canvas, (80, 245, 180), [(cx + fx - 2, cy - 8), (cx + fx, cy - 18), (cx + fx + 2, cy - 8)])

        elif name in ("skill_soul_burst", "soul_burst"):
            # Trio of screaming souls
            for a_off in [-0.5, 0.0, 0.5]:
                sx = cx + int(math.cos(a_off) * 16)
                sy = cy + int(math.sin(a_off) * 16)
                pygame.draw.circle(canvas, (72, 202, 228), (sx, sy), 6)
                pygame.draw.circle(canvas, (15, 25, 35), (sx, sy), 2)
            pygame.draw.circle(canvas, (255, 255, 255), (cx - 6, cy), 5)

        elif name in ("skill_ghost_step", "ghost_step"):
            # Spectral ethereal phantom mist
            pygame.draw.ellipse(canvas, (72, 202, 228), (cx - 10, cy - 14, 20, 26), 2)
            pygame.draw.circle(canvas, (0, 245, 212), (cx, cy - 4), 5)
            for wy in [-6, 2, 10]:
                pygame.draw.line(canvas, (180, 245, 255), (cx - 14, cy + wy), (cx - 4, cy + wy), 2)

        # -------------------------------------------------------------------------
        # 6. CAMP & GENERAL UI ICONS
        # -------------------------------------------------------------------------
        elif name in ("hp_boost", "heart", "health", "hp", "stat_hp") or name.endswith("_hp"):
            # Ruby Heart with Gold Border & Highlight
            pts_l = [(cx, cy + 18), (cx - 16, cy + 2), (cx - 16, cy - 10), (cx - 8, cy - 16), (cx, cy - 8)]
            pts_r = [(cx, cy - 8), (cx + 8, cy - 16), (cx + 16, cy - 10), (cx + 16, cy + 2), (cx, cy + 18)]
            pygame.draw.polygon(canvas, (230, 57, 70), pts_l + pts_r)
            pygame.draw.polygon(canvas, (245, 166, 35), pts_l + pts_r, 2)
            # Specular Glint
            pygame.draw.ellipse(canvas, (255, 200, 210), (cx - 12, cy - 12, 6, 6))

        elif name in ("damage_boost", "sword", "weapons", "damage", "stat_damage") or name.endswith("_damage"):
            # Crossed Golden Blades
            for ang in [-0.785, 0.785]:
                sw_surf = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)
                pygame.draw.line(sw_surf, (245, 166, 35), (cx, cy - 20), (cx, cy + 20), 3)
                pygame.draw.line(sw_surf, (255, 255, 255), (cx, cy - 18), (cx, cy + 12), 1)
                pygame.draw.line(sw_surf, (200, 120, 20), (cx - 5, cy + 12), (cx + 5, cy + 12), 2)
                rot = pygame.transform.rotate(sw_surf, math.degrees(ang))
                canvas.blit(rot, rot.get_rect(center=(cx, cy)).topleft)

        elif name in ("speed_boost", "boots", "wings", "speed", "stat_speed") or name.endswith("_speed"):
            # Winged Boots
            pygame.draw.polygon(canvas, (72, 202, 228), [(cx - 4, cy - 8), (cx + 8, cy - 8), (cx + 10, cy + 6), (cx + 18, cy + 8), (cx + 18, cy + 14), (cx - 6, cy + 14)])
            pygame.draw.polygon(canvas, (255, 255, 255), [(cx - 4, cy - 8), (cx + 8, cy - 8), (cx + 10, cy + 6), (cx + 18, cy + 8), (cx + 18, cy + 14), (cx - 6, cy + 14)], 1)
            # Wings
            pygame.draw.polygon(canvas, (245, 166, 35), [(cx - 2, cy), (cx - 16, cy - 12), (cx - 6, cy - 6)])

        elif name in ("lock", "locked", "padlock"):
            # Steel shackle + golden padlock body
            pygame.draw.arc(canvas, (200, 210, 225), (cx - 9, cy - 20, 18, 20), 0, math.pi, 4)
            pygame.draw.rect(canvas, (245, 166, 35), (cx - 14, cy - 6, 28, 22), border_radius=4)
            pygame.draw.rect(canvas, (180, 115, 20), (cx - 14, cy - 6, 28, 22), width=2, border_radius=4)
            pygame.draw.circle(canvas, (20, 25, 35), (cx, cy + 2), 3)
            pygame.draw.line(canvas, (20, 25, 35), (cx, cy + 2), (cx, cy + 9), 2)

        elif name in ("star", "mastery", "crown"):
            # Golden radiant star / emblem
            pygame.draw.circle(canvas, (245, 166, 35, 60), (cx, cy), 24)
            star_pts = []
            for i in range(10):
                r = 22 if i % 2 == 0 else 9
                a = -math.pi / 2 + i * (math.pi / 5)
                star_pts.append((cx + int(math.cos(a) * r), cy + int(math.sin(a) * r)))
            pygame.draw.polygon(canvas, (255, 215, 0), star_pts)
            pygame.draw.polygon(canvas, (255, 255, 255), star_pts, 1)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 4)

        elif name in ("magnet_boost", "magnet"):
            # Golden Horseshoe Magnet
            pygame.draw.arc(canvas, (245, 166, 35), (cx - 16, cy - 14, 32, 32), 0, math.pi, 8)
            # Red/Blue Pole Tips
            pygame.draw.rect(canvas, (230, 57, 70), (cx - 16, cy + 2, 8, 12), border_radius=2)
            pygame.draw.rect(canvas, (72, 202, 228), (cx + 8, cy + 2, 8, 12), border_radius=2)
            # Magnetic Wave Sparks
            pygame.draw.arc(canvas, (255, 255, 255), (cx - 10, cy + 8, 20, 14), math.pi * 0.1, math.pi * 0.9, 1)

        elif name in ("soul", "souls", "gem"):
            # Ethereal Cyan Soul Gem / Flame Wisp
            gem_pts = [(cx, cy - 18), (cx + 12, cy - 2), (cx, cy + 18), (cx - 12, cy - 2)]
            pygame.draw.polygon(canvas, (72, 202, 228), gem_pts)
            pygame.draw.polygon(canvas, (255, 255, 255), gem_pts, 2)
            inner_pts = [(cx, cy - 10), (cx + 6, cy - 2), (cx, cy + 10), (cx - 6, cy - 2)]
            pygame.draw.polygon(canvas, (200, 255, 250), inner_pts)

        elif name in ("skull", "kills"):
            # Stylized Skull
            pygame.draw.circle(canvas, (230, 235, 240), (cx, cy - 2), 12)
            pygame.draw.rect(canvas, (200, 205, 210), (cx - 7, cy + 6, 14, 8), border_radius=2)
            pygame.draw.circle(canvas, (20, 25, 30), (cx - 5, cy - 1), 3)
            pygame.draw.circle(canvas, (20, 25, 30), (cx + 5, cy - 1), 3)
            pygame.draw.circle(canvas, (230, 57, 70), (cx - 5, cy - 1), 1)
            pygame.draw.circle(canvas, (230, 57, 70), (cx + 5, cy - 1), 1)

        elif name in ("trophy", "cup", "records"):
            # Golden Cup / Trophy
            pygame.draw.polygon(canvas, (245, 166, 35), [(cx - 14, cy - 14), (cx + 14, cy - 14), (cx + 10, cy + 4), (cx - 10, cy + 4)])
            pygame.draw.rect(canvas, (180, 115, 20), (cx - 4, cy + 4, 8, 10))
            pygame.draw.rect(canvas, (245, 166, 35), (cx - 12, cy + 14, 24, 6), border_radius=2)
            # Handles
            pygame.draw.arc(canvas, (245, 166, 35), (cx - 20, cy - 12, 10, 14), math.pi * 0.5, math.pi * 1.5, 2)
            pygame.draw.arc(canvas, (245, 166, 35), (cx + 10, cy - 12, 10, 14), -math.pi * 0.5, math.pi * 0.5, 2)
            pygame.draw.circle(canvas, (230, 57, 70), (cx, cy - 5), 2)  # Gem

        elif name in ("gear", "settings"):
            # Steampunk Brass Gear
            pygame.draw.circle(canvas, (245, 166, 35), (cx, cy), 14)
            for i in range(8):
                ang = i * (math.pi / 4)
                tx = cx + int(math.cos(ang) * 16)
                ty = cy + int(math.sin(ang) * 16)
                pygame.draw.circle(canvas, (245, 166, 35), (tx, ty), 4)
            pygame.draw.circle(canvas, (25, 30, 40), (cx, cy), 7)
            pygame.draw.circle(canvas, (245, 166, 35), (cx, cy), 4)

        elif name in ("keyboard", "keys"):
            # Detailed Retro Keyboard
            pygame.draw.rect(canvas, (35, 42, 54), (cx - 20, cy - 12, 40, 24), border_radius=3)
            pygame.draw.rect(canvas, (72, 202, 228), (cx - 20, cy - 12, 40, 24), width=1, border_radius=3)
            for ky in [-6, 0, 6]:
                for kx in [-14, -6, 2, 10]:
                    pygame.draw.rect(canvas, (70, 80, 100), (cx + kx, cy + ky, 5, 4))
            # Glowing WASD Keys
            pygame.draw.rect(canvas, (245, 166, 35), (cx - 6, cy - 6, 5, 4))

        elif name in ("gamepad", "controller"):
            # Classic Gamepad
            pygame.draw.rect(canvas, (35, 42, 54), (cx - 18, cy - 10, 36, 20), border_radius=8)
            pygame.draw.rect(canvas, (160, 110, 240), (cx - 18, cy - 10, 36, 20), width=1, border_radius=8)
            # D-Pad Cross
            pygame.draw.rect(canvas, (200, 210, 225), (cx - 12, cy - 4, 8, 3))
            pygame.draw.rect(canvas, (200, 210, 225), (cx - 10, cy - 6, 3, 8))
            # Colored Buttons
            pygame.draw.circle(canvas, (230, 57, 70), (cx + 8, cy - 3), 2)
            pygame.draw.circle(canvas, (72, 202, 228), (cx + 13, cy + 1), 2)
            pygame.draw.circle(canvas, (82, 183, 136), (cx + 8, cy + 3), 2)
            pygame.draw.circle(canvas, (245, 166, 35), (cx + 4, cy + 1), 2)

        elif name in ("shield", "defense", "armor"):
            # Polished Knight Heater Shield
            sh_pts = [(cx - 18, cy - 20), (cx + 18, cy - 20), (cx + 18, cy + 4), (cx, cy + 24), (cx - 18, cy + 4)]
            pygame.draw.polygon(canvas, (40, 55, 80), sh_pts)
            pygame.draw.polygon(canvas, (245, 166, 35), sh_pts, 3)
            inner_pts = [(cx - 13, cy - 16), (cx + 13, cy - 16), (cx + 13, cy + 2), (cx, cy + 18), (cx - 13, cy + 2)]
            pygame.draw.polygon(canvas, (28, 40, 60), inner_pts)
            # Heraldic Cross
            pygame.draw.line(canvas, (72, 202, 228), (cx, cy - 16), (cx, cy + 17), 3)
            pygame.draw.line(canvas, (72, 202, 228), (cx - 12, cy - 5), (cx + 12, cy - 5), 3)
            # Corner rivets
            for rx, ry in [(cx - 14, cy - 16), (cx + 14, cy - 16), (cx, cy + 20)]:
                pygame.draw.circle(canvas, (245, 166, 35), (rx, ry), 2)
            # Specular sheen
            pygame.draw.line(canvas, (255, 255, 255, 160), (cx - 12, cy - 14), (cx - 2, cy - 4), 2)

        elif name in ("sound_on", "audio_on"):
            # Speaker megaphone emitting sound waves
            spk_pts = [(cx - 16, cy - 6), (cx - 8, cy - 6), (cx, cy - 14), (cx, cy + 14), (cx - 8, cy + 6), (cx - 16, cy + 6)]
            pygame.draw.polygon(canvas, (200, 215, 230), spk_pts)
            pygame.draw.polygon(canvas, (255, 255, 255), spk_pts, 1)
            # Wave arcs
            pygame.draw.arc(canvas, (82, 183, 136), (cx - 2, cy - 8, 12, 16), -math.pi * 0.4, math.pi * 0.4, 2)
            pygame.draw.arc(canvas, (82, 183, 136), (cx + 4, cy - 14, 16, 28), -math.pi * 0.4, math.pi * 0.4, 2)
            pygame.draw.arc(canvas, (72, 202, 228), (cx + 10, cy - 20, 20, 40), -math.pi * 0.4, math.pi * 0.4, 2)

        elif name in ("sound_off", "audio_off", "mute"):
            # Speaker megaphone with red strike line
            spk_pts = [(cx - 16, cy - 6), (cx - 8, cy - 6), (cx, cy - 14), (cx, cy + 14), (cx - 8, cy + 6), (cx - 16, cy + 6)]
            pygame.draw.polygon(canvas, (130, 140, 155), spk_pts)
            pygame.draw.polygon(canvas, (170, 180, 195), spk_pts, 1)
            # Red slash
            pygame.draw.line(canvas, (230, 57, 70), (cx - 14, cy - 14), (cx + 16, cy + 14), 3)
            pygame.draw.line(canvas, (255, 100, 110), (cx - 14, cy - 14), (cx + 16, cy + 14), 1)

        # -------------------------------------------------------------------------
        # 7. RUN-TIME UPGRADE CARDS (LEVEL UP) & ABILITY ICONS
        # -------------------------------------------------------------------------
        # --- COMMON UPGRADES ---
        elif name in ("upg_dmg", "common_dmg_sharp", "dmg_sharp", "sharp", "blade"):
            # Sharpened Steel Sword with Whetting Sparks & Golden Aura
            pygame.draw.circle(canvas, (245, 166, 35, 50), (cx, cy), 24)
            pygame.draw.line(canvas, (230, 240, 255), (cx - 16, cy + 16), (cx + 18, cy - 18), 4)
            pygame.draw.line(canvas, (255, 255, 255), (cx - 16, cy + 16), (cx + 18, cy - 18), 2)
            pygame.draw.line(canvas, (245, 166, 35), (cx - 14, cy + 8), (cx - 6, cy + 16), 3)
            pygame.draw.circle(canvas, (245, 166, 35), (cx - 18, cy + 18), 3)
            for sx, sy in [(cx + 14, cy - 14), (cx + 6, cy - 4), (cx - 2, cy + 6)]:
                pygame.draw.circle(canvas, (255, 220, 50), (sx + 4, sy - 3), 3)
                pygame.draw.circle(canvas, (255, 255, 255), (sx + 4, sy - 3), 1)

        elif name in ("upg_vitality", "common_vitality", "vitality_armor", "cuirass"):
            # Steel Armored Cuirass with Pulsing Ruby Heart
            pygame.draw.polygon(canvas, (70, 85, 110), [(cx - 18, cy - 16), (cx + 18, cy - 16), (cx + 14, cy + 16), (cx - 14, cy + 16)])
            pygame.draw.polygon(canvas, (245, 166, 35), [(cx - 18, cy - 16), (cx + 18, cy - 16), (cx + 14, cy + 16), (cx - 14, cy + 16)], 2)
            pygame.draw.arc(canvas, (20, 25, 35), (cx - 8, cy - 22, 16, 12), 0, math.pi, 3)
            h_pts = [(cx, cy + 10), (cx - 9, cy - 1), (cx - 8, cy - 8), (cx, cy - 3), (cx + 8, cy - 8), (cx + 9, cy - 1)]
            pygame.draw.polygon(canvas, (230, 45, 65), h_pts)
            pygame.draw.polygon(canvas, (255, 200, 210), h_pts, 1)

        elif name in ("upg_speed", "common_swiftness", "swift_boots", "boots"):
            # Winged Boots with Speed Trails
            for ty in [-8, 0, 8]:
                pygame.draw.line(canvas, (72, 202, 228, 160), (cx - 22, cy + ty), (cx - 8, cy + ty), 2)
            boot_pts = [(cx - 4, cy - 10), (cx + 8, cy - 10), (cx + 10, cy + 4), (cx + 18, cy + 6), (cx + 18, cy + 12), (cx - 6, cy + 12)]
            pygame.draw.polygon(canvas, (245, 166, 35), boot_pts)
            pygame.draw.polygon(canvas, (255, 255, 255), boot_pts, 1)
            pygame.draw.polygon(canvas, (72, 202, 228), [(cx - 2, cy - 2), (cx - 14, cy - 14), (cx - 4, cy - 8)])
            pygame.draw.polygon(canvas, (255, 255, 255), [(cx - 2, cy - 2), (cx - 14, cy - 14), (cx - 4, cy - 8)], 1)

        elif name in ("upg_magnet", "common_magnet", "soul_magnet"):
            # Golden Lodestone with Inflowing Soul Wisps
            pygame.draw.arc(canvas, (245, 166, 35), (cx - 16, cy - 12, 32, 28), 0, math.pi, 7)
            pygame.draw.rect(canvas, (230, 57, 70), (cx - 16, cy + 2, 7, 10), border_radius=2)
            pygame.draw.rect(canvas, (72, 202, 228), (cx + 9, cy + 2, 7, 10), border_radius=2)
            for ox, oy in [(-9, 14), (0, 18), (9, 14)]:
                pygame.draw.circle(canvas, (72, 202, 228), (cx + ox, cy + oy), 3)
                pygame.draw.circle(canvas, (255, 255, 255), (cx + ox, cy + oy), 1)

        elif name in ("upg_haste", "common_haste", "haste_steel", "haste"):
            # Hourglass with Lightning Flash
            pygame.draw.polygon(canvas, (245, 166, 35), [(cx - 12, cy - 16), (cx + 12, cy - 16), (cx, cy), (cx + 12, cy + 16), (cx - 12, cy + 16)], 2)
            pygame.draw.line(canvas, (255, 220, 50), (cx - 14, cy - 16), (cx + 14, cy - 16), 2)
            pygame.draw.line(canvas, (255, 220, 50), (cx - 14, cy + 16), (cx + 14, cy + 16), 2)
            pygame.draw.lines(canvas, (72, 202, 228), False, [(cx + 6, cy - 14), (cx - 4, cy), (cx + 4, cy + 2), (cx - 6, cy + 14)], 3)

        # --- WARRIOR UPGRADES ---
        elif name in ("upg_cleave", "war_cleave", "broad_cleave", "cleave"):
            pygame.draw.arc(canvas, (245, 166, 35), (cx - 24, cy - 24, 48, 48), -math.pi * 0.4, math.pi * 0.8, 5)
            pygame.draw.arc(canvas, (255, 255, 255), (cx - 24, cy - 24, 48, 48), -math.pi * 0.3, math.pi * 0.7, 2)
            pygame.draw.line(canvas, (240, 245, 250), (cx - 14, cy + 18), (cx + 18, cy - 14), 4)
            pygame.draw.circle(canvas, (245, 166, 35), (cx - 16, cy + 20), 4)

        elif name in ("upg_iron_skin", "war_iron_skin", "iron_skin"):
            pygame.draw.polygon(canvas, (80, 95, 115), [(cx - 16, cy - 16), (cx + 16, cy - 16), (cx + 12, cy + 16), (cx, cy + 22), (cx - 12, cy + 16)])
            pygame.draw.polygon(canvas, (200, 215, 230), [(cx - 16, cy - 16), (cx + 16, cy - 16), (cx + 12, cy + 16), (cx, cy + 22), (cx - 12, cy + 16)], 2)
            pygame.draw.line(canvas, (245, 166, 35), (cx - 10, cy - 10), (cx + 10, cy + 10), 2)
            pygame.draw.line(canvas, (245, 166, 35), (cx + 10, cy - 10), (cx - 10, cy + 10), 2)

        elif name in ("upg_whirlwind", "war_whirlwind"):
            pygame.draw.circle(canvas, (230, 57, 70, 70), (cx, cy), 22)
            for a_offset in [0, math.pi * 0.5, math.pi, math.pi * 1.5]:
                p1 = (cx + int(math.cos(a_offset) * 8), cy + int(math.sin(a_offset) * 8))
                p2 = (cx + int(math.cos(a_offset) * 22), cy + int(math.sin(a_offset) * 22))
                pygame.draw.line(canvas, (255, 180, 40), p1, p2, 3)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 5)

        elif name in ("upg_wind_blade", "war_wind_blade"):
            pygame.draw.arc(canvas, (72, 202, 228), (cx - 20, cy - 20, 40, 40), -math.pi * 0.4, math.pi * 0.5, 4)
            pygame.draw.arc(canvas, (255, 255, 255), (cx - 22, cy - 22, 44, 44), -math.pi * 0.35, math.pi * 0.45, 2)
            pygame.draw.line(canvas, (72, 202, 228), (cx - 12, cy + 12), (cx + 14, cy - 14), 2)

        elif name in ("upg_thorns", "war_thorns", "spiked_bulwark", "thorns", "spikes"):
            pygame.draw.polygon(canvas, (55, 65, 80), [(cx - 16, cy - 18), (cx + 16, cy - 18), (cx + 16, cy + 6), (cx, cy + 22), (cx - 16, cy + 6)])
            pygame.draw.polygon(canvas, (180, 190, 205), [(cx - 16, cy - 18), (cx + 16, cy - 18), (cx + 16, cy + 6), (cx, cy + 22), (cx - 16, cy + 6)], 2)
            for sx, sy in [(cx, cy - 8), (cx - 8, cy + 4), (cx + 8, cy + 4)]:
                pygame.draw.polygon(canvas, (245, 166, 35), [(sx, sy - 5), (sx - 3, sy + 3), (sx + 3, sy + 3)])

        elif name in ("upg_vampirism", "war_vampirism", "vampiric_edge", "drain"):
            pygame.draw.polygon(canvas, (40, 25, 45), [(cx, cy - 20), (cx + 7, cy + 4), (cx, cy + 8), (cx - 7, cy + 4)])
            pygame.draw.polygon(canvas, (230, 57, 70), [(cx, cy - 20), (cx + 7, cy + 4), (cx, cy + 8), (cx - 7, cy + 4)], 2)
            pygame.draw.circle(canvas, (245, 166, 35), (cx, cy + 14), 4)
            b_drop = [(cx, cy - 22), (cx + 4, cy - 16), (cx, cy - 12), (cx - 4, cy - 16)]
            pygame.draw.polygon(canvas, (230, 20, 40), b_drop)

        elif name in ("upg_berserk", "war_berserk", "fury"):
            pygame.draw.circle(canvas, (230, 57, 70, 80), (cx, cy), 22)
            for ang in [-0.75, 0.75]:
                ax_surf = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)
                pygame.draw.line(ax_surf, (140, 85, 45), (cx, cy - 20), (cx, cy + 20), 3)
                pygame.draw.arc(ax_surf, (220, 230, 240), (cx - 14, cy - 22, 14, 18), -math.pi * 0.5, math.pi * 0.5, 4)
                rot = pygame.transform.rotate(ax_surf, math.degrees(ang))
                canvas.blit(rot, rot.get_rect(center=(cx, cy)).topleft)

        elif name in ("upg_dash_smash", "war_dash_smash", "charge"):
            pygame.draw.line(canvas, (245, 166, 35), (cx - 18, cy + 8), (cx + 12, cy - 14), 5)
            pygame.draw.polygon(canvas, (255, 255, 255), [(cx + 16, cy - 18), (cx + 6, cy - 20), (cx + 18, cy - 8)])
            for d in [6, 12, 18]:
                pygame.draw.line(canvas, (72, 202, 228), (cx - d, cy + 14), (cx - d - 6, cy + 14), 2)

        elif name in ("upg_holy_regen", "war_holy_regen", "holy_regen", "regen"):
            pygame.draw.circle(canvas, (82, 183, 136, 70), (cx, cy), 22)
            pygame.draw.rect(canvas, (245, 166, 35), (cx - 4, cy - 16, 8, 32), border_radius=2)
            pygame.draw.rect(canvas, (245, 166, 35), (cx - 14, cy - 9, 28, 8), border_radius=2)
            pygame.draw.circle(canvas, (190, 255, 220), (cx - 12, cy - 12), 3)
            pygame.draw.circle(canvas, (190, 255, 220), (cx + 12, cy - 12), 3)

        elif name in ("upg_executioner", "war_executioner", "executioner", "crit"):
            pygame.draw.line(canvas, (180, 190, 205), (cx - 16, cy + 18), (cx + 16, cy - 14), 4)
            pygame.draw.circle(canvas, (230, 57, 70), (cx + 6, cy - 6), 7)
            pygame.draw.circle(canvas, (15, 15, 20), (cx + 4, cy - 7), 1)
            pygame.draw.circle(canvas, (15, 15, 20), (cx + 8, cy - 7), 1)

        # --- RANGER UPGRADES ---
        elif name in ("upg_arrow_dmg", "rng_arrow_dmg"):
            pygame.draw.line(canvas, (150, 105, 60), (cx - 16, cy + 16), (cx + 14, cy - 14), 3)
            head = [(cx + 18, cy - 18), (cx + 6, cy - 12), (cx + 12, cy - 6)]
            pygame.draw.polygon(canvas, (82, 183, 136), head)
            pygame.draw.polygon(canvas, (255, 255, 255), head, 1)

        elif name in ("upg_arrow_speed", "rng_arrow_speed", "ballistics"):
            pygame.draw.line(canvas, (255, 255, 255), (cx - 18, cy), (cx + 18, cy), 3)
            pygame.draw.polygon(canvas, (72, 202, 228), [(cx + 22, cy), (cx + 14, cy - 5), (cx + 14, cy + 5)])
            for off in [-12, -4, 4]:
                pygame.draw.arc(canvas, (72, 202, 228), (cx + off - 6, cy - 8, 12, 16), -math.pi * 0.5, math.pi * 0.5, 2)

        elif name in ("upg_piercing", "rng_piercing", "pierce"):
            pygame.draw.line(canvas, (220, 230, 245), (cx - 20, cy), (cx + 20, cy), 3)
            pygame.draw.polygon(canvas, (245, 166, 35), [(cx + 22, cy), (cx + 14, cy - 5), (cx + 14, cy + 5)])
            pygame.draw.line(canvas, (230, 57, 70), (cx, cy - 14), (cx, cy + 14), 4)

        elif name in ("upg_multishot", "rng_multishot"):
            for ang in [-0.35, 0.0, 0.35]:
                tx = cx + int(math.cos(ang) * 22)
                ty = cy + int(math.sin(ang) * 22)
                pygame.draw.line(canvas, (82, 183, 136), (cx - 6, cy), (tx, ty), 2)
                pygame.draw.circle(canvas, (255, 255, 255), (tx, ty), 2)

        elif name in ("upg_explosive", "rng_explosive"):
            pygame.draw.line(canvas, (180, 120, 70), (cx - 14, cy + 14), (cx + 8, cy - 8), 3)
            pygame.draw.circle(canvas, (230, 57, 70), (cx + 12, cy - 12), 8)
            pygame.draw.circle(canvas, (255, 220, 50), (cx + 12, cy - 12), 4)
            pygame.draw.circle(canvas, (255, 255, 255), (cx + 12, cy - 12), 2)

        elif name in ("upg_eagle_eye", "rng_eagle_eye", "aim"):
            pygame.draw.circle(canvas, (82, 183, 136), (cx, cy), 18, 2)
            pygame.draw.line(canvas, (82, 183, 136), (cx - 22, cy), (cx + 22, cy), 1)
            pygame.draw.line(canvas, (82, 183, 136), (cx, cy - 22), (cx, cy + 22), 1)
            pygame.draw.circle(canvas, (230, 57, 70), (cx, cy), 4)

        elif name in ("upg_acrobat", "rng_acrobat", "roll"):
            pygame.draw.arc(canvas, (82, 183, 136), (cx - 16, cy - 16, 32, 32), 0.2, math.pi * 1.8, 3)
            pygame.draw.polygon(canvas, (255, 255, 255), [(cx + 16, cy), (cx + 8, cy - 6), (cx + 8, cy + 6)])

        elif name in ("upg_poison", "rng_poison", "venom"):
            pygame.draw.polygon(canvas, (82, 183, 136), [(cx - 8, cy - 14), (cx + 8, cy - 14), (cx + 12, cy + 12), (cx - 12, cy + 12)])
            pygame.draw.polygon(canvas, (45, 106, 79), [(cx - 8, cy - 14), (cx + 8, cy - 14), (cx + 12, cy + 12), (cx - 12, cy + 12)], 1)
            pygame.draw.circle(canvas, (190, 255, 210), (cx - 3, cy + 2), 3)
            pygame.draw.circle(canvas, (190, 255, 210), (cx + 4, cy - 2), 2)

        elif name in ("upg_ricochet", "rng_ricochet", "bounce"):
            pts = [(cx - 18, cy + 14), (cx - 4, cy - 8), (cx + 8, cy + 6), (cx + 20, cy - 14)]
            pygame.draw.lines(canvas, (245, 166, 35), False, pts, 3)
            for px, py in pts:
                pygame.draw.circle(canvas, (255, 255, 255), (px, py), 3)

        elif name in ("upg_hunter", "rng_hunter", "wolf"):
            pygame.draw.circle(canvas, (82, 183, 136, 60), (cx, cy), 22)
            pts = [(cx, cy - 16), (cx - 12, cy - 6), (cx - 6, cy + 12), (cx, cy + 6), (cx + 6, cy + 12), (cx + 12, cy - 6)]
            pygame.draw.polygon(canvas, (82, 183, 136), pts)
            pygame.draw.circle(canvas, (255, 240, 100), (cx - 4, cy - 4), 2)
            pygame.draw.circle(canvas, (255, 240, 100), (cx + 4, cy - 4), 2)

        # --- MAGE UPGRADES ---
        elif name in ("upg_arcane", "mage_arcane_focus"):
            pygame.draw.circle(canvas, (160, 110, 240, 80), (cx, cy), 22)
            pygame.draw.circle(canvas, (180, 130, 255), (cx, cy), 12)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 5)
            for ang in [0, 1.2, 2.4, 3.6, 4.8]:
                sx = cx + int(math.cos(ang) * 19)
                sy = cy + int(math.sin(ang) * 19)
                pygame.draw.circle(canvas, (220, 180, 255), (sx, sy), 2)

        elif name in ("upg_fireball", "mage_fireball_mastery"):
            pygame.draw.circle(canvas, (230, 57, 70), (cx, cy), 14)
            pygame.draw.circle(canvas, (255, 166, 35), (cx - 2, cy - 2), 9)
            pygame.draw.circle(canvas, (255, 255, 220), (cx - 3, cy - 3), 4)

        elif name in ("upg_frost", "mage_frost_nova"):
            pygame.draw.circle(canvas, (72, 202, 228, 60), (cx, cy), 22)
            for a_deg in [0, 60, 120, 180, 240, 300]:
                rad = math.radians(a_deg)
                tx = cx + int(math.cos(rad) * 18)
                ty = cy + int(math.sin(rad) * 18)
                pygame.draw.line(canvas, (220, 245, 255), (cx, cy), (tx, ty), 2)
                pygame.draw.circle(canvas, (72, 202, 228), (tx, ty), 2)

        elif name in ("upg_blink", "mage_blink_blast", "blink"):
            pygame.draw.ellipse(canvas, (160, 110, 240), (cx - 16, cy - 10, 32, 20), 2)
            pygame.draw.ellipse(canvas, (245, 240, 255), (cx - 8, cy - 5, 16, 10))

        elif name in ("upg_mana_shield", "mage_mana_shield"):
            pts = [(cx, cy - 18), (cx + 16, cy - 8), (cx + 16, cy + 10), (cx, cy + 20), (cx - 16, cy + 10), (cx - 16, cy - 8)]
            pygame.draw.polygon(canvas, (160, 110, 240, 100), pts)
            pygame.draw.polygon(canvas, (72, 202, 228), pts, 2)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 4)

        elif name in ("upg_barrage", "mage_arcane_barrage"):
            for offx, offy in [(-8, -8), (8, -4), (0, 8)]:
                pygame.draw.circle(canvas, (160, 110, 240), (cx + offx, cy + offy), 6)
                pygame.draw.circle(canvas, (255, 255, 255), (cx + offx, cy + offy), 2)

        elif name in ("upg_spell_haste", "mage_spell_haste"):
            pygame.draw.arc(canvas, (160, 110, 240), (cx - 18, cy - 18, 36, 36), 0, math.pi * 1.5, 3)
            pygame.draw.polygon(canvas, (255, 255, 255), [(cx + 18, cy), (cx + 12, cy - 6), (cx + 12, cy + 6)])

        elif name in ("upg_lightning", "mage_chain_lightning"):
            pts = [(cx + 8, cy - 20), (cx - 6, cy - 4), (cx + 4, cy - 1), (cx - 8, cy + 18)]
            pygame.draw.lines(canvas, (72, 202, 228), False, pts, 3)
            pygame.draw.lines(canvas, (255, 255, 255), False, pts, 1)

        elif name in ("upg_supernova", "mage_supernova"):
            pygame.draw.circle(canvas, (160, 110, 240, 90), (cx, cy), 24)
            pygame.draw.circle(canvas, (255, 220, 100), (cx, cy), 10)
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 5)
            for ox, oy in [(-16, 0), (16, 0), (0, -16), (0, 16)]:
                pygame.draw.line(canvas, (255, 255, 255), (cx, cy), (cx + ox, cy + oy), 2)

        elif name in ("upg_siphon", "mage_soul_siphon"):
            pygame.draw.arc(canvas, (160, 110, 240), (cx - 16, cy - 16, 32, 32), 0, math.pi * 1.6, 3)
            pygame.draw.circle(canvas, (230, 57, 70), (cx, cy), 6)

        # --- SUMMONER UPGRADES ---
        elif name in ("upg_minion_dmg", "sum_minion_dmg", "claws"):
            pygame.draw.line(canvas, (200, 215, 210), (cx - 10, cy + 14), (cx - 12, cy - 12), 3)
            pygame.draw.line(canvas, (200, 215, 210), (cx, cy + 14), (cx, cy - 16), 3)
            pygame.draw.line(canvas, (200, 215, 210), (cx + 10, cy + 14), (cx + 12, cy - 12), 3)
            for ox, oy in [(-12, -12), (0, -16), (12, -12)]:
                pygame.draw.circle(canvas, (72, 202, 228), (cx + ox, cy + oy), 3)

        elif name in ("upg_army", "sum_minion_army"):
            for ox in [-12, 0, 12]:
                pygame.draw.circle(canvas, (220, 230, 225), (cx + ox, cy - 2), 6)
                pygame.draw.circle(canvas, (15, 20, 25), (cx + ox - 2, cy - 2), 1)
                pygame.draw.circle(canvas, (15, 20, 25), (cx + ox + 2, cy - 2), 1)
                pygame.draw.line(canvas, (200, 210, 205), (cx + ox, cy + 4), (cx + ox, cy + 14), 2)

        elif name in ("upg_minion_armor", "sum_minion_hp"):
            pygame.draw.circle(canvas, (220, 230, 225), (cx, cy - 4), 8)
            pygame.draw.rect(canvas, (55, 65, 80), (cx - 12, cy + 2, 24, 14), border_radius=3)
            pygame.draw.rect(canvas, (72, 202, 228), (cx - 12, cy + 2, 24, 14), width=1, border_radius=3)

        elif name in ("upg_minion_speed", "sum_minion_speed"):
            pygame.draw.circle(canvas, (72, 202, 228, 70), (cx, cy), 20)
            pygame.draw.circle(canvas, (220, 230, 225), (cx, cy - 6), 7)
            pygame.draw.line(canvas, (200, 210, 205), (cx, cy + 1), (cx - 8, cy + 14), 2)
            pygame.draw.line(canvas, (200, 210, 205), (cx, cy + 1), (cx + 8, cy + 14), 2)

        elif name in ("upg_soul_burst", "sum_soul_burst"):
            for ang in [-0.5, 0.0, 0.5]:
                tx = cx + int(math.cos(ang) * 16)
                ty = cy + int(math.sin(ang) * 16)
                pygame.draw.circle(canvas, (72, 202, 228), (tx, ty), 5)
                pygame.draw.circle(canvas, (255, 255, 255), (tx, ty), 2)

        elif name in ("upg_whip", "sum_spirit_whip"):
            pts = [(cx - 16, cy + 14), (cx - 6, cy + 2), (cx + 8, cy + 8), (cx + 18, cy - 14)]
            pygame.draw.lines(canvas, (72, 202, 228), False, pts, 3)
            pygame.draw.lines(canvas, (255, 255, 255), False, pts, 1)

        elif name in ("upg_corpse_exp", "sum_corpse_explosion"):
            pygame.draw.circle(canvas, (82, 183, 136, 90), (cx, cy), 22)
            pygame.draw.circle(canvas, (230, 57, 70), (cx, cy), 8)
            for a_deg in [0, 72, 144, 216, 288]:
                rad = math.radians(a_deg)
                tx = cx + int(math.cos(rad) * 18)
                ty = cy + int(math.sin(rad) * 18)
                pygame.draw.line(canvas, (255, 240, 100), (cx, cy), (tx, ty), 2)

        elif name in ("upg_harvest", "sum_soul_harvest"):
            pygame.draw.arc(canvas, (200, 215, 225), (cx - 18, cy - 18, 36, 36), 0.2, math.pi * 0.9, 4)
            pygame.draw.line(canvas, (140, 90, 50), (cx - 14, cy + 18), (cx + 14, cy - 10), 3)
            pygame.draw.circle(canvas, (72, 202, 228), (cx + 10, cy + 10), 4)

        elif name in ("upg_spectral_shield", "sum_spectral_shield"):
            pygame.draw.circle(canvas, (55, 65, 80), (cx, cy), 14)
            pygame.draw.circle(canvas, (72, 202, 228), (cx, cy), 14, 2)
            for ang in [0, 1.57, 3.14, 4.71]:
                tx = cx + int(math.cos(ang) * 22)
                ty = cy + int(math.sin(ang) * 22)
                pygame.draw.circle(canvas, (72, 202, 228), (tx, ty), 3)

        elif name in ("upg_vamp_bond", "sum_vampiric_bond"):
            pygame.draw.circle(canvas, (230, 57, 70), (cx - 7, cy), 6)
            pygame.draw.circle(canvas, (72, 202, 228), (cx + 7, cy), 6)
            pygame.draw.line(canvas, (255, 255, 255), (cx - 7, cy), (cx + 7, cy), 2)

        else:
            # Default fallback: mystical glowing rune talisman
            pygame.draw.circle(canvas, (35, 45, 65), (cx, cy), 22)
            pygame.draw.circle(canvas, (245, 166, 35), (cx, cy), 22, 2)
            pygame.draw.polygon(canvas, (72, 202, 228), [(cx, cy - 12), (cx + 10, cy), (cx, cy + 12), (cx - 10, cy)])
            pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 3)

        # Scale down smoothly to requested size
        if size != canvas_size:
            scaled = pygame.transform.smoothscale(canvas, (size, size))
            return scaled
        return canvas
