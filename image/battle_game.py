"""
Mythical Elemental Warriors - Turn-Based Battle Game
CS5001 Final Project
A team-based turn-based battle game built with Python and Pygame.
Players draft a team of 3 warriors and battle against an AI opponent.
"""

import pygame
import random
import math
import sys
import struct
import array

# ---------------------------------------------------------------------------
# Initialise Pygame
# ---------------------------------------------------------------------------
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

WIDTH, HEIGHT = 1100, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mythical Elemental Warriors")
clock = pygame.time.Clock()
FPS = 60

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GREY       = (60, 60, 70)
DARK_GREY  = (35, 35, 45)
LIGHT_GREY = (140, 140, 155)
RED        = (220, 50, 50)
GREEN      = (50, 200, 80)
BLUE       = (50, 120, 220)
GOLD       = (255, 210, 60)
ORANGE     = (240, 140, 40)
PURPLE     = (160, 60, 220)
CYAN       = (40, 200, 230)
TEAL       = (30, 170, 160)
PINK       = (230, 100, 160)
DARK_RED   = (120, 20, 20)
DARK_GREEN = (20, 80, 30)
DARK_BLUE  = (20, 40, 100)

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_SM   = pygame.font.SysFont("consolas", 14)
FONT_MD   = pygame.font.SysFont("consolas", 18)
FONT_LG   = pygame.font.SysFont("consolas", 24)
FONT_XL   = pygame.font.SysFont("consolas", 36, bold=True)
FONT_TITLE = pygame.font.SysFont("consolas", 52, bold=True)

