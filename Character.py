import math
import random

# ---------------------------------------------------------------------------------------------------------
# Skill base class
# This is the parent class for all special skills.
# Every skill has:
# - a name
# - a cooldown length
# - a current cooldown value
# - a description
# - whether the skill targets self or an enemy
# ---------------------------------------------------------------------------------------------------------
class Skill:
    """
    Parent class for all skills.
    Child classes must implement execute().
    """
    def __init__(self, name, cooldown, description="", target_self=False):
        self.name = name
        self.cooldown = cooldown          # total cooldown turns
        self.current_cd = 0               # current remaining cooldown
        self.description = description
        self.target_self = target_self    # True if this skill is used on self

    def execute(self, user, target):
        """
        Child classes must define what the skill actually does.
        """
        raise NotImplementedError("Subclasses must implement execute().")


# ---------------------------------------------------------------------------------------------------------
# 6 specific skill classes
# Each execute() method:
# 1. applies damage or heal
# 2. gives experience
# 3. returns a message for battle log
# ---------------------------------------------------------------------------------------------------------
class Special_1(Skill):
    def __init__(self):
        super().__init__("Overload", 3, "Deal 30 direct damage.")

    def execute(self, user, target):
        # Deal fixed damage
        dmg = target.take_damage(30)

        # Give exp to attacker and defender
        user.gain_exp(dmg, is_attack=True)
        target.gain_exp(dmg, is_attack=False)

        # Return battle log message
        if target.last_defended:
            return f"{target.name} defended! {user.name}'s Overload dealt only {dmg} damage."
        return f"{user.name} released Overload! {target.name} took {dmg} damage."


class Special_2(Skill):
    def __init__(self):
        super().__init__("Healing Magic", 3, "Recover 20 HP.", target_self=True)

    def execute(self, user, target):
        # Save old hp first so we can calculate actual healed amount
        old_hp = user.hp

        # Heal but do not exceed max hp
        user.hp = min(user.max_hp, user.hp + 20)
        heal = user.hp - old_hp

        # Healing also gives exp
        user.gain_exp(heal, is_attack=True)

        return f"{user.name} activated Healing Magic! Recovered {heal} HP."


class Special_3(Skill):
    def __init__(self):
        super().__init__("Fire Arrow", 3, "Deal damage equal to 20% of target HP.")

    def execute(self, user, target):
        # Damage is based on 20% of target current hp
        damage = max(1, int(target.hp * 0.2))
        dmg = target.take_damage(damage)

        user.gain_exp(dmg, is_attack=True)
        target.gain_exp(dmg, is_attack=False)

        if target.last_defended:
            return f"{target.name} defended! {user.name}'s Fire Arrow dealt only {dmg} damage."
        return f"{user.name} shot Fire Arrow at {target.name}! Dealt {dmg} damage."


class Special_4(Skill):
    def __init__(self):
        super().__init__("Sonic Bark", 3, "Random massive damage.")

    def execute(self, user, target):
        # Random damage from 20 to 40
        dmg = target.take_damage(random.randint(20, 40))

        user.gain_exp(dmg, is_attack=True)
        target.gain_exp(dmg, is_attack=False)

        if target.last_defended:
            return f"{target.name} defended! {user.name}'s Sonic Bark dealt only {dmg} damage."
        return f"{user.name} barked on {target.name}! Dealt {dmg} damage."


class Special_5(Skill):
    def __init__(self):
        super().__init__("Assault Rifle", 3, "Deal 1.5x ATK damage.")

    def execute(self, user, target):
        # Damage is 1.5 times user's attack
        dmg = target.take_damage(int(user.atk * 1.5))

        user.gain_exp(dmg, is_attack=True)
        target.gain_exp(dmg, is_attack=False)

        if target.last_defended:
            return f"{target.name} defended! {user.name}'s Assault Rifle dealt only {dmg} damage."
        return f"{user.name} raided to {target.name}! Dealt {dmg} massive damage."


