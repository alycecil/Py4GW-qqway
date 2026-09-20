from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Dark_Aura_ID = Skill.GetID("Dark_Aura")
Blood_is_Power_ID = Skill.GetID("Blood_is_Power")
Soul_Taker_ID = Skill.GetID("Soul_Taker")
Foul_Feast_ID = Skill.GetID("Foul_Feast")
Great_Dwarf_Weapon_ID = Skill.GetID("Great_Dwarf_Weapon")
Stand_Your_Ground_ID = Skill.GetID("Stand_Your_Ground")


class Dark_Aura_Battery(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Dark Aura Battery",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Paragon,
            template_code="OAllQUFrRaanIRHsKeHkA+JqjRXWjB",
            required_skills=[
                Dark_Aura_ID,
                Blood_is_Power_ID,
                Foul_Feast_ID,
                Great_Dwarf_Weapon_ID,
            ],
            # NOTE: Inspirational Speech, "Help Me!" and Ebon Escape are
            # deliberately NOT listed here. Supported skills are masked from
            # the HeroAI fallback, and none of the three has local logic —
            # listing them would orphan the ally buffs and the emergency
            # shadow step. Unlisted, the fallback keeps firing them per its
            # own targeting data.
            optional_skills=[
                Stand_Your_Ground_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # Damage engine first: Dark Aura on a Soul Taker attacker turns
        # every dagger/scythe sacrifice into party-wide shadow damage.
        # Aggro/close gating and re-application tracking live inside.
        if self.IsSkillEquipped(Dark_Aura_ID) and (
            yield from self.skills.Necromancer.DeathMagic.Dark_Aura(
                required_skill_id=Soul_Taker_ID
            )
        ):
            return True

        # Support cleanse: move conditions off allies (ally resolution via
        # the skill's own targeting data).
        if self.IsSkillEquipped(Foul_Feast_ID) and (yield from self.skills.Necromancer.SoulReaping.Foul_Feast()):
            return True

        # Battery feed: energy to the target ally with its own HP-safety
        # floors and throttle inside.
        if self.IsSkillEquipped(Blood_is_Power_ID) and (yield from self.skills.Necromancer.BloodMagic.Blood_is_Power()):
            return True

        if not self.IsInAggro():
            return False

        # Party weapon buff, then party armor. Both helpers gate themselves.
        if self.IsSkillEquipped(Great_Dwarf_Weapon_ID) and (yield from self.skills.Any.NoAttribute.Great_Dwarf_Weapon()):
            return True

        if self.IsSkillEquipped(Stand_Your_Ground_ID) and (yield from self.skills.Paragon.Command.Stand_Your_Ground()):
            return True

        return False