# ---------------------------------------------------------------------------
# Sound Generation (no external files needed)
# ---------------------------------------------------------------------------
def generate_sound(frequency=440, duration_ms=150, volume=0.3, wave="square",
                   fade_out=True, noise_mix=0.0):
    """Generate a pygame Sound object from parameters."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array('h', [0] * n_samples)
    max_amp = int(32767 * volume)
    for i in range(n_samples):
        t = i / sample_rate
        # Base wave
        if wave == "square":
            val = max_amp if math.sin(2 * math.pi * frequency * t) >= 0 else -max_amp
        elif wave == "sine":
            val = int(max_amp * math.sin(2 * math.pi * frequency * t))
        elif wave == "sawtooth":
            val = int(max_amp * (2 * (frequency * t % 1) - 1))
        else:
            val = int(max_amp * (2 * random.random() - 1))
        # Noise mix
        if noise_mix > 0:
            noise = int(max_amp * noise_mix * (2 * random.random() - 1))
            val = int(val * (1 - noise_mix) + noise)
        # Fade out
        if fade_out and n_samples > 0:
            fade_factor = 1.0 - (i / n_samples)
            val = int(val * fade_factor)
        buf[i] = max(-32767, min(32767, val))
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

# Pre-generate sounds
SFX_ATTACK   = generate_sound(220, 120, 0.25, "square", True, 0.3)
SFX_DEFEND   = generate_sound(600, 200, 0.15, "sine", True, 0.0)
SFX_SPECIAL  = generate_sound(330, 300, 0.25, "sawtooth", True, 0.1)
SFX_HIT      = generate_sound(120, 80, 0.3, "noise", True, 0.8)
SFX_HEAL     = generate_sound(523, 350, 0.15, "sine", True, 0.0)
SFX_LEVELUP  = generate_sound(660, 400, 0.2, "sine", True, 0.0)
SFX_DEFEAT   = generate_sound(100, 500, 0.2, "sawtooth", True, 0.2)
SFX_VICTORY  = generate_sound(440, 600, 0.2, "sine", True, 0.0)
SFX_SELECT   = generate_sound(800, 60, 0.1, "square", True, 0.0)
SFX_CLICK    = generate_sound(1000, 40, 0.08, "square", True, 0.0)


# ===========================================================================
# PARTICLE SYSTEM
# ===========================================================================
class Particle:
    """A single visual particle for effects."""
    def __init__(self, x, y, vx, vy, colour, life, size=3, gravity=0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.colour = colour
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt

    def draw(self, surface):
        alpha = max(0, self.life / self.max_life)
        r = max(1, int(self.size * alpha))
        colour = tuple(int(c * alpha) for c in self.colour)
        pygame.draw.circle(surface, colour, (int(self.x), int(self.y)), r)

    @property
    def alive(self):
        return self.life > 0


class ParticleSystem:
    """Manages all active particles."""
    def __init__(self):
        self.particles = []

    def emit_burst(self, x, y, colour, count=20, speed=150, life=0.6,
                   size=4, gravity=0):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            p = Particle(x, y, vx, vy, colour,
                         random.uniform(life * 0.5, life), size, gravity)
            self.particles.append(p)

    def emit_rising(self, x, y, colour, count=10, life=1.0, size=3):
        for _ in range(count):
            vx = random.uniform(-30, 30)
            vy = random.uniform(-120, -40)
            p = Particle(x + random.uniform(-15, 15),
                         y + random.uniform(-10, 10),
                         vx, vy, colour,
                         random.uniform(life * 0.5, life), size)
            self.particles.append(p)

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)


particles = ParticleSystem()

# ===========================================================================
# FLOATING TEXT (damage numbers, status text)
# ===========================================================================
class FloatingText:
    """Animated text that floats upward and fades out."""
    def __init__(self, x, y, text, colour, duration=1.2, font=None):
        self.x = x
        self.y = y
        self.start_y = y
        self.text = text
        self.colour = colour
        self.duration = duration
        self.timer = duration
        self.font = font or FONT_LG

    def update(self, dt):
        self.timer -= dt
        self.y = self.start_y - (1 - self.timer / self.duration) * 50

    def draw(self, surface):
        if self.timer <= 0:
            return
        alpha = max(0, min(1, self.timer / self.duration))
        colour = tuple(int(c * alpha) for c in self.colour)
        txt_surf = self.font.render(self.text, True, colour)
        rect = txt_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(txt_surf, rect)

    @property
    def alive(self):
        return self.timer > 0


floating_texts = []


# ===========================================================================
# SCREEN SHAKE
# ===========================================================================
class ScreenShake:
    """Screen shake effect controller."""
    def __init__(self):
        self.intensity = 0
        self.timer = 0

    def trigger(self, intensity=8, duration=0.3):
        self.intensity = intensity
        self.timer = duration

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt

    def get_offset(self):
        if self.timer > 0:
            return (random.randint(-int(self.intensity), int(self.intensity)),
                    random.randint(-int(self.intensity), int(self.intensity)))
        return (0, 0)


shake = ScreenShake()


# ===========================================================================
# CHARACTER DEFINITIONS
# ===========================================================================
# Each character class has: name, element, colour, atk range, def range,
# special ability description, and special type.

CHARACTER_TEMPLATES = [
    {
        "name": "Ignis",
        "title": "Flame Warden",
        "element": "Fire",
        "colour": ORANGE,
        "colour2": RED,
        "atk_range": (22, 30),
        "def_range": (8, 14),
        "special_type": "damage",       # Heavy fire damage
        "special_name": "Inferno Blast",
        "special_desc": "Unleashes massive fire damage (2x ATK)",
        "special_multiplier": 2.0,
    },
    {
        "name": "Aquara",
        "title": "Tidal Sage",
        "element": "Water",
        "colour": CYAN,
        "colour2": BLUE,
        "atk_range": (16, 22),
        "def_range": (14, 20),
        "special_type": "heal",          # Heals self
        "special_name": "Tidal Restore",
        "special_desc": "Restores 30 HP to self",
        "special_multiplier": 30,
    },
    {
        "name": "Terra",
        "title": "Stone Guardian",
        "element": "Earth",
        "colour": (180, 140, 60),
        "colour2": (120, 90, 30),
        "atk_range": (14, 20),
        "def_range": (20, 28),
        "special_type": "fortify",       # Boosts defense for 2 turns
        "special_name": "Iron Fortress",
        "special_desc": "Doubles DEF for 2 turns",
        "special_multiplier": 2,
    },
    {
        "name": "Voltis",
        "title": "Storm Caller",
        "element": "Lightning",
        "colour": GOLD,
        "colour2": (255, 255, 150),
        "atk_range": (25, 34),
        "def_range": (5, 10),
        "special_type": "chain",         # Hits all enemies
        "special_name": "Chain Lightning",
        "special_desc": "Strikes ALL enemies for 0.7x ATK",
        "special_multiplier": 0.7,
    },
    {
        "name": "Umbra",
        "title": "Shadow Assassin",
        "element": "Shadow",
        "colour": PURPLE,
        "colour2": (80, 20, 120),
        "atk_range": (26, 35),
        "def_range": (4, 9),
        "special_type": "critical",      # Guaranteed crit (3x damage)
        "special_name": "Shadow Strike",
        "special_desc": "Guaranteed critical hit (3x ATK, ignores DEF)",
        "special_multiplier": 3.0,
    },
    {
        "name": "Sylva",
        "title": "Nature Druid",
        "element": "Nature",
        "colour": GREEN,
        "colour2": TEAL,
        "atk_range": (15, 22),
        "def_range": (12, 18),
        "special_type": "team_heal",     # Heals all teammates
        "special_name": "Nature's Grace",
        "special_desc": "Heals all allies for 20 HP",
        "special_multiplier": 20,
    },
]


class Character:
    """Represents a single battle unit with stats, actions, and state."""

    def __init__(self, template, team_side):
        self.name = template["name"]
        self.title = template["title"]
        self.element = template["element"]
        self.colour = template["colour"]
        self.colour2 = template["colour2"]
        self.team_side = team_side  # "player" or "enemy"

        # Core stats (randomly initialised within ranges per spec)
        self.max_hp = 100
        self.hp = 100
        self.atk = random.randint(*template["atk_range"])
        self.base_def = random.randint(*template["def_range"])
        self.defense = self.base_def

        # Experience & levelling
        self.epx = 0
        self.level = 1

        # Special ability
        self.special_type = template["special_type"]
        self.special_name = template["special_name"]
        self.special_desc = template["special_desc"]
        self.special_multiplier = template["special_multiplier"]
        self.special_cooldown = 0          # turns until special is available
        self.special_cooldown_max = 3      # usable every 3 turns

        # Status effects
        self.is_defending = False
        self.fortify_turns = 0             # extra defense buff duration

        # Visual state
        self.display_hp = 100              # for smooth health bar animation
        self.x, self.y = 0, 0             # position on screen
        self.anim_offset_x = 0
        self.anim_offset_y = 0
        self.flash_timer = 0
        self.flash_colour = WHITE
        self.pulse_timer = 0               # for idle breathing animation

    @property
    def alive(self):
        return self.hp > 0

    def get_effective_def(self):
        """Return defense considering buffs."""
        d = self.defense
        if self.fortify_turns > 0:
            d = int(d * 2)
        return d

    def start_turn(self):
        """Called at the beginning of this character's turn."""
        self.is_defending = False
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        if self.fortify_turns > 0:
            self.fortify_turns -= 1

    def perform_attack(self, target):
        """Execute a normal attack on target. Returns (damage, messages)."""
        messages = []
        raw_def = target.get_effective_def()
        if target.is_defending:
            raw_def = int(raw_def * 1.5)  # defend action boosts def further
        modifier = random.randint(-5, 10)
        damage = self.atk - raw_def + modifier
        # Minimum 1 damage on attack unless defending heavily
        if damage < 0:
            damage = 0

        target.hp -= damage
        target.hp = max(target.hp, 0)

        # Experience gains (per spec)
        self.gain_epx(damage)
        target_epx = target.base_def
        if damage > 10:
            target_epx += int(target.base_def * 0.2)
        elif damage <= 0:
            target_epx += int(target.base_def * 0.5)
        target.gain_epx(target_epx)

        if target.is_defending:
            messages.append(f"{target.name} braces! Damage reduced!")
        messages.insert(0,
            f"{self.name} attacks {target.name} for {damage} damage!")

        # Visual effects
        target.flash_timer = 0.3
        target.flash_colour = RED
        shake.trigger(6 + damage * 0.3, 0.2)
        particles.emit_burst(target.x, target.y, self.colour, 15,
                             100 + damage * 5, 0.5, 4, 100)
        SFX_ATTACK.play()
        if damage > 0:
            SFX_HIT.play()
            floating_texts.append(
                FloatingText(target.x, target.y - 30,
                             f"-{damage}", RED, 1.5, FONT_XL))
        else:
            floating_texts.append(
                FloatingText(target.x, target.y - 30,
                             "BLOCKED!", GOLD, 1.2, FONT_LG))

        if not target.alive:
            messages.append(f"{target.name} has been defeated!")
            SFX_DEFEAT.play()
            particles.emit_burst(target.x, target.y, target.colour, 40,
                                 200, 1.0, 6, 50)

        return damage, messages

    def perform_defend(self):
        """Activate defensive stance. Returns messages."""
        self.is_defending = True
        SFX_DEFEND.play()
        particles.emit_rising(self.x, self.y, CYAN, 8, 0.8, 3)
        floating_texts.append(
            FloatingText(self.x, self.y - 30, "DEFEND", CYAN, 1.0))
        self.flash_timer = 0.3
        self.flash_colour = CYAN
        return [f"{self.name} takes a defensive stance!"]

    def perform_special(self, target=None, allies=None, enemies=None):
        """Execute special ability. Returns messages."""
        messages = []
        self.special_cooldown = self.special_cooldown_max
        SFX_SPECIAL.play()

        if self.special_type == "damage":
            # Heavy single-target damage
            raw_def = target.get_effective_def()
            if target.is_defending:
                raw_def = int(raw_def * 1.5)
            damage = int(self.atk * self.special_multiplier) - raw_def
            damage = max(damage, 0)
            modifier = random.randint(-5, 10)
            damage += modifier
            damage = max(damage, 0)
            target.hp -= damage
            target.hp = max(target.hp, 0)
            self.gain_epx(damage)
            messages.append(
                f"{self.name} uses {self.special_name} on {target.name} "
                f"for {damage} damage!")
            target.flash_timer = 0.5
            target.flash_colour = ORANGE
            shake.trigger(12, 0.4)
            particles.emit_burst(target.x, target.y, ORANGE, 30, 200, 0.8, 6, 80)
            particles.emit_burst(target.x, target.y, GOLD, 15, 150, 0.6, 3, 50)
            floating_texts.append(
                FloatingText(target.x, target.y - 30,
                             f"-{damage}", ORANGE, 1.5, FONT_XL))
            if not target.alive:
                messages.append(f"{target.name} has been defeated!")
                SFX_DEFEAT.play()

        elif self.special_type == "heal":
            heal = int(self.special_multiplier)
            self.hp = min(self.max_hp, self.hp + heal)
            messages.append(
                f"{self.name} uses {self.special_name}! Restored {heal} HP!")
            SFX_HEAL.play()
            particles.emit_rising(self.x, self.y, GREEN, 15, 1.0, 4)
            floating_texts.append(
                FloatingText(self.x, self.y - 30,
                             f"+{heal} HP", GREEN, 1.5, FONT_LG))

        elif self.special_type == "fortify":
            self.fortify_turns = int(self.special_multiplier)
            messages.append(
                f"{self.name} uses {self.special_name}! "
                f"DEF doubled for {self.fortify_turns} turns!")
            particles.emit_burst(self.x, self.y, (180, 140, 60), 20,
                                 80, 0.8, 5, 0)
            floating_texts.append(
                FloatingText(self.x, self.y - 30,
                             "DEF x2!", GOLD, 1.5, FONT_LG))

        elif self.special_type == "chain":
            # Hit all enemies
            total_dmg = 0
            for enemy in enemies:
                if enemy.alive:
                    raw_def = enemy.get_effective_def()
                    if enemy.is_defending:
                        raw_def = int(raw_def * 1.5)
                    dmg = int(self.atk * self.special_multiplier) - raw_def
                    dmg += random.randint(-5, 10)
                    dmg = max(dmg, 0)
                    enemy.hp -= dmg
                    enemy.hp = max(enemy.hp, 0)
                    total_dmg += dmg
                    enemy.flash_timer = 0.4
                    enemy.flash_colour = GOLD
                    particles.emit_burst(enemy.x, enemy.y, GOLD, 12,
                                         120, 0.5, 3, 60)
                    floating_texts.append(
                        FloatingText(enemy.x, enemy.y - 30,
                                     f"-{dmg}", GOLD, 1.5, FONT_LG))
                    if not enemy.alive:
                        messages.append(f"  {enemy.name} has been defeated!")
                        SFX_DEFEAT.play()
            self.gain_epx(total_dmg)
            messages.insert(0,
                f"{self.name} uses {self.special_name}! "
                f"Hits all enemies for {total_dmg} total damage!")
            shake.trigger(10, 0.35)

        elif self.special_type == "critical":
            # Ignore defense, massive damage
            damage = int(self.atk * self.special_multiplier)
            target.hp -= damage
            target.hp = max(target.hp, 0)
            self.gain_epx(damage)
            messages.append(
                f"{self.name} uses {self.special_name} on {target.name} "
                f"for {damage} CRITICAL damage!")
            target.flash_timer = 0.5
            target.flash_colour = PURPLE
            shake.trigger(15, 0.5)
            particles.emit_burst(target.x, target.y, PURPLE, 35, 250, 0.9, 5, 60)
            floating_texts.append(
                FloatingText(target.x, target.y - 30,
                             f"CRIT -{damage}", PURPLE, 1.8, FONT_XL))
            if not target.alive:
                messages.append(f"{target.name} has been defeated!")
                SFX_DEFEAT.play()

        elif self.special_type == "team_heal":
            heal = int(self.special_multiplier)
            for ally in allies:
                if ally.alive:
                    ally.hp = min(ally.max_hp, ally.hp + heal)
                    particles.emit_rising(ally.x, ally.y, GREEN, 10, 0.8, 3)
                    floating_texts.append(
                        FloatingText(ally.x, ally.y - 30,
                                     f"+{heal} HP", GREEN, 1.2))
            SFX_HEAL.play()
            messages.append(
                f"{self.name} uses {self.special_name}! "
                f"All allies healed for {heal} HP!")

        return messages

    def gain_epx(self, amount):
        """Add experience and handle level ups."""
        if amount <= 0:
            return
        self.epx += amount
        while self.epx >= 100:
            self.epx -= 100
            self.level += 1
            self.atk += 2
            self.base_def += 1
            self.defense = self.base_def
            self.max_hp += 10
            self.hp = min(self.hp + 10, self.max_hp)
            SFX_LEVELUP.play()
            particles.emit_rising(self.x, self.y, GOLD, 20, 1.2, 5)
            floating_texts.append(
                FloatingText(self.x, self.y - 50,
                             f"LEVEL {self.level}!", GOLD, 2.0, FONT_XL))

    def update_visuals(self, dt):
        """Update animation timers."""
        # Smooth health bar
        speed = 80 * dt
        if self.display_hp > self.hp:
            self.display_hp = max(self.hp, self.display_hp - speed)
        elif self.display_hp < self.hp:
            self.display_hp = min(self.hp, self.display_hp + speed)
        # Flash timer
        if self.flash_timer > 0:
            self.flash_timer -= dt
        # Idle pulse
        self.pulse_timer += dt
        # Anim offset decay
        self.anim_offset_x *= 0.9
        self.anim_offset_y *= 0.9


