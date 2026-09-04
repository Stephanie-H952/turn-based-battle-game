import pygame
import random
from Button import Button
from Character import Player, Enemy, Special_1, Special_2, Special_3, Special_4, Special_5, Special_6

# -------------------------------------------------------------------------------------------------
# Initialize pygame and audio
# -------------------------------------------------------------------------------------------------
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

# -------------------------------------------------------------------------------------------------
# Screen settings
# -------------------------------------------------------------------------------------------------
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Turn-Based Battle Game")
background = pygame.transform.scale(
    pygame.image.load("image/bg7.jpg").convert(),
    (WIDTH, HEIGHT)
)

clock = pygame.time.Clock()

# -------------------------------------------------------------------------------------------------
# Colors
# -------------------------------------------------------------------------------------------------
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GOODBLUE   = (40,  100, 230)
RED        = (200, 50,  50 )
GREEN      = (50,  180, 50 )
BLUE       = (50,  100, 200)
DARK_GRAY  = (180, 180, 200)
YELLOW     = (220, 220, 50 )
LIGHT_BLUE = (160, 210, 255)
ORANGE     = (255, 180, 50 )

# -------------------------------------------------------------------------------------------------
# Fonts
# -------------------------------------------------------------------------------------------------
title_font = pygame.font.SysFont(None, 52)
font       = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont(None, 24)

# -------------------------------------------------------------------------------------------------
# Layout positions
# All coordinate constants live here so they are easy to adjust in one place.
# -------------------------------------------------------------------------------------------------
HERO_X   = [90,  330]
GOBLIN_X = [700, 940]
CHAR_Y   = 120

HERO_SEL_X   = [10, 200, 390]
GOBLIN_SEL_X = [620, 800, 990]
SEL_CHAR_Y   = 250

TEAM_LABEL_Y   = 85
DIVIDER_X      = WIDTH // 2
ACTION_PANEL_RECT = pygame.Rect(40, 560, 330, 190)
LOG_RECT          = pygame.Rect(400, 560, 760, 190)
BUTTON_Y          = 625
RESTART_RECT      = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 - 25, 150, 50)

# Delay (ms) before the enemy carries out its action each turn
ENEMY_ACTION_DELAY = 1800


# -------------------------------------------------------------------------------------------------
# Asset loading helpers
# -------------------------------------------------------------------------------------------------
def load_image(path, w, h):
    """
    Load and scale an image from disk.
    Returns None silently if the file is missing or unreadable.
    """
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (w, h))
    except (pygame.error, FileNotFoundError):
        return None


def load_sound(path, volume=1.0):
    """
    Load a sound effect from disk and set its volume.
    Returns None if the mixer is unavailable or the file is missing.
    """
    if not pygame.mixer.get_init():
        return None
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        return sound
    except (pygame.error, FileNotFoundError):
        return None


def play_sound(sound):
    """Play a sound only if it was loaded successfully."""
    if sound is not None:
        sound.play()


def start_bgm():
    """
    Start looping background music.
    Does nothing if the mixer is unavailable or the file is missing.
    """
    if not pygame.mixer.get_init():
        return
    try:
        pygame.mixer.music.load("sound/bgm2.mp3")
        pygame.mixer.music.set_volume(0.25)
        pygame.mixer.music.play(-1)
    except (pygame.error, FileNotFoundError):
        pass


# -------------------------------------------------------------------------------------------------
# Sound assets
# Each character has its own attack sound keyed by name.
# -------------------------------------------------------------------------------------------------
ACTION_SOUNDS = {
    "Orangecat": load_sound("sound/magic.mp3",    0.2),
    "Applecat":  load_sound("sound/bow_shoot.mp3", 0.5),
    "Bananacat": load_sound("sound/sword.mp3",    0.3),
    "Drog":      load_sound("sound/knife.mp3",    0.3),
    "Cheems":    load_sound("sound/gunshot.mp3",  0.2),
    "Witchdog":  load_sound("sound/lightning.mp3", 0.3),
}
DEFENSE_SOUND = load_sound("sound/defense.mp3",  0.3)
WIN_SOUND  = load_sound("sound/yay.mp3",  0.5)
LOSE_SOUND = load_sound("sound/bell.mp3", 0.5)
HEAL_SOUND = load_sound("sound/heal.mp3", 0.4)


def play_action_sound(character):
    """Play the attack sound for this character (if any)."""
    play_sound(ACTION_SOUNDS.get(character.name))


def play_special_sound(character):
    """
    Play the appropriate sound for a special skill.
    Healing-type skills use the heal sound; all others use the attack sound.
    """
    if character.name in ("Orangecat", "Witchdog"):
        play_sound(HEAL_SOUND)
    else:
        play_action_sound(character)

def play_defense_sound(character):
    play_sound(DEFENSE_SOUND)


# -------------------------------------------------------------------------------------------------
# Draw helpers
# -------------------------------------------------------------------------------------------------
def draw_character(surface, character, x, y, fallback_color, is_active=False, is_target=False):
    """
    Draw one character card at position (x, y).

    Renders (in order):
    1. Yellow highlight border  — when this character is taking their turn
    2. Orange highlight border  — when this character is a selected target
    3. Name label
    4. Sprite image (or a solid rectangle if the image is missing)
    5. HP bar
    6. EXP bar with level label

    Parameters
    ----------
    surface       : pygame.Surface to draw on
    character     : Character instance to render
    x, y          : top-left anchor position
    fallback_color: color rectangle drawn if no sprite image is loaded
    is_active     : True if this character is currently acting (yellow border)
    is_target     : True if this character is currently being targeted (orange border)
    """
    # Skip dead characters entirely
    if not character.is_alive():
        return

    ox       = character.shake_offset()
    slot_w   = max(character.sprite_w, 120)
    center_x = x + slot_w // 2

    # Active-turn border (yellow)
    if is_active:
        pygame.draw.rect(
            surface, YELLOW,
            (x + ox - 4, y - 4, slot_w + 8, character.sprite_h + 32),
            3, border_radius=10
        )

    # Target border (orange)
    if is_target:
        pygame.draw.rect(
            surface, ORANGE,
            (x + ox - 4, y - 4, slot_w + 8, character.sprite_h + 32),
            3, border_radius=10
        )

    # Name label above the sprite
    name_surf = small_font.render(character.name, True, WHITE)
    surface.blit(name_surf, (center_x + ox - name_surf.get_width() // 2, y))

    # Sprite: use current action image, fall back to base, then solid rectangle
    img = character.images.get(character.current_action) or character.images.get("base")
    if img:
        surface.blit(img, (x + ox, y + 18))
    else:
        pygame.draw.rect(
            surface, fallback_color,
            (x + ox, y + 18, character.sprite_w, character.sprite_h),
            border_radius=10
        )

    # ---------- HP bar ----------
    bar_w = 100
    bar_h = 12
    bar_y = y + 230
    bar_x = center_x - bar_w // 2

    # Background (red = missing HP), foreground (green = current HP)
    pygame.draw.rect(surface, RED,   (bar_x, bar_y, bar_w, bar_h))
    hp_ratio = character.hp / character.max_hp
    pygame.draw.rect(surface, GREEN, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
    pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

    hp_text = small_font.render(f"{character.hp}/{character.max_hp}", True, WHITE)
    surface.blit(hp_text, (center_x - hp_text.get_width() // 2, bar_y + 14))

    # ---------- EXP bar ----------
    exp_y    = bar_y + 60
    exp_ratio = min(1, character.exp / 100)

    level_text1 = small_font.render(f"Lv {character.level}", True, WHITE)
    surface.blit(level_text1, (bar_x, exp_y - 18))

    pygame.draw.rect(surface, DARK_GRAY, (bar_x, exp_y, bar_w, bar_h))
    pygame.draw.rect(surface, GOODBLUE,  (bar_x, exp_y, int(bar_w * exp_ratio), bar_h))
    pygame.draw.rect(surface, WHITE,     (bar_x, exp_y, bar_w, bar_h), 1)

    exp_text = small_font.render(f"EXP {character.exp}/100", True, WHITE)
    surface.blit(exp_text, (bar_x, exp_y + bar_h + 4))


def draw_log(surface, log_messages):
    """
    Draw the battle log panel showing the most recent messages.
    Displays up to 6 lines of text.
    """
    pygame.draw.rect(surface, LIGHT_BLUE, LOG_RECT, border_radius=10)
    pygame.draw.rect(surface, BLACK,      LOG_RECT, 2, border_radius=10)

    title = font.render("Battle Log", True, WHITE)
    surface.blit(title, (LOG_RECT.x + 10, LOG_RECT.y + 10))

    start_y = LOG_RECT.y + 45
    for i, msg in enumerate(log_messages[-6:]):
        text_surface = small_font.render(str(msg), True, WHITE)
        surface.blit(text_surface, (LOG_RECT.x + 10, start_y + i * 24))


# -------------------------------------------------------------------------------------------------
# Battle helpers
# -------------------------------------------------------------------------------------------------
def special_target_for(character, opponents):
    """
    Determine the target for a special skill.

    If the skill is self-targeting, return the caster.
    Otherwise, return one random alive opponent.
    Returns None if there are no alive opponents.
    """
    if getattr(character.skill, "target_self", False):
        return character

    alive_opponents = [opp for opp in opponents if opp.is_alive()]
    if not alive_opponents:
        return None
    return random.choice(alive_opponents)


def goblin_act(goblin, heroes, battle_log):
    """
    Enemy AI: pick one action and execute it.

    Decision weights:
    - Low HP (< 50 %): favors defending  [defend 50%, attack 30%, special 20%]
    - Normal HP:       favors attacking   [attack 60%, defend 20%, special 20%]

    If the chosen action is "special" but the skill is still on cooldown,
    the goblin falls through to a normal attack instead.
    """
    alive_heroes = [h for h in heroes if h.is_alive()]
    if not alive_heroes:
        return

    # Clear any leftover defend state from the previous turn
    goblin.stop_defending()

    # Choose action probabilities based on current HP
    if goblin.hp < goblin.max_hp * 0.5:
        choices = ["defend", "attack", "special"]
        weights = [0.5, 0.3, 0.2]
    else:
        choices = ["attack", "defend", "special"]
        weights = [0.6, 0.2, 0.2]

    action = random.choices(choices, weights=weights, k=1)[0]

    if action == "special" and goblin.special_cooldown == 0:
        # Use special skill on an appropriate target
        target = special_target_for(goblin, heroes)
        result = goblin.use_special(target)
        if result is not None:
            battle_log.append(result)
        play_special_sound(goblin)
        goblin.trigger_action("special")

    elif action == "defend":
        goblin.defend()
        battle_log.append(f"{goblin.name} used DEFEND.")
        play_defense_sound(goblin)
        goblin.trigger_action("defend")

    else:
        # Normal attack (also used as fallback when special is on cooldown)
        target = random.choice(alive_heroes)
        damage = goblin.attack_target(target)

        if target.last_defended:
            battle_log.append(f"{target.name} defended! {goblin.name} dealt only {damage} dmg.")
        else:
            battle_log.append(f"{goblin.name} dealt {damage} dmg to {target.name}.")

        play_action_sound(goblin)
        goblin.trigger_action("attack")

    goblin.reduce_cooldown()


def create_all_characters():
    """
    Create all six characters (3 heroes + 3 goblins) and attach their sprites.

    Sprite images are loaded from the image/ folder using each character's
    lowercase name (e.g. "orangecat_base.png").
    Returns (heroes list, goblins list).
    """
    heroes = [
        Player("Orangecat", 100, (20, 30), (5, 11),  Special_2()),   # magic attacker, moderate def
        Player("Applecat",  100, (15, 25), (7, 13),  Special_3()),   # balanced attacker
        Player("Bananacat", 100, (25, 35), (2, 6),   Special_1()),   # heavy attacker, low def
    ]

    goblins = [
        Enemy("Drog",     100, (25, 35), (3, 9),   Special_4()),    # heavy attacker
        Enemy("Cheems",   100, (15, 25), (7, 13),  Special_5()),    # balanced fighter
        Enemy("Witchdog", 100, (20, 30), (2, 8),   Special_6()),    # magic type, low def
    ]

    # Sprite dimensions per character
    hero_sizes = {
        "Orangecat": (180, 180),
        "Applecat":  (180, 180),
        "Bananacat": (220, 180),
    }
    goblin_sizes = {
        "Drog":     (150, 150),
        "Cheems":   (160, 160),
        "Witchdog": (210, 160),
    }

    # Loop through every hero and attach their 4 action sprites
    # (base, attack, defend, special). load_image() returns None if a
    # file is missing, so a missing sprite will simply not be drawn.
    for hero in heroes:
        n = hero.name.lower()
        w, h = hero_sizes[hero.name]
        hero.sprite_w, hero.sprite_h = w, h
        hero.images["base"]    = load_image(f"image/{n}_base.png",    w, h)
        hero.images["attack"]  = load_image(f"image/{n}_attack.png",  w, h)
        hero.images["defend"]  = load_image(f"image/{n}_defend.png",  w, h)
        hero.images["special"] = load_image(f"image/{n}_special.png", w, h)

    # Same sprite-loading loop for every goblin
    for goblin in goblins:
        n = goblin.name.lower()
        w, h = goblin_sizes[goblin.name]
        goblin.sprite_w, goblin.sprite_h = w, h
        goblin.images["base"]    = load_image(f"image/{n}_base.png",    w, h)
        goblin.images["attack"]  = load_image(f"image/{n}_attack.png",  w, h)
        goblin.images["defend"]  = load_image(f"image/{n}_defend.png",  w, h)
        goblin.images["special"] = load_image(f"image/{n}_special.png", w, h)

    return heroes, goblins


def character_select_screen(all_heroes, all_goblins):
    """
    Show the character selection screen.

    The player clicks to choose exactly 2 heroes, then clicks Start.
    The enemy team of 2 goblins is chosen randomly.

    Returns (selected_heroes, selected_goblins) as lists of Character objects.
    """
    hero_selected = []   # holds indices of chosen heroes (max 2)

    start_button = Button(
        WIDTH // 2 - 80, HEIGHT - 85, 160, 50,
        text="Start Battle",
        bg_color=GREEN,
        text_color=WHITE,
        font=font,
    )

    # Keep showing the selection screen until the player confirms their team.
    # This is an infinite loop that only exits via return when Start is clicked.
    while True:
        clock.tick(60)

        # Process every pending input event from the OS (clicks, window close, etc.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User closed the window — shut down pygame and exit immediately
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # Loop through each hero card to check if the click lands on it.
                # i is the index of the hero in all_heroes (0, 1, or 2).
                for i, hero in enumerate(all_heroes):
                    slot_w = max(hero.sprite_w, 120)
                    hit = pygame.Rect(HERO_SEL_X[i], SEL_CHAR_Y, slot_w, hero.sprite_h + 20)

                    if hit.collidepoint(mx, my):
                        if i in hero_selected:
                            # Hero was already selected — deselect it (toggle off)
                            hero_selected.remove(i)
                        elif len(hero_selected) < 2:
                            # Slot is free and limit not reached — select this hero
                            hero_selected.append(i)

                # Start button becomes active only when exactly 2 heroes are chosen.
                # The boolean (len == 2) guards against starting with fewer heroes.
                if len(hero_selected) == 2 and start_button.is_clicked((mx, my)):
                    # Randomly pick 2 out of 3 goblins for the enemy team
                    goblin_selected = sorted(random.sample(range(3), 2))
                    return (
                        [all_heroes[i] for i in sorted(hero_selected)],
                        [all_goblins[i] for i in goblin_selected],
                    )

        # ---------- Draw selection screen ----------
        screen.blit(background, (0, 0))

        title_surf = title_font.render("Select Your Team", True, WHITE)
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 20))

        inst_surf = font.render(
            "Click to choose 2 heroes  |  Enemy team is chosen at random",
            True, DARK_GRAY
        )
        screen.blit(inst_surf, (WIDTH // 2 - inst_surf.get_width() // 2, 78))

        pygame.draw.line(screen, WHITE, (DIVIDER_X, 110), (DIVIDER_X, 660), 2)

        hl = font.render("Heroes",  True, YELLOW)
        gl = font.render("Goblins", True, ORANGE)
        screen.blit(hl, (DIVIDER_X // 2           - hl.get_width() // 2, 115))
        screen.blit(gl, (DIVIDER_X + DIVIDER_X // 2 - gl.get_width() // 2, 115))

        # Loop through all heroes and draw each card.
        # is_active=True (i in hero_selected) adds a yellow border to selected heroes.
        for i, hero in enumerate(all_heroes):
            draw_character(screen, hero, HERO_SEL_X[i], SEL_CHAR_Y, BLUE, is_active=(i in hero_selected))

        # Goblins are shown for preview only — no selection needed here
        for i, goblin in enumerate(all_goblins):
            draw_character(screen, goblin, GOBLIN_SEL_X[i], SEL_CHAR_Y, RED)

        count_surf = font.render(f"Heroes selected: {len(hero_selected)} / 2", True, WHITE)
        screen.blit(count_surf, (40, HEIGHT - 90))

        # Pass the boolean (len == 2) to draw(): button is greyed out until 2 are chosen
        start_button.draw(screen, len(hero_selected) == 2)
        pygame.display.flip()


def create_new_game(heroes, goblins):
    """
    Initialize a fresh battle and return the starting game state.
    Returns (heroes, goblins, battle_log).
    """
    battle_log = ["The battle begins!"]
    return heroes, goblins, battle_log


def next_alive(characters, start_idx):
    """
    Find the index of the next living character starting from start_idx.

    Wraps around the list, so if start_idx is out of bounds it is
    normalised with % n before searching.
    Returns None if no character in the list is alive.
    """
    n = len(characters)
    if n == 0:
        return None

    i = start_idx % n

    for _ in range(n):
        if characters[i].is_alive():
            return i
        i = (i + 1) % n

    return None   # every character is dead


def random_alive_enemy(enemies):
    """
    Return one random alive enemy, or None if all are defeated.
    Used for the player's normal attack to pick a target.
    """
    alive_enemies = [e for e in enemies if e.is_alive()]
    if not alive_enemies:
        return None
    return random.choice(alive_enemies)


# -------------------------------------------------------------------------------------------------
# Main game loop
# This is the entry point of the game.
# It contains:
# - reset_battle_state()  : restarts the game by recreating characters and running selection screen
# - finish_hero_turn()    : advances to the next alive hero and starts the turn transition timer
# - finish_player_action(): shared cleanup after any player action (attack / defend / special)
# - end_game()            : marks the game as over and plays the win/lose sound
#
# Main logic flow:
# 1. Show character selection screen; player picks 2 heroes, enemy team is chosen randomly
# 2. Enter the main loop:
#    a. Player turn  — player clicks Attack / Defend / Special for each hero one at a time
#    b. Transition   — short delay (1000 ms) after the last hero acts before enemy goes
#    c. Enemy turn   — one goblin acts automatically (AI), then rotates to the next goblin
#    d. Win/Lose check — if all goblins are dead → You Win; if all heroes are dead → You Lose
# 3. Once game over, a Restart button appears to replay from the selection screen
# -------------------------------------------------------------------------------------------------
def main():
    start_bgm()

    # ----------------------------------------------------------------
    # Helper: run character selection and set up a fresh battle
    # ----------------------------------------------------------------
    def reset_battle_state():
        all_heroes, all_goblins = create_all_characters()
        selected_heroes, selected_goblins = character_select_screen(all_heroes, all_goblins)
        return create_new_game(selected_heroes, selected_goblins)

    heroes, goblins, battle_log = reset_battle_state()

    # ----------------------------------------------------------------
    # Turn state variables
    # ----------------------------------------------------------------
    player_turn      = True
    current_hero_idx = next_alive(heroes, 0)   # index of the hero currently acting

    # turn_transition: a short delay between the last hero's action and the enemy turn
    turn_transition       = False
    turn_transition_timer = 0
    TURN_TRANSITION_DELAY = 1000               # ms

    current_goblin_idx = 0          # tracks which goblin acts next (rotates each enemy turn)
    enemy_action_timer = 0          # countdown before the enemy performs its action

    game_over    = False
    winner_text  = ""

    # ----------------------------------------------------------------
    # Action buttons
    # ----------------------------------------------------------------
    attack_button = Button(
        ACTION_PANEL_RECT.x + 20,  BUTTON_Y, 70, 90,
        text="Attack",
        text_color=WHITE,
        font=font,
        image_path="image/sword.png"
    )

    defend_button = Button(
        ACTION_PANEL_RECT.x + 115, BUTTON_Y, 95, 90,
        text="Defend",
        text_color=WHITE,
        font=font,
        image_path="image/shield.png"
    )

    special_button = Button(
        ACTION_PANEL_RECT.x + 240, BUTTON_Y, 60, 90,
        text="Special",
        text_color=WHITE,
        font=font,
        image_path="image/special.png"
    )

    restart_button = Button(
        RESTART_RECT.x, RESTART_RECT.y,
        RESTART_RECT.width, RESTART_RECT.height,
        "Restart", GREEN
    )

    # ----------------------------------------------------------------
    # Inner helpers for turn management
    # ----------------------------------------------------------------
    def finish_hero_turn():
        """
        Advance to the next living hero and start the transition timer.
        The transition timer adds a brief pause before control passes to the enemy.
        """
        nonlocal current_hero_idx, turn_transition, turn_transition_timer

        # Move to the next alive hero (wraps around the list)
        next_idx = next_alive(heroes, current_hero_idx + 1)
        if next_idx is not None:
            current_hero_idx = next_idx

        turn_transition       = True
        turn_transition_timer = TURN_TRANSITION_DELAY

    def finish_player_action(hero, action_name):
        """
        Shared cleanup called after any player action (attack / defend / special).
        Reduces cooldown, triggers the action animation, and ends the hero's turn.
        """
        hero.reduce_cooldown()
        hero.trigger_action(action_name)
        finish_hero_turn()

    def end_game(text, sound):
        """Mark the game as over, store the result text, and play the outcome sound."""
        nonlocal game_over, winner_text
        game_over   = True
        winner_text = text
        play_sound(sound)

    # ================================================================
    # Main loop
    # ================================================================
    # running is a boolean flag that keeps the game alive.
    # Setting running = False anywhere will cleanly exit the loop
    # and reach pygame.quit() at the bottom.
    running = True
    while running:
        # dt = time elapsed since last frame in milliseconds (e.g. ~16 ms at 60 fps).
        # Used to count down timers in a frame-rate-independent way.
        dt = clock.tick(60)

        # Loop through every character on both teams each frame to tick their
        # shake animation timer. When the timer hits 0, the sprite returns to "base".
        for c in heroes + goblins:
            c.update(dt)

        # ============================================================
        # Event handling
        # ============================================================
        # pygame.event.get() returns all events queued since the last frame.
        # We loop through each one and respond to the ones we care about.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Player closed the window — set running to False to exit the main loop
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos

                # ---- Restart button (only visible after game over) ----
                # game_over is True means the battle has ended.
                # Only then should a click on Restart be registered.
                if game_over and restart_button.is_clicked(mouse_pos):
                    heroes, goblins, battle_log = reset_battle_state()
                    # Reset all boolean flags and counters back to their initial values
                    player_turn           = True    # player always goes first on a new game
                    current_hero_idx      = next_alive(heroes, 0)
                    turn_transition       = False   # no transition in progress
                    turn_transition_timer = 0
                    current_goblin_idx    = 0
                    enemy_action_timer    = 0
                    game_over             = False   # clear game-over state
                    winner_text           = ""
                    start_bgm()

                # ---- Player action buttons (only active on player's turn) ----
                # All four conditions must be True before we accept a button click:
                #   player_turn       : it is the player's turn
                #   not turn_transition: we are not in the brief pause between turns
                #   not game_over     : the battle is still ongoing
                #   current_hero_idx is not None: at least one hero is still alive
                if player_turn and not turn_transition and not game_over and current_hero_idx is not None:
                    hero = heroes[current_hero_idx]
                    if not hero.is_alive():
                        current_hero_idx = next_alive(heroes, current_hero_idx + 1)
                        if current_hero_idx is None:
                            continue  # no heroes left, skip action
                        hero = heroes[current_hero_idx]

                    # Attack: hit a random alive enemy
                    if attack_button.is_clicked(mouse_pos):
                        goblin = random_alive_enemy(goblins)
                        if goblin is not None:
                            hero.stop_defending()
                            damage = hero.attack_target(goblin)

                            # goblin.last_defended is True if the goblin had defend active
                            # when it received this hit — show a different log message
                            if goblin.last_defended:
                                battle_log.append(f"{goblin.name} defended! {hero.name} dealt only {damage} dmg.")
                            else:
                                battle_log.append(f"{hero.name} attacked {goblin.name} for {damage} dmg.")

                            play_action_sound(hero)
                            finish_player_action(hero, "attack")

                    # Defend: enter defense state for the next incoming hit
                    elif defend_button.is_clicked(mouse_pos):
                        hero.defend()
                        battle_log.append(f"{hero.name} used DEFEND.")
                        play_defense_sound(hero)
                        finish_player_action(hero, "defend")

                    # Special: use skill only if the cooldown counter has reached 0
                    elif special_button.is_clicked(mouse_pos):
                        if hero.special_cooldown > 0:
                            # Cooldown > 0 means skill is not ready yet.
                            # Log the message but do NOT call finish_player_action —
                            # the turn is not consumed and the player can try again.
                            battle_log.append(
                                f"Special not ready. Cooldown: {hero.special_cooldown} turn(s)."
                            )
                        else:
                            # Cooldown == 0: skill is ready to use
                            target = special_target_for(hero, goblins)
                            if target is not None:
                                hero.stop_defending()
                                result = hero.use_special(target)

                                # use_special() returns a log string; append it if not None
                                if result is not None:
                                    battle_log.append(result)

                                play_special_sound(hero)
                                finish_player_action(hero, "special")

        # ============================================================
        # Win check  (checked before enemy acts so a killing blow ends the game)
        # ============================================================
        # all(...) returns True only when every goblin's is_alive() is False.
        # The second boolean "not game_over" prevents triggering end_game() twice.
        if all(not g.is_alive() for g in goblins) and not game_over:
            end_game("You Win!", WIN_SOUND)

        # ============================================================
        # Transition: short pause between last hero action and enemy turn
        # ============================================================
        # turn_transition is set to True by finish_hero_turn() after a hero acts.
        # Each frame we count down the timer using dt.
        # When it reaches 0, we flip player_turn to False (enemy's turn begins).
        if turn_transition and not game_over:
            turn_transition_timer -= dt
            if turn_transition_timer <= 0:
                turn_transition    = False   # pause is over
                player_turn        = False   # hand control to the enemy
                enemy_action_timer = ENEMY_ACTION_DELAY  # start enemy delay countdown

        # ============================================================
        # Enemy turn: one goblin acts, then control returns to the player
        # ============================================================
        # not player_turn means it is currently the enemy's turn.
        # We wait out the enemy_action_timer before goblin_act() is called,
        # giving the player a moment to see what just happened.
        if not player_turn and not game_over:
            enemy_action_timer -= dt
            if enemy_action_timer <= 0:
                # Find the next alive goblin starting from current_goblin_idx
                alive_goblin_idx = next_alive(goblins, current_goblin_idx)

                if alive_goblin_idx is not None:
                    current_goblin_idx = alive_goblin_idx
                    goblin_act(goblins[current_goblin_idx], heroes, battle_log)

                    # Advance the goblin pointer so the NEXT enemy turn
                    # starts from the following goblin (fair rotation).
                    current_goblin_idx = (current_goblin_idx + 1) % len(goblins)

                # Set player_turn back to True — control returns to the hero team
                player_turn = True

        # ============================================================
        # Lose check  (checked after enemy acts so damage is applied first)
        # ============================================================
        # all(...) returns True only when every hero's is_alive() is False.
        if all(not h.is_alive() for h in heroes) and not game_over:
            end_game("You Lose!", LOSE_SOUND)

        # ============================================================
        # Drawing
        # ============================================================
        screen.blit(background, (0, 0))

        # Title banner: text and color change based on the current boolean state
        #   game_over=True          → show win/lose result
        #   player_turn or transition → show "Your Turn" (transition keeps the banner stable)
        #   otherwise               → show "Enemy Turn"
        if game_over:
            title_text  = winner_text
            title_color = WHITE
        elif player_turn or turn_transition:
            title_text  = "Your Turn"
            title_color = BLUE
        else:
            title_text  = "Enemy Turn"
            title_color = RED

        title_surface = title_font.render(title_text, True, title_color)
        screen.blit(title_surface, (WIDTH // 2 - title_surface.get_width() // 2, 25))

        # Team labels
        heroes_label  = font.render("Heroes",  True, YELLOW)
        goblins_label = font.render("Goblins", True, ORANGE)
        screen.blit(heroes_label,  (DIVIDER_X // 2             - heroes_label.get_width()  // 2, TEAM_LABEL_Y))
        screen.blit(goblins_label, (DIVIDER_X + DIVIDER_X // 2 - goblins_label.get_width() // 2, TEAM_LABEL_Y))

        # Loop through each hero to draw their card.
        # is_active is a boolean computed each frame:
        #   True only when it is the player's turn AND this hero is the currently acting one.
        #   A True value causes draw_character() to add a yellow highlight border.
        for i, hero in enumerate(heroes):
            is_active = player_turn and not game_over and not turn_transition and i == current_hero_idx
            draw_character(screen, hero, HERO_X[i], CHAR_Y, BLUE, is_active=is_active)

        # Same loop for goblins.
        # is_active is True only on the enemy's turn for the goblin that is about to act.
        for i, goblin in enumerate(goblins):
            is_active = not player_turn and not game_over and i == current_goblin_idx
            draw_character(screen, goblin, GOBLIN_X[i], CHAR_Y, RED, is_active=is_active)

        # Action panel background
        pygame.draw.rect(screen, LIGHT_BLUE, ACTION_PANEL_RECT, border_radius=10)
        pygame.draw.rect(screen, BLACK,      ACTION_PANEL_RECT, 2, border_radius=10)
        screen.blit(small_font.render("Actions", True, WHITE), (ACTION_PANEL_RECT.x + 8, ACTION_PANEL_RECT.y + 5))

        # buttons_enabled is a single boolean passed to each button's draw() method.
        # When False, buttons are rendered as greyed-out and unclickable visually.
        # Buttons are disabled during the enemy's turn, the transition pause, or after game over.
        buttons_enabled = player_turn and not game_over and not turn_transition
        attack_button.draw(screen,  buttons_enabled)
        defend_button.draw(screen,  buttons_enabled)
        special_button.draw(screen, buttons_enabled)

        # Status line above the battle log: shows the current acting character's stats.
        # Uses the same boolean conditions as the button guard to decide whose info to show.
        if player_turn and not turn_transition and not game_over and current_hero_idx is not None:
            hero = heroes[current_hero_idx]
            info = small_font.render(
                f"{hero.name}'s action  |  Lv: {hero.level}  EXP: {hero.exp}  Special CD: {hero.special_cooldown}",
                True, WHITE
            )
            screen.blit(info, (LOG_RECT.x + 10, LOG_RECT.y - 35))

        elif not player_turn and not game_over:
            # Enemy turn — show the goblin that is about to act
            goblin_idx = next_alive(goblins, current_goblin_idx)
            if goblin_idx is not None:
                goblin = goblins[goblin_idx]
                info = small_font.render(
                    f"{goblin.name}'s action  |  Lv: {goblin.level}  EXP: {goblin.exp}  Special CD: {goblin.special_cooldown}",
                    True, WHITE
                )
                screen.blit(info, (LOG_RECT.x + 10, LOG_RECT.y - 35))

        # Restart button only appears when game_over is True
        if game_over:
            restart_button.draw(screen, True)

        draw_log(screen, battle_log)
        pygame.display.flip()

    pygame.quit()

# Call main function
if __name__ == "__main__":
    main()