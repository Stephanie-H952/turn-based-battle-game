import os
import sys
import pytest
import random
from unittest.mock import MagicMock, patch

# ── Headless SDL so pygame works without a real display or audio device ──────
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

# ── Character (pure Python – no pygame dependency) ───────────────────────────
from Character import (
    Character, Player, Enemy,
    Special_1, Special_2, Special_3, Special_4, Special_5, Special_6,
)

# ── Button (uses pygame.Rect / font) ─────────────────────────────────────────
from Button import Button

# ── Game_Template pure helpers (patch file I/O so assets are not needed) ─────
_fake_surf = MagicMock()
_fake_surf.convert.return_value = _fake_surf
_fake_surf.convert_alpha.return_value = _fake_surf
_fake_surf.get_width.return_value = 60
_fake_surf.get_height.return_value = 60

with patch("pygame.image.load", return_value=_fake_surf), \
     patch("pygame.transform.scale", return_value=_fake_surf), \
     patch("pygame.mixer.Sound", return_value=MagicMock()), \
     patch("pygame.mixer.music.load"):
    from Game_Template_Final import (
        next_alive,
        random_alive_enemy,
        special_target_for,
        create_new_game,
        play_defense_sound,
        play_sound,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def hero():
    """A standard hero with fixed stats and Special_2 (Healing Magic)."""
    return Player("TestHero", 100, 20, 10, Special_2())


@pytest.fixture
def enemy():
    """A standard enemy with fixed stats and Special_1 (Overload)."""
    return Enemy("TestEnemy", 100, 15, 5, Special_1())


@pytest.fixture
def pair(hero, enemy):
    return hero, enemy


# ─────────────────────────────────────────────────────────────────────────────
# Character – initialisation
# ─────────────────────────────────────────────────────────────────────────────

class TestCharacterInit:
    def test_name(self, hero):
        assert hero.name == "TestHero"

    def test_hp_equals_max_hp(self, hero):
        assert hero.hp == hero.max_hp == 100

    def test_level_starts_at_one(self, hero):
        assert hero.level == 1

    def test_exp_starts_at_zero(self, hero):
        assert hero.exp == 0

    def test_not_defending_initially(self, hero):
        assert hero.defending is False

    def test_player_type_label(self, hero):
        assert hero.type == "Player"

    def test_enemy_type_label(self, enemy):
        assert enemy.type == "Enemy"

    def test_stat_range_gives_int(self):
        c = Character("R", 50, (10, 20), (3, 7), None)
        assert 10 <= c.atk <= 20
        assert 3 <= c.dfn <= 7

    def test_stat_fixed_value(self):
        c = Character("F", 50, 15, 5, None)
        assert c.atk == 15
        assert c.dfn == 5


# ─────────────────────────────────────────────────────────────────────────────
# Character – is_alive
# ─────────────────────────────────────────────────────────────────────────────

class TestIsAlive:
    def test_alive_with_full_hp(self, hero):
        assert hero.is_alive() is True

    def test_alive_with_one_hp(self, hero):
        hero.hp = 1
        assert hero.is_alive() is True

    def test_dead_at_zero_hp(self, hero):
        hero.hp = 0
        assert hero.is_alive() is False


# ─────────────────────────────────────────────────────────────────────────────
# Character – take_damage
# ─────────────────────────────────────────────────────────────────────────────

class TestTakeDamage:
    def test_reduces_hp(self, hero):
        hero.take_damage(30)
        assert hero.hp == 70

    def test_returns_actual_damage(self, hero):
        actual = hero.take_damage(25)
        assert actual == 25

    def test_hp_floor_is_zero(self, hero):
        hero.take_damage(9999)
        assert hero.hp == 0

    def test_zero_damage_does_nothing(self, hero):
        hero.take_damage(0)
        assert hero.hp == 100

    def test_defending_halves_damage(self, hero):
        hero.defend()
        actual = hero.take_damage(40)
        assert actual == 20
        assert hero.hp == 80

    def test_defending_consumed_after_hit(self, hero):
        hero.defend()
        hero.take_damage(20)
        assert hero.defending is False

    def test_last_defended_set_when_blocking(self, hero):
        hero.defend()
        hero.take_damage(20)
        assert hero.last_defended is True

    def test_last_defended_false_without_block(self, hero):
        hero.take_damage(10)
        assert hero.last_defended is False

    def test_odd_damage_halved_rounds_down(self, hero):
        hero.defend()
        actual = hero.take_damage(15)
        assert actual == 7   # 15 // 2


# ─────────────────────────────────────────────────────────────────────────────
# Character – defend / stop_defending
# ─────────────────────────────────────────────────────────────────────────────

class TestDefend:
    def test_defend_sets_flag(self, hero):
        hero.defend()
        assert hero.defending is True

    def test_stop_defending_clears_flag(self, hero):
        hero.defend()
        hero.stop_defending()
        assert hero.defending is False

    def test_stop_defending_clears_last_defended(self, hero):
        hero.defend()
        hero.take_damage(10)       # sets last_defended = True
        hero.stop_defending()
        assert hero.last_defended is False


# ─────────────────────────────────────────────────────────────────────────────
# Character – cooldown
# ─────────────────────────────────────────────────────────────────────────────

class TestCooldown:
    def test_initial_cooldown_is_zero(self, hero):
        assert hero.special_cooldown == 0

    def test_set_cooldown(self, hero):
        hero.special_cooldown = 3
        assert hero.special_cooldown == 3

    def test_reduce_cooldown_decrements(self, hero):
        hero.special_cooldown = 3
        hero.reduce_cooldown()
        assert hero.special_cooldown == 2

    def test_reduce_cooldown_does_not_go_below_zero(self, hero):
        hero.special_cooldown = 0
        hero.reduce_cooldown()
        assert hero.special_cooldown == 0

    def test_no_skill_cooldown_returns_zero(self):
        c = Character("NoSkill", 100, 10, 5, None)
        assert c.special_cooldown == 0
        c.reduce_cooldown()     # should not raise
        assert c.special_cooldown == 0


# ─────────────────────────────────────────────────────────────────────────────
# Character – experience and levelling
# ─────────────────────────────────────────────────────────────────────────────

class TestGainExp:
    def test_attacker_gains_damage_as_exp(self, hero):
        hero.gain_exp(30, is_attack=True)
        assert hero.exp == 30

    def test_defender_gains_dfn_as_base(self):
        c = Character("D", 100, 10, 10, None)   # dfn = 10
        c.gain_exp(5, is_attack=False)            # damage <= 10, no bonus
        assert c.exp == 10

    def test_defender_high_damage_bonus(self):
        c = Character("D", 100, 10, 10, None)
        c.gain_exp(20, is_attack=False)           # damage > 10  → ×1.2
        assert c.exp == int(10 * 1.2)

    def test_defender_blocked_all_bonus(self):
        c = Character("D", 100, 10, 10, None)
        c.gain_exp(0, is_attack=False)            # damage == 0 → ×1.5
        assert c.exp == int(10 * 1.5)

    def test_level_up_at_100_exp(self, hero):
        hero.gain_exp(100, is_attack=True)
        assert hero.level == 2
        assert hero.exp == 0

    def test_level_up_increases_atk_and_dfn(self, hero):
        old_atk = hero.atk
        old_dfn = hero.dfn
        hero.gain_exp(100, is_attack=True)
        assert hero.atk == old_atk + 2
        assert hero.dfn == old_dfn + 1

    def test_multiple_level_ups(self, hero):
        hero.gain_exp(250, is_attack=True)
        assert hero.level == 3
        assert hero.exp == 50


# ─────────────────────────────────────────────────────────────────────────────
# Character – attack_target
# ─────────────────────────────────────────────────────────────────────────────

class TestAttackTarget:
    def test_attack_reduces_target_hp(self, pair):
        hero, enemy = pair
        hero.attack_target(enemy)
        assert enemy.hp < enemy.max_hp

    def test_attack_returns_positive_damage(self, pair):
        hero, enemy = pair
        dmg = hero.attack_target(enemy)
        assert dmg >= 1

    def test_minimum_damage_is_one(self, pair):
        hero, enemy = pair
        # Force modifier to worst case (-5) via seed
        with patch("random.randint", return_value=-5):
            dmg = hero.attack_target(enemy)
        assert dmg >= 1

    def test_defending_target_takes_half(self, pair):
        hero, enemy = pair
        enemy.defend()
        with patch("random.randint", return_value=10):  # best modifier
            dmg = hero.attack_target(enemy)
        assert enemy.last_defended is True
        assert dmg <= (hero.atk + 10) // 2 + 1   # roughly half

    def test_attacker_gains_exp(self, pair):
        hero, enemy = pair
        hero.gain_exp = MagicMock(return_value=(1, 0))
        enemy.gain_exp = MagicMock(return_value=(1, 0))
        hero.attack_target(enemy)
        hero.gain_exp.assert_called_once()
        enemy.gain_exp.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# Character – use_special
# ─────────────────────────────────────────────────────────────────────────────

class TestUseSpecial:
    def test_no_skill_returns_message(self):
        c = Character("NoSkill", 100, 10, 5, None)
        result = c.use_special(c)
        assert "no special skill" in result.lower()

    def test_on_cooldown_returns_none(self, hero):
        hero.special_cooldown = 2
        result = hero.use_special(hero)
        assert result is None

    def test_ready_skill_returns_string(self, hero):
        result = hero.use_special(hero)   # Special_2 targets self
        assert isinstance(result, str)

    def test_ready_skill_sets_cooldown(self, hero):
        hero.use_special(hero)
        assert hero.special_cooldown == hero.skill.cooldown

    def test_cooldown_skill_not_consumed(self, hero):
        hero.special_cooldown = 1
        hero.use_special(hero)
        assert hero.special_cooldown == 1   # unchanged


# ─────────────────────────────────────────────────────────────────────────────
# Individual skills
# ─────────────────────────────────────────────────────────────────────────────

def _char(name="A", hp=100, atk=20, dfn=5, skill=None):
    return Character(name, hp, atk, dfn, skill)


class TestSpecials:
    def test_special_1_deals_30_damage(self):
        user, target = _char(), _char()
        Special_1().execute(user, target)
        assert target.hp == 70

    def test_special_1_message_contains_name(self):
        user, target = _char("Hero"), _char("Foe")
        msg = Special_1().execute(user, target)
        assert "Hero" in msg and "Foe" in msg

    def test_special_2_heals_20(self):
        user = _char(hp=80)
        user.hp = 80
        user.max_hp = 100
        Special_2().execute(user, user)
        assert user.hp == 100

    def test_special_2_does_not_exceed_max_hp(self):
        user = _char()
        user.hp = 95
        user.max_hp = 100
        Special_2().execute(user, user)
        assert user.hp == 100

    def test_special_2_targets_self(self):
        assert Special_2().target_self is True

    def test_special_3_deals_20_percent_of_target_hp(self):
        user = _char()
        target = _char(hp=100)
        target.hp = 100
        target.max_hp = 100
        Special_3().execute(user, target)
        assert target.hp == 80   # 100 - 20% of 100

    def test_special_3_minimum_one_damage(self):
        user = _char()
        target = _char(hp=1)
        target.hp = 1
        target.max_hp = 100
        msg = Special_3().execute(user, target)
        assert target.hp == 0

    def test_special_4_random_damage_range(self):
        user = _char()
        target = _char()
        Special_4().execute(user, target)
        assert 60 <= target.hp <= 80   # 100 - 40..20

    def test_special_5_deals_1_5x_atk(self):
        user = _char(atk=20)
        target = _char(dfn=0)   # dfn=0 so no reduction in take_damage
        target.dfn = 0
        Special_5().execute(user, target)
        assert target.hp == 100 - int(20 * 1.5)

    def test_special_5_defending_halves_damage(self):
        user = _char(atk=20)
        target = _char()
        target.defend()
        Special_5().execute(user, target)
        assert target.last_defended is True

    def test_special_6_heals_and_buffs_atk(self):
        user = _char(atk=10)
        user.hp = 85
        user.max_hp = 100
        old_atk = user.atk
        Special_6().execute(user, user)
        assert user.hp == 100
        assert user.atk == old_atk + 1

    def test_special_6_targets_self(self):
        assert Special_6().target_self is True

    def test_skill_cooldown_is_three(self):
        for Cls in (Special_1, Special_2, Special_3, Special_4, Special_5, Special_6):
            assert Cls().cooldown == 3


# ─────────────────────────────────────────────────────────────────────────────
# Button
# ─────────────────────────────────────────────────────────────────────────────

class TestButton:
    def test_rect_position_and_size(self):
        btn = Button(10, 20, 100, 50)
        assert btn.rect.x == 10
        assert btn.rect.y == 20
        assert btn.rect.width == 100
        assert btn.rect.height == 50

    def test_is_clicked_inside(self):
        btn = Button(0, 0, 100, 50)
        assert btn.is_clicked((50, 25)) is True

    def test_is_clicked_outside(self):
        btn = Button(0, 0, 100, 50)
        assert btn.is_clicked((200, 200)) is False

    def test_is_clicked_top_left_corner(self):
        btn = Button(50, 50, 100, 50)
        assert btn.is_clicked((50, 50)) is True

    def test_is_clicked_just_outside_right(self):
        btn = Button(0, 0, 100, 50)
        assert btn.is_clicked((101, 25)) is False

    def test_is_clicked_just_outside_bottom(self):
        btn = Button(0, 0, 100, 50)
        assert btn.is_clicked((50, 51)) is False

    def test_default_text_empty(self):
        btn = Button(0, 0, 100, 50)
        assert btn.text == ""

    def test_text_stored(self):
        btn = Button(0, 0, 100, 50, text="Attack")
        assert btn.text == "Attack"

    def test_bg_color_stored(self):
        btn = Button(0, 0, 100, 50, bg_color=(255, 0, 0))
        assert btn.bg_color == (255, 0, 0)

    def test_image_none_when_no_path(self):
        btn = Button(0, 0, 100, 50)
        assert btn.image is None

    def test_image_none_when_bad_path(self):
        btn = Button(0, 0, 100, 50, image_path="nonexistent.png")
        assert btn.image is None


# ─────────────────────────────────────────────────────────────────────────────
# Game_Template helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_char(alive=True):
    c = Character("X", 100, 10, 5, None)
    if not alive:
        c.hp = 0
    return c


class TestNextAlive:
    def test_returns_first_alive_index(self):
        chars = [_make_char(alive=True), _make_char(alive=True)]
        assert next_alive(chars, 0) == 0

    def test_skips_dead_characters(self):
        chars = [_make_char(alive=False), _make_char(alive=True)]
        assert next_alive(chars, 0) == 1

    def test_wraps_around(self):
        dead = _make_char(alive=False)
        alive = _make_char(alive=True)
        chars = [alive, dead]
        assert next_alive(chars, 1) == 0   # index 1 is dead, wraps to 0

    def test_all_dead_returns_none(self):
        chars = [_make_char(alive=False), _make_char(alive=False)]
        assert next_alive(chars, 0) is None

    def test_empty_list_returns_none(self):
        assert next_alive([], 0) is None

    def test_start_index_out_of_bounds_wraps(self):
        chars = [_make_char(alive=True)]
        assert next_alive(chars, 5) == 0


class TestRandomAliveEnemy:
    def test_returns_alive_enemy(self):
        chars = [_make_char(alive=True), _make_char(alive=True)]
        result = random_alive_enemy(chars)
        assert result in chars

    def test_returns_none_when_all_dead(self):
        chars = [_make_char(alive=False), _make_char(alive=False)]
        assert random_alive_enemy(chars) is None

    def test_returns_only_alive_enemy(self):
        dead = _make_char(alive=False)
        alive = _make_char(alive=True)
        result = random_alive_enemy([dead, alive])
        assert result is alive


class TestSpecialTargetFor:
    def test_target_self_skill_returns_caster(self):
        caster = Character("Caster", 100, 10, 5, Special_2())   # target_self=True
        opponents = [_make_char(alive=True)]
        result = special_target_for(caster, opponents)
        assert result is caster

    def test_target_enemy_skill_returns_opponent(self):
        caster = Character("Caster", 100, 10, 5, Special_1())   # target_self=False
        opp = _make_char(alive=True)
        result = special_target_for(caster, [opp])
        assert result is opp

    def test_no_alive_opponents_returns_none(self):
        caster = Character("Caster", 100, 10, 5, Special_1())
        result = special_target_for(caster, [_make_char(alive=False)])
        assert result is None


class TestCreateNewGame:
    def test_returns_same_heroes_and_goblins(self):
        h = [_make_char()]
        g = [_make_char()]
        out_h, out_g, log = create_new_game(h, g)
        assert out_h is h
        assert out_g is g

    def test_battle_log_starts_with_message(self):
        _, _, log = create_new_game([], [])
        assert len(log) == 1
        assert "battle" in log[0].lower()


# ─────────────────────────────────────────────────────────────────────────────
# play_defense_sound  (new in Game_Template_Final)
# ─────────────────────────────────────────────────────────────────────────────

class TestPlayDefenseSound:
    def test_callable(self):
        assert callable(play_defense_sound)

    def test_calls_play_sound(self):
        char = _make_char()
        with patch("Game_Template_Final.play_sound") as mock_play:
            play_defense_sound(char)
            mock_play.assert_called_once()

    def test_does_not_raise_for_any_character(self):
        for name in ("Orangecat", "Drog", "Unknown"):
            c = _make_char()
            c.name = name
            play_defense_sound(c)   # should never raise