# ===========================================================================
# AI CONTROLLER
# ===========================================================================
class AIController:
    """Controls enemy team decisions with strategic behaviour."""

    def choose_action(self, unit, allies, enemies):
        """
        Returns (action, target) where action is 'attack', 'defend', or 'special'.
        Per spec: prefers Defend when HP < 50%.
        Enhanced: also considers tactical factors.
        """
        alive_enemies = [e for e in enemies if e.alive]
        if not alive_enemies:
            return ("defend", None)

        can_special = unit.special_cooldown == 0

        # Health ratio
        hp_ratio = unit.hp / unit.max_hp

        # Prefer defend when HP < 50% (per spec)
        if hp_ratio < 0.5:
            roll = random.random()
            if can_special and unit.special_type in ("heal", "team_heal"):
                # Prefer healing special when low HP
                return ("special", self._pick_target(unit, alive_enemies))
            elif roll < 0.55:
                return ("defend", None)
            elif can_special and roll < 0.75:
                return ("special", self._pick_target(unit, alive_enemies))
            else:
                return ("attack", self._pick_target(unit, alive_enemies))
        else:
            roll = random.random()
            if can_special and roll < 0.35:
                return ("special", self._pick_target(unit, alive_enemies))
            elif roll < 0.15:
                return ("defend", None)
            else:
                return ("attack", self._pick_target(unit, alive_enemies))

    def _pick_target(self, unit, enemies):
        """Pick a smart target - prefer low HP enemies."""
        # Sort by HP, pick lowest HP target with some randomness
        sorted_enemies = sorted(enemies, key=lambda e: e.hp)
        if random.random() < 0.7:
            return sorted_enemies[0]  # Target weakest
        return random.choice(enemies)