class Special_6(Skill):
    def __init__(self):
        super().__init__("Recovery Magic", 3, "Heal 15 HP and gain +1 ATK.", target_self=True)

    def execute(self, user, target):
        # Save old hp so we know actual heal amount
        old_hp = user.hp

        # Heal and buff attack
        user.hp = min(user.max_hp, user.hp + 15)
        user.atk += 1

        heal = user.hp - old_hp
        user.gain_exp(heal, is_attack=True)

        return f"{user.name} used Recovery Magic! Healed {heal} HP and powered up!"


# ---------------------------------------------------------------------------------------------------------
# Character class
# This class handles:
# - battle logic
# - cooldown logic
# - defend state
# - experience / level system
# - animation state for pygame UI
# ---------------------------------------------------------------------------------------------------------
SHAKE_DURATION = 1000


class Character:
    """
    One character in the battle game.
    This class stores both combat data and some UI animation data.
    """

    def __init__(self, name, max_hp, atk_range, dfn_range, skill_pack):
        # ---------------- Basic info ----------------
        self.name = name
        self.max_hp = max_hp
        self.hp = self.max_hp

        # atk and dfn may be a single value or a range like (20, 30)
        self.atk = self._stat_value(atk_range)
        self.dfn = self._stat_value(dfn_range)

        # ---------------- Growth system ----------------
        self.level = 1
        self.exp = 0

        # ---------------- Battle states ----------------
        # defending: whether the character is currently in defense mode
        # last_defended: whether the most recent hit was reduced by defense
        self.defending = False
        self.last_defended = False

        # ---------------- Skill ----------------
        self.skill = skill_pack

        # ---------------- UI-only fields ----------------
        # These are used by pygame for drawing and animation
        self.sprite_w = 80
        self.sprite_h = 80
        self.images = {}
        self.current_action = "base"
        self.shake_timer = 0

    def _stat_value(self, value):
        """
        If value is a tuple/list, randomly pick one number in the range.
        Otherwise return the value directly.
        Example:
            (20, 30) -> random number between 20 and 30
            25 -> 25
        """
        if isinstance(value, (tuple, list)):
            return random.randint(value[0], value[1])
        return value

    # -----------------------------------------------------------------------------------------------------
    # Cooldown management
    # special_cooldown lets outside code access skill.current_cd in a cleaner way
    # -----------------------------------------------------------------------------------------------------
    @property
    def special_cooldown(self):
        """
        Return current remaining cooldown for special skill.
        If the character has no skill, return 0.
        """
        if self.skill is None:
            return 0
        return self.skill.current_cd

    @special_cooldown.setter
    def special_cooldown(self, value):
        """
        Set current remaining cooldown for special skill.
        """
        if self.skill is not None:
            self.skill.current_cd = value

    def reduce_cooldown(self):
        """
        Reduce cooldown by 1 after a turn/action, but never below 0.
        """
        if self.special_cooldown > 0:
            self.special_cooldown -= 1

    # -----------------------------------------------------------------------------------------------------
    # Status check
    # -----------------------------------------------------------------------------------------------------
    def is_alive(self):
        """
        Return True if the character still has hp left.
        """
        return self.hp > 0

    # -----------------------------------------------------------------------------------------------------
    # Defense system
    # -----------------------------------------------------------------------------------------------------
    def defend(self):
        """
        Enter defense state.
        The next incoming damage will be reduced by half.
        """
        self.defending = True
        self.last_defended = False

    def stop_defending(self):
        """
        Clear defense state.
        Used when the character starts a new action and should no longer stay in defense mode.
        """
        self.defending = False
        self.last_defended = False

    def take_damage(self, damage):
        """
        Apply damage to this character.

        If defending is True:
        - damage is cut in half
        - last_defended becomes True
        - defending is consumed and reset to False

        Otherwise:
        - take full damage
        """
        if self.defending:
            actual_damage = max(0, damage // 2)
            self.last_defended = True
            self.defending = False
        else:
            actual_damage = max(0, damage)
            self.last_defended = False

        # HP should never go below 0
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    # -----------------------------------------------------------------------------------------------------
    # Normal attack
    # -----------------------------------------------------------------------------------------------------
    def attack_target(self, target):
        """
        Perform a normal attack on target.

        Steps:
        1. Generate a random modifier
        2. Calculate raw attack points
        3. Guarantee at least 1 damage
        4. Let target handle damage through take_damage()
        5. Give exp to both sides
        6. Return actual damage dealt
        """
        modifier = random.randint(-5, 10)
        attack_points = self.atk + modifier - target.dfn
        damage = max(1, attack_points)

        actual_damage = target.take_damage(damage)

        # attacker gains attack exp, defender gains defense exp
        self.gain_exp(actual_damage, is_attack=True)
        target.gain_exp(actual_damage, is_attack=False)

        return actual_damage

    # -----------------------------------------------------------------------------------------------------
    # Special skill usage
    # -----------------------------------------------------------------------------------------------------
    def use_special(self, target):
        """
        Use this character's special skill.

        Steps:
        1. Check whether the character has a skill
        2. Check whether the skill is still on cooldown
        3. Execute the skill
        4. Reset cooldown to full cooldown length
        5. Return battle log text
        """
        if self.skill is None:
            return f"{self.name} has no special skill."

        if self.special_cooldown > 0:
            return None

        result = self.skill.execute(self, target)
        self.special_cooldown = self.skill.cooldown
        return result

    # -----------------------------------------------------------------------------------------------------
    # Experience and level system
    # -----------------------------------------------------------------------------------------------------
    def gain_exp(self, damage, is_attack):
        """
        Gain exp after an action.

        If this character is the attacker:
            gain exp equal to actual damage dealt

        If this character is the defender:
            gain base exp from defense value
            gain a little more if damage is large
            gain even more if damage is blocked very well
        """
        if is_attack:
            self.exp += damage
        else:
            base_gain = self.dfn

            if damage > 10:
                base_gain *= 1.2
            elif damage <= 0:
                base_gain *= 1.5

            self.exp += int(base_gain)

        # Level up whenever exp reaches 100 or more
        while self.exp >= 100:
            self.level += 1
            self.exp -= 100
            self.atk += 2
            self.dfn += 1

        return self.level, self.exp

    # -----------------------------------------------------------------------------------------------------
    # UI animation helpers
    # These methods are used by pygame drawing code in template.py
    # -----------------------------------------------------------------------------------------------------
    def trigger_action(self, action):
        """
        Change current action image and start shake animation.
        Example action values: 'attack', 'defend', 'special'
        """
        self.current_action = action
        self.shake_timer = SHAKE_DURATION

    def update(self, dt):
        """
        Update animation timer each frame.
        When shake animation ends, return to base image.
        dt = time passed since last frame
        """
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_timer = 0
                self.current_action = "base"

    def shake_offset(self):
        """
        Return horizontal shake offset for animation.
        This creates the left-right shaking effect when the character acts.
        """
        if self.shake_timer <= 0:
            return 0

        progress = self.shake_timer / SHAKE_DURATION
        return int(math.sin(progress * math.pi * 6) * 6 * progress)


# ---------------------------------------------------------------------------------------------------------
# Subclasses for distinguishing player and enemy
# They currently only add a type label
# ---------------------------------------------------------------------------------------------------------
class Player(Character):
    """Player character"""
    def __init__(self, name, max_hp, atk_range, dfn_range, skill_pack):
        super().__init__(name, max_hp, atk_range, dfn_range, skill_pack)
        self.type = "Player"


class Enemy(Character):
    """Enemy character"""
    def __init__(self, name, max_hp, atk_range, dfn_range, skill_pack):
        super().__init__(name, max_hp, atk_range, dfn_range, skill_pack)
        self.type = "Enemy"