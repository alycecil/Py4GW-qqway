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
from Py4GWCoreLib.Builds.Skills import HexRemovalPriority, SkillsTemplate


Arcane_Mimicry_ID = Skill.GetID("Arcane_Mimicry")
Unyielding_Aura_ID = Skill.GetID("Unyielding_Aura")
Healers_Boon_ID = Skill.GetID("Healers_Boon")
Ebon_Escape_ID = Skill.GetID("Ebon_Escape")
Orison_of_Healing_ID = Skill.GetID("Orison_of_Healing")
Seed_of_Life_ID = Skill.GetID("Seed_of_Life")
Power_Drain_ID = Skill.GetID("Power_Drain")
Cure_Hex_ID = Skill.GetID("Cure_Hex")
Dwaynas_Kiss_ID = Skill.GetID("Dwaynas_Kiss")
Patient_Spirit_ID = Skill.GetID("Patient_Spirit")
Divine_Healing_ID = Skill.GetID("Divine_Healing")
Heavens_Delight_ID = Skill.GetID("Heavens_Delight")
Peace_and_Harmony_ID = Skill.GetID("Peace_and_Harmony")
Lightbringer_Signet_ID = Skill.GetID("Lightbringer_Signet")
Blessed_Aura_ID = Skill.GetID("Blessed_Aura")
Selfless_Spirit_Kurzick_ID = Skill.GetID("Selfless_Spirit_kurzick")
Selfless_Spirit_Luxon_ID = Skill.GetID("Selfless_Spirit_luxon")

_MAX_HERO_POSITIONS = 8
_UA_SOURCE_SCAN_MS = 1000
_DROP_SUPPRESS_MS = 3000

# Shared heal-chain tuning for both UA builds in this module. All HP values
# are fractions (0.0-1.0); energy values are fractions of max energy.
_GRAVE_WOUND_HP = 0.60
_MEDIUM_WOUND_HP = 0.80
_COMBO_MIN_ENERGY_PCT = 0.30
_POWER_DRAIN_ENERGY_PCT = 0.50
_PARTY_WIDE_AVG_HP = 0.90

DEBUG_LOGS: bool = False