ai = AIController()


# ===========================================================================
# UI DRAWING HELPERS
# ===========================================================================
def draw_background(surface):
    """Draw a gradient battle arena background."""
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(15 + ratio * 20)
        g = int(10 + ratio * 25)
        b = int(35 + ratio * 30)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

    # Ground
    pygame.draw.rect(surface, (25, 30, 20),
                     (0, HEIGHT - 180, WIDTH, 180))
    for y in range(HEIGHT - 180, HEIGHT):
        ratio = (y - (HEIGHT - 180)) / 180
        r = int(25 + ratio * 15)
        g = int(30 + ratio * 10)
        b = int(20 + ratio * 10)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

    # Decorative grid lines on ground
    for i in range(0, WIDTH, 80):
        alpha = 20
        pygame.draw.line(surface, (40, 50, 35), (i, HEIGHT - 180),
                         (i - 60, HEIGHT), 1)


def draw_character_sprite(surface, char, selected=False, targetable=False):
    """Draw a character as an animated geometric sprite."""
    if not char.alive:
        return

    bx = char.x + char.anim_offset_x
    by = char.y + char.anim_offset_y

    # Idle breathing animation
    breath = math.sin(char.pulse_timer * 2) * 3

    # Flash effect
    col = char.colour
    if char.flash_timer > 0:
        flash_ratio = char.flash_timer / 0.3
        col = tuple(
            int(c * (1 - flash_ratio) + fc * flash_ratio)
            for c, fc in zip(char.colour, char.flash_colour)
        )

    # Shadow
    shadow_w = 40
    shadow_surf = pygame.Surface((shadow_w * 2, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60),
                        (0, 0, shadow_w * 2, 12))
    surface.blit(shadow_surf, (bx - shadow_w, by + 35))

    # Body (main triangle/shape)
    body_pts = [
        (bx, by - 35 + breath),
        (bx - 22, by + 25),
        (bx + 22, by + 25),
    ]
    pygame.draw.polygon(surface, col, body_pts)
    pygame.draw.polygon(surface, char.colour2, body_pts, 2)

    # Inner detail
    inner_pts = [
        (bx, by - 18 + breath),
        (bx - 10, by + 12),
        (bx + 10, by + 12),
    ]
    pygame.draw.polygon(surface, char.colour2, inner_pts)

    # Head circle
    head_y = int(by - 42 + breath)
    pygame.draw.circle(surface, col, (int(bx), head_y), 14)
    pygame.draw.circle(surface, char.colour2, (int(bx), head_y), 14, 2)

    # Eyes
    eye_col = WHITE if char.flash_timer <= 0 else char.flash_colour
    pygame.draw.circle(surface, eye_col, (int(bx) - 5, head_y - 1), 3)
    pygame.draw.circle(surface, eye_col, (int(bx) + 5, head_y - 1), 3)
    pygame.draw.circle(surface, BLACK, (int(bx) - 5, head_y - 1), 1)
    pygame.draw.circle(surface, BLACK, (int(bx) + 5, head_y - 1), 1)

    # Element indicator (small orbiting particle)
    orb_angle = char.pulse_timer * 3
    orb_x = bx + math.cos(orb_angle) * 28
    orb_y = by - 5 + math.sin(orb_angle) * 15
    pygame.draw.circle(surface, char.colour2, (int(orb_x), int(orb_y)), 4)
    pygame.draw.circle(surface, col, (int(orb_x), int(orb_y)), 2)

    # Defend shield effect
    if char.is_defending:
        shield_alpha = int(128 + 50 * math.sin(char.pulse_timer * 5))
        pygame.draw.arc(surface, CYAN,
                        (int(bx) - 30, int(by) - 45, 60, 80),
                        -0.5, 3.6, 3)

    # Fortify effect
    if char.fortify_turns > 0:
        pygame.draw.arc(surface, GOLD,
                        (int(bx) - 35, int(by) - 50, 70, 90),
                        0, 6.28, 2)

    # Selection highlight
    if selected:
        pygame.draw.circle(surface, GOLD, (int(bx), int(by)), 50, 3)

    # Targetable indicator
    if targetable:
        pygame.draw.circle(surface, RED, (int(bx), int(by)), 48, 2)
        # Crosshair
        pygame.draw.line(surface, RED, (int(bx) - 8, int(by)),
                         (int(bx) + 8, int(by)), 1)
        pygame.draw.line(surface, RED, (int(bx), int(by) - 8),
                         (int(bx), int(by) + 8), 1)

    # Name label
    name_surf = FONT_SM.render(char.name, True, WHITE)
    name_rect = name_surf.get_rect(center=(int(bx), int(by) + 48))
    surface.blit(name_surf, name_rect)

    # Level badge
    lvl_surf = FONT_SM.render(f"Lv{char.level}", True, GOLD)
    surface.blit(lvl_surf, (int(bx) - lvl_surf.get_width() // 2,
                            int(by) + 58))


def draw_health_bar(surface, char, x, y, width=100, height=10):
    """Draw an animated health bar with HP text."""
    # Background
    pygame.draw.rect(surface, DARK_GREY, (x, y, width, height), border_radius=3)

    # Damage preview (yellow bar showing recent damage)
    display_ratio = max(0, char.display_hp / char.max_hp)
    display_w = int(width * display_ratio)
    if display_w > 0:
        pygame.draw.rect(surface, (180, 150, 30),
                         (x, y, display_w, height), border_radius=3)

    # Current HP bar
    hp_ratio = max(0, char.hp / char.max_hp)
    hp_w = int(width * hp_ratio)
    # Colour gradient: green > yellow > red
    if hp_ratio > 0.5:
        bar_col = GREEN
    elif hp_ratio > 0.25:
        bar_col = GOLD
    else:
        bar_col = RED
    if hp_w > 0:
        pygame.draw.rect(surface, bar_col,
                         (x, y, hp_w, height), border_radius=3)

    # Border
    pygame.draw.rect(surface, LIGHT_GREY, (x, y, width, height), 1,
                     border_radius=3)

    # HP text
    hp_text = f"{max(0, char.hp)}/{char.max_hp}"
    txt_surf = FONT_SM.render(hp_text, True, WHITE)
    surface.blit(txt_surf, (x + width // 2 - txt_surf.get_width() // 2,
                            y + height + 2))

    # EXP bar (tiny)
    exp_y = y + height + 17
    exp_h = 4
    pygame.draw.rect(surface, DARK_GREY, (x, exp_y, width, exp_h),
                     border_radius=2)
    exp_w = int(width * (char.epx / 100))
    if exp_w > 0:
        pygame.draw.rect(surface, PURPLE, (x, exp_y, exp_w, exp_h),
                         border_radius=2)


