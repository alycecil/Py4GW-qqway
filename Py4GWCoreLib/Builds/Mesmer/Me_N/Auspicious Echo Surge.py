from dataclasses import dataclass

from Py4GWCoreLib import Agent, AgentArray, GLOBAL_CACHE, Player, Profession, Range, Routines, Utils, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Unnatural_Signet_ID = Skill.GetID("Unnatural_Signet")
Overload_ID = Skill.GetID("Overload")
Necrosis_ID = Skill.GetID("Necrosis")
Ebon_Escape_ID = Skill.GetID("Ebon_Escape")
Auspicious_Incantation_ID = Skill.GetID("Auspicious_Incantation")
Arcane_Echo_ID = Skill.GetID("Arcane_Echo")
Energy_Surge_ID = Skill.GetID("Energy_Surge")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")


@dataclass(slots=True)
class _EchoSurgeSnapshot:
    in_aggro: bool = False
    close_to_aggro: bool = False
    enemy_in_spellcast: bool = False
    enemy_casting: bool = False


class Auspicious_Echo_Surge(BuildMgr):
    """Me/N echo-spike bar: Auspicious Incantation -> Arcane Echo -> payload.

    Carries OQRDAowjSmOCO3g0liOLBnA7iA (Unnatural Signet, Overload, Necrosis,
    Ebon Escape, Auspicious Incantation, Arcane Echo, Energy Surge,
    Ebon Vanguard Assassin Support). Fast Casting 8 / Domination 12 /
    Inspiration 10.

    The combo, in order:
    1. Auspicious Incantation (next spell refunded at 110-200% of its cost,
       at the price of extra disable — harmless on Echo).
    2. Arcane Echo under Auspicious (Echo becomes the payload spell).
    3. Payload: Energy Surge if ready, else Ebon Vanguard Assassin Support
       as backup, else Overload as the worst case.

    Hard gate: while Auspicious or Echo is up, NOTHING else casts — any
    other spell would either eat the Auspicious refund or overwrite/kill
    the Echo (non-spells like Necrosis end it prematurely). If the payload
    cannot fire on a tick, the build holds the setup and retries instead
    of leaking into the normal rotation. Ebon Escape is blocked from the
    HeroAI fallback for the same reason and handled locally, so a rescue
    step cannot overwrite a live Echo.

    Double-tap: after the payload fires under Echo, the Echo slot holds a
    ready copy for 20s. The build tracks the Echo slot (ShadowForm-build
    pattern) and fires the copy via CastSkillSlot, so the combo pays out
    twice. Only Surge/EVAS/Overload copies are fired — anything else in
    that slot is left alone.
    """

    arcane_echo_slot: int = 0

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Auspicious Echo Surge",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Necromancer,
            template_code="OQRDAowjSmOCO3g0liOLBnA7iA",
            required_skills=[
                Auspicious_Incantation_ID,
                Arcane_Echo_ID,
                Energy_Surge_ID,
                Necrosis_ID,
                Unnatural_Signet_ID,
            ],
            optional_skills=[
                Overload_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Ebon_Escape_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills(
            [
                Unnatural_Signet_ID,
                Overload_ID,
                Necrosis_ID,
                Ebon_Escape_ID,
                Auspicious_Incantation_ID,
                Arcane_Echo_ID,
                Energy_Surge_ID,
                Ebon_Vanguard_Assassin_Support_ID,
            ]
        )
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _EchoSurgeSnapshot:
        snapshot = _EchoSurgeSnapshot()
        snapshot.in_aggro = bool(self.IsInAggro())
        snapshot.close_to_aggro = snapshot.in_aggro or self.IsCloseToAggro()

        if not snapshot.in_aggro:
            return snapshot

        snapshot.enemy_in_spellcast = bool(Routines.Agents.GetNearestEnemy(Range.Spellcast.value))
        if snapshot.enemy_in_spellcast:
            snapshot.enemy_casting = bool(Routines.Targeting.GetEnemyCasting(Range.Spellcast.value))

        return snapshot

    def _setup_active(self) -> tuple[bool, bool]:
        """(auspicious_up, echo_up) on the caster."""
        player_id = Player.GetAgentID()
        return (
            bool(Routines.Checks.Agents.HasEffect(player_id, Auspicious_Incantation_ID)),
            bool(Routines.Checks.Agents.HasEffect(player_id, Arcane_Echo_ID)),
        )

    def _start_combo(self):
        """Open with Auspicious — only when Echo is ready to follow, so the
        refund never sits stranded on an Echo that is still recharging."""
        if not self.IsSkillEquipped(Auspicious_Incantation_ID):
            return False
        if not self.CanCastSkillID(Auspicious_Incantation_ID):
            return False
        if not self.CanCastSkillID(Arcane_Echo_ID):
            return False
        return (
            yield from self.CastSkillID(
                skill_id=Auspicious_Incantation_ID,
                log=False,
                aftercast_delay=250,
            )
        )

    def _resolve_echo_slot(self) -> int:
        """Echo slot, resolved lazily so a bar swap never strands a stale 0."""
        slot = int(self.arcane_echo_slot or 0)
        if not slot:
            slot = int(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(Arcane_Echo_ID) or 0)
            self.arcane_echo_slot = slot
        return slot

    def _fire_echoed_copy(self):
        """Fire the spell Arcane Echo is currently holding, if it is one of
        ours and the slot is ready. Slot content is the detector: Echo ID
        means not loaded yet (or expired back), anything outside the payload
        set is not ours and is never touched."""
        echo_slot = self._resolve_echo_slot()
        if not echo_slot:
            return False
        echoed_id = int(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(echo_slot) or 0)
        if echoed_id == Arcane_Echo_ID:
            return False
        if echoed_id not in (Energy_Surge_ID, Ebon_Vanguard_Assassin_Support_ID, Overload_ID):
            return False

        target_acquired, _ = self._resolve_target("EnemyClustered")
        if not target_acquired:
            return False
        return (
            yield from self.CastSkillSlot(
                echo_slot,
                target_agent_id=self.current_target_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _run_combo(self, auspicious_up: bool, echo_up: bool):
        """Combo-only mode. Returns True on a cast, False to hold (never
        falls through — the setup is worth more than any single spike)."""
        # Echo first: also latency-safe, since the Auspicious effect can
        # linger in cache the tick after Echo consumes it.
        if echo_up:
            # Copy already loaded (payload fired on an earlier tick while the
            # buff read lags) — double-tap immediately.
            if (yield from self._fire_echoed_copy()):
                return True

            if self.IsSkillEquipped(Energy_Surge_ID) and (
                yield from self.skills.Mesmer.DominationMagic.Energy_Surge()
            ):
                return True

            if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (
                yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()
            ):
                return True

            if self.IsSkillEquipped(Overload_ID) and (yield from self._echo_overload()):
                return True

            return False

        if auspicious_up:
            # The ONLY legal cast under Auspicious. Shared helper skips when
            # Echo is already up (it is not — checked above).
            if (yield from self.skills.Mesmer.NoAttribute.Arcane_Echo()):
                return True
            return False

        return False

    def _echo_overload(self):
        """Worst-case echo payload. The shared Overload helper demands a
        casting enemy and would strand the Echo on a quiet field, so this
        local variant prefers casters but falls back to any cluster rather
        than holding a 20s Echo for nothing."""
        if not self.IsSkillEquipped(Overload_ID):
            return False

        overload_aoe = Range.Adjacent.value
        try:
            from Py4GWCoreLib import GLOBAL_CACHE

            overload_aoe = GLOBAL_CACHE.Skill.Data.GetAoERange(Overload_ID) or Range.Adjacent.value
        except Exception:
            pass

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=overload_aoe,
            preferred_condition=lambda agent_id: Agent.IsCasting(agent_id),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            target_agent_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=overload_aoe,
                filter_radius=Range.Spellcast.value,
            )
        if not target_agent_id:
            return False

        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Overload_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_necrosis(self):
        """Bonus damage only against a hexed or conditioned foe."""
        if not self.IsSkillEquipped(Necrosis_ID):
            return False
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

    def _ebon_escape_rescue(self):
        """In-combat shadow step to the safest ally when pressured. Kept
        local (and the skill blocked from fallback) so a rescue never
        overwrites a live Echo mid-combo."""
        if not self.IsSkillEquipped(Ebon_Escape_ID):
            return False
        if not self.IsInAggro():
            return False

        player_id = Player.GetAgentID()
        player_x, player_y = Player.GetXY()
        adjacent_foes = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Adjacent.value) or []
        if Agent.GetHealth(player_id) >= 0.50 and len(adjacent_foes) < 3:
            return False

        allies = Routines.Agents.GetFilteredAllyArray(player_x, player_y, Range.Spellcast.value, other_ally=True) or []
        candidates = [aid for aid in allies if Agent.IsValid(aid) and Routines.Checks.Agents.IsAlive(aid)]
        if not candidates:
            return False

        def _enemies_near(agent_id: int) -> int:
            ally_x, ally_y = Agent.GetXY(agent_id)
            nearby = Routines.Agents.GetFilteredEnemyArray(ally_x, ally_y, Range.Earshot.value) or []
            return len(nearby)

        candidates.sort(key=lambda aid: (_enemies_near(aid), -Agent.GetHealth(aid)))
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Ebon_Escape_ID,
                target_agent_id=candidates[0],
                log=False,
                aftercast_delay=250,
            )
        )

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        snapshot = self._get_bar_snapshot()

        auspicious_up, echo_up = self._setup_active()
        if auspicious_up or echo_up:
            # Combo gate: setup is live, nothing else may cast.
            return (yield from self._run_combo(auspicious_up, echo_up))

        # Echoed copy pending (buff faded, 20s copy still loaded) — cash it
        # in before opening a fresh combo or spiking normally.
        if (yield from self._fire_echoed_copy()):
            return True

        # OOC travel: step toward the party when lagging behind.
        if self.IsSkillEquipped(Ebon_Escape_ID) and (
            yield from self.skills.Any.PvE.Ebon_Escape_CatchUp()
        ):
            return True

        # Open the combo on approach or in combat.
        if snapshot.close_to_aggro and (yield from self._start_combo()):
            return True

        if not snapshot.in_aggro:
            return False

        # Rescue before damage.
        if (yield from self._ebon_escape_rescue()):
            return True

        # Normal spike rotation (combo on recharge behind all of this).
        if self.IsSkillEquipped(Necrosis_ID) and (yield from self._cast_necrosis()):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Mesmer.DominationMagic.Unnatural_Signet()):
            return True

        if snapshot.enemy_casting and (yield from self.skills.Mesmer.DominationMagic.Overload()):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        return False
