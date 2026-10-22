"""
Процедурный рендерер спрайтов героев для интерфейса и меню.
Отрисовывает детальные пиксель-арт спрайты персонажей: Воин, Лучник, Маг и Призыватель.
"""

import math
import pygame


def draw_hero_character(surface: pygame.Surface, cx: int, cy: int, class_type: str, anim_time: float = 0.0, scale: float = 1.0) -> None:
    """
    Отрисовывает процедурный спрайт персонажа на поверхности с центром в (cx, cy).
    Поддерживает анимацию дыхания, колыхание плаща и масштабирование.
    """
    size = 96
    body_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    bcx, bcy = size // 2, size // 2

    # Subtle breathing and idle mantle sway
    sway = int(math.sin(anim_time * 2.5) * 3)
    breathe = int(math.cos(anim_time * 2.0) * 1.5)

    if class_type == "ranger":
        # Billowing hunter cloak
        cloak_pts = [
            (bcx - 16, bcy - 14 + breathe),
            (bcx - 28 + sway, bcy - 18),
            (bcx - 24 + sway, bcy),
            (bcx - 28 + sway, bcy + 18),
            (bcx - 16, bcy + 14 + breathe),
        ]
        pygame.draw.polygon(body_surf, (30, 70, 50), cloak_pts)
        pygame.draw.polygon(body_surf, (45, 106, 79), cloak_pts, 1)

        # Leather Boots
        pygame.draw.rect(body_surf, (50, 35, 25), (bcx - 12, bcy - 14, 8, 8), border_radius=2)
        pygame.draw.rect(body_surf, (50, 35, 25), (bcx - 12, bcy + 6, 8, 8), border_radius=2)
        pygame.draw.line(body_surf, (140, 95, 60), (bcx - 12, bcy - 10), (bcx - 4, bcy - 10), 1)
        pygame.draw.line(body_surf, (140, 95, 60), (bcx - 12, bcy + 10), (bcx - 4, bcy + 10), 1)

        # Quiver on back packed with arrows
        quiver_pts = [(bcx - 18, bcy - 14), (bcx - 8, bcy - 18), (bcx - 4, bcy + 14), (bcx - 14, bcy + 18)]
        pygame.draw.polygon(body_surf, (110, 65, 30), quiver_pts)
        pygame.draw.polygon(body_surf, (160, 110, 60), quiver_pts, 1)
        pygame.draw.line(body_surf, (245, 166, 35), (bcx - 16, bcy - 2), (bcx - 6, bcy - 6), 2)
        for f_col, ox, oy in [((255, 255, 255), -14, -22), ((82, 183, 136), -10, -25), ((245, 166, 35), -6, -23)]:
            pygame.draw.line(body_surf, (150, 105, 60), (bcx + ox, bcy + oy + 8), (bcx + ox, bcy + oy), 2)
            pygame.draw.polygon(body_surf, f_col, [(bcx + ox - 2, bcy + oy + 3), (bcx + ox, bcy + oy), (bcx + ox + 2, bcy + oy + 3)])

        # Studded Leather Tunic
        pygame.draw.rect(body_surf, (60, 42, 30), (bcx - 14, bcy - 14 + breathe, 28, 28), border_radius=5)
        pygame.draw.rect(body_surf, (40, 100, 70), (bcx - 12, bcy - 12 + breathe, 24, 24), border_radius=4)
        pygame.draw.line(body_surf, (120, 80, 40), (bcx - 12, bcy - 12 + breathe), (bcx + 12, bcy + 12 + breathe), 3)
        pygame.draw.line(body_surf, (120, 80, 40), (bcx - 12, bcy + 12 + breathe), (bcx + 12, bcy - 12 + breathe), 2)
        pygame.draw.circle(body_surf, (245, 166, 35), (bcx, bcy + breathe), 3)

        # Hunter Hood & Glowing Emerald Eyes
        pygame.draw.circle(body_surf, (45, 106, 79), (bcx + 1, bcy + breathe), 11)
        pygame.draw.polygon(body_surf, (30, 75, 55), [(bcx - 13, bcy - 7 + breathe), (bcx - 2, bcy + breathe), (bcx - 13, bcy + 7 + breathe)])
        pygame.draw.ellipse(body_surf, (15, 20, 25), (bcx + 2, bcy - 6 + breathe, 7, 12))
        pygame.draw.circle(body_surf, (80, 245, 180), (bcx + 5, bcy - 3 + breathe), 1)
        pygame.draw.circle(body_surf, (80, 245, 180), (bcx + 5, bcy + 3 + breathe), 1)

        # Recurve Composite Bow in hands
        bow_cx = bcx + 18
        pygame.draw.arc(body_surf, (180, 115, 45), (bow_cx - 8, bcy - 22, 16, 44), -math.pi / 2, math.pi / 2, 3)
        pygame.draw.arc(body_surf, (120, 70, 25), (bow_cx - 9, bcy - 22, 16, 44), -math.pi / 2, math.pi / 2, 1)
        pygame.draw.circle(body_surf, (245, 166, 35), (bow_cx, bcy - 21), 2)
        pygame.draw.circle(body_surf, (245, 166, 35), (bow_cx, bcy + 21), 2)
        pygame.draw.line(body_surf, (230, 235, 240), (bow_cx, bcy - 21), (bow_cx - 6, bcy), 1)
        pygame.draw.line(body_surf, (230, 235, 240), (bow_cx - 6, bcy), (bow_cx, bcy + 21), 1)
        pygame.draw.line(body_surf, (160, 115, 65), (bow_cx - 6, bcy), (bow_cx + 14, bcy), 2)
        pygame.draw.polygon(body_surf, (240, 245, 250), [(bow_cx + 12, bcy - 3), (bow_cx + 17, bcy), (bow_cx + 12, bcy + 3)])

    elif class_type == "mage":
        # Flowing Robe Tail behind with gold trim
        robe_pts = [
            (bcx - 15, bcy - 14 + breathe),
            (bcx - 26 + sway, bcy - 16),
            (bcx - 23 + sway, bcy),
            (bcx - 26 + sway, bcy + 16),
            (bcx - 15, bcy + 14 + breathe),
        ]
        pygame.draw.polygon(body_surf, (55, 25, 90), robe_pts)
        pygame.draw.polygon(body_surf, (245, 166, 35), robe_pts, 1)

        # Robe Body
        pygame.draw.rect(body_surf, (80, 40, 130), (bcx - 14, bcy - 14 + breathe, 28, 28), border_radius=7)
        pygame.draw.rect(body_surf, (100, 50, 160), (bcx - 12, bcy - 12 + breathe, 24, 24), border_radius=5)
        pygame.draw.circle(body_surf, (245, 166, 35), (bcx - 3, bcy + breathe), 5, 1)
        pygame.draw.line(body_surf, (245, 166, 35), (bcx - 3, bcy - 7 + breathe), (bcx - 3, bcy + 7 + breathe), 1)
        pygame.draw.line(body_surf, (245, 166, 35), (bcx - 10, bcy + breathe), (bcx + 4, bcy + breathe), 1)

        # Collar & Amulet
        pygame.draw.circle(body_surf, (0, 245, 212), (bcx + 1, bcy + breathe), 3)
        pygame.draw.circle(body_surf, (255, 255, 255), (bcx + 1, bcy + breathe), 1)

        # Wizard Hat
        pygame.draw.ellipse(body_surf, (60, 25, 100), (bcx - 14, bcy - 12 + breathe, 28, 24))
        pygame.draw.ellipse(body_surf, (245, 166, 35), (bcx - 14, bcy - 12 + breathe, 28, 24), 1)
        hat_pts = [(bcx - 8, bcy - 8 + breathe), (bcx - 20, bcy + breathe), (bcx - 8, bcy + 8 + breathe), (bcx + 4, bcy + breathe)]
        pygame.draw.polygon(body_surf, (95, 45, 150), hat_pts)
        pygame.draw.polygon(body_surf, (245, 166, 35), hat_pts, 1)
        pygame.draw.circle(body_surf, (160, 110, 255), (bcx + 5, bcy - 3 + breathe), 1)
        pygame.draw.circle(body_surf, (160, 110, 255), (bcx + 5, bcy + 3 + breathe), 1)

        # Arcane Staff with Floating Crystal
        staff_x, staff_y = bcx + 16, bcy + 12
        pygame.draw.line(body_surf, (110, 70, 40), (staff_x - 12, staff_y + 12), (staff_x + 16, staff_y - 16), 4)
        pygame.draw.line(body_surf, (160, 110, 65), (staff_x - 11, staff_y + 12), (staff_x + 16, staff_y - 16), 1)
        pygame.draw.arc(body_surf, (245, 166, 35), (staff_x + 10, staff_y - 22, 14, 14), 0, math.pi * 1.5, 2)
        cryst_pts = [(staff_x + 17, staff_y - 23), (staff_x + 22, staff_y - 15), (staff_x + 17, staff_y - 7), (staff_x + 12, staff_y - 15)]
        pygame.draw.polygon(body_surf, (0, 245, 212), cryst_pts)
        pygame.draw.polygon(body_surf, (255, 255, 255), cryst_pts, 1)
        pygame.draw.circle(body_surf, (255, 255, 255), (staff_x + 17, staff_y - 15), 2)

        # Offhand Floating Mana Rune Spark
        spark_y = bcy - 12 + int(math.sin(anim_time * 4.0) * 3)
        pygame.draw.circle(body_surf, (160, 110, 240), (bcx + 10, spark_y), 5)
        pygame.draw.circle(body_surf, (255, 255, 255), (bcx + 10, spark_y), 2)

    elif class_type == "summoner":
        # Ragged Soul Cloak
        shred_pts = [
            (bcx - 15, bcy - 14 + breathe),
            (bcx - 26 + sway, bcy - 16),
            (bcx - 22 + sway, bcy - 6),
            (bcx - 27 + sway, bcy + 6),
            (bcx - 23 + sway, bcy + 16),
            (bcx - 15, bcy + 14 + breathe),
        ]
        pygame.draw.polygon(body_surf, (18, 22, 28), shred_pts)
        pygame.draw.polygon(body_surf, (72, 202, 228), shred_pts, 1)

        # Dark Robes & Pauldrons
        pygame.draw.rect(body_surf, (25, 30, 36), (bcx - 14, bcy - 14 + breathe, 28, 28), border_radius=6)
        pygame.draw.rect(body_surf, (35, 42, 50), (bcx - 12, bcy - 12 + breathe, 24, 24), border_radius=5)
        pygame.draw.circle(body_surf, (72, 202, 228), (bcx - 2, bcy + breathe), 3)

        pygame.draw.polygon(body_surf, (220, 230, 225), [(bcx - 8, bcy - 16 + breathe), (bcx + 4, bcy - 16 + breathe), (bcx, bcy - 22 + breathe)])
        pygame.draw.polygon(body_surf, (220, 230, 225), [(bcx - 8, bcy + 16 + breathe), (bcx + 4, bcy + 16 + breathe), (bcx, bcy + 22 + breathe)])

        # Cowl Hood & Skull Faceplate
        pygame.draw.circle(body_surf, (15, 18, 24), (bcx, bcy + breathe), 11)
        pygame.draw.polygon(body_surf, (10, 12, 16), [(bcx - 13, bcy - 7 + breathe), (bcx - 3, bcy + breathe), (bcx - 13, bcy + 7 + breathe)])
        pygame.draw.ellipse(body_surf, (215, 225, 220), (bcx + 1, bcy - 6 + breathe, 8, 12))
        pygame.draw.circle(body_surf, (15, 20, 25), (bcx + 4, bcy - 3 + breathe), 2)
        pygame.draw.circle(body_surf, (15, 20, 25), (bcx + 4, bcy + 3 + breathe), 2)
        pygame.draw.circle(body_surf, (80, 245, 180), (bcx + 4, bcy - 3 + breathe), 1)
        pygame.draw.circle(body_surf, (80, 245, 180), (bcx + 4, bcy + 3 + breathe), 1)

        # Scepter of the Damned
        scep_x, scep_y = bcx + 16, bcy + 12
        pygame.draw.line(body_surf, (180, 190, 185), (scep_x - 12, scep_y + 12), (scep_x + 14, scep_y - 14), 4)
        pygame.draw.circle(body_surf, (230, 240, 235), (scep_x + 14, scep_y - 14), 7)
        pygame.draw.polygon(body_surf, (80, 245, 180), [(scep_x + 12, scep_y - 20), (scep_x + 17, scep_y - 14), (scep_x + 10, scep_y - 13)])
        pygame.draw.circle(body_surf, (80, 245, 180), (scep_x + 14, scep_y - 14), 4)
        pygame.draw.circle(body_surf, (255, 255, 255), (scep_x + 14, scep_y - 14), 1)

    else:
        # --- WARRIOR / KNIGHT ---
        cape_pts = [
            (bcx - 16, bcy - 14 + breathe),
            (bcx - 28 + sway, bcy - 18),
            (bcx - 25 + sway, bcy),
            (bcx - 28 + sway, bcy + 18),
            (bcx - 16, bcy + 14 + breathe),
        ]
        pygame.draw.polygon(body_surf, (160, 20, 30), cape_pts)
        pygame.draw.polygon(body_surf, (230, 57, 70), [(bcx - 16, bcy - 12 + breathe), (bcx - 26 + sway, bcy - 16), (bcx - 23 + sway, bcy), (bcx - 26 + sway, bcy + 16), (bcx - 16, bcy + 12 + breathe)])
        pygame.draw.polygon(body_surf, (245, 166, 35), cape_pts, 1)

        # Steel Greaves
        pygame.draw.rect(body_surf, (73, 80, 87), (bcx - 12, bcy - 14, 8, 8), border_radius=2)
        pygame.draw.rect(body_surf, (73, 80, 87), (bcx - 12, bcy + 6, 8, 8), border_radius=2)
        pygame.draw.line(body_surf, (206, 212, 218), (bcx - 12, bcy - 14), (bcx - 4, bcy - 14), 2)
        pygame.draw.line(body_surf, (206, 212, 218), (bcx - 12, bcy + 6), (bcx - 4, bcy + 6), 2)

        # Cuirass with Crimson Cross
        pygame.draw.rect(body_surf, (173, 181, 189), (bcx - 15, bcy - 15 + breathe, 30, 30), border_radius=6)
        pygame.draw.rect(body_surf, (73, 80, 87), (bcx - 15, bcy - 15 + breathe, 30, 30), width=2, border_radius=6)
        pygame.draw.line(body_surf, (240, 245, 250), (bcx - 13, bcy - 13 + breathe), (bcx + 13, bcy - 13 + breathe), 2)
        pygame.draw.rect(body_surf, (230, 57, 70), (bcx - 3, bcy - 12 + breathe, 6, 24))
        pygame.draw.rect(body_surf, (230, 57, 70), (bcx - 10, bcy - 5 + breathe, 20, 6))
        pygame.draw.circle(body_surf, (245, 166, 35), (bcx, bcy - 2 + breathe), 3)

        # Pauldrons
        pygame.draw.ellipse(body_surf, (206, 212, 218), (bcx - 10, bcy - 22 + breathe, 16, 10))
        pygame.draw.ellipse(body_surf, (73, 80, 87), (bcx - 10, bcy - 22 + breathe, 16, 10), 1)
        pygame.draw.ellipse(body_surf, (206, 212, 218), (bcx - 10, bcy + 12 + breathe, 16, 10))
        pygame.draw.ellipse(body_surf, (73, 80, 87), (bcx - 10, bcy + 12 + breathe, 16, 10), 1)

        # Great Helm with Slit & Red Plume
        pygame.draw.circle(body_surf, (206, 212, 218), (bcx + 1, bcy + breathe), 11)
        pygame.draw.circle(body_surf, (73, 80, 87), (bcx + 1, bcy + breathe), 11, 2)
        pygame.draw.line(body_surf, (245, 166, 35), (bcx - 2, bcy - 5 + breathe), (bcx + 10, bcy - 5 + breathe), 2)
        pygame.draw.line(body_surf, (245, 166, 35), (bcx - 2, bcy + 5 + breathe), (bcx + 10, bcy + 5 + breathe), 2)
        pygame.draw.line(body_surf, (245, 166, 35), (bcx + 4, bcy - 9 + breathe), (bcx + 4, bcy + 9 + breathe), 2)
        pygame.draw.line(body_surf, (72, 202, 228), (bcx + 4, bcy - 2 + breathe), (bcx + 9, bcy - 2 + breathe), 2)
        pygame.draw.line(body_surf, (72, 202, 228), (bcx + 4, bcy + 2 + breathe), (bcx + 9, bcy + 2 + breathe), 2)

        plume_pts = [(bcx - 4, bcy - 5 + breathe), (bcx - 14, bcy + breathe), (bcx - 4, bcy + 5 + breathe)]
        pygame.draw.polygon(body_surf, (230, 57, 70), plume_pts)
        pygame.draw.polygon(body_surf, (245, 166, 35), plume_pts, 1)

        # Shield & Broadsword
        shield_pts = [(bcx + 2, bcy - 22 + breathe), (bcx + 14, bcy - 22 + breathe), (bcx + 12, bcy - 10 + breathe), (bcx + 4, bcy - 8 + breathe)]
        pygame.draw.polygon(body_surf, (43, 45, 66), shield_pts)
        pygame.draw.polygon(body_surf, (245, 166, 35), shield_pts, 2)
        pygame.draw.circle(body_surf, (230, 57, 70), (bcx + 8, bcy - 16 + breathe), 3)

        sword_surf = pygame.Surface((64, 32), pygame.SRCALPHA)
        scx, scy = 12, 16
        pygame.draw.circle(sword_surf, (245, 166, 35), (scx - 8, scy), 3)
        pygame.draw.rect(sword_surf, (110, 65, 30), (scx - 6, scy - 2, 8, 4))
        pygame.draw.rect(sword_surf, (245, 166, 35), (scx + 2, scy - 8, 4, 16), border_radius=1)
        blade_pts = [(scx + 6, scy - 4), (scx + 38, scy - 3), (scx + 46, scy), (scx + 38, scy + 3), (scx + 6, scy + 4)]
        pygame.draw.polygon(sword_surf, (248, 249, 250), blade_pts)
        pygame.draw.polygon(sword_surf, (173, 181, 189), blade_pts, 1)
        pygame.draw.line(sword_surf, (200, 210, 220), (scx + 8, scy), (scx + 34, scy), 2)
        rot_sw = pygame.transform.rotate(sword_surf, -12)
        body_surf.blit(rot_sw, rot_sw.get_rect(center=(bcx + 14, bcy + 14 + breathe)).topleft)

    # Scale and blit to target surface
    if abs(scale - 1.0) > 0.01:
        tw = max(1, int(size * scale))
        th = max(1, int(size * scale))
        scaled_surf = pygame.transform.smoothscale(body_surf, (tw, th))
        surface.blit(scaled_surf, (cx - tw // 2, cy - th // 2))
    else:
        surface.blit(body_surf, (cx - size // 2, cy - size // 2))

