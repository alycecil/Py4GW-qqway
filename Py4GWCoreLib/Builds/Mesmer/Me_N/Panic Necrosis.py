from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Panic_ID = Skill.GetID("Panic")
Fragility_ID = Skill.GetID("Fragility")
Power_Drain_ID = Skill.GetID("Power_Drain")
Clumsiness_ID = Skill.GetID("Clumsiness")
Hex_Eater_Signet_ID = Skill.GetID("Hex_Eater_Signet")
Necrosis_ID = Skill.GetID("Necrosis")
Cry_of_Pain_ID = Skill.GetID("Cry_of_Pain")
Mantra_of_Frost_ID = Skill.GetID("Mantra_of_Frost")


@dataclass(slots=True)
class _PanicNecrosisSnapshot:
    in_aggro: bool = False
    enemy_in_spellcast: bool = False
    enemy_casting: bool = False
    enemy_casting_spell_or_chant: bool = False
    player_energy_pct: float = 1.0


class Panic_Necrosis(BuildMgr):
    """Me/N shutdown bar: Panic plus Necrosis.

    Keeps Mantra of Frost up at all times, strips hexes for energy with
    Hex Eater Signet, spreads Panic over clustered casters, interrupts
    with Power Drain and Cry of Pain, shuts attackers down with
    Clumsiness, spikes hexed or conditioned foes with Necrosis, and
    keeps Fragility rolling for condition-tick damage.

    Carries OQREAaYiOIRDMBkBsCMCdDaDiAA (Panic, Fragility, Power Drain,
    Clumsiness, Hex Eater Signet, Necrosis, Cry of Pain, Mantra of
    Frost). Distinct from the generic Panic build, which requires Cry
    of Frustration and Mistrust that this bar does not carry.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Panic Necrosis",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Necromancer,
            template_code="OQREAaYiOIRDMBkBsCMCdDaDiAA",
            required_skills=[
                Panic_ID,
                Necrosis_ID,
                Cry_of_Pain_ID,
            ],
            optional_skills=[
                Fragility_ID,
                Power_Drain_ID,
                Clumsiness_ID,
                Hex_Eater_Signet_ID,
                Mantra_of_Frost_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills(
            [
                Panic_ID,
                Fragility_ID,
                Power_Drain_ID,
                Clumsiness_ID,
                Hex_Eater_Signet_ID,
                Necrosis_ID,
                Cry_of_Pain_ID,
                Mantra_of_Frost_ID,
            ]
        )
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _PanicNecrosisSnapshot:
        snapshot = _PanicNecrosisSnapshot()
        snapshot.in_aggro = bool(self.IsInAggro())
        snapshot.player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))

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
        player_id = Player.GetAgentID()

        # Mantra of Frost shell, in and out of combat.
        if (
            self.IsSkillEquipped(Mantra_of_Frost_ID)
            and not Routines.Checks.Agents.HasEffect(player_id, Mantra_of_Frost_ID)
            and (
                yield from self.CastSkillID(
                    skill_id=Mantra_of_Frost_ID,
                    log=False,
                    aftercast_delay=0,
                )
            )
        ):
            return True

        # Hex removal plus energy, touch range resolved inside the helper.
        if self.IsSkillEquipped(Hex_Eater_Signet_ID) and (
            yield from self.skills.Mesmer.InspirationMagic.Hex_Eater_Signet()
        ):
            return True

        if not snapshot.in_aggro:
            return False

        if snapshot.enemy_in_spellcast and (yield from self.skills.Mesmer.DominationMagic.Panic()):
            return True

        if snapshot.enemy_casting_spell_or_chant and (yield from self.skills.Mesmer.InspirationMagic.Power_Drain()):
            return True

        if self.IsSkillEquipped(Clumsiness_ID) and (yield from self._cast_hex(Clumsiness_ID, "EnemyAttacking")):
            return True

        if snapshot.enemy_casting and (yield from self.skills.Any.PvE.Cry_of_Pain(require_mesmer_hex=True)):
            return True

        if self.IsSkillEquipped(Necrosis_ID) and (yield from self._cast_necrosis()):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Any.PvE.Cry_of_Pain()):
            return True

        if self.IsSkillEquipped(Fragility_ID) and (yield from self._cast_hex(Fragility_ID, "EnemyInjured")):
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
