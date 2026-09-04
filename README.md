# turn-based-battle-game

A Python/Pygame turn-based battle game created for a CS5001 final project. The player chooses a team of two heroes, battles against two randomly selected enemies, and wins by defeating the full enemy team.

## Features

- Character selection screen with three playable heroes.
- Turn-based combat with Attack, Defend, and Special actions.
- Enemy AI that chooses actions automatically and favors defense when health is low.
- Six unique special skills with cooldowns, including healing, direct damage, HP-based damage, and attack buffs.
- HP bars, EXP bars, level tracking, action animations, sound effects, and background music.
- Restart flow after a win or loss.
- Automated tests for character logic, button behavior, and game helper functions.

## Requirements

- Python 3
- Pygame
- pytest, for running tests

Install the Python dependencies:

```bash
python3 -m pip install pygame pytest
```

## How To Run

Run the game from the project directory so the image and sound asset paths resolve correctly:

```bash
python3 Game_Template_Final.py
```

## How To Play

1. Choose two heroes on the selection screen.
2. Click `Start Battle`.
3. On each hero turn, choose one action:
   - `Attack`: damage a random living enemy.
   - `Defend`: reduce the next incoming damage by half.
   - `Special`: use the hero's unique skill if it is off cooldown.
4. The enemy team takes automatic turns after the player team acts.
5. Defeat all enemies to win. If all heroes are defeated, the game is lost.

## Project Structure

```text
.
|-- Button.py                 # Reusable Pygame button class
|-- Character.py              # Character stats, combat, skills, EXP, and leveling
|-- Game_Template_Final.py    # Main Pygame app, screens, turn loop, AI, and rendering
|-- image/                    # Character sprites, backgrounds, and action icons
|-- sound/                    # Background music and sound effects
`-- test_Game.py              # pytest test suite
```

## Running Tests

```bash
python3 -m pytest test_Game.py
```

The tests use dummy SDL video and audio drivers so Pygame can run in a headless test environment.
