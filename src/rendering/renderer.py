"""
Комплексный рендерер в 8-битной стилистике с поддержкой всех 4 классов персонажей:
- Воин (Рыцарь)
- Лучник (Стрелок)
- Маг (Архимаг)
- Призыватель (Некромант) и его миньоны-скелеты.
"""

import math
from typing import List, Tuple, Optional
import pygame
from ..config import settings
from ..entities.player import BasePlayer
from ..entities.zombie import Zombie
from ..entities.orb import ExperienceOrb
from .effects import Particle, DamageNumber, BloodDecal


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.vignette_surface = None
        self._init_vignette()

    def _init_vignette(self) -> None:
        w, h = self.screen.get_size()
        self.vignette_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        center_x, center_y = w // 2, h // 2
        max_dist = math.hypot(center_x, center_y)
        steps = 18
        for i in range(steps):
            factor = i / float(steps)
            dist = max_dist * (0.45 + 0.55 * factor)
            alpha = int(220 * (factor ** 2.2))
            ring_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(ring_surf, (2, 3, 6, alpha), (0, 0, w, h))
            pygame.draw.circle(ring_surf, (0, 0, 0, 0), (center_x, center_y), int(dist))
            self.vignette_surface.blit(ring_surf, (0, 0))

    def on_resize(self, new_screen: Optional[pygame.Surface] = None) -> None:
        if new_screen is not None:
            self.screen = new_screen
        else:
            surf = pygame.display.get_surface()
            if surf is not None:
                self.screen = surf
        self._init_vignette()

    def render_world(
        self,
        camera,
        player: BasePlayer,
        zombies: List[Zombie],
        projectiles: list,
        orbs: List[ExperienceOrb],
        particles: List[Particle],
        damage_numbers: List[DamageNumber],
        blood_decals: List[BloodDecal],
        mouse_pos: Tuple[int, int]
    ) -> None:
        self.screen.fill(settings.COLOR_BG)

        # 1. Arena Tiles
        self._draw_arena(camera)

        # 2. Blood Decals
        for decal in blood_decals:
            decal.draw(self.screen, camera)

        # 3. Experience Orbs
        for orb in orbs:
            orb.draw(self.screen, camera)

        # 4. Summoner Minions
        if player and hasattr(player, "minions"):
            for m in player.minions:
                m.draw(self.screen, camera)

        # 5. Zombies
        for z in zombies:
            self._draw_zombie(z, camera)

        # 6. Player
        if player:
            self._draw_player(player, camera)

        # 7. Projectiles
        for proj in projectiles:
            proj.draw(self.screen, camera)

        # 8. Particles
        for part in particles:
            part.draw(self.screen, camera)

        # 9. Damage Numbers
        for dn in damage_numbers:
            dn.draw(self.screen, camera)

        # 10. Vignette Atmospheric Overlay
        if self.vignette_surface:
            self.screen.blit(self.vignette_surface, (0, 0))

        # 11. Crosshair
        self._draw_crosshair(mouse_pos)

    def _draw_arena(self, camera) -> None:
        tile_size = settings.TILE_SIZE
        w, h = self.screen.get_size()

        start_col = max(0, int(camera.x // tile_size))
        end_col = min(settings.FIELD_SIZE[0], int((camera.x + w) // tile_size) + 1)
        start_row = max(0, int(camera.y // tile_size))
        end_row = min(settings.FIELD_SIZE[1], int((camera.y + h) // tile_size) + 1)

        for c in range(start_col, end_col):
            for r in range(start_row, end_row):
                sx = int(c * tile_size - camera.x)
                sy = int(r * tile_size - camera.y)
                is_border = (c <= 1 or c >= settings.FIELD_SIZE[0] - 2 or r <= 1 or r >= settings.FIELD_SIZE[1] - 2)

                if is_border:
                    pygame.draw.rect(self.screen, settings.COLOR_BORDER, (sx, sy, tile_size, tile_size))
                    pygame.draw.rect(self.screen, (16, 20, 26), (sx, sy, tile_size, tile_size), 1)
                else:
                    color = settings.COLOR_TILE_A if (c + r) % 2 == 0 else settings.COLOR_TILE_B
                    pygame.draw.rect(self.screen, color, (sx, sy, tile_size, tile_size))
                    pygame.draw.rect(self.screen, (17, 21, 28), (sx, sy, tile_size, tile_size), 1)

    def _draw_player(self, player: BasePlayer, camera) -> None:
        sx = int(player.x - camera.x)
        sy = int(player.y - camera.y)

        # 1. Dash Afterimages
        for g in player.ghost_trail:
            gx = int(g.x - camera.x)
            gy = int(g.y - camera.y)
            alpha = max(0, min(255, int((g.life / g.max_life) * 125)))
            ghost_surf = pygame.Surface((int(player.radius * 2 + 12), int(player.radius * 2 + 12)), pygame.SRCALPHA)
            pygame.draw.circle(ghost_surf, (*g.color, alpha), (ghost_surf.get_width() // 2, ghost_surf.get_height() // 2), int(player.radius))
            self.screen.blit(ghost_surf, (gx - ghost_surf.get_width() // 2, gy - ghost_surf.get_height() // 2))

        # 2. Invulnerability blink
        if player.invulnerable_timer > 0 and int(player.invulnerable_timer * 20) % 2 == 0:
            return

        # 3. Ground Shadow
        shadow_surf = pygame.Surface((44, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 110), (0, 0, 44, 22))
        self.screen.blit(shadow_surf, (sx - 22, sy + 6))

        # 4. Render rotating class body on isolated surface
        size = 96
        body_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        leg_offset = int(math.sin(player.walk_cycle) * 5)
        cape_sway = int(math.cos(player.walk_cycle) * 4)

        if player.class_type == "ranger":
            # --- RANGER (Detailed Hunter Hood, Studded Leather Armor, Quiver, Recurve Bow) ---
            # Billowing green cloak mantle behind shoulders
            cloak_pts = [
                (cx - 16, cy - 14),
                (cx - 28 + cape_sway, cy - 18),
                (cx - 24 + cape_sway, cy),
                (cx - 28 + cape_sway, cy + 18),
                (cx - 16, cy + 14),
            ]
            pygame.draw.polygon(body_surf, (30, 70, 50), cloak_pts)
            pygame.draw.polygon(body_surf, (45, 106, 79), cloak_pts, 1)

            # Boots with leather straps
            pygame.draw.rect(body_surf, (50, 35, 25), (cx - 12, cy - 14 + leg_offset, 8, 8), border_radius=2)
            pygame.draw.rect(body_surf, (50, 35, 25), (cx - 12, cy + 6 - leg_offset, 8, 8), border_radius=2)
            pygame.draw.line(body_surf, (140, 95, 60), (cx - 12, cy - 10 + leg_offset), (cx - 4, cy - 10 + leg_offset), 1)
            pygame.draw.line(body_surf, (140, 95, 60), (cx - 12, cy + 10 - leg_offset), (cx - 4, cy + 10 - leg_offset), 1)

            # Quiver on back packed with individual arrows
            quiver_pts = [(cx - 18, cy - 14), (cx - 8, cy - 18), (cx - 4, cy + 14), (cx - 14, cy + 18)]
            pygame.draw.polygon(body_surf, (110, 65, 30), quiver_pts)
            pygame.draw.polygon(body_surf, (160, 110, 60), quiver_pts, 1)
            pygame.draw.line(body_surf, (245, 166, 35), (cx - 16, cy - 2), (cx - 6, cy - 6), 2)
            # Arrow shafts and colored fletching
            for a_i, (f_col, ox, oy) in enumerate([
                ((255, 255, 255), -14, -22),
                ((82, 183, 136), -10, -25),
                ((245, 166, 35), -6, -23),
            ]):
                pygame.draw.line(body_surf, (150, 105, 60), (cx + ox, cy + oy + 8), (cx + ox, cy + oy), 2)
                pygame.draw.polygon(body_surf, f_col, [(cx + ox - 2, cy + oy + 3), (cx + ox, cy + oy), (cx + ox + 2, cy + oy + 3)])

            # Studded Leather Tunic with Cross-belt
            pygame.draw.rect(body_surf, (60, 42, 30), (cx - 14, cy - 14, 28, 28), border_radius=5)
            pygame.draw.rect(body_surf, (40, 100, 70), (cx - 12, cy - 12, 24, 24), border_radius=4)
            # Cross-straps and brass rivets
            pygame.draw.line(body_surf, (120, 80, 40), (cx - 12, cy - 12), (cx + 12, cy + 12), 3)
            pygame.draw.line(body_surf, (120, 80, 40), (cx - 12, cy + 12), (cx + 12, cy - 12), 2)
            pygame.draw.circle(body_surf, (245, 166, 35), (cx, cy), 3)  # Central Brass Buckle

            # Hunter Hood with Shaded Face & Glowing Amber/Emerald Eyes
            pygame.draw.circle(body_surf, (45, 106, 79), (cx + 1, cy), 11)
            pygame.draw.polygon(body_surf, (30, 75, 55), [(cx - 13, cy - 7), (cx - 2, cy), (cx - 13, cy + 7)])
            # Shadow under hood
            pygame.draw.ellipse(body_surf, (15, 20, 25), (cx + 2, cy - 6, 7, 12))
            # Glowing Hunter Eyes
            pygame.draw.circle(body_surf, (80, 245, 180), (cx + 5, cy - 3), 1)
            pygame.draw.circle(body_surf, (80, 245, 180), (cx + 5, cy + 3), 1)

            # Recurve Composite Bow in hands
            bow_cx = cx + 18
            pygame.draw.arc(body_surf, (180, 115, 45), (bow_cx - 8, cy - 22, 16, 44), -math.pi / 2, math.pi / 2, 3)
            pygame.draw.arc(body_surf, (120, 70, 25), (bow_cx - 9, cy - 22, 16, 44), -math.pi / 2, math.pi / 2, 1)
            # Gold reinforced bow tips
            pygame.draw.circle(body_surf, (245, 166, 35), (bow_cx, cy - 21), 2)
            pygame.draw.circle(body_surf, (245, 166, 35), (bow_cx, cy + 21), 2)
            # Taut Bowstring & Nocked Arrow
            pygame.draw.line(body_surf, (230, 235, 240), (bow_cx, cy - 21), (bow_cx - 6, cy), 1)
            pygame.draw.line(body_surf, (230, 235, 240), (bow_cx - 6, cy), (bow_cx, cy + 21), 1)
            pygame.draw.line(body_surf, (160, 115, 65), (bow_cx - 6, cy), (bow_cx + 14, cy), 2)
            pygame.draw.polygon(body_surf, (240, 245, 250), [(bow_cx + 12, cy - 3), (bow_cx + 17, cy), (bow_cx + 12, cy + 3)])

        elif player.class_type == "mage":
            # --- MAGE (Royal Violet/Indigo Robes, Gold Runes, Wizard Hat, Arcane Crystal Staff) ---
            # Flowing Robe Tail behind with gold trim
            robe_pts = [
                (cx - 15, cy - 14),
                (cx - 26 + cape_sway, cy - 16),
                (cx - 23 + cape_sway, cy),
                (cx - 26 + cape_sway, cy + 16),
                (cx - 15, cy + 14),
            ]
            pygame.draw.polygon(body_surf, (55, 25, 90), robe_pts)
            pygame.draw.polygon(body_surf, (245, 166, 35), robe_pts, 1)

            # Robe Body
            pygame.draw.rect(body_surf, (80, 40, 130), (cx - 14, cy - 14, 28, 28), border_radius=7)
            pygame.draw.rect(body_surf, (100, 50, 160), (cx - 12, cy - 12, 24, 24), border_radius=5)
            # Gold embroidered celestial star & runes
            pygame.draw.circle(body_surf, (245, 166, 35), (cx - 3, cy), 5, 1)
            pygame.draw.line(body_surf, (245, 166, 35), (cx - 3, cy - 7), (cx - 3, cy + 7), 1)
            pygame.draw.line(body_surf, (245, 166, 35), (cx - 10, cy), (cx + 4, cy), 1)

            # High Robe Collar & Mana Amulet
            pygame.draw.circle(body_surf, (0, 245, 212), (cx + 1, cy), 3)
            pygame.draw.circle(body_surf, (255, 255, 255), (cx + 1, cy), 1)

            # Wide-Brim Wizard Hat
            pygame.draw.ellipse(body_surf, (60, 25, 100), (cx - 14, cy - 12, 28, 24))
            pygame.draw.ellipse(body_surf, (245, 166, 35), (cx - 14, cy - 12, 28, 24), 1)
            # Tall Conical Crown curving backward
            hat_pts = [(cx - 8, cy - 8), (cx - 20, cy), (cx - 8, cy + 8), (cx + 4, cy)]
            pygame.draw.polygon(body_surf, (95, 45, 150), hat_pts)
            pygame.draw.polygon(body_surf, (245, 166, 35), hat_pts, 1)
            # Hat star buckle
            pygame.draw.circle(canvas_star := pygame.Surface((8, 8), pygame.SRCALPHA), (255, 220, 50), (4, 4), 3)
            body_surf.blit(canvas_star, (cx - 12, cy - 4))
            # Glowing Astral Eyes
            pygame.draw.circle(body_surf, (160, 110, 255), (cx + 5, cy - 3), 1)
            pygame.draw.circle(body_surf, (160, 110, 255), (cx + 5, cy + 3), 1)

            # Arcane Staff in hands
            staff_x, staff_y = cx + 16, cy + 12
            pygame.draw.line(body_surf, (110, 70, 40), (staff_x - 12, staff_y + 12), (staff_x + 16, staff_y - 16), 4)
            pygame.draw.line(body_surf, (160, 110, 65), (staff_x - 11, staff_y + 12), (staff_x + 16, staff_y - 16), 1)
            # Staff Gold Prongs
            pygame.draw.arc(body_surf, (245, 166, 35), (staff_x + 10, staff_y - 22, 14, 14), 0, math.pi * 1.5, 2)
            # Floating Rotating Mana Crystal Prism
            cryst_pts = [(staff_x + 17, staff_y - 23), (staff_x + 22, staff_y - 15), (staff_x + 17, staff_y - 7), (staff_x + 12, staff_y - 15)]
            pygame.draw.polygon(body_surf, (0, 245, 212), cryst_pts)
            pygame.draw.polygon(body_surf, (255, 255, 255), cryst_pts, 1)
            pygame.draw.circle(body_surf, (255, 255, 255), (staff_x + 17, staff_y - 15), 2)

            # Offhand Floating Mana Rune Spark
            pygame.draw.circle(body_surf, (160, 110, 240, 160), (cx + 10, cy - 12), 5)
            pygame.draw.circle(body_surf, (255, 255, 255), (cx + 10, cy - 12), 2)

        elif player.class_type == "summoner":
            # --- SUMMONER (Dark Warlock Cowl, Spiked Bone Pauldrons, Horned Skull Scepter) ---
            # Ragged Soul Cloak with cyan ethereal lining
            shred_pts = [
                (cx - 15, cy - 14),
                (cx - 26 + cape_sway, cy - 16),
                (cx - 22 + cape_sway, cy - 6),
                (cx - 27 + cape_sway, cy + 6),
                (cx - 23 + cape_sway, cy + 16),
                (cx - 15, cy + 14),
            ]
            pygame.draw.polygon(body_surf, (18, 22, 28), shred_pts)
            pygame.draw.polygon(body_surf, (72, 202, 228), shred_pts, 1)

            # Dark Robes
            pygame.draw.rect(body_surf, (25, 30, 36), (cx - 14, cy - 14, 28, 28), border_radius=6)
            pygame.draw.rect(body_surf, (35, 42, 50), (cx - 12, cy - 12, 24, 24), border_radius=5)
            # Bone amulet / Necrotic runes on chest
            pygame.draw.circle(body_surf, (72, 202, 228), (cx - 2, cy), 3)

            # Spiked Bone Pauldrons (Shoulders)
            pygame.draw.polygon(body_surf, (220, 230, 225), [(cx - 8, cy - 16), (cx + 4, cy - 16), (cx, cy - 22)])
            pygame.draw.polygon(body_surf, (220, 230, 225), [(cx - 8, cy + 16), (cx + 4, cy + 16), (cx, cy + 22)])

            # Dark Cowl Hood & Pale Bone Mask
            pygame.draw.circle(body_surf, (15, 18, 24), (cx, cy), 11)
            pygame.draw.polygon(body_surf, (10, 12, 16), [(cx - 13, cy - 7), (cx - 3, cy), (cx - 13, cy + 7)])
            # Pale Skull Faceplate
            pygame.draw.ellipse(body_surf, (215, 225, 220), (cx + 1, cy - 6, 8, 12))
            # Glowing Green Spectral Pupils
            pygame.draw.circle(body_surf, (15, 20, 25), (cx + 4, cy - 3), 2)
            pygame.draw.circle(body_surf, (15, 20, 25), (cx + 4, cy + 3), 2)
            pygame.draw.circle(body_surf, (80, 245, 180), (cx + 4, cy - 3), 1)
            pygame.draw.circle(body_surf, (80, 245, 180), (cx + 4, cy + 3), 1)

            # Scepter of the Damned (Bone handle + Horned Demon Skull Head)
            scep_x, scep_y = cx + 16, cy + 12
            pygame.draw.line(body_surf, (180, 190, 185), (scep_x - 12, scep_y + 12), (scep_x + 14, scep_y - 14), 4)
            # Horned Skull Head
            pygame.draw.circle(body_surf, (230, 240, 235), (scep_x + 14, scep_y - 14), 7)
            pygame.draw.polygon(body_surf, (80, 245, 180), [(scep_x + 12, scep_y - 20), (scep_x + 17, scep_y - 14), (scep_x + 10, scep_y - 13)])
            # Burning soul fire in skull
            pygame.draw.circle(body_surf, (80, 245, 180), (scep_x + 14, scep_y - 14), 4)
            pygame.draw.circle(body_surf, (255, 255, 255), (scep_x + 14, scep_y - 14), 1)

        else:
            # --- WARRIOR / KNIGHT (Default) ---
            # Billowing Royal Crimson Cape with Gold Trim
            cape_pts = [
                (cx - 16, cy - 14),
                (cx - 28 + cape_sway, cy - 18),
                (cx - 25 + cape_sway, cy),
                (cx - 28 + cape_sway, cy + 18),
                (cx - 16, cy + 14),
            ]
            pygame.draw.polygon(body_surf, (160, 20, 30), cape_pts)
            pygame.draw.polygon(body_surf, (230, 57, 70), [(cx - 16, cy - 12), (cx - 26 + cape_sway, cy - 16), (cx - 23 + cape_sway, cy), (cx - 26 + cape_sway, cy + 16), (cx - 16, cy + 12)])
            pygame.draw.polygon(body_surf, (245, 166, 35), cape_pts, 1)

            # Polished Steel Greaves & Boots
            pygame.draw.rect(body_surf, (73, 80, 87), (cx - 12, cy - 14 + leg_offset, 8, 8), border_radius=2)
            pygame.draw.rect(body_surf, (73, 80, 87), (cx - 12, cy + 6 - leg_offset, 8, 8), border_radius=2)
            pygame.draw.line(body_surf, (206, 212, 218), (cx - 12, cy - 14 + leg_offset), (cx - 4, cy - 14 + leg_offset), 2)
            pygame.draw.line(body_surf, (206, 212, 218), (cx - 12, cy + 6 - leg_offset), (cx - 4, cy + 6 - leg_offset), 2)

            # Steel Cuirass (Breastplate) with rivets and heraldic tabard
            pygame.draw.rect(body_surf, (173, 181, 189), (cx - 15, cy - 15, 30, 30), border_radius=6)
            pygame.draw.rect(body_surf, (73, 80, 87), (cx - 15, cy - 15, 30, 30), width=2, border_radius=6)
            # Specular light gleam on cuirass
            pygame.draw.line(body_surf, (240, 245, 250), (cx - 13, cy - 13), (cx + 13, cy - 13), 2)

            # Heraldic Crimson Tabard Cross
            pygame.draw.rect(body_surf, (230, 57, 70), (cx - 3, cy - 12, 6, 24))
            pygame.draw.rect(body_surf, (230, 57, 70), (cx - 10, cy - 5, 20, 6))
            pygame.draw.circle(body_surf, (245, 166, 35), (cx, cy - 2), 3)  # Golden Boss

            # Steel Pauldrons (Shoulder Plates)
            pygame.draw.ellipse(body_surf, (206, 212, 218), (cx - 10, cy - 22, 16, 10))
            pygame.draw.ellipse(body_surf, (73, 80, 87), (cx - 10, cy - 22, 16, 10), 1)
            pygame.draw.ellipse(body_surf, (206, 212, 218), (cx - 10, cy + 12, 16, 10))
            pygame.draw.ellipse(body_surf, (73, 80, 87), (cx - 10, cy + 12, 16, 10), 1)

            # Ornate Great Helm
            pygame.draw.circle(body_surf, (206, 212, 218), (cx + 1, cy), 11)
            pygame.draw.circle(body_surf, (73, 80, 87), (cx + 1, cy), 11, 2)
            # Visor Cross & Slits
            pygame.draw.line(body_surf, (245, 166, 35), (cx - 2, cy - 5), (cx + 10, cy - 5), 2)
            pygame.draw.line(body_surf, (245, 166, 35), (cx - 2, cy + 5), (cx + 10, cy + 5), 2)
            pygame.draw.line(body_surf, (245, 166, 35), (cx + 4, cy - 9), (cx + 4, cy + 9), 2)
            # Glowing Visor Slit
            pygame.draw.line(body_surf, (72, 202, 228), (cx + 4, cy - 2), (cx + 9, cy - 2), 2)
            pygame.draw.line(body_surf, (72, 202, 228), (cx + 4, cy + 2), (cx + 9, cy + 2), 2)

            # Feathery Red Plume tilting backward
            plume_pts = [(cx - 4, cy - 5), (cx - 14, cy), (cx - 4, cy + 5)]
            pygame.draw.polygon(body_surf, (230, 57, 70), plume_pts)
            pygame.draw.polygon(body_surf, (245, 166, 35), plume_pts, 1)

            # Heater Shield on left arm
            shield_pts = [(cx + 2, cy - 22), (cx + 14, cy - 22), (cx + 12, cy - 10), (cx + 4, cy - 8)]
            pygame.draw.polygon(body_surf, (43, 45, 66), shield_pts)
            pygame.draw.polygon(body_surf, (245, 166, 35), shield_pts, 2)
            pygame.draw.circle(body_surf, (230, 57, 70), (cx + 8, cy - 16), 3)

            # Broadsword in main hand with dynamic animation angle
            sword_angle = 0.2
            if player.atk1_anim_timer > 0:
                prog = 1.0 - (player.atk1_anim_timer / player.atk1_anim_duration)
                sword_angle = -1.2 + prog * 2.4
            elif player.atk2_anim_timer > 0:
                prog = 1.0 - (player.atk2_anim_timer / player.atk2_anim_duration)
                sword_angle = prog * math.pi * 2.0

            sword_surf = pygame.Surface((64, 32), pygame.SRCALPHA)
            scx, scy = 12, 16
            # Pommel & Leather hilt
            pygame.draw.circle(sword_surf, (245, 166, 35), (scx - 8, scy), 3)
            pygame.draw.rect(sword_surf, (110, 65, 30), (scx - 6, scy - 2, 8, 4))
            # Golden Crossguard
            pygame.draw.rect(sword_surf, (245, 166, 35), (scx + 2, scy - 8, 4, 16), border_radius=1)
            # Polished Steel Blade with fuller
            blade_pts = [(scx + 6, scy - 4), (scx + 38, scy - 3), (scx + 46, scy), (scx + 38, scy + 3), (scx + 6, scy + 4)]
            pygame.draw.polygon(sword_surf, (248, 249, 250), blade_pts)
            pygame.draw.polygon(sword_surf, (173, 181, 189), blade_pts, 1)
            pygame.draw.line(sword_surf, (200, 210, 220), (scx + 8, scy), (scx + 34, scy), 2)  # Fuller groove

            rot_sword = pygame.transform.rotate(sword_surf, -math.degrees(sword_angle))
            sw_rect = rot_sword.get_rect(center=(cx + 14, cy + 14))
            body_surf.blit(rot_sword, sw_rect.topleft)

        # Rotate entire body to player's facing angle
        deg = -math.degrees(player.facing_angle)
        rot_body = pygame.transform.rotate(body_surf, deg)
        body_rect = rot_body.get_rect(center=(sx, sy))
        self.screen.blit(rot_body, body_rect.topleft)

        # Active Mana Shield aura (Mage)
        if getattr(player, "mana_shield", 0.0) > 0:
            self._draw_mana_shield(player, sx, sy)

        # Active Barrier Orbs (Mage Mastery: 3 rotating celestial spheres)
        if getattr(player, "barrier_orbs_active", False) and getattr(player, "barrier_orbs", 0) > 0:
            self._draw_barrier_orbs(player, sx, sy)

        # Warrior Berserk fiery rage aura (when HP < 50% and berserk_bonus active)
        if getattr(player, "berserk_bonus", 0.0) > 0 and player.hp < (player.max_hp * 0.5):
            self._draw_berserk_aura(player, sx, sy)

        # Attack visual trails
        if player.class_type == "warrior":
            if player.atk1_anim_timer > 0:
                self._draw_swing_arc(player, sx, sy)
            elif player.atk2_anim_timer > 0:
                self._draw_spin_ring(player, sx, sy)
        elif player.class_type == "summoner" and player.atk1_anim_timer > 0:
            # Spirit whip lash arc
            self._draw_spirit_whip_arc(player, sx, sy)

    def _draw_mana_shield(self, player: BasePlayer, sx: int, sy: int) -> None:
        shield_r = int(player.radius + 14)
        shield_surf = pygame.Surface((shield_r * 2 + 10, shield_r * 2 + 10), pygame.SRCALPHA)
        scx, scy = shield_surf.get_width() // 2, shield_surf.get_height() // 2

        t = player.walk_cycle * 2.0
        pulse = 0.90 + 0.10 * math.sin(t)
        cur_r = int(shield_r * pulse)

        # Translucent bubble fill
        pygame.draw.circle(shield_surf, (0, 245, 212, 38), (scx, scy), cur_r)
        # Inner glow ring
        pygame.draw.circle(shield_surf, (72, 202, 228, 85), (scx, scy), cur_r, width=2)
        # Outer bright barrier border
        pygame.draw.circle(shield_surf, (200, 255, 255, 160), (scx, scy), cur_r, width=1)

        # Shimmering orbit runes
        for i in range(3):
            ang = t + i * (math.pi * 2 / 3)
            ox = int(math.cos(ang) * cur_r)
            oy = int(math.sin(ang) * cur_r)
            pygame.draw.circle(shield_surf, (0, 245, 212, 220), (scx + ox, scy + oy), 3)
            pygame.draw.circle(shield_surf, (255, 255, 255, 240), (scx + ox, scy + oy), 1)

        self.screen.blit(shield_surf, (sx - scx, sy - scy))

    def _draw_barrier_orbs(self, player: BasePlayer, sx: int, sy: int) -> None:
        num_orbs = getattr(player, "barrier_orbs", 3)
        base_ang = getattr(player, "barrier_orbit_angle", 0.0)
        orbit_r = 34.0

        for i in range(num_orbs):
            ang = base_ang + i * (math.pi * 2 / 3)
            ox = sx + math.cos(ang) * orbit_r
            oy = sy + math.sin(ang) * orbit_r

            # Soft glowing halo
            glow_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (0, 245, 212, 60), (14, 14), 12)
            pygame.draw.circle(glow_surf, (160, 110, 240, 80), (14, 14), 8)
            self.screen.blit(glow_surf, (int(ox - 14), int(oy - 14)))

            # Glowing sphere core & golden ring
            pygame.draw.circle(self.screen, (72, 202, 228), (int(ox), int(oy)), 6)
            pygame.draw.circle(self.screen, (220, 255, 255), (int(ox - 1), int(oy - 1)), 3)
            pygame.draw.circle(self.screen, (245, 166, 35), (int(ox), int(oy)), 7, 1)

    def _draw_berserk_aura(self, player: BasePlayer, sx: int, sy: int) -> None:
        r = int(player.radius + 10)
        aura_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
        acx, acy = aura_surf.get_width() // 2, aura_surf.get_height() // 2

        t = player.walk_cycle * 2.5
        pulse = 0.85 + 0.15 * math.sin(t)
        cur_r = int(r * pulse)

        # Crimson fiery glow
        pygame.draw.circle(aura_surf, (230, 57, 70, 45), (acx, acy), cur_r)
        pygame.draw.circle(aura_surf, (245, 166, 35, 90), (acx, acy), cur_r, width=2)
        self.screen.blit(aura_surf, (sx - acx, sy - acy))

    def _draw_swing_arc(self, player: BasePlayer, sx: int, sy: int) -> None:
        prog = 1.0 - (player.atk1_anim_timer / player.atk1_anim_duration)
        radius = int(85 * player.area_multi)
        arc_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        acx, acy = arc_surf.get_width() // 2, arc_surf.get_height() // 2

        start_a = player.facing_angle - 1.1 + prog * 0.4
        end_a = player.facing_angle + 1.1
        for thickness, color, alpha in [(8, (72, 202, 228), 90), (4, (255, 255, 255), 230)]:
            rect = pygame.Rect(acx - radius, acy - radius, radius * 2, radius * 2)
            pygame.draw.arc(arc_surf, (*color, alpha), rect, -end_a, -start_a, thickness)

        self.screen.blit(arc_surf, (sx - acx, sy - acy))

    def _draw_spin_ring(self, player: BasePlayer, sx: int, sy: int) -> None:
        radius = int(115 * player.area_multi)
        ring_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        rcx, rcy = ring_surf.get_width() // 2, ring_surf.get_height() // 2
        prog = 1.0 - (player.atk2_anim_timer / player.atk2_anim_duration)
        alpha = int(220 * (1.0 - prog))

        pygame.draw.circle(ring_surf, (245, 166, 35, alpha // 2), (rcx, rcy), radius, width=10)
        pygame.draw.circle(ring_surf, (255, 230, 100, alpha), (rcx, rcy), radius - 2, width=4)
        self.screen.blit(ring_surf, (sx - rcx, sy - rcy))

    def _draw_spirit_whip_arc(self, player: BasePlayer, sx: int, sy: int) -> None:
        radius = int(95 * player.area_multi)
        arc_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        acx, acy = arc_surf.get_width() // 2, arc_surf.get_height() // 2
        start_a = player.facing_angle - 1.0
        end_a = player.facing_angle + 1.0
        rect = pygame.Rect(acx - radius, acy - radius, radius * 2, radius * 2)
        pygame.draw.arc(arc_surf, (80, 245, 180, 200), rect, -end_a, -start_a, 5)
        self.screen.blit(arc_surf, (sx - acx, sy - acy))

    def _draw_zombie(self, z: Zombie, camera) -> None:
        if z.dead:
            return
        sx = int(z.x - camera.x)
        sy = int(z.y - camera.y)
        r = int(z.radius)

        # 1. Soft Dynamic Ground Shadow
        sh_w, sh_h = int(r * 2.3), int(r * 1.2)
        shadow_surf = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, sh_w, sh_h))
        self.screen.blit(shadow_surf, (sx - sh_w // 2, sy + int(r * 0.45)))

        # 2. Flash Hit Silhouette
        if z.flash_timer > 0:
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), r + 2)
            pygame.draw.circle(self.screen, (230, 57, 70), (sx, sy), r + 2, 2)
            return

        # 3. Canvas for directional/detailed zombie rendering
        z_size = max(50, int(r * 2.8))
        z_surf = pygame.Surface((z_size, z_size), pygame.SRCALPHA)
        zcx, zcy = z_size // 2, z_size // 2

        walk_bob = int(math.sin(z.walk_cycle) * 3)
        arm_reach = int(math.cos(z.walk_cycle) * 4)

        if z.type == "runner":
            # --- RUNNER (Flayed Crimson Muscle, Spinal Bone Spikes, Razor Claws, Demonic Eyes) ---
            # Hunched feral body
            pygame.draw.ellipse(z_surf, (193, 18, 31), (zcx - 10, zcy - 12 + walk_bob, 20, 24))
            pygame.draw.ellipse(z_surf, (140, 10, 20), (zcx - 8, zcy - 10 + walk_bob, 16, 20))
            # Exposed muscle fibers
            for my in [-4, 0, 4]:
                pygame.draw.line(z_surf, (230, 57, 70), (zcx - 6, zcy + my + walk_bob), (zcx + 6, zcy + my + walk_bob), 1)

            # Spinal Bone Spikes along back
            for sy_off in [-10, -5, 0, 5]:
                pygame.draw.polygon(z_surf, (240, 245, 240), [(zcx - 8, zcy + sy_off + walk_bob), (zcx - 15, zcy + sy_off + walk_bob - 2), (zcx - 8, zcy + sy_off + walk_bob + 2)])

            # Feral Snarling Head
            pygame.draw.circle(z_surf, (193, 18, 31), (zcx + 5, zcy - 2 + walk_bob), 8)
            # Burning Red Demonic Eyes
            pygame.draw.circle(z_surf, (255, 220, 50), (zcx + 8, zcy - 4 + walk_bob), 2)
            pygame.draw.circle(z_surf, (255, 220, 50), (zcx + 8, zcy + 1 + walk_bob), 2)
            pygame.draw.circle(z_surf, (255, 255, 255), (zcx + 8, zcy - 4 + walk_bob), 1)
            # Needle fangs & dripping blood
            pygame.draw.polygon(z_surf, (240, 245, 250), [(zcx + 11, zcy - 1 + walk_bob), (zcx + 14, zcy + walk_bob), (zcx + 11, zcy + 2 + walk_bob)])

            # Predatory Razor Claws reaching out
            pygame.draw.line(z_surf, (160, 15, 25), (zcx + 4, zcy - 8), (zcx + 14 + arm_reach, zcy - 11), 3)
            pygame.draw.line(z_surf, (160, 15, 25), (zcx + 4, zcy + 8), (zcx + 14 - arm_reach, zcy + 11), 3)
            for claw_y in [-11, 11]:
                pygame.draw.circle(z_surf, (240, 245, 250), (zcx + 15, zcy + claw_y), 2)

        elif z.type == "spitter":
            # --- SPITTER (Distended Glowing Acid Belly, Toxic Pustules, Tri-mandible Jaw) ---
            # Mutated hunched body
            pygame.draw.circle(z_surf, (70, 140, 30), (zcx - 2, zcy + walk_bob), 12)
            # Distended Translucent Acid Sac (Glowing Lime)
            acid_surf = pygame.Surface((18, 18), pygame.SRCALPHA)
            pygame.draw.circle(acid_surf, (112, 224, 0, 190), (9, 9), 8)
            pygame.draw.circle(acid_surf, (180, 255, 50), (9, 9), 5)
            z_surf.blit(acid_surf, (zcx - 9, zcy - 9 + walk_bob))

            # Pulsing Acid Pustules on Shoulders
            pygame.draw.circle(z_surf, (112, 224, 0), (zcx - 6, zcy - 9 + walk_bob), 3)
            pygame.draw.circle(z_surf, (112, 224, 0), (zcx - 6, zcy + 9 + walk_bob), 3)

            # Head with Tri-Mandible Jaws
            pygame.draw.circle(z_surf, (80, 160, 40), (zcx + 6, zcy + walk_bob), 7)
            # Bulbous Yellow Eyes
            pygame.draw.circle(z_surf, (255, 240, 50), (zcx + 8, zcy - 3 + walk_bob), 2)
            pygame.draw.circle(z_surf, (255, 240, 50), (zcx + 8, zcy + 2 + walk_bob), 2)
            # Sizzling Acid Slime dripping from mandibles
            pygame.draw.circle(z_surf, (112, 224, 0), (zcx + 12, zcy + walk_bob), 2)

        elif z.type == "brute":
            # --- BRUTE (Massive Hulk, Spiked Iron Shoulder Armor, Chains, Iron Cage Mask, Scars) ---
            # Giant Muscular Torso
            pygame.draw.circle(z_surf, (35, 75, 55), (zcx, zcy + walk_bob), int(r * 0.95))
            pygame.draw.circle(z_surf, (25, 55, 40), (zcx, zcy + walk_bob), int(r * 0.95), 2)

            # Heavy Iron Pauldron with Spikes on left shoulder
            p_rect = pygame.Rect(zcx - int(r * 0.6), zcy - int(r * 0.9) + walk_bob, int(r * 1.1), 10)
            pygame.draw.rect(z_surf, (85, 95, 105), p_rect, border_radius=3)
            pygame.draw.rect(z_surf, (30, 35, 40), p_rect, width=2, border_radius=3)
            for sp_ox in [-6, 0, 6]:
                pygame.draw.polygon(z_surf, (200, 210, 220), [
                    (zcx + sp_ox - 2, zcy - int(r * 0.9) + walk_bob),
                    (zcx + sp_ox, zcy - int(r * 0.9) - 6 + walk_bob),
                    (zcx + sp_ox + 2, zcy - int(r * 0.9) + walk_bob)
                ])

            # Rusted Chains wrapping torso
            pygame.draw.line(z_surf, (140, 95, 50), (zcx - int(r * 0.6), zcy - 6 + walk_bob), (zcx + int(r * 0.6), zcy + 6 + walk_bob), 2)
            pygame.draw.line(z_surf, (140, 95, 50), (zcx - int(r * 0.6), zcy + 6 + walk_bob), (zcx + int(r * 0.6), zcy - 6 + walk_bob), 2)

            # Massive Head with Iron Mask / Cage
            pygame.draw.circle(z_surf, (40, 85, 60), (zcx + 6, zcy + walk_bob), 10)
            pygame.draw.rect(z_surf, (60, 68, 75), (zcx + 7, zcy - 5 + walk_bob, 7, 10), border_radius=2)
            # Fiery Red Furnace Eye-Slits
            pygame.draw.line(z_surf, (255, 50, 50), (zcx + 6, zcy - 2 + walk_bob), (zcx + 11, zcy - 2 + walk_bob), 2)
            pygame.draw.line(z_surf, (255, 50, 50), (zcx + 6, zcy + 2 + walk_bob), (zcx + 11, zcy + 2 + walk_bob), 2)

            # Giant Stone Fists with spiked wraps
            pygame.draw.circle(z_surf, (55, 65, 75), (zcx + 16, zcy - 12 + arm_reach), 6)
            pygame.draw.circle(z_surf, (55, 65, 75), (zcx + 16, zcy + 12 - arm_reach), 6)

        else:
            # --- WALKER (Decaying Flesh, Shredded Blue Jeans, Exposed Ribcage, Rot Gaping Jaws) ---
            # Decaying Olive-Green Torso
            pygame.draw.ellipse(z_surf, (75, 120, 80), (zcx - 10, zcy - 10 + walk_bob, 20, 20))
            # Shredded Jeans / Tattered Rags
            pygame.draw.rect(z_surf, (40, 60, 85), (zcx - 11, zcy - 2 + walk_bob, 10, 10), border_radius=2)

            # Exposed White Ribs and Crimson Meat on side
            pygame.draw.rect(z_surf, (150, 20, 30), (zcx - 4, zcy - 6 + walk_bob, 7, 8))
            for rib_y in [-5, -2, 1]:
                pygame.draw.line(z_surf, (240, 245, 240), (zcx - 4, zcy + rib_y + walk_bob), (zcx + 3, zcy + rib_y + walk_bob), 1)

            # Rotting Head with Missing Patches
            pygame.draw.circle(z_surf, (85, 135, 90), (zcx + 4, zcy + walk_bob), 8)
            # Sunken Dark Sockets with Sickly Yellow-Red Pupils
            pygame.draw.circle(z_surf, (25, 30, 20), (zcx + 6, zcy - 3 + walk_bob), 2)
            pygame.draw.circle(z_surf, (25, 30, 20), (zcx + 6, zcy + 2 + walk_bob), 2)
            pygame.draw.circle(z_surf, (245, 166, 35), (zcx + 6, zcy - 3 + walk_bob), 1)
            pygame.draw.circle(z_surf, (245, 166, 35), (zcx + 6, zcy + 2 + walk_bob), 1)

            # Open Gaping Rot Jaws with Dripping Blood
            pygame.draw.polygon(z_surf, (20, 10, 10), [(zcx + 8, zcy - 1 + walk_bob), (zcx + 12, zcy + walk_bob), (zcx + 8, zcy + 2 + walk_bob)])
            pygame.draw.circle(z_surf, (200, 20, 30), (zcx + 12, zcy + walk_bob), 1)

            # Outstretched clawed shambling arms
            pygame.draw.line(z_surf, (75, 120, 80), (zcx + 2, zcy - 8), (zcx + 12 + arm_reach, zcy - 10), 3)
            pygame.draw.line(z_surf, (75, 120, 80), (zcx + 2, zcy + 8), (zcx + 12 - arm_reach, zcy + 10), 3)
            pygame.draw.circle(z_surf, (180, 160, 60), (zcx + 13 + arm_reach, zcy - 10), 2)
            pygame.draw.circle(z_surf, (180, 160, 60), (zcx + 13 - arm_reach, zcy + 10), 2)

        # 4. Rotate entire zombie body to facing angle towards player
        deg = -math.degrees(z.facing_angle)
        rot_z = pygame.transform.rotate(z_surf, deg)
        z_rect = rot_z.get_rect(center=(sx, sy))
        self.screen.blit(rot_z, z_rect.topleft)

        # 5. Frost/Freeze Coating Overlay (if frozen by Frost Nova)
        if z.frozen:
            frost_surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(frost_surf, (0, 245, 212, 110), (r + 4, r + 4), r + 2)
            pygame.draw.circle(frost_surf, (255, 255, 255, 180), (r + 4, r + 4), r + 2, 2)
            # Frost crystal branches
            for a_deg in [0, 60, 120]:
                rad = math.radians(a_deg)
                fx, fy = int(math.cos(rad) * r), int(math.sin(rad) * r)
                pygame.draw.line(frost_surf, (220, 255, 255), (r + 4 - fx, r + 4 - fy), (r + 4 + fx, r + 4 + fy), 1)
            self.screen.blit(frost_surf, (sx - r - 4, sy - r - 4))

        # 6. Overhead Health Bar
        bar_w = int(r * 2.2 + 6)
        bar_h = 5
        bar_x = sx - bar_w // 2
        bar_y = sy - r - 10
        # Dark border
        pygame.draw.rect(self.screen, (15, 18, 25), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=2)
        pygame.draw.rect(self.screen, (35, 42, 54), (bar_x, bar_y, bar_w, bar_h))

        hp_pct = max(0.0, min(1.0, z.hp / z.max_hp))
        if z.type == "brute":
            fill_col = (245, 166, 35)
        elif z.type == "runner":
            fill_col = (230, 57, 70)
        elif z.type == "spitter":
            fill_col = (112, 224, 0)
        else:
            fill_col = (239, 35, 60)
        pygame.draw.rect(self.screen, fill_col, (bar_x, bar_y, int(bar_w * hp_pct), bar_h))
        # Health bar metallic shine
        pygame.draw.line(self.screen, (255, 255, 255, 120), (bar_x, bar_y), (bar_x + int(bar_w * hp_pct), bar_y), 1)

    def _draw_crosshair(self, mouse_pos: Tuple[int, int]) -> None:
        mx, my = mouse_pos
        reticle_color = (245, 166, 35)
        pygame.draw.circle(self.screen, reticle_color, (mx, my), 8, 2)
        pygame.draw.line(self.screen, reticle_color, (mx, my - 13), (mx, my - 7), 2)
        pygame.draw.line(self.screen, reticle_color, (mx, my + 7), (mx, my + 13), 2)
        pygame.draw.line(self.screen, reticle_color, (mx - 13, my), (mx - 7, my), 2)
        pygame.draw.line(self.screen, reticle_color, (mx + 7, my), (mx + 13, my), 2)
