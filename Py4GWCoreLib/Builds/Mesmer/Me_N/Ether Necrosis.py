from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Signet_of_Corruption_Kurzick_ID = Skill.GetID("Signet_of_Corruption_kurzick")
Signet_of_Corruption_Luxon_ID = Skill.GetID("Signet_of_Corruption_luxon")
Ether_Nightmare_Kurzick_ID = Skill.GetID("Ether_Nightmare_kurzick")
Ether_Nightmare_Luxon_ID = Skill.GetID("Ether_Nightmare_luxon")
Hex_Eater_Signet_ID = Skill.GetID("Hex_Eater_Signet")
Cry_of_Frustration_ID = Skill.GetID("Cry_of_Frustration")
Power_Drain_ID = Skill.GetID("Power_Drain")
Spiritual_Pain_ID = Skill.GetID("Spiritual_Pain")
Energy_Surge_ID = Skill.GetID("Energy_Surge")


@dataclass(slots=True)
class _EtherNecrosisSnapshot:
    in_aggro: bool = False
    enemy_in_spellcast: bool = False
    enemy_casting: bool = False
    enemy_casting_spell_or_chant: bool = False


class Ether_Necrosis(BuildMgr):
    """Me/N domination spike bar: Ether Nightmare plus Energy Surge.

    Drains casters with Ether Nightmare (energy loss plus area
    degeneration per point lost), spikes with Energy Surge and
    Spiritual Pain, interrupts with Cry of Frustration and Power
    Drain, strips hexes for energy with Hex Eater Signet, and cashes
    hexed packs in with Signet of Corruption. Ether Nightmare lands
    before Corruption so the degen hex is down before the signet
    counts it.

    Carries OQRDArwjRwleedejQ5AZA4UnAA (Air of Superiority, Signet of
    Corruption, Ether Nightmare, Hex Eater Signet, Cry of Frustration,
    Power Drain, Spiritual Pain, Energy Surge). Distinct from the
    Energy Surge build, which requires Ebon Vanguard Assassin Support
    that this bar does not carry.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Ether Necrosis",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Necromancer,
            template_code="OQRDArwjRwleedejQ5AZA4UnAA",
            required_skills=[
                Energy_Surge_ID,
                Cry_of_Frustration_ID,
            ],
            optional_skills=[
                Air_of_Superiority_ID,
                Signet_of_Corruption_Kurzick_ID,
                Signet_of_Corruption_Luxon_ID,
                Ether_Nightmare_Kurzick_ID,
                Ether_Nightmare_Luxon_ID,
                Hex_Eater_Signet_ID,
                Power_Drain_ID,
                Spiritual_Pain_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _EtherNecrosisSnapshot:
        snapshot = _EtherNecrosisSnapshot()
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

        if (
            self.IsSkillEquipped(Air_of_Superiority_ID)
            and (snapshot.in_aggro or self.IsCloseToAggro())
            and (yield from self.skills.Any.PvE.Air_of_Superiority())
        ):
            return True

        if not snapshot.in_aggro:
            return False

        if (yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.30)):
            return True

        ether_id = self._equipped_variant(Ether_Nightmare_Kurzick_ID, Ether_Nightmare_Luxon_ID)
        if ether_id and (yield from self._cast_ether_nightmare(ether_id)):
            return True

        if self.IsSkillEquipped(Energy_Surge_ID) and (
            yield from self.skills.Mesmer.DominationMagic.Energy_Surge()
        ):
            return True

        if self.IsSkillEquipped(Cry_of_Frustration_ID) and (
            yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()
        ):
            return True

        if self.IsSkillEquipped(Hex_Eater_Signet_ID) and (
            yield from self.skills.Mesmer.InspirationMagic.Hex_Eater_Signet()
        ):
            return True

        if self.IsSkillEquipped(Spiritual_Pain_ID) and (yield from self._cast_hex(Spiritual_Pain_ID, "EnemyInjured")):
            return True

        signet_id = self._equipped_variant(Signet_of_Corruption_Kurzick_ID, Signet_of_Corruption_Luxon_ID)
        if signet_id and (yield from self._signet_of_corruption(signet_id)):
            return True

        if snapshot.enemy_casting_spell_or_chant and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain()
        ):
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

    def _cast_ether_nightmare(self, skill_id: int):
        """Ether Nightmare on a casting foe: energy drain plus area degen."""
        if not self.CanCastSkillID(skill_id):
            return False
        target_agent_id = int(Routines.Targeting.GetEnemyCasting(Range.Spellcast.value) or 0)
        if not target_agent_id:
            return False
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
