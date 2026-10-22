"""
Процедурный 8-битный аудиодвижок с использованием Pygame Mixer и синтеза чиптюна.
Генерирует ретро звуковые эффекты напрямую в оперативной памяти без внешних файлов.
"""

import io
import math
import struct
import wave
import pygame
from typing import Dict, Optional


class SoundEngine:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.muted = False
        self.volume = 1.0
        self.available = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.sample_rate, -16, 1, 512)
            self.available = True
            self._generate_all_sounds()
        except Exception as e:
            print(f"[SoundEngine] Audio init warning: {e}. Audio disabled.")
            self.available = False

    def set_volume(self, vol: float) -> None:
        self.volume = max(0.0, min(1.0, float(vol)))
        if self.available:
            for snd in self.sounds.values():
                try:
                    snd.set_volume(self.volume)
                except Exception:
                    pass

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        return self.muted

    def _build_wav(self, duration: float, generator_fn) -> Optional[pygame.mixer.Sound]:
        if not self.available:
            return None
        total_samples = int(self.sample_rate * duration)
        buf = io.BytesIO()
        try:
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                raw_frames = bytearray()
                for i in range(total_samples):
                    t = i / float(self.sample_rate)
                    progress = i / float(total_samples) if total_samples > 0 else 0
                    sample_val = generator_fn(t, progress, duration)
                    # Clamp between -32767 and 32767
                    clamped = max(-32767, min(32767, int(sample_val * 32767)))
                    raw_frames.extend(struct.pack("<h", clamped))
                wf.writeframes(bytes(raw_frames))
            buf.seek(0)
            return pygame.mixer.Sound(buf)
        except Exception as e:
            print(f"[SoundEngine] Error building sound: {e}")
            return None

    def _generate_all_sounds(self) -> None:
        # 1. Sword Swing (triangle pitch drop)
        def sword_gen(t, p, d):
            freq = 380.0 * ((90.0 / 380.0) ** (p))
            phase = (t * freq) % 1.0
            # Triangle wave:
            raw = 4.0 * abs(phase - 0.5) - 1.0
            env = max(0.0, 1.0 - p) ** 1.5
            return raw * env * 0.45

        s = self._build_wav(0.13, sword_gen)
        if s: self.sounds["sword_swing"] = s

        # 2. Spin Attack (sawtooth rising then falling)
        def spin_gen(t, p, d):
            if p < 0.5:
                freq = 260.0 + (540.0 - 260.0) * (p / 0.5)
            else:
                freq = 540.0 * ((100.0 / 540.0) ** ((p - 0.5) / 0.5))
            phase = (t * freq) % 1.0
            raw = 2.0 * phase - 1.0  # Sawtooth
            env = (1.0 - p) ** 1.2
            return raw * env * 0.5

        s = self._build_wav(0.28, spin_gen)
        if s: self.sounds["spin_attack"] = s

        # 3. Wind Blade (high sine sweeping down)
        def wind_gen(t, p, d):
            freq = 800.0 * ((220.0 / 800.0) ** p)
            raw = math.sin(2.0 * math.pi * freq * t)
            # Add slight harmonics
            raw = 0.8 * raw + 0.2 * math.sin(4.0 * math.pi * freq * t)
            env = (1.0 - p) ** 1.3
            return raw * env * 0.5

        s = self._build_wav(0.25, wind_gen)
        if s: self.sounds["wind_blade"] = s

        # 4. Hit Zombie (crunchy low square punch)
        def hit_gen(t, p, d):
            freq = 140.0 * ((40.0 / 140.0) ** p)
            phase = (t * freq) % 1.0
            raw = 1.0 if phase < 0.5 else -1.0
            # mix with white noise
            noise = ((math.sin(t * 123456.7) * 43758.5453) % 2.0) - 1.0
            val = 0.7 * raw + 0.3 * noise
            env = (1.0 - p) ** 2
            return val * env * 0.55

        s = self._build_wav(0.09, hit_gen)
        if s: self.sounds["hit_zombie"] = s

        # 5. Player Hurt (buzzing warning sawtooth)
        def hurt_gen(t, p, d):
            freq = 180.0 - 100.0 * p
            phase = (t * freq) % 1.0
            raw = 2.0 * phase - 1.0
            env = (1.0 - p)
            return raw * env * 0.6

        s = self._build_wav(0.22, hurt_gen)
        if s: self.sounds["player_hurt"] = s

        # 6. Dash (airy rising whoosh)
        def dash_gen(t, p, d):
            freq = 220.0 + 380.0 * p
            phase = (t * freq) % 1.0
            raw = 4.0 * abs(phase - 0.5) - 1.0
            noise = ((math.sin(t * 98765.4) * 12345.67) % 2.0) - 1.0
            val = 0.5 * raw + 0.5 * noise
            env = math.sin(p * math.pi)
            return val * env * 0.4

        s = self._build_wav(0.18, dash_gen)
        if s: self.sounds["dash"] = s

        # 7. Level Up (cheerful 4-note arpeggio)
        notes = [261.63, 329.63, 392.00, 523.25]
        def levelup_gen(t, p, d):
            step = int(p * 4)
            step = min(3, max(0, step))
            freq = notes[step]
            step_p = (p * 4) % 1.0
            raw = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - step_p) ** 0.8
            return raw * env * 0.55

        s = self._build_wav(0.40, levelup_gen)
        if s: self.sounds["level_up"] = s

        # 8. Wave Start (menacing horn)
        def wave_gen(t, p, d):
            freq = 95.0 + 35.0 * p
            raw = 2.0 * ((t * freq) % 1.0) - 1.0
            env = math.sin(min(1.0, p * 3.0) * math.pi * 0.5) * (1.0 - p)
            return raw * env * 0.65

        s = self._build_wav(0.60, wave_gen)
        if s: self.sounds["wave_start"] = s

        # 9. Game Over (sad descending sequence)
        down_notes = [220.0, 207.65, 196.0, 174.61]
        def gameover_gen(t, p, d):
            step = int(p * 4)
            step = min(3, max(0, step))
            freq = down_notes[step]
            step_p = (p * 4) % 1.0
            raw = 2.0 * ((t * freq) % 1.0) - 1.0
            env = max(0.0, 1.0 - step_p)
            return raw * env * 0.55

        s = self._build_wav(0.75, gameover_gen)
        if s: self.sounds["game_over"] = s

        # 10. Menu Hover
        def hover_gen(t, p, d):
            freq = 520.0
            phase = (t * freq) % 1.0
            raw = 4.0 * abs(phase - 0.5) - 1.0
            env = max(0.0, 1.0 - p) ** 2
            return raw * env * 0.25

        s = self._build_wav(0.03, hover_gen)
        if s: self.sounds["menu_hover"] = s

        # 11. Menu Click
        def click_gen(t, p, d):
            freq = 440.0 + 440.0 * p
            raw = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - p) ** 1.5
            return raw * env * 0.45

        s = self._build_wav(0.05, click_gen)
        if s: self.sounds["menu_click"] = s

        # 12. Buy Upgrade / Coins Chime
        def coin_gen(t, p, d):
            freq = 587.33 if p < 0.5 else 880.00
            raw = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - (p % 0.5) / 0.5) ** 1.2
            return raw * env * 0.45

        s = self._build_wav(0.16, coin_gen)
        if s: self.sounds["buy_upgrade"] = s

        # 13. Bow Shoot (twang)
        def bow_gen(t, p, d):
            freq = 520.0 * (0.35 ** p)
            noise = ((math.sin(t * 88888.8) * 43758.5) % 2.0) - 1.0
            raw = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - p) ** 2.5
            return (0.7 * raw + 0.3 * noise) * env * 0.45

        s = self._build_wav(0.11, bow_gen)
        if s: self.sounds["bow_shoot"] = s

        # 14. Explosion (fireball & explosive arrow)
        def exp_gen(t, p, d):
            noise = ((math.sin(t * 123456.7) * 43758.5453) % 2.0) - 1.0
            sub = math.sin(2.0 * math.pi * 55.0 * t)
            env = max(0.0, 1.0 - p) ** 1.8
            return (0.6 * noise + 0.4 * sub) * env * 0.70

        s = self._build_wav(0.36, exp_gen)
        if s: self.sounds["explosion"] = s

        # 15. Freeze / Frost Nova
        def freeze_gen(t, p, d):
            freq = 650.0 + 550.0 * p
            raw = math.sin(2.0 * math.pi * freq * t)
            shimmer = math.sin(2.0 * math.pi * (freq * 2.5) * t)
            env = math.sin(p * math.pi) * (1.0 - p)
            return (0.6 * raw + 0.4 * shimmer) * env * 0.50

        s = self._build_wav(0.24, freeze_gen)
        if s: self.sounds["freeze"] = s

        # 16. Teleport / Blink
        def blink_gen(t, p, d):
            freq = 320.0 + 560.0 * math.sin(p * math.pi)
            raw = 2.0 * ((t * freq) % 1.0) - 1.0
            env = math.sin(p * math.pi)
            return raw * env * 0.45

        s = self._build_wav(0.18, blink_gen)
        if s: self.sounds["teleport"] = s

        # 17. Summon Minion
        def summon_gen(t, p, d):
            freq = 180.0 + 40.0 * math.sin(t * 30.0)
            raw = 4.0 * abs(((t * freq) % 1.0) - 0.5) - 1.0
            env = math.sin(p * math.pi)
            return raw * env * 0.50

        s = self._build_wav(0.28, summon_gen)
        if s: self.sounds["summon"] = s

    def _play(self, sound_name: str) -> None:
        if self.muted or not self.available:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def play_sword_swing(self): self._play("sword_swing")
    def play_spin_attack(self): self._play("spin_attack")
    def play_wind_blade(self): self._play("wind_blade")
    def play_hit_zombie(self): self._play("hit_zombie")
    def play_player_hurt(self): self._play("player_hurt")
    def play_dash(self): self._play("dash")
    def play_level_up(self): self._play("level_up")
    def play_wave_start(self): self._play("wave_start")
    def play_game_over(self): self._play("game_over")
    def play_menu_hover(self): self._play("menu_hover")
    def play_menu_click(self): self._play("menu_click")
    def play_buy_upgrade(self): self._play("buy_upgrade")
    def play_bow_shoot(self): self._play("bow_shoot")
    def play_explosion(self): self._play("explosion")
    def play_freeze(self): self._play("freeze")
    def play_teleport(self): self._play("teleport")
    def play_summon(self): self._play("summon")

