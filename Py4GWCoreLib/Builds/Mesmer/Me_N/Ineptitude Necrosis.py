from dataclasses import dataclass

from Py4GWCoreLib import Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Fragility_ID = Skill.GetID("Fragility")
Arcane_Conundrum_ID = Skill.GetID("Arcane_Conundrum")
Necrosis_ID = Skill.GetID("Necrosis")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
Ineptitude_ID = Skill.GetID("Ineptitude")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Signet_of_Clumsiness_ID = Skill.GetID("Signet_of_Clumsiness")
Power_Drain_ID = Skill.GetID("Power_Drain")


@dataclass(slots=True)
class _IneptitudeNecrosisSnapshot:
    in_aggro: bool = False
    enemy_in_spellcast: bool = False
    enemy_casting: bool = False
    enemy_casting_spell_or_chant: bool = False


class Ineptitude_Necrosis(BuildMgr):
    """Me/N illusion shutdown bar: Ineptitude plus Necrosis.

    Shuts attackers down with Ineptitude and Signet of Clumsiness,
    punishes casters with Arcane Conundrum and Power Drain, spikes
    hexed or conditioned foes with Necrosis, keeps Fragility rolling
    for cracked-armor chip, and maintains Air of Superiority plus Ebon
    Battle Standard of Wisdom while fighting.

    Carries OQRDAawDSTAkA3g4ivAwl5ZZAA (Fragility, Arcane Conundrum,
    Necrosis, Ebon Battle Standard of Wisdom, Ineptitude, Air of
    Superiority, Signet of Clumsiness, Power Drain). Distinct from the
    generic Ineptitude build, which requires Wandering Eye that this
    bar does not carry, and from Panic Necrosis, which requires Panic
    and Cry of Pain.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Ineptitude Necrosis",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Necromancer,
            template_code="OQRDAawDSTAkA3g4ivAwl5ZZAA",
            required_skills=[
                Ineptitude_ID,
                Necrosis_ID,
                Signet_of_Clumsiness_ID,
            ],
            optional_skills=[
                Fragility_ID,
                Arcane_Conundrum_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                Air_of_Superiority_ID,
                Power_Drain_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _IneptitudeNecrosisSnapshot:
        snapshot = _IneptitudeNecrosisSnapshot()
        snapshot.in_aggro = bool(self.IsInAggro())

        if not snapshot.in_aggro:
            return snapshot

        snapshot.enemy_in_spellcast = bool(Routines.Agents.GetNearestEnemy(Range.Spellcast.value))
        if snapshot.enemy_in_spellcast:
            snapshot.enemy_casting = bool(Routines.Targeting.GetEnemyCasting(Range.Spellcast.value))
            snapshot.enemy_casting_spell_or_chant = bool(
                Routines.Targeting.GetEnemyCastingSpellOrChant(Range.Spellcast.value)
            )

        return snapshot

    def _run_local_skill_logic(self):
        # NOTE: every block chains with `and` so that a failed cast
        # attempt (e.g. skill still on recharge) falls through to the next
        # priority instead of aborting the whole chain with `return False`.
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        snapshot = self._get_bar_snapshot()

        if (
            self.IsSkillEquipped(Air_of_Superiority_ID)
            and (snapshot.in_aggro or self.IsCloseToAggro())
            and (yield from self.skills.Any.PvE.Air_of_Superiority())
        ):
            return True

        if not snapshot.in_aggro:
            return False

        if self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID) and (
            yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Wisdom()
        ):
            return True

        if (yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.30)):
            return True

        if (yield from self.skills.Mesmer.IllusionMagic.Ineptitude()):
            return True

        if (yield from self.skills.Mesmer.IllusionMagic.Signet_of_Clumsiness()):
            return True

        if self.IsSkillEquipped(Arcane_Conundrum_ID) and (
            yield from self.skills.Mesmer.IllusionMagic.Arcane_Conundrum()
        ):
            return True

        if snapshot.enemy_casting_spell_or_chant and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain()
        ):
            return True

        if self.IsSkillEquipped(Necrosis_ID) and (yield from self._cast_necrosis()):
            return True

        if self.IsSkillEquipped(Fragility_ID) and (yield from self._cast_hex(Fragility_ID, "EnemyInjured")):
            return True

        if (yield from self.AutoAttack(target_type="EnemyClustered")):
            return True

        return False

    def _cast_hex(self, skill_id: int, target_type: str):
        """Cast a hex without overwriting an existing copy on the target."""
        if not self.CanCastSkillID(skill_id):
            return False
        target_acquired, _ = self._resolve_target(target_type)
        if not target_acquired:
            return False
        target_agent_id = self.current_target_id
        if Routines.Checks.Agents.HasEffect(target_agent_id, skill_id):
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=skill_id,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_necrosis(self):
        """Necrosis only pays out on a hexed or conditioned foe."""
        if not self.CanCastSkillID(Necrosis_ID):
            return False
        target_acquired, _ = self._resolve_target("EnemyHexedOrEnchantedClustered")
        if not target_acquired:
            return False
        target_agent_id = self.current_target_id
        if not (
            Routines.Checks.Agents.IsHexed(target_agent_id) or Routines.Checks.Agents.IsConditioned(target_agent_id)
        ):
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Necrosis_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )
