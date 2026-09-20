from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Panic_ID = Skill.GetID("Panic")
Mistrust_ID = Skill.GetID("Mistrust")
Power_Drain_ID = Skill.GetID("Power_Drain")
Unnatural_Signet_ID = Skill.GetID("Unnatural_Signet")
Cry_of_Pain_ID = Skill.GetID("Cry_of_Pain")
Cry_of_Frustration_ID = Skill.GetID("Cry_of_Frustration")
Hex_Eater_Signet_ID = Skill.GetID("Hex_Eater_Signet")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")


class Panic_Mistrust(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Panic Mistrust",
            required_primary=Profession.Mesmer,
            required_secondary=Profession(0),  # Any
            template_code="OQBDArwjR4i0Awl0lTPjQmOZAA",
            required_skills=[
                Panic_ID,
                Mistrust_ID,
                Power_Drain_ID,
                Cry_of_Frustration_ID,
            ],
            # NOTE: Ebon Escape and Empathy are deliberately NOT listed here.
            # Supported skills are masked from the HeroAI fallback, and neither
            # has local logic — listing them would orphan Ebon Escape's
            # emergency shadow step and Empathy's generic pressure hex.
            # Unlisted, the fallback keeps firing both per its targeting data.
            # Unnatural Signet is optional (not required) so the Cry/Empathy
            # variant bar matches this handler too.
            optional_skills=[
                Unnatural_Signet_ID,
                Cry_of_Pain_ID,
                Hex_Eater_Signet_ID,
                Air_of_Superiority_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
            ],
        )
        # Variant bars swap Mistrust/Unnatural/Ebon Escape for Cry of
        # Frustration/Cry of Pain/Empathy, so any 3 of the 4 required skills
        # identifies this handler. Set before the early return so match-only
        # registry instances score the same as runtime ones.
        self.minimum_required_match = 3

        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # Upkeep first so the Asuran benefit engine runs all fight long.
        if (
            self.IsSkillEquipped(Air_of_Superiority_ID)
            and (self.IsInAggro() or self.IsCloseToAggro())
            and (yield from self.skills.Any.PvE.Air_of_Superiority())
        ):
            return True

        # Emergency energy: drain a casting foe while running on fumes.
        if self.IsSkillEquipped(Power_Drain_ID) and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.30)
        ):
            return True

        # Shutdown core: Panic cascade on the densest caster pack, Mistrust
        # on the active caster, Unnatural punishing enchanted/hexed clusters.
        # All three are target-gated in their helpers, so they hold on empty
        # fields and pre-load Panic before a pull.
        if self.IsSkillEquipped(Panic_ID) and (yield from self.skills.Mesmer.DominationMagic.Panic()):
            return True

        if self.IsSkillEquipped(Mistrust_ID) and (yield from self.skills.Mesmer.DominationMagic.Mistrust()):
            return True

        # Variant-bar interrupt: AoE punish on clustered casting foes.
        if self.IsSkillEquipped(Cry_of_Pain_ID) and (yield from self.skills.Any.PvE.Cry_of_Pain()):
            return True

        # Variant-bar interrupt: single-target punish on a casting foe.
        if self.IsSkillEquipped(Cry_of_Frustration_ID) and (yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()):
            return True

        if self.IsSkillEquipped(Unnatural_Signet_ID) and (yield from self.skills.Mesmer.DominationMagic.Unnatural_Signet()):
            return True

        # Support cleanse whenever a hexed ally qualifies.
        if self.IsSkillEquipped(Hex_Eater_Signet_ID) and (yield from self.skills.Mesmer.InspirationMagic.Hex_Eater_Signet()):
            return True

        # Opportunistic energy refill below 70%.
        if self.IsSkillEquipped(Power_Drain_ID) and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain()
        ):
            return True

        # Caster-ward: needs 2+ live caster allies nearby, gated inside.
        if self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID) and (
            yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Wisdom()
        ):
            return True

        return False
