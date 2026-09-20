import PySystem

from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Party import Party
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Skillbar import SkillBar


Arcane_Mimicry_ID = Skill.GetID("Arcane_Mimicry")
Unyielding_Aura_ID = Skill.GetID("Unyielding_Aura")
Healers_Boon_ID = Skill.GetID("Healer's_Boon")

_MAX_HERO_POSITIONS = 8
_UA_SOURCE_SCAN_MS = 1000
_DROP_SUPPRESS_MS = 3000

DEBUG_LOGS: bool = False


class Unyielding_Aura_Drop(BuildMgr):
    """Mo/Me mimicry-UA variant that actively drops the copied aura.

    Root cause for the sibling ``Unyielding_Aura`` build: on a dead party
    member it only returned ``False`` (refused to recast). A maintained
    enchantment does not end that way, so the resurrect end-effect never
    fired. This variant issues a real ``DropBuff`` through the owning
    ``GLOBAL_CACHE.Effects`` queue before falling back to the same
    mimicry/maintain logic.

    The maintained copy is looked up as skill 268 first, with skill 65
    (Arcane Mimicry) as a fallback while the live buff identity is
    confirmed in-client. See the UA widget's "no droppable buff found"
    warning for the diagnostic counterpart.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Unyielding Aura Drop",
            required_primary=Profession.Monk,
            required_secondary=Profession.Mesmer,
            required_skills=[Arcane_Mimicry_ID, Healers_Boon_ID],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self._ua_source_agent_id: int = 0
        self._ua_source_next_scan_ms: int = 0
        self._last_drop_tick_ms: int = 0
        self._debug_enabled: bool = DEBUG_LOGS
        self._debug_last_log_ms: int = 0
        self._debug_log_interval_ms: int = 1000

    def _log_debug(self, message: str) -> None:
        if not self._debug_enabled:
            return
        now_ms = int(PySystem.get_tick_count64())
        if now_ms - self._debug_last_log_ms < self._debug_log_interval_ms:
            return
        self._debug_last_log_ms = now_ms
        self._debug(message)

    def _find_maintained_ua_buff(self, player_id: int) -> tuple[int, int]:
        """Return (skill_id, buff_id) for the maintained UA copy, else (0, 0)."""
        from Py4GWCoreLib import GLOBAL_CACHE

        try:
            buffs = list(GLOBAL_CACHE.Effects.GetBuffs(player_id) or [])
        except Exception:
            buffs = []
        for wanted_id in (Unyielding_Aura_ID, Arcane_Mimicry_ID):
            if not wanted_id:
                continue
            for buff in buffs:
                if int(getattr(buff, "skill_id", 0) or 0) == int(wanted_id):
                    return int(wanted_id), int(getattr(buff, "buff_id", 0) or 0)
        return 0, 0

    def _is_maintaining_ua(self, player_id: int) -> bool:
        skill_id, buff_id = self._find_maintained_ua_buff(player_id)
        if buff_id:
            return True
        return bool(Routines.Checks.Agents.HasEffect(player_id, Unyielding_Aura_ID))

    def _drop_suppressed(self) -> bool:
        if self._last_drop_tick_ms == 0:
            return False
        return int(PySystem.get_tick_count64()) - self._last_drop_tick_ms < _DROP_SUPPRESS_MS

    def _drop_maintained_ua(self, player_id: int, reason: str) -> bool:
        """Actively end the copied UA so its resurrect end-effect fires."""
        from Py4GWCoreLib import GLOBAL_CACHE

        skill_id, buff_id = self._find_maintained_ua_buff(player_id)
        if not buff_id:
            self._log_debug(f"drop requested ({reason}) but no droppable UA buff found")
            return False
        try:
            GLOBAL_CACHE.Effects.DropBuff(int(buff_id))
        except Exception as exc:
            self._log_debug(f"DropBuff({buff_id}) failed: {exc}")
            return False
        self._last_drop_tick_ms = int(PySystem.get_tick_count64())
        self._debug(f"Dropped copied Unyielding Aura (skill {skill_id}, buff {buff_id}): {reason}")
        return True

    def _scan_unyielding_aura_source(self) -> int:
        # The reliable signal is the UA effect on a primary-Monk ally: they
        # just cast UA as their elite, so Arcane Mimicry will copy it. This
        # covers player accounts; the hero skillbar scan is a fallback.
        try:
            player_x, player_y = Player.GetXY()
            ally_array = Routines.Agents.GetFilteredAllyArray(
                player_x,
                player_y,
                Range.Spellcast.value,
                other_ally=True,
            )
            monk_count = 0
            for ally_id in ally_array or []:
                ally_id = int(ally_id)
                if ally_id == 0:
                    continue
                primary_profession, _ = Agent.GetProfessions(ally_id)
                if int(primary_profession) != Profession.Monk.value:
                    continue
                monk_count += 1
                if Routines.Checks.Agents.HasEffect(ally_id, Unyielding_Aura_ID):
                    self._log_debug(f"UA source found via effect: ally {ally_id}")
                    return ally_id
            self._log_debug(f"effect scan hit: allies={len(ally_array or [])}, monks={monk_count}, monks_with_ua=0")
        except Exception:
            pass

        player_id = Player.GetAgentID()
        try:
            for hero_position in range(1, _MAX_HERO_POSITIONS + 1):
                hero_id = int(Party.Heroes.GetHeroAgentIDByPartyPosition(hero_position) or 0)
                if hero_id == 0 or hero_id == player_id:
                    continue
                if not Agent.IsAlive(hero_id):
                    continue

                hero_skillbar = SkillBar.GetHeroSkillbar(hero_position)
                if not hero_skillbar:
                    continue

                for hero_skill in hero_skillbar:
                    hero_skill_id = int(getattr(getattr(hero_skill, "id", None), "id", 0) or 0)
                    if hero_skill_id == Unyielding_Aura_ID:
                        self._log_debug(f"UA source found via hero skillbar: hero {hero_id}")
                        return hero_id
        except Exception:
            pass
        return 0

    def GetUnyieldingAuraSource(self) -> int:
        now_ms = int(PySystem.get_tick_count64())
        if self._ua_source_next_scan_ms != 0 and now_ms < self._ua_source_next_scan_ms:
            return self._ua_source_agent_id

        self._ua_source_next_scan_ms = now_ms + _UA_SOURCE_SCAN_MS
        self._ua_source_agent_id = self._scan_unyielding_aura_source()
        return self._ua_source_agent_id

    def _get_fallback_monk_target(self) -> int:
        # No UA confirmed on any bar: pick whom to mimicry anyway. Prefer the
        # last confirmed UA source; otherwise the nearest living primary-Monk
        # ally in cast range. Arcane Mimicry copies the target's last-used
        # elite, so mimicking a monk stays on UA in practice.
        if self._ua_source_agent_id:
            cached_id = int(self._ua_source_agent_id)
            if Agent.IsValid(cached_id) and Agent.IsAlive(cached_id):
                me_x, me_y = Player.GetXY()
                cached_x, cached_y = Agent.GetXY(cached_id)
                if ((cached_x - me_x) ** 2 + (cached_y - me_y) ** 2) ** 0.5 <= Range.Spellcast.value:
                    return cached_id

        try:
            player_x, player_y = Player.GetXY()
            ally_array = Routines.Agents.GetFilteredAllyArray(
                player_x,
                player_y,
                Range.Spellcast.value,
                other_ally=True,
            )
            best_ally_id = 0
            best_squared_distance = float("inf")
            for ally_id in ally_array or []:
                ally_id = int(ally_id)
                if ally_id == 0:
                    continue
                primary_profession, _ = Agent.GetProfessions(ally_id)
                if int(primary_profession) != Profession.Monk.value:
                    continue
                ally_x, ally_y = Agent.GetXY(ally_id)
                squared_distance = (ally_x - player_x) ** 2 + (ally_y - player_y) ** 2
                if squared_distance < best_squared_distance:
                    best_squared_distance = squared_distance
                    best_ally_id = ally_id
            return best_ally_id
        except Exception:
            return 0

    def _dead_party_member_in_range(self) -> bool:
        return bool(Routines.Party.GetDeadPartyMemberID(max_distance=Range.Spellcast.value))

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            self._log_debug("tick: blocked, CanCast=False")
            return False

        player_id = Player.GetAgentID()

        # Someone is dead and we hold the copied aura: end it now so the
        # end-effect resurrects. This is the step the sibling build lacked.
        if self._is_maintaining_ua(player_id) and self._dead_party_member_in_range():
            if self._drop_maintained_ua(player_id, "dead party member in Spellcast range"):
                return True
            self._log_debug("tick: party member dead in Spellcast range, UA drop failed")
            return False

        if self._drop_suppressed():
            self._log_debug("tick: drop suppress window, holding mimicry")
            return False

        if self.IsSkillEquipped(Unyielding_Aura_ID):
            # While a party member is dead within cast range we must not
            # maintain Unyielding Aura. The drop above already ended it;
            # this guard only stops an immediate recast.
            if self._dead_party_member_in_range():
                self._log_debug("tick: party member dead in Spellcast range, not maintaining UA")
                return False
            if not Routines.Checks.Agents.HasEffect(player_id, Unyielding_Aura_ID):
                self._log_debug(
                    f"casting Unyielding Aura on self "
                    f"(slot={int(SkillBar.GetSlotBySkillID(Unyielding_Aura_ID) or 0)})"
                )
                return (
                    yield from self.CastSkillID(
                        skill_id=Unyielding_Aura_ID,
                        target_agent_id=player_id,
                        aftercast_delay=250,
                    )
                )
            self._log_debug("tick: UA copied and effect active, nothing to do")
            return False

        # Already maintaining UA: the effect is up on us, so there is no need
        # to re-copy the elite yet. Only re-mimic once the effect has lapsed.
        if self._is_maintaining_ua(player_id):
            self._log_debug("tick: UA effect active, skipping mimicry")
            return False

        # Arcane Mimicry is only ever cast on the party monk whose skillbar
        # actually carries Unyielding Aura - never on any other ally.
        source_id = self.GetUnyieldingAuraSource()
        if not source_id:
            source_id = self._get_fallback_monk_target()
            if not source_id:
                self._log_debug("tick: no UA source or fallback monk found, skipping")
                return False
            self._log_debug(f"tick: no UA on any bar, falling back to mimicry on monk {source_id}")

        me_x, me_y = Player.GetXY()
        source_x, source_y = Agent.GetXY(source_id)
        if ((source_x - me_x) ** 2 + (source_y - me_y) ** 2) ** 0.5 > Range.Spellcast.value:
            self._log_debug(f"tick: UA source {source_id} out of Spellcast range")
            return False

        cast = yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Arcane_Mimicry_ID,
            target_agent_id=source_id,
            aftercast_delay=250,
        )
        if not cast:
            self._log_debug(f"tick: mimicry blocked for source {source_id}")
            return False
        return True