class Unyielding_Aura_Drop(BuildMgr):
    """Mo/Me mimicry-UA variant that actively drops the copied aura.

    The normal UA source bar (``Unyielding_Aura``) lives in this module
    below so the pair stays together.

    Root cause for the former sibling ``Unyielding_Aura_Mimicry`` build
    (since removed): on a dead party member it only returned ``False`` (refused to recast). A maintained
    enchantment does not end that way, so the resurrect end-effect never
    fired. This variant issues a real ``DropBuff`` through the owning
    ``GLOBAL_CACHE.Effects`` queue before falling back to the same
    mimicry/maintain logic.

    The maintained copy is looked up as skill 268 first, with skill 65
    (Arcane Mimicry) as a fallback while the live buff identity is
    confirmed in-client. See the UA widget's "no droppable buff found"
    warning for the diagnostic counterpart.

    Carries OwUTMw2CXiuMjIHMDIIY6LuC0DA (Ebon Escape, Orison of Healing,
    Seed of Life, Power Drain, Arcane Mimicry, Cure Hex, Healer's Boon,
    Selfless Spirit). Dwayna's Kiss is supported in the Orison slot when
    the bar carries it instead. Also supports OwUS0YITBBZEXEdR5gKEXcAE
    (Arcane Mimicry, Orison of Healing, Divine Healing, Heaven's Delight,
    Seed of Life, Peace and Harmony, Lightbringer Signet, Blessed Aura).

    Tick priority: drop the copy to resurrect, maintain Healer's Boon and
    Blessed Aura, maintain a directly-equipped UA, acquire the copy via
    Mimicry, then work the support chain (Power Drain interrupt, Peace
    and Harmony mass removal, Cure Hex tiers, Seed of Life, Dwayna's
    Kiss, Orison, Ebon Escape rescue, Divine Healing / Heaven's Delight
    party-wide top-up, Selfless Spirit upkeep, Lightbringer Signet
    energy). The post-drop suppress window gates Mimicry acquisition
    only; everything else stays live.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Unyielding Aura Drop",
            required_primary=Profession.Monk,
            required_secondary=Profession.Mesmer,
            template_code="OwUTMw2CXiuMjIHMDIIY6LuC0DA",
            required_skills=[Arcane_Mimicry_ID],
            optional_skills=[
                Healers_Boon_ID,
                Blessed_Aura_ID,
                Ebon_Escape_ID,
                Orison_of_Healing_ID,
                Dwaynas_Kiss_ID,
                Seed_of_Life_ID,
                Power_Drain_ID,
                Cure_Hex_ID,
                Peace_and_Harmony_ID,
                Divine_Healing_ID,
                Heavens_Delight_ID,
                Lightbringer_Signet_ID,
                Selfless_Spirit_Kurzick_ID,
                Selfless_Spirit_Luxon_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)
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

    def _lowest_injured_ally(self, player_id: int, threshold: float, include_self: bool) -> int:
        """Lowest-health living ally in Spellcast range below threshold, else 0."""
        try:
            player_x, player_y = Player.GetXY()
            allies = (
                Routines.Agents.GetFilteredAllyArray(
                    player_x,
                    player_y,
                    Range.Spellcast.value,
                    other_ally=not include_self,
                )
                or []
            )
        except Exception:
            return 0
        best_id = 0
        best_hp = float(threshold)
        for ally_id in allies:
            ally_id = int(ally_id)
            if ally_id == 0 or not Agent.IsAlive(ally_id):
                continue
            hp = float(Agent.GetHealth(ally_id))
            if hp < best_hp:
                best_id, best_hp = ally_id, hp
        if include_self and Agent.IsAlive(player_id):
            own_hp = float(Agent.GetHealth(player_id))
            if own_hp < best_hp:
                return player_id
        return best_id

    def _party_average_hp_in_earshot(self, player_id: int) -> float | None:
        """Mean HP fraction of living allies in Earshot (self included), else None."""
        try:
            player_x, player_y = Player.GetXY()
            allies = (
                Routines.Agents.GetFilteredAllyArray(
                    player_x,
                    player_y,
                    Range.Earshot.value,
                    other_ally=True,
                )
                or []
            )
        except Exception:
            return None
        total_hp = 0.0
        count = 0
        for ally_id in allies:
            ally_id = int(ally_id)
            if ally_id == 0 or ally_id == player_id or not Agent.IsAlive(ally_id):
                continue
            total_hp += float(Agent.GetHealth(ally_id))
            count += 1
        if Agent.IsAlive(player_id):
            total_hp += float(Agent.GetHealth(player_id))
            count += 1
        if count == 0:
            return None
        return total_hp / count

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

        # Healer's Boon upkeep. Sits ahead of mimicry acquisition so a
        # lapsed Boon is re-cast even while the copied aura is up, in or
        # out of combat.
        if self.IsSkillEquipped(Healers_Boon_ID):
            if not Routines.Checks.Agents.HasEffect(player_id, Healers_Boon_ID):
                self._log_debug("tick: Healer's Boon lapsed, re-casting")
                return (
                    yield from self.CastSkillID(
                        skill_id=Healers_Boon_ID,
                        log=False,
                        aftercast_delay=250,
                    )
                )

        # Blessed Aura upkeep. Same slot as Boon: a maintained enchantment
        # the bar is designed around, so it is kept up whenever missing and
        # stretches subsequently cast monk enchantments (Seed, Peace and
        # Harmony) by ~30%.
        if self.IsSkillEquipped(Blessed_Aura_ID):
            if not Routines.Checks.Agents.HasEffect(player_id, Blessed_Aura_ID):
                self._log_debug("tick: Blessed Aura lapsed, re-casting")
                return (
                    yield from self.CastSkillID(
                        skill_id=Blessed_Aura_ID,
                        log=False,
                        aftercast_delay=250,
                    )
                )

        if self.IsSkillEquipped(Unyielding_Aura_ID):
            # Cast whenever the effect is missing, even with a dead party
            # member present: the drop block above ends it for the rez on
            # the following ticks. Refusing here would deadlock - never
            # maintaining means never dropping means never rezzing.
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

        # Mimicry acquisition is the primary job, but it never preempts the
        # support chain below: failures fall through to healing instead of
        # aborting the tick. The drop-suppress window gates only this block,
        # so UA, Boon, and support all stay live right after a drop.
        if not self._is_maintaining_ua(player_id):
            if self._drop_suppressed():
                self._log_debug("tick: drop suppress window, holding mimicry")
            else:
                # Arcane Mimicry is only ever cast on the party monk whose
                # skillbar actually carries Unyielding Aura - never on any
                # other ally.
                source_id = self.GetUnyieldingAuraSource()
                if not source_id:
                    source_id = self._get_fallback_monk_target()
                    if source_id:
                        self._log_debug(f"tick: no UA on any bar, falling back to mimicry on monk {source_id}")

                if not source_id:
                    self._log_debug("tick: no UA source or fallback monk found, skipping mimicry")
                else:
                    me_x, me_y = Player.GetXY()
                    source_x, source_y = Agent.GetXY(source_id)
                    if ((source_x - me_x) ** 2 + (source_y - me_y) ** 2) ** 0.5 > Range.Spellcast.value:
                        self._log_debug(f"tick: UA source {source_id} out of Spellcast range")
                    elif (
                        yield from self.CastSkillIDAndRestoreTarget(
                            skill_id=Arcane_Mimicry_ID,
                            target_agent_id=source_id,
                            aftercast_delay=250,
                        )
                    ):
                        return True
                    else:
                        self._log_debug(f"tick: mimicry blocked for source {source_id}")
        else:
            self._log_debug("tick: UA effect active, skipping mimicry")

        # Support chain. Time-sensitive protection first (interrupt, hex
        # removal), then heals, rescue, and energy upkeep. Helpers resolve
        # their own targets and return False when nothing needs doing.
        if self.IsSkillEquipped(Power_Drain_ID) and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain()
        ):
            return True

        # Peace and Harmony mass removal. Elite: strips up to 7 conditions
        # and hexes off one ally plus 3s of 90% faster expiry. Triggered
        # only on stacked condi+hex targets, so Cure Hex below still owns
        # hex-only cases.
        if self.IsSkillEquipped(Peace_and_Harmony_ID):
            peace_and_harmony = self.GetCustomSkill(Peace_and_Harmony_ID)
            peace_target = self.ResolvePreferredAllyTarget(
                Peace_and_Harmony_ID,
                peace_and_harmony,
                validator=lambda agent_id: Agent.IsAlive(agent_id)
                and Routines.Checks.Agents.IsConditioned(agent_id)
                and Routines.Checks.Agents.IsHexed(agent_id),
            )
            if peace_target and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Peace_and_Harmony_ID,
                    target_agent_id=peace_target,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        if self.IsSkillEquipped(Cure_Hex_ID) and (
            yield from self.skills.Monk.HealingPrayers.Cure_Hex(min_priority=HexRemovalPriority.HIGH)
        ):
            return True

        if self.IsSkillEquipped(Seed_of_Life_ID) and (
            yield from self.skills.Monk.NoAttribute.Seed_of_Life()
        ):
            return True

        if self.IsSkillEquipped(Dwaynas_Kiss_ID) and (
            yield from self.skills.Monk.HealingPrayers.Dwaynas_Kiss()
        ):
            return True

        if self.IsSkillEquipped(Orison_of_Healing_ID):
            orison_target = self._lowest_injured_ally(player_id, 0.80, include_self=True)
            if orison_target and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Orison_of_Healing_ID,
                    target_agent_id=orison_target,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        if self.IsSkillEquipped(Ebon_Escape_ID):
            ebon_target = self._lowest_injured_ally(player_id, 0.60, include_self=False)
            if ebon_target and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Ebon_Escape_ID,
                    target_agent_id=ebon_target,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        # Out of combat, Ebon Escape is a catch-up step via the shared PvE
        # helper (shadow step to the party leader when lagging).
        if self.IsSkillEquipped(Ebon_Escape_ID) and (
            yield from self.skills.Any.PvE.Ebon_Escape_CatchUp()
        ):
            return True

        # Party-wide top-up (51 each at Divine Favor 12): Divine Healing
        # then Heaven's Delight whenever the earshot average sags. Both
        # heal self plus the party, so self is a valid anchor target.
        party_avg_hp = self._party_average_hp_in_earshot(player_id)
        if party_avg_hp is not None and party_avg_hp < _PARTY_WIDE_AVG_HP:
            if self.IsSkillEquipped(Divine_Healing_ID) and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Divine_Healing_ID,
                    target_agent_id=player_id,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True
            if self.IsSkillEquipped(Heavens_Delight_ID) and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Heavens_Delight_ID,
                    target_agent_id=player_id,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        player_energy_pct = float(Agent.GetEnergy(player_id))
        # Selfless Spirit is combat-only upkeep: out of combat the energy
        # regen is not worth the cast, so both variants hold until aggro.
        if self.IsInAggro() and self.IsSkillEquipped(Selfless_Spirit_Kurzick_ID):
            if not Routines.Checks.Agents.HasEffect(
                player_id, Selfless_Spirit_Kurzick_ID
            ) and player_energy_pct < 0.50:
                self._log_debug("tick: energy low, maintaining Selfless Spirit")
                return (
                    yield from self.CastSkillID(
                        skill_id=Selfless_Spirit_Kurzick_ID,
                        log=False,
                        aftercast_delay=250,
                    )
                )
        if self.IsInAggro() and self.IsSkillEquipped(Selfless_Spirit_Luxon_ID):
            if not Routines.Checks.Agents.HasEffect(player_id, Selfless_Spirit_Luxon_ID):
                self._log_debug("tick: maintaining Selfless Spirit")
                return (
                    yield from self.CastSkillID(
                        skill_id=Selfless_Spirit_Luxon_ID,
                        log=False,
                        aftercast_delay=250,
                    )
                )

        # Free energy, but only inside the area of a demonic servant of
        # Abaddon. Energy-gated so a fizzle outside demon areas costs at most
        # one cast per recharge cycle.
        if self.IsInAggro() and self.IsSkillEquipped(Lightbringer_Signet_ID):
            if player_energy_pct < 0.85:
                self._log_debug("tick: energy low, casting Lightbringer Signet")
                return (
                    yield from self.CastSkillID(
                        skill_id=Lightbringer_Signet_ID,
                        log=False,
                        aftercast_delay=250,
                    )
                )

        if player_energy_pct >= 0.50 and self.IsSkillEquipped(Cure_Hex_ID) and (
            yield from self.skills.Monk.HealingPrayers.Cure_Hex(min_priority=HexRemovalPriority.MEDIUM)
        ):
            return True

        if player_energy_pct >= 0.70 and self.IsSkillEquipped(Cure_Hex_ID) and (
            yield from self.skills.Monk.HealingPrayers.Cure_Hex()
        ):
            return True

        return False


class Unyielding_Aura(BuildMgr):
    """Monk-primary bar that carries Unyielding Aura itself.

    Normal (non-mimicry) counterpart to the Mo/Me mimicry builds above:
    maintains the elite on self, actively drops it through the owning
    Effects queue when a dead party member is in spellcast range, and
    recasts it on self once ready. Mirrors
    Widgets/Guild Wars/Unyielding Aura.py. Merged into this module so the
    UA source bar and its mimicry pair live together; the registry
    discovers both classes independently.

    Carries OwUTMw2CXqBcjIHkuMD4ioLihAA (Patient Spirit, Dwayna's Kiss,
    Seed of Life, Ebon Escape, Power Drain, Divine Healing,
    Heaven's Delight, Unyielding Aura) as its template, and declares the
    support set as optional skills so local logic owns their priority:
    every declared skill is masked from the HeroAI fallback each tick.
    Required stays Unyielding Aura alone so the build still matches any
    Monk-primary bar carrying the elite.

    Tick priority: drop UA to resurrect, maintain UA on self, then work
    the heal chain - Seed of Life first (primary party-wide heal), grave
    wounds via the Patient Spirit + Ebon Escape combo when energy allows
    (single Dwayna's Kiss when it does not), medium wounds via Patient
    Spirit alone, Power Drain below half energy, Divine Healing and
    Heaven's Delight while the earshot party average sags.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Unyielding Aura",
            required_primary=Profession.Monk,
            template_code="OwUTMw2CXqBcjIHkuMD4ioLihAA",
            required_skills=[Unyielding_Aura_ID],
            optional_skills=[
                Patient_Spirit_ID,
                Dwaynas_Kiss_ID,
                Seed_of_Life_ID,
                Ebon_Escape_ID,
                Power_Drain_ID,
                Divine_Healing_ID,
                Heavens_Delight_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)
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

    def _drop_suppressed(self) -> bool:
        if self._last_drop_tick_ms == 0:
            return False
        return int(PySystem.get_tick_count64()) - self._last_drop_tick_ms < _DROP_SUPPRESS_MS

    def _find_maintained_ua_buff(self, player_id: int) -> int:
        from Py4GWCoreLib import GLOBAL_CACHE

        try:
            buffs = list(GLOBAL_CACHE.Effects.GetBuffs(player_id) or [])
        except Exception:
            return 0
        for buff in buffs:
            if int(getattr(buff, "skill_id", 0) or 0) == int(Unyielding_Aura_ID):
                return int(getattr(buff, "buff_id", 0) or 0)
        return 0

    def _dead_party_member_in_range(self) -> bool:
        return bool(Routines.Party.GetDeadPartyMemberID(max_distance=Range.Spellcast.value))

    def _lowest_injured_ally(self, player_id: int, threshold: float, include_self: bool) -> int:
        """Lowest-health living ally in Spellcast range below threshold, else 0."""
        try:
            player_x, player_y = Player.GetXY()
            allies = (
                Routines.Agents.GetFilteredAllyArray(
                    player_x,
                    player_y,
                    Range.Spellcast.value,
                    other_ally=not include_self,
                )
                or []
            )
        except Exception:
            return 0
        best_id = 0
        best_hp = float(threshold)
        for ally_id in allies:
            ally_id = int(ally_id)
            if ally_id == 0 or not Agent.IsAlive(ally_id):
                continue
            hp = float(Agent.GetHealth(ally_id))
            if hp < best_hp:
                best_id, best_hp = ally_id, hp
        if include_self and Agent.IsAlive(player_id):
            own_hp = float(Agent.GetHealth(player_id))
            if own_hp < best_hp:
                return player_id
        return best_id

    def _party_average_hp_in_earshot(self, player_id: int) -> float | None:
        """Mean HP fraction of living allies in Earshot (self included), else None."""
        try:
            player_x, player_y = Player.GetXY()
            allies = (
                Routines.Agents.GetFilteredAllyArray(
                    player_x,
                    player_y,
                    Range.Earshot.value,
                    other_ally=True,
                )
                or []
            )
        except Exception:
            return None
        total_hp = 0.0
        count = 0
        for ally_id in allies:
            ally_id = int(ally_id)
            if ally_id == 0 or ally_id == player_id or not Agent.IsAlive(ally_id):
                continue
            total_hp += float(Agent.GetHealth(ally_id))
            count += 1
        if Agent.IsAlive(player_id):
            total_hp += float(Agent.GetHealth(player_id))
            count += 1
        if count == 0:
            return None
        return total_hp / count

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            self._log_debug("tick: blocked, CanCast=False")
            return False

        player_id = Player.GetAgentID()

        if Routines.Checks.Agents.HasEffect(player_id, Unyielding_Aura_ID):
            if self._dead_party_member_in_range():
                from Py4GWCoreLib import GLOBAL_CACHE

                buff_id = self._find_maintained_ua_buff(player_id)
                if not buff_id:
                    self._log_debug("tick: party member dead in Spellcast range, UA drop failed (no buff)")
                else:
                    try:
                        GLOBAL_CACHE.Effects.DropBuff(int(buff_id))
                    except Exception as exc:
                        self._log_debug(f"DropBuff({buff_id}) failed: {exc}")
                        buff_id = 0
                    if buff_id:
                        self._last_drop_tick_ms = int(PySystem.get_tick_count64())
                        self._debug(
                            f"Dropped Unyielding Aura (buff {buff_id}): dead party member in Spellcast range."
                        )
                        return True
            else:
                self._log_debug("tick: UA up, working support chain")
        elif not self._drop_suppressed() and self.IsSkillEquipped(Unyielding_Aura_ID):
            self._log_debug(
                f"casting Unyielding Aura on self "
                f"(slot={int(SkillBar.GetSlotBySkillID(Unyielding_Aura_ID) or 0)})"
            )
            if (
                yield from self.CastSkillID(
                    skill_id=Unyielding_Aura_ID,
                    target_agent_id=player_id,
                    aftercast_delay=250,
                )
            ):
                return True
            self._log_debug("tick: UA recast failed, working support chain")
        else:
            self._log_debug("tick: UA not up (suppressed or unequipped), working support chain")

        # Seed of Life is the primary party-wide heal. The helper resolves
        # its own spike target and goes quiet when nothing needs it.
        if self.IsSkillEquipped(Seed_of_Life_ID) and (
            yield from self.skills.Monk.NoAttribute.Seed_of_Life()
        ):
            return True

        player_energy_pct = float(Agent.GetEnergy(player_id))

        # Grave wounds: Patient Spirit + Ebon Escape combo when energy
        # allows for two casts (Patient lands first, Ebon follows next
        # tick once Patient is on the target); a single Dwayna's Kiss
        # when it does not. Dwayna's Kiss cannot self-target, so a grave
        # self-wound falls through to Patient Spirit below.
        grave_target = self._lowest_injured_ally(player_id, _GRAVE_WOUND_HP, include_self=False)
        if grave_target:
            if player_energy_pct >= _COMBO_MIN_ENERGY_PCT:
                if self.IsSkillEquipped(Patient_Spirit_ID) and not Routines.Checks.Agents.HasEffect(
                    grave_target, Patient_Spirit_ID
                ):
                    if (
                        yield from self.CastSkillIDAndRestoreTarget(
                            skill_id=Patient_Spirit_ID,
                            target_agent_id=grave_target,
                            log=False,
                            aftercast_delay=250,
                        )
                    ):
                        return True
                if self.IsSkillEquipped(Ebon_Escape_ID) and (
                    yield from self.CastSkillIDAndRestoreTarget(
                        skill_id=Ebon_Escape_ID,
                        target_agent_id=grave_target,
                        log=False,
                        aftercast_delay=250,
                    )
                ):
                    return True
            if self.IsSkillEquipped(Dwaynas_Kiss_ID) and (
                yield from self.skills.Monk.HealingPrayers.Dwaynas_Kiss()
            ):
                return True

        # Medium wounds: Patient Spirit alone. Targets already carrying it
        # are skipped so the delayed heal is never overwritten early.
        patient_target = self._lowest_injured_ally(player_id, _MEDIUM_WOUND_HP, include_self=True)
        if patient_target and not Routines.Checks.Agents.HasEffect(patient_target, Patient_Spirit_ID):
            if self.IsSkillEquipped(Patient_Spirit_ID) and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Patient_Spirit_ID,
                    target_agent_id=patient_target,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        # Energy upkeep: actively refill below half. The helper only fires
        # on an enemy casting a spell or chant in Spellcast range.
        if self.IsSkillEquipped(Power_Drain_ID) and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain(
                energy_threshold_pct=_POWER_DRAIN_ENERGY_PCT
            )
        ):
            return True

        # Party-wide top-up: Divine Healing then Heaven's Delight whenever
        # the earshot average sags. Both heal self plus the party, so self
        # is a valid anchor target.
        party_avg_hp = self._party_average_hp_in_earshot(player_id)
        if party_avg_hp is not None and party_avg_hp < _PARTY_WIDE_AVG_HP:
            if self.IsSkillEquipped(Divine_Healing_ID) and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Divine_Healing_ID,
                    target_agent_id=player_id,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True
            if self.IsSkillEquipped(Heavens_Delight_ID) and (
                yield from self.CastSkillIDAndRestoreTarget(
                    skill_id=Heavens_Delight_ID,
                    target_agent_id=player_id,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

        # Out-of-combat catch-up: shadow step to the party leader when
        # lagging behind, via the shared PvE helper.
        if self.IsSkillEquipped(Ebon_Escape_ID) and (
            yield from self.skills.Any.PvE.Ebon_Escape_CatchUp()
        ):
            return True

        return False
