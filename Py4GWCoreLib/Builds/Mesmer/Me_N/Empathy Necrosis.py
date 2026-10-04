from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Empathy_ID = Skill.GetID("Empathy")
Mind_Wrack_ID = Skill.GetID("Mind_Wrack")
Cry_of_Frustration_ID = Skill.GetID("Cry_of_Frustration")
Power_Drain_ID = Skill.GetID("Power_Drain")
Ebon_Escape_ID = Skill.GetID("Ebon_Escape")
Signet_of_Corruption_Kurzick_ID = Skill.GetID("Signet_of_Corruption_kurzick")
Signet_of_Corruption_Luxon_ID = Skill.GetID("Signet_of_Corruption_luxon")
Necrosis_ID = Skill.GetID("Necrosis")
Energy_Surge_ID = Skill.GetID("Energy_Surge")


@dataclass(slots=True)
class _EmpathyNecrosisSnapshot:
    in_aggro: bool = False
    enemy_in_spellcast: bool = False
    enemy_casting: bool = False
    enemy_casting_spell_or_chant: bool = False


class Empathy_Necrosis(BuildMgr):
    """Me/N attacker shutdown bar: Empathy plus Necrosis.

    Punishes attackers with Empathy and Mind Wrack, interrupts with Cry
    of Frustration and Power Drain, spikes with Energy Surge, detonates
    hexed packs with Necrosis and Signet of Corruption, and shadow steps
    out of combat with Ebon Escape. Mind Wrack goes on early: every
    follow-up non-hex Mesmer skill on that foe then drains energy for
    damage, with a burst if the foe hits zero.

    Carries OQRDArwjRaAxA5AZA0lee3gnAA (Empathy, Mind Wrack, Cry of
    Frustration, Power Drain, Ebon Escape, Signet of Corruption,
    Necrosis, Energy Surge). Distinct from the Energy Surge build, which
    requires Air of Superiority and Ebon Vanguard Assassin Support, and
    from Panic Necrosis, which requires Panic and Cry of Pain.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Empathy Necrosis",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Necromancer,
            template_code="OQRDArwjRaAxA5AZA0lee3gnAA",
            required_skills=[
                Energy_Surge_ID,
                Cry_of_Frustration_ID,
                Necrosis_ID,
            ],
            optional_skills=[
                Empathy_ID,
                Mind_Wrack_ID,
                Power_Drain_ID,
                Ebon_Escape_ID,
                Signet_of_Corruption_Kurzick_ID,
                Signet_of_Corruption_Luxon_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _EmpathyNecrosisSnapshot:
        snapshot = _EmpathyNecrosisSnapshot()
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

    def _equipped_variant(self, *skill_ids: int) -> int:
        for skill_id in skill_ids:
            if skill_id and self.IsSkillEquipped(skill_id):
                return int(skill_id)
        return 0

    def _run_local_skill_logic(self):
        # NOTE: every block chains with `and` so that a failed cast
        # attempt (e.g. skill still on recharge) falls through to the next
        # priority instead of aborting the whole chain with `return False`.
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        snapshot = self._get_bar_snapshot()

        if not snapshot.in_aggro:
            if self.IsSkillEquipped(Ebon_Escape_ID) and (
                yield from self.skills.Any.PvE.Ebon_Escape_CatchUp()
            ):
                return True
            return False

        if (yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.30)):
            return True

        # Prime the focus target first: Mind Wrack makes every later
        # non-hex Mesmer skill on that foe drain energy for damage.
        if self.IsSkillEquipped(Mind_Wrack_ID) and (yield from self._cast_mind_wrack()):
            return True

        if self.IsSkillEquipped(Energy_Surge_ID) and (
            yield from self.skills.Mesmer.DominationMagic.Energy_Surge()
        ):
            return True

        if self.IsSkillEquipped(Cry_of_Frustration_ID) and (
            yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()
        ):
            return True

        if self.IsSkillEquipped(Empathy_ID) and (yield from self._cast_hex(Empathy_ID, "EnemyAttacking")):
            return True

        if snapshot.enemy_casting_spell_or_chant and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain()
        ):
            return True

        if self.IsSkillEquipped(Necrosis_ID) and (yield from self._cast_necrosis()):
            return True

        signet_id = self._equipped_variant(Signet_of_Corruption_Kurzick_ID, Signet_of_Corruption_Luxon_ID)
        if signet_id and (yield from self._signet_of_corruption(signet_id)):
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

    def _cast_mind_wrack(self):
        """Mind Wrack on a casting foe so follow-up skills drain it dry."""
        if not self.CanCastSkillID(Mind_Wrack_ID):
            return False
        target_agent_id = int(Routines.Targeting.GetEnemyCasting(Range.Spellcast.value) or 0)
        if not target_agent_id:
            return False
        if Routines.Checks.Agents.HasEffect(target_agent_id, Mind_Wrack_ID):
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Mind_Wrack_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_necrosis(self):
        # Necrosis only pays out on a hexed or conditioned foe, so resolve
        # a fresh target every tick: the old sticky _resolve_target handed
        # back whatever the bar was chewing on (usually unhexed), and the
        # old HexedOrEnchanted type never matched conditioned foes at all.
        # Anchor the biggest cluster around a hexed or conditioned foe;
        # hold on clean fields.
        if not self.CanCastSkillID(Necrosis_ID):
            return False
        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Nearby.value,
            preferred_condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Necrosis_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _signet_of_corruption(self, skill_id: int):
        # Free AoE + energy per hexed/conditioned foe hit. Anchor the biggest
        # cluster around a hexed or conditioned foe; hold on clean fields.
        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Nearby.value,
            preferred_condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=skill_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
