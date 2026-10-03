from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, Utils, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Seven_Weapons_Stance_ID = Skill.GetID("Seven_Weapons_Stance")
Club_of_a_Thousand_Bears_ID = Skill.GetID("Club_of_a_Thousand_Bears")
Whirlwind_Attack_ID = Skill.GetID("Whirlwind_Attack")
Crude_Swing_ID = Skill.GetID("Crude_Swing")
Yeti_Smash_ID = Skill.GetID("Yeti_Smash")
Renewing_Smash_ID = Skill.GetID("Renewing_Smash")
Distracting_Blow_ID = Skill.GetID("Distracting_Blow")
Weaken_Armor_ID = Skill.GetID("Weaken_Armor")


class Seven_Weapons_Hammer(BuildMgr):
    """W/N hammer-knockdown bar: Weaken Armor -> Yeti Smash -> Renewing Smash.

    Carries OQQTc2IPNSsOncHMsIOS8po4TAA (Seven Weapons Stance, Club of a
    Thousand Bears, Whirlwind Attack, Crude Swing, Yeti Smash, Renewing
    Smash, Distracting Blow, Weaken Armor). Curses 11 / Strength 12 /
    Hammer Mastery 6.

    The chain: Weaken Armor spreads Cracked Armor (a condition) over a
    cluster, Yeti Smash spends all adrenaline to knock down conditioned
    foes around the target, and Renewing Smash follows up on knocked-down
    foes for bonus damage plus 3 Energy and an instant recharge. Seven
    Weapons Stance (weapon attributes + 33% IAS) is kept up underneath it
    all. Club of a Thousand Bears, Crude Swing, and Whirlwind Attack are
    adjacent-AoE fillers; Distracting Blow is a casting-gated interrupt.

    Hammer attacks only fire in melee contact — no whiffed swings from
    range. Adrenaline readiness is enforced by CanCastSkillID inside each
    cast, so no manual adrenaline bookkeeping.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Seven Weapons Hammer",
            required_primary=Profession.Warrior,
            required_secondary=Profession.Necromancer,
            template_code="OQQTc2IPNSsOncHMsIOS8po4TAA",
            required_skills=[
                Seven_Weapons_Stance_ID,
                Weaken_Armor_ID,
                Yeti_Smash_ID,
                Renewing_Smash_ID,
            ],
            optional_skills=[
                Club_of_a_Thousand_Bears_ID,
                Whirlwind_Attack_ID,
                Crude_Swing_ID,
                Distracting_Blow_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills(
            [
                Seven_Weapons_Stance_ID,
                Club_of_a_Thousand_Bears_ID,
                Whirlwind_Attack_ID,
                Crude_Swing_ID,
                Yeti_Smash_ID,
                Renewing_Smash_ID,
                Distracting_Blow_ID,
                Weaken_Armor_ID,
            ]
        )
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _melee_target(self, prefer_knocked_down: bool = False) -> int:
        """Clustered enemy in hammer (adjacent) contact, or 0. Knockdown
        preference is for Renewing Smash follow-ups."""
        target_acquired, _ = self._resolve_target("EnemyClustered")
        if not target_acquired:
            return 0
        target_agent_id = int(self.current_target_id or 0)
        if not self._is_in_melee_contact(target_agent_id):
            if prefer_knocked_down:
                return self._knocked_down_in_contact()
            return 0
        if prefer_knocked_down and not Agent.IsKnockedDown(target_agent_id):
            knocked_down_id = self._knocked_down_in_contact()
            if knocked_down_id:
                return knocked_down_id
        return target_agent_id

    def _knocked_down_in_contact(self) -> int:
        player_x, player_y = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Adjacent.value) or []
        for agent_id in enemy_array:
            if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id) and Agent.IsKnockedDown(agent_id):
                return int(agent_id)
        return 0

    def _is_in_melee_contact(self, target_agent_id: int) -> bool:
        if not target_agent_id or not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return False
        return Utils.Distance(Player.GetXY(), Agent.GetXY(target_agent_id)) <= Range.Adjacent.value

    def _cast_hammer_attack(self, skill_id: int, target_agent_id: int):
        if not target_agent_id:
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=skill_id,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_yeti_smash(self):
        """Adrenaline dump: knocks down conditioned foes around the target.
        Held until a conditioned foe is in contact — without the condition
        there is no knockdown and the dump is wasted."""
        if not self.IsSkillEquipped(Yeti_Smash_ID):
            return False
        target_agent_id = self._melee_target()
        if not target_agent_id:
            return False
        if not Agent.IsConditioned(target_agent_id):
            return False
        return (yield from self._cast_hammer_attack(Yeti_Smash_ID, target_agent_id))

    def _cast_renewing_smash(self):
        """Bonus damage on knocked-down foes, plus 3 Energy and an instant
        recharge on hit — prefers KD targets but still swings otherwise."""
        if not self.IsSkillEquipped(Renewing_Smash_ID):
            return False
        target_agent_id = self._melee_target(prefer_knocked_down=True)
        if not target_agent_id:
            return False
        return (yield from self._cast_hammer_attack(Renewing_Smash_ID, target_agent_id))

    def _cast_club_of_a_thousand_bears(self):
        """Damage per adjacent foe, knockdown vs non-humans. Pure contact
        AoE — no extra gate beyond being in the pack."""
        if not self.IsSkillEquipped(Club_of_a_Thousand_Bears_ID):
            return False
        target_agent_id = self._melee_target()
        if not target_agent_id:
            return False
        return (yield from self._cast_hammer_attack(Club_of_a_Thousand_Bears_ID, target_agent_id))

    def _cast_crude_swing(self):
        """Plain adjacent AoE. No gate beyond contact."""
        if not self.IsSkillEquipped(Crude_Swing_ID):
            return False
        target_agent_id = self._melee_target()
        if not target_agent_id:
            return False
        return (yield from self._cast_hammer_attack(Crude_Swing_ID, target_agent_id))

    def _cast_distracting_blow(self):
        """Interrupt: only fires on a casting foe in contact (plus free
        adjacent disruption). Time-sensitive, so it sits ahead of the
        filler attacks in the rotation."""
        if not self.IsSkillEquipped(Distracting_Blow_ID):
            return False
        target_agent_id = self._melee_target()
        if not target_agent_id:
            return False
        if not Agent.IsCasting(target_agent_id):
            return False
        return (yield from self._cast_hammer_attack(Distracting_Blow_ID, target_agent_id))

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        # Stance upkeep, in and out of combat — IAS and weapon attributes
        # under everything else. Refresh window lives in the helper.
        if (yield from self.skills.Warrior.Strength.Seven_Weapon_Stance()):
            return True

        if not self.IsInAggro():
            return False

        # Enabler first: Cracked Armor is the condition Yeti Smashes into.
        if self.IsSkillEquipped(Weaken_Armor_ID) and (
            yield from self.skills.Necromancer.Curses.Weaken_Armor()
        ):
            return True

        # Interrupt before damage — cast windows are short.
        if (yield from self._cast_distracting_blow()):
            return True

        # Knockdown chain.
        if (yield from self._cast_yeti_smash()):
            return True

        if (yield from self._cast_renewing_smash()):
            return True

        # Adjacent-AoE fillers.
        if (yield from self._cast_club_of_a_thousand_bears()):
            return True

        if (yield from self._cast_crude_swing()):
            return True

        if self.IsSkillEquipped(Whirlwind_Attack_ID) and (
            yield from self.skills.Warrior.NoAttribute.Whirlwind_Attack()
        ):
            return True

        return False