def draw_button(surface, rect, text, colour=GREY, text_colour=WHITE,
                hover=False, disabled=False, font=None):
    """Draw a styled button. Returns the rect for click detection."""
    if font is None:
        font = FONT_MD
    r = pygame.Rect(rect)
    col = colour
    if disabled:
        col = tuple(max(20, c // 3) for c in colour)
        text_colour = (80, 80, 80)
    elif hover:
        col = tuple(min(255, c + 40) for c in colour)

    pygame.draw.rect(surface, col, r, border_radius=6)
    pygame.draw.rect(surface, WHITE if hover and not disabled else LIGHT_GREY,
                     r, 2, border_radius=6)

    txt = font.render(text, True, text_colour)
    txt_rect = txt.get_rect(center=r.center)
    surface.blit(txt, txt_rect)
    return r


def draw_panel(surface, rect, title=None, bg_colour=None):
    """Draw a dark panel with optional title."""
    r = pygame.Rect(rect)
    bg = bg_colour or (20, 22, 30, 200)
    panel = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
    panel.fill(bg)
    surface.blit(panel, r.topleft)
    pygame.draw.rect(surface, LIGHT_GREY, r, 1, border_radius=4)
    if title:
        title_surf = FONT_MD.render(title, True, GOLD)
        surface.blit(title_surf, (r.x + 10, r.y + 5))


# ===========================================================================
# GAME STATES
# ===========================================================================
STATE_TITLE       = "title"
STATE_SELECT      = "select"
STATE_BATTLE      = "battle"
STATE_PLAYER_TURN = "player_turn"
STATE_PICK_TARGET = "pick_target"
STATE_ENEMY_TURN  = "enemy_turn"
STATE_ANIMATING   = "animating"
STATE_GAME_OVER   = "game_over"


# ===========================================================================
# MAIN GAME CLASS
# ===========================================================================
class Game:
    """Main game controller managing all states, logic, and rendering."""

    def __init__(self):
        self.state = STATE_TITLE
        self.player_team = []
        self.enemy_team = []
        self.battle_log = []
        self.selected_unit = None
        self.current_action = None
        self.target_unit = None
        self.turn_queue = []
        self.current_turn_index = 0
        self.anim_timer = 0
        self.winner = None

        # Selection screen state
        self.available_chars = list(range(6))
        self.player_picks = []
        self.hover_char = None

        # Hover state for buttons
        self.hover_buttons = {}

        # Stars background
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT // 2),
                       random.uniform(0.5, 2)) for _ in range(80)]

    def reset(self):
        """Reset game to title screen."""
        self.__init__()

    def start_battle(self):
        """Initialize battle after team selection."""
        self.state = STATE_BATTLE

        # AI picks its team (random 3 from remaining or all)
        ai_indices = random.sample(range(6), 3)
        self.enemy_team = [Character(CHARACTER_TEMPLATES[i], "enemy")
                           for i in ai_indices]

        # Position characters
        for i, char in enumerate(self.player_team):
            char.x = 150 + i * 130
            char.y = HEIGHT - 310
        for i, char in enumerate(self.enemy_team):
            char.x = WIDTH - 150 - i * 130
            char.y = HEIGHT - 310

        # Build turn order
        self.build_turn_queue()
        self.battle_log = ["=== Battle Begins! ==="]
        self.advance_turn()

    def build_turn_queue(self):
        """Create alternating turn order: player units then enemy units."""
        alive_player = [c for c in self.player_team if c.alive]
        alive_enemy = [c for c in self.enemy_team if c.alive]
        self.turn_queue = []
        max_len = max(len(alive_player), len(alive_enemy))
        for i in range(max_len):
            if i < len(alive_player):
                self.turn_queue.append(alive_player[i])
            if i < len(alive_enemy):
                self.turn_queue.append(alive_enemy[i])
        self.current_turn_index = 0

    def advance_turn(self):
        """Move to next unit's turn."""
        # Check win conditions
        alive_player = [c for c in self.player_team if c.alive]
        alive_enemy = [c for c in self.enemy_team if c.alive]

        if not alive_enemy:
            self.winner = "player"
            self.state = STATE_GAME_OVER
            SFX_VICTORY.play()
            self.battle_log.append("=== VICTORY! You win! ===")
            return
        if not alive_player:
            self.winner = "enemy"
            self.state = STATE_GAME_OVER
            SFX_DEFEAT.play()
            self.battle_log.append("=== DEFEAT! Enemy wins! ===")
            return

        # Rebuild turn queue if we've gone through everyone
        if self.current_turn_index >= len(self.turn_queue):
            self.build_turn_queue()

        # Find next alive unit
        while self.current_turn_index < len(self.turn_queue):
            unit = self.turn_queue[self.current_turn_index]
            if unit.alive:
                break
            self.current_turn_index += 1

        if self.current_turn_index >= len(self.turn_queue):
            self.build_turn_queue()
            unit = self.turn_queue[0]

        unit.start_turn()
        self.selected_unit = unit

        if unit.team_side == "player":
            self.state = STATE_PLAYER_TURN
            self.battle_log.append(f"--- {unit.name}'s turn ---")
        else:
            self.state = STATE_ENEMY_TURN
            self.anim_timer = 0.8  # Brief pause before AI acts

    def execute_ai_turn(self):
        """Execute the AI's chosen action."""
        unit = self.selected_unit
        allies = [c for c in self.enemy_team if c.alive]
        enemies = [c for c in self.player_team if c.alive]

        if not enemies:
            self.advance_turn()
            return

        action, target = ai.choose_action(unit, allies, enemies)

        if action == "attack" and target:
            _, msgs = unit.perform_attack(target)
            self.battle_log.extend(msgs)
        elif action == "defend":
            msgs = unit.perform_defend()
            self.battle_log.extend(msgs)
        elif action == "special":
            if unit.special_type in ("heal", "fortify", "team_heal"):
                msgs = unit.perform_special(target=target, allies=allies,
                                            enemies=enemies)
            else:
                if target is None:
                    target = random.choice(enemies)
                msgs = unit.perform_special(target=target, allies=allies,
                                            enemies=enemies)
            self.battle_log.extend(msgs)

        # Post-action animation delay
        self.state = STATE_ANIMATING
        self.anim_timer = 1.0
        self.current_turn_index += 1

    def handle_player_action(self, action, target=None):
        """Execute the player's chosen action."""
        unit = self.selected_unit
        allies = [c for c in self.player_team if c.alive]
        enemies = [c for c in self.enemy_team if c.alive]

        if action == "attack" and target:
            _, msgs = unit.perform_attack(target)
            self.battle_log.extend(msgs)
        elif action == "defend":
            msgs = unit.perform_defend()
            self.battle_log.extend(msgs)
        elif action == "special":
            if unit.special_type in ("heal", "fortify", "team_heal"):
                msgs = unit.perform_special(allies=allies, enemies=enemies)
            else:
                msgs = unit.perform_special(target=target, allies=allies,
                                            enemies=enemies)
            self.battle_log.extend(msgs)

        self.state = STATE_ANIMATING
        self.anim_timer = 1.0
        self.current_turn_index += 1

    # -------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------
    def update(self, dt):
        """Update game logic each frame."""
        particles.update(dt)
        shake.update(dt)

        # Update floating texts
        global floating_texts
        for ft in floating_texts:
            ft.update(dt)
        floating_texts = [ft for ft in floating_texts if ft.alive]

        # Update character visuals
        all_chars = self.player_team + self.enemy_team
        for c in all_chars:
            c.update_visuals(dt)

        # State-specific updates
        if self.state == STATE_ENEMY_TURN:
            self.anim_timer -= dt
            if self.anim_timer <= 0:
                self.execute_ai_turn()

        elif self.state == STATE_ANIMATING:
            self.anim_timer -= dt
            if self.anim_timer <= 0:
                self.advance_turn()

    # -------------------------------------------------------------------
    # DRAW
    # -------------------------------------------------------------------
    def draw(self, surface):
        """Render the current game state."""
        ox, oy = shake.get_offset()

        if self.state == STATE_TITLE:
            self.draw_title(surface)
        elif self.state == STATE_SELECT:
            self.draw_select(surface)
        else:
            # Battle screen
            draw_background(surface)
            render_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

            self.draw_battle(render_surf)
            surface.blit(render_surf, (ox, oy))

    def draw_title(self, surface):
        """Draw the title screen."""
        # Background
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(10 + ratio * 15)
            g = int(5 + ratio * 10)
            b = int(30 + ratio * 40)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

        # Stars
        for sx, sy, brightness in self.stars:
            pulse = math.sin(pygame.time.get_ticks() / 1000 * brightness) * 0.3 + 0.7
            c = int(min(255, 150 * brightness * pulse))
            pygame.draw.circle(surface, (c, c, int(c * 0.8)),
                               (int(sx), int(sy)), max(1, int(brightness)))

        # Title
        t = pygame.time.get_ticks() / 1000
        title_y = 180 + math.sin(t * 1.5) * 8

        # Title glow
        glow_text = FONT_TITLE.render("MYTHICAL ELEMENTAL", True, GOLD)
        glow_rect = glow_text.get_rect(center=(WIDTH // 2, title_y))
        surface.blit(glow_text, glow_rect)

        sub_text = FONT_XL.render("WARRIORS", True, ORANGE)
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, title_y + 55))
        surface.blit(sub_text, sub_rect)

        # Subtitle
        sub2 = FONT_MD.render("A Turn-Based Battle Game", True, LIGHT_GREY)
        surface.blit(sub2, sub2.get_rect(center=(WIDTH // 2, title_y + 100)))

        # Start button
        mx, my = pygame.mouse.get_pos()
        btn_rect = pygame.Rect(WIDTH // 2 - 120, 420, 240, 55)
        hover = btn_rect.collidepoint(mx, my)
        pulse_size = int(math.sin(t * 3) * 3)
        btn_rect.inflate_ip(pulse_size, pulse_size)
        draw_button(surface, btn_rect, "START BATTLE", DARK_BLUE, WHITE,
                    hover, font=FONT_LG)

        # Character preview at bottom
        for i, tmpl in enumerate(CHARACTER_TEMPLATES):
            cx = 100 + i * 160
            cy = 580
            bob = math.sin(t * 2 + i * 0.8) * 5
            pygame.draw.circle(surface, tmpl["colour"],
                               (cx, int(cy + bob)), 18)
            pygame.draw.circle(surface, tmpl["colour2"],
                               (cx, int(cy + bob)), 18, 2)
            name_s = FONT_SM.render(tmpl["name"], True, tmpl["colour"])
            surface.blit(name_s, name_s.get_rect(center=(cx, cy + 35)))

        # Credits
        cred = FONT_SM.render("CS5001 Final Project", True, (80, 80, 100))
        surface.blit(cred, cred.get_rect(center=(WIDTH // 2, HEIGHT - 30)))

    def draw_select(self, surface):
        """Draw the character selection screen."""
        # Background
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            surface.fill((int(15 + ratio * 10), int(12 + ratio * 8),
                          int(35 + ratio * 20)),
                         (0, y, WIDTH, 1))

        # Title
        title = FONT_XL.render("CHOOSE YOUR WARRIORS (Pick 3)", True, GOLD)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 40)))

        mx, my = pygame.mouse.get_pos()

        # Character cards
        for i, idx in enumerate(range(6)):
            tmpl = CHARACTER_TEMPLATES[idx]
            card_x = 50 + (i % 3) * 350
            card_y = 90 + (i // 3) * 295
            card_w, card_h = 310, 270
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

            is_picked = idx in self.player_picks
            is_hover = card_rect.collidepoint(mx, my) and not is_picked

            # Card background
            bg_col = (30, 35, 50) if not is_picked else (20, 50, 30)
            if is_hover:
                bg_col = (45, 50, 70)
            draw_panel(surface, card_rect, bg_colour=(*bg_col, 220))

            if is_picked:
                pick_num = self.player_picks.index(idx) + 1
                badge = FONT_LG.render(f"#{pick_num}", True, GREEN)
                surface.blit(badge, (card_x + card_w - 40, card_y + 8))

            # Character icon
            icon_x = card_x + 50
            icon_y = card_y + 80
            pygame.draw.circle(surface, tmpl["colour"],
                               (icon_x, icon_y), 30)
            pygame.draw.circle(surface, tmpl["colour2"],
                               (icon_x, icon_y), 30, 3)
            # Eyes
            pygame.draw.circle(surface, WHITE, (icon_x - 8, icon_y - 3), 5)
            pygame.draw.circle(surface, WHITE, (icon_x + 8, icon_y - 3), 5)
            pygame.draw.circle(surface, BLACK, (icon_x - 8, icon_y - 3), 2)
            pygame.draw.circle(surface, BLACK, (icon_x + 8, icon_y - 3), 2)

            # Info
            name_s = FONT_LG.render(tmpl["name"], True, tmpl["colour"])
            surface.blit(name_s, (card_x + 95, card_y + 55))
            title_s = FONT_SM.render(tmpl["title"], True, LIGHT_GREY)
            surface.blit(title_s, (card_x + 95, card_y + 82))
            elem_s = FONT_SM.render(f"Element: {tmpl['element']}", True,
                                    tmpl["colour"])
            surface.blit(elem_s, (card_x + 95, card_y + 102))

            # Stats
            atk_avg = sum(tmpl["atk_range"]) / 2
            def_avg = sum(tmpl["def_range"]) / 2
            stats_y = card_y + 135

            surface.blit(FONT_SM.render("ATK", True, RED),
                         (card_x + 20, stats_y))
            bar_w = int((atk_avg / 35) * 150)
            pygame.draw.rect(surface, DARK_GREY,
                             (card_x + 60, stats_y + 2, 150, 12),
                             border_radius=3)
            pygame.draw.rect(surface, RED,
                             (card_x + 60, stats_y + 2, bar_w, 12),
                             border_radius=3)
            surface.blit(FONT_SM.render(
                f"{tmpl['atk_range'][0]}-{tmpl['atk_range'][1]}", True, WHITE),
                (card_x + 220, stats_y))

            stats_y += 22
            surface.blit(FONT_SM.render("DEF", True, BLUE),
                         (card_x + 20, stats_y))
            bar_w = int((def_avg / 28) * 150)
            pygame.draw.rect(surface, DARK_GREY,
                             (card_x + 60, stats_y + 2, 150, 12),
                             border_radius=3)
            pygame.draw.rect(surface, BLUE,
                             (card_x + 60, stats_y + 2, bar_w, 12),
                             border_radius=3)
            surface.blit(FONT_SM.render(
                f"{tmpl['def_range'][0]}-{tmpl['def_range'][1]}", True, WHITE),
                (card_x + 220, stats_y))

            # Special ability
            stats_y += 28
            surface.blit(FONT_SM.render(f"Special: {tmpl['special_name']}",
                                        True, GOLD), (card_x + 20, stats_y))
            stats_y += 18
            # Wrap special description
            desc = tmpl["special_desc"]
            surface.blit(FONT_SM.render(desc[:42], True, LIGHT_GREY),
                         (card_x + 20, stats_y))
            if len(desc) > 42:
                surface.blit(FONT_SM.render(desc[42:], True, LIGHT_GREY),
                             (card_x + 20, stats_y + 15))

        # Confirm button
        if len(self.player_picks) == 3:
            btn_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 60, 240, 45)
            hover = btn_rect.collidepoint(mx, my)
            draw_button(surface, btn_rect, "BEGIN BATTLE!", GREEN, WHITE,
                        hover, font=FONT_LG)

        # Instructions
        remaining = 3 - len(self.player_picks)
        if remaining > 0:
            inst = FONT_MD.render(
                f"Click to select {remaining} more warrior(s)",
                True, LIGHT_GREY)
            surface.blit(inst, inst.get_rect(center=(WIDTH // 2,
                                                     HEIGHT - 40)))

    def draw_battle(self, surface):
        """Draw the main battle screen."""
        alive_player = [c for c in self.player_team if c.alive]
        alive_enemy = [c for c in self.enemy_team if c.alive]
        mx, my = pygame.mouse.get_pos()

        # Team labels
        surface.blit(FONT_MD.render("YOUR TEAM", True, GREEN), (20, 10))
        surface.blit(FONT_MD.render("ENEMY TEAM", True, RED),
                     (WIDTH - 150, 10))

        # Draw all characters
        for c in self.player_team:
            is_selected = (c == self.selected_unit and
                           self.state in (STATE_PLAYER_TURN, STATE_PICK_TARGET))
            draw_character_sprite(surface, c, selected=is_selected)

        # Draw enemy characters (with targetable indicator)
        for c in self.enemy_team:
            is_target = (self.state == STATE_PICK_TARGET and c.alive)
            draw_character_sprite(surface, c, targetable=is_target)

        # Health bars for all characters
        for i, c in enumerate(self.player_team):
            if c.alive:
                draw_health_bar(surface, c, c.x - 50, c.y + 70, 100, 10)
        for i, c in enumerate(self.enemy_team):
            if c.alive:
                draw_health_bar(surface, c, c.x - 50, c.y + 70, 100, 10)

        # Particles and floating texts
        particles.draw(surface)
        for ft in floating_texts:
            ft.draw(surface)

        # === Bottom UI Panel ===
        panel_y = HEIGHT - 180
        draw_panel(surface, (0, panel_y, WIDTH, 180),
                   bg_colour=(15, 18, 25, 230))

        # Action buttons (only during player's turn)
        if self.state == STATE_PLAYER_TURN and self.selected_unit:
            unit = self.selected_unit
            btn_x = 20
            btn_y = panel_y + 15

            # Current unit info
            info = f"{unit.name} (Lv{unit.level}) - {unit.element}"
            surface.blit(FONT_MD.render(info, True, unit.colour),
                         (btn_x, btn_y))
            btn_y += 28

            # Attack button
            atk_rect = pygame.Rect(btn_x, btn_y, 160, 38)
            atk_hover = atk_rect.collidepoint(mx, my)
            draw_button(surface, atk_rect, "ATTACK", (150, 40, 40),
                        WHITE, atk_hover)

            # Defend button
            def_rect = pygame.Rect(btn_x + 170, btn_y, 160, 38)
            def_hover = def_rect.collidepoint(mx, my)
            draw_button(surface, def_rect, "DEFEND", (40, 100, 150),
                        WHITE, def_hover)

            # Special button
            sp_rect = pygame.Rect(btn_x, btn_y + 48, 330, 38)
            sp_hover = sp_rect.collidepoint(mx, my)
            sp_disabled = unit.special_cooldown > 0
            sp_text = f"{unit.special_name}"
            if sp_disabled:
                sp_text += f" (CD: {unit.special_cooldown})"
            draw_button(surface, sp_rect, sp_text, (120, 50, 150),
                        WHITE, sp_hover, sp_disabled)

            # Tooltip for special
            if sp_hover and not sp_disabled:
                tip = FONT_SM.render(unit.special_desc, True, GOLD)
                surface.blit(tip, (btn_x, btn_y + 90))

            self.hover_buttons = {
                "attack": (atk_rect, atk_hover),
                "defend": (def_rect, def_hover),
                "special": (sp_rect, sp_hover, sp_disabled),
            }
        elif self.state == STATE_PICK_TARGET:
            # Targeting mode instruction
            inst = FONT_LG.render("Click an enemy to target!", True, RED)
            surface.blit(inst, (20, panel_y + 15))
            cancel_rect = pygame.Rect(20, panel_y + 50, 160, 38)
            cancel_hover = cancel_rect.collidepoint(mx, my)
            draw_button(surface, cancel_rect, "CANCEL", DARK_RED, WHITE,
                        cancel_hover)
            self.hover_buttons = {"cancel": (cancel_rect, cancel_hover)}
        elif self.state == STATE_ENEMY_TURN:
            if self.selected_unit:
                info = f"{self.selected_unit.name} is thinking..."
                surface.blit(FONT_LG.render(info, True, RED),
                             (20, panel_y + 20))
            self.hover_buttons = {}
        elif self.state == STATE_ANIMATING:
            self.hover_buttons = {}
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over(surface, panel_y)
            self.hover_buttons = {}

        # === Battle Log ===
        log_x = 400
        log_y = panel_y + 10
        log_w = WIDTH - log_x - 15
        log_h = 165
        draw_panel(surface, (log_x, log_y, log_w, log_h),
                   title="Battle Log", bg_colour=(10, 12, 20, 200))

        # Show last ~7 log entries
        visible_log = self.battle_log[-7:]
        for i, entry in enumerate(visible_log):
            col = LIGHT_GREY
            if "defeat" in entry.lower():
                col = RED
            elif "heal" in entry.lower() or "restore" in entry.lower():
                col = GREEN
            elif "defend" in entry.lower():
                col = CYAN
            elif "===" in entry:
                col = GOLD
            elif "---" in entry:
                col = WHITE
            # Truncate long entries
            display = entry[:75]
            txt = FONT_SM.render(display, True, col)
            surface.blit(txt, (log_x + 10, log_y + 25 + i * 19))

        # Turn indicator at top
        if self.state not in (STATE_GAME_OVER,):
            turn_text = ""
            turn_col = WHITE
            if self.state in (STATE_PLAYER_TURN, STATE_PICK_TARGET):
                turn_text = "YOUR TURN"
                turn_col = GREEN
            elif self.state == STATE_ENEMY_TURN:
                turn_text = "ENEMY TURN"
                turn_col = RED
            elif self.state == STATE_ANIMATING:
                turn_text = "..."
                turn_col = GOLD

            indicator = FONT_LG.render(turn_text, True, turn_col)
            surface.blit(indicator,
                         indicator.get_rect(center=(WIDTH // 2, 18)))

    def draw_game_over(self, surface, panel_y):
        """Draw the game over overlay."""
        # Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        mx, my = pygame.mouse.get_pos()

        if self.winner == "player":
            text = "VICTORY!"
            colour = GOLD
        else:
            text = "DEFEAT!"
            colour = RED

        # Pulsing text
        t = pygame.time.get_ticks() / 1000
        scale = 1.0 + math.sin(t * 3) * 0.05
        big_font = pygame.font.SysFont("consolas", int(64 * scale), bold=True)
        txt = big_font.render(text, True, colour)
        surface.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))

        # Stats summary
        stats_y = HEIGHT // 2
        for c in self.player_team:
            status = f"{'ALIVE' if c.alive else 'FALLEN'}"
            col = GREEN if c.alive else RED
            line = f"{c.name} Lv{c.level} - {status}"
            txt = FONT_MD.render(line, True, col)
            surface.blit(txt, txt.get_rect(center=(WIDTH // 2, stats_y)))
            stats_y += 25

        # Buttons
        retry_rect = pygame.Rect(WIDTH // 2 - 130, stats_y + 20, 120, 42)
        retry_hover = retry_rect.collidepoint(mx, my)
        draw_button(surface, retry_rect, "RETRY", GREEN, WHITE, retry_hover)

        quit_rect = pygame.Rect(WIDTH // 2 + 10, stats_y + 20, 120, 42)
        quit_hover = quit_rect.collidepoint(mx, my)
        draw_button(surface, quit_rect, "QUIT", RED, WHITE, quit_hover)

        self.hover_buttons = {
            "retry": (retry_rect, retry_hover),
            "quit": (quit_rect, quit_hover),
        }

    # -------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------
    def handle_event(self, event):
        """Process a single pygame event."""
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            self.handle_click(mx, my)

        return True

    def handle_click(self, mx, my):
        """Handle mouse click based on current state."""

        if self.state == STATE_TITLE:
            btn_rect = pygame.Rect(WIDTH // 2 - 120, 420, 240, 55)
            if btn_rect.collidepoint(mx, my):
                SFX_SELECT.play()
                self.state = STATE_SELECT
                self.player_picks = []

        elif self.state == STATE_SELECT:
            # Check character cards
            for i in range(6):
                card_x = 50 + (i % 3) * 350
                card_y = 90 + (i // 3) * 295
                card_rect = pygame.Rect(card_x, card_y, 310, 270)
                if card_rect.collidepoint(mx, my):
                    if i in self.player_picks:
                        self.player_picks.remove(i)
                        SFX_CLICK.play()
                    elif len(self.player_picks) < 3:
                        self.player_picks.append(i)
                        SFX_SELECT.play()

            # Confirm button
            if len(self.player_picks) == 3:
                btn_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 60, 240, 45)
                if btn_rect.collidepoint(mx, my):
                    SFX_SELECT.play()
                    self.player_team = [
                        Character(CHARACTER_TEMPLATES[i], "player")
                        for i in self.player_picks
                    ]
                    self.start_battle()

        elif self.state == STATE_PLAYER_TURN:
            # Check action buttons
            if "attack" in self.hover_buttons:
                rect, hover = self.hover_buttons["attack"]
                if rect.collidepoint(mx, my):
                    SFX_CLICK.play()
                    self.current_action = "attack"
                    self.state = STATE_PICK_TARGET

            if "defend" in self.hover_buttons:
                rect, hover = self.hover_buttons["defend"]
                if rect.collidepoint(mx, my):
                    SFX_CLICK.play()
                    self.handle_player_action("defend")

            if "special" in self.hover_buttons:
                rect, hover, disabled = self.hover_buttons["special"]
                if rect.collidepoint(mx, my) and not disabled:
                    SFX_CLICK.play()
                    unit = self.selected_unit
                    if unit.special_type in ("heal", "fortify", "team_heal"):
                        # Self/team targeted - no target needed
                        self.handle_player_action("special")
                    else:
                        self.current_action = "special"
                        self.state = STATE_PICK_TARGET

        elif self.state == STATE_PICK_TARGET:
            # Cancel button
            if "cancel" in self.hover_buttons:
                rect, hover = self.hover_buttons["cancel"]
                if rect.collidepoint(mx, my):
                    SFX_CLICK.play()
                    self.state = STATE_PLAYER_TURN
                    return

            # Check if clicking on an enemy character
            for c in self.enemy_team:
                if c.alive:
                    dist = math.sqrt((mx - c.x) ** 2 + (my - c.y) ** 2)
                    if dist < 48:
                        SFX_CLICK.play()
                        self.handle_player_action(self.current_action,
                                                  target=c)
                        return

        elif self.state == STATE_GAME_OVER:
            if "retry" in self.hover_buttons:
                rect, hover = self.hover_buttons["retry"]
                if rect.collidepoint(mx, my):
                    SFX_SELECT.play()
                    self.reset()
            if "quit" in self.hover_buttons:
                rect, hover = self.hover_buttons["quit"]
                if rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()


# ===========================================================================
# MAIN LOOP
# ===========================================================================
def main():
    """Entry point - runs the main game loop."""
    game = Game()
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)  # Cap delta time

        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False

        game.update(dt)

        screen.fill(BLACK)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
