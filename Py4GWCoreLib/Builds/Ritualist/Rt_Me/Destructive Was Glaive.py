from Py4GWCoreLib import AgentArray, BuildMgr, Profession, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Destructive_Was_Glaive_ID = Skill.GetID("Destructive_Was_Glaive")
Spirit_Rift_ID = Skill.GetID("Spirit_Rift")
Mantra_of_Frost_ID = Skill.GetID("Mantra_of_Frost")
Essence_Strike_ID = Skill.GetID("Essence_Strike")
Ebon_Escape_ID = Skill.GetID("Ebon_Escape")
Ancestors_Rage_ID = Skill.GetID("Ancestors_Rage")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Flesh_of_My_Flesh_ID = Skill.GetID("Flesh_of_My_Flesh")
Empathy_ID = Skill.GetID("Empathy")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
Power_Drain_ID = Skill.GetID("Power_Drain")
Fragility_ID = Skill.GetID("Fragility")


# Energy kept unspent so an Ebon Escape emergency bail or a Mantra of
# Frost refresh can always fire. Every cast below honors this except
# the emergency Escape, the Mantra refresh, and Power Drain (which
# refills energy instead of spending it).
ENERGY_RESERVE = 10


class Destructive_Was_Glaive(BuildMgr):
    """Rt/Me Destructive Was Glaive farmer and its variants.

    Runs with the pack and spams Destructive Was Glaive into the most
    clustered enemies as fast as recharge allows, while keeping Mantra
    of Frost up at all times, in and out of combat.

    Priority 1 is Ebon Escape as an emergency bail when our own health
    or the step target's health drops below 40%. Priority 2 is Ebon
    Vanguard Assassin Support: open with extra bodies, more allies on
    the field keeps us alive, so it outranks everything but the
    emergency bail. Priority 3 is Mantra of Frost upkeep. Priority 4
    is Ebon Escape as a gap-closer: when nothing is in spell range but
    an ally already stands among enemies, shadow step to them instead
    of standing around. Priority 5 is Destructive Was Glaive. Every
    cast drops the held ashes onto nearby foes and puts fresh ones in
    hand, so the first cast (empty hands) fires immediately from range
    while recasts only fire standing in the pack; carrying walks toward
    the biggest available group. Other spells cast freely while
    carrying (they do not drop the ashes, and gain the armor
    penetration bonus). Everything after that is the remaining attacks
    as available: Spirit Rift, Ancestors' Rage, Ebon Battle Standard of
    Wisdom, Essence Strike, Empathy, Power Drain, Fragility. Flesh of My
    Flesh is left to the HeroAI fallback, which only casts it on actual
    deaths.

    Matches OAWjMwhjITEbOOeTIALT7i0lXMA and its variants
    (OAWiMwiMpBQs54sLuMhLSXiAA, OAWiMwiMpBQs54sLuMlBQXiAA,
    OAWjMwhjIT7iEbOO0lLTZAXMIAA, OAWjEYDs4SZAEbOOeTTALT0lIAA):
    the five skills common to every variant are required, the rest are
    optional and only fire when equipped.
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Destructive Was Glaive",
            required_primary=Profession.Ritualist,
            required_secondary=Profession.Mesmer,
            template_code="OAWjMwhjITEbOOeTIALT7i0lXMA",
            required_skills=[
                Destructive_Was_Glaive_ID,
                Spirit_Rift_ID,
                Mantra_of_Frost_ID,
                Essence_Strike_ID,
                Ebon_Escape_ID,
            ],
            optional_skills=[
                Ancestors_Rage_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Flesh_of_My_Flesh_ID,
                Empathy_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                Power_Drain_ID,
                Fragility_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetBlockedSkills(
            [
                Destructive_Was_Glaive_ID,
                Spirit_Rift_ID,
                Mantra_of_Frost_ID,
                Essence_Strike_ID,
                Ebon_Escape_ID,
                Ancestors_Rage_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Empathy_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                Power_Drain_ID,
                Fragility_ID,
            ]
        )
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _keep_energy_reserve(self, skill_id: int) -> bool:
        """True if casting skill_id still leaves the energy reserve."""
        player_id = Player.GetAgentID()
        current = Agent.GetEnergy(player_id) * Agent.GetMaxEnergy(player_id)
        cost = Routines.Checks.Skills.GetEnergyCostWithEffects(skill_id, player_id)
        return (current - cost) >= ENERGY_RESERVE

    def _run_local_skill_logic(self):
        # NOTE: every block chains with `and` so that a failed cast
        # attempt (e.g. skill still on recharge) falls through to the next
        # priority instead of aborting the whole chain with `return False`.
        if not Routines.Checks.Skills.CanCast():
            return False

        player_id = Player.GetAgentID()
        in_aggro = bool(self.IsInAggro())

        # Priority 1: Ebon Escape emergency bail.
        if (yield from self._ebon_escape_emergency()):
            return True

        # Priority 2: open with extra bodies. No aggro gate on purpose:
        # the helper only fires on a clustered enemy in spellcast range,
        # so this pre-summons on approach and keeps summons rolling.
        if (
            self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID)
            and self._keep_energy_reserve(Ebon_Vanguard_Assassin_Support_ID)
            and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support())
        ):
            return True

        # Priority 3: Mantra of Frost shell, in and out of combat.
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

        # Priority 4: Ebon Escape gap-closer onto an ally already in the pack.
        if in_aggro and (yield from self._ebon_escape_gap_close()):
            return True

        # Priority 4b: Ebon Escape travel. Out of combat, shadow step to
        # the party leader when lagging behind, via the shared PvE helper.
        if (
            not in_aggro
            and self.IsSkillEquipped(Ebon_Escape_ID)
            and (yield from self.skills.Any.PvE.Ebon_Escape_CatchUp())
        ):
            return True

        if not in_aggro:
            return False

        # Priority 5: Destructive Was Glaive carry-and-detonate loop.
        if self.IsSkillEquipped(Destructive_Was_Glaive_ID) and (yield from self._cast_destructive_was_glaive()):
            return True

        if self.IsSkillEquipped(Spirit_Rift_ID) and (yield from self._cast_clustered_spell(Spirit_Rift_ID)):
            return True

        if self.IsSkillEquipped(Ancestors_Rage_ID) and (yield from self._cast_ancestors_rage()):
            return True

        if (
            self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID)
            and self._keep_energy_reserve(Ebon_Battle_Standard_of_Wisdom_ID)
            and (yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Wisdom())
        ):
            return True

        if self.IsSkillEquipped(Essence_Strike_ID) and (
            yield from self._cast_single_target_spell(Essence_Strike_ID, "EnemyInjured")
        ):
            return True

        if self.IsSkillEquipped(Empathy_ID) and (
            yield from self._cast_single_target_spell(Empathy_ID, "EnemyAttacking")
        ):
            return True

        if self.IsSkillEquipped(Power_Drain_ID) and (yield from self.skills.Mesmer.InspirationMagic.Power_Drain()):
            return True

        if self.IsSkillEquipped(Fragility_ID) and (
            yield from self._cast_single_target_spell(Fragility_ID, "EnemyInjured")
        ):
            return True

        return False

    def _resolve_attack_target(self, skill_id: int, target_type: str) -> int:
        if not self.CanCastSkillID(skill_id):
            return 0
        target_acquired, _ = self._resolve_target(target_type)
        if not target_acquired:
            return 0
        return self.current_target_id

    def _cast_clustered_spell(self, skill_id: int):
        """Cast an AoE spell at the most clustered enemy."""
        if not self._keep_energy_reserve(skill_id):
            return False
        target_agent_id = self._resolve_attack_target(skill_id, "EnemyClustered")
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

    def _cast_single_target_spell(self, skill_id: int, target_type: str):
        """Cast a single-target spell, restoring the previous target after."""
        if not self._keep_energy_reserve(skill_id):
            return False
        target_agent_id = self._resolve_attack_target(skill_id, target_type)
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

    def _count_live_enemies(self, x: float, y: float, radius: float) -> int:
        """Live enemies within radius of a position."""
        enemies = Routines.Agents.GetFilteredEnemyArray(x, y, radius)
        count = 0
        for enemy_id in enemies or []:
            if Agent.IsAlive(int(enemy_id)):
                count += 1
        return count

    def _enemies_near_self(self) -> int:
        """Live enemies within Nearby range of the player."""
        player_pos = Player.GetXY()
        return self._count_live_enemies(player_pos[0], player_pos[1], Range.Nearby.value)

    def _destructive_was_glaive_holding(self):
        """Carry state: walk to the biggest pack, detonate once inside it.

        A strictly bigger group elsewhere always wins over recasting here,
        so the blast lands on the densest pack instead of stragglers.
        Recasting also needs the skill ready; walking does not, so the
        hero keeps closing while waiting out the recharge.
        """
        target_acquired, _ = self._resolve_target("EnemyClustered")
        if target_acquired:
            target_agent_id = self.current_target_id
            target_x, target_y = Agent.GetXY(target_agent_id)
            cluster_count = self._count_live_enemies(target_x, target_y, Range.Nearby.value)
            if cluster_count > self._enemies_near_self():
                Player.Move(target_x, target_y)
                return True

        if self._enemies_near_self() < 1:
            return False
        if not self.CanCastSkillID(Destructive_Was_Glaive_ID):
            return False
        if not self._keep_energy_reserve(Destructive_Was_Glaive_ID):
            return False
        return (
            yield from self.CastSkillID(
                skill_id=Destructive_Was_Glaive_ID,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_destructive_was_glaive(self):
        """Carry-and-detonate loop for the ashes.

        Every cast drops the held ashes and puts fresh ones in hand.
        Empty hands: cast immediately from range, nothing to drop so no
        walking. Holding: carry them to the biggest available pack (see
        _destructive_was_glaive_holding) and recast there. Other spells
        do not drop the ashes, so the rest of the chain fires freely in
        both states.
        """
        player_id = Player.GetAgentID()
        if Agent.IsHoldingItem(player_id):
            return (yield from self._destructive_was_glaive_holding())

        if not self.CanCastSkillID(Destructive_Was_Glaive_ID):
            return False
        if not self._keep_energy_reserve(Destructive_Was_Glaive_ID):
            return False

        # Empty hands: nothing to drop, so cast immediately from range.
        # No walking: positioning only matters while carrying.
        target_agent_id = self._resolve_attack_target(Destructive_Was_Glaive_ID, "EnemyClustered")
        if not target_agent_id:
            return False

        return (
            yield from self.CastSkillID(
                skill_id=Destructive_Was_Glaive_ID,
                log=False,
                aftercast_delay=250,
            )
        )

    def _cast_ancestors_rage(self):
        """Ancestors' Rage on a martial ally, preferring one already fighting."""
        if not self.IsInAggro():
            return False
        if not self.CanCastSkillID(Ancestors_Rage_ID):
            return False
        if not self._keep_energy_reserve(Ancestors_Rage_ID):
            return False

        player_pos = Player.GetXY()
        allies = Routines.Agents.GetFilteredAllyArray(
            player_pos[0],
            player_pos[1],
            Range.Spellcast.value,
            other_ally=True,
        )

        fallback_ally_id = 0
        for ally_id in allies or []:
            ally_id = int(ally_id)
            if not Agent.IsAlive(ally_id) or not Agent.IsMartial(ally_id):
                continue
            if Routines.Checks.Agents.HasEffect(ally_id, Ancestors_Rage_ID):
                continue
            if Agent.IsAttacking(ally_id):
                fallback_ally_id = 0
                break
            if not fallback_ally_id:
                fallback_ally_id = ally_id
        else:
            ally_id = fallback_ally_id

        if not ally_id:
            return False
        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Ancestors_Rage_ID,
                target_agent_id=ally_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _ebon_escape_target(self):
        """Ally (never self) in spellcast range standing among the most enemies.

        Returns ``(ally_id, enemy_count)``; ``(0, -1)`` when no ally qualifies.
        """
        player_pos = Player.GetXY()
        allies = Routines.Agents.GetFilteredAllyArray(
            player_pos[0],
            player_pos[1],
            Range.Spellcast.value,
            other_ally=True,
        )

        target_agent_id = 0
        best_enemy_count = -1
        for ally_id in allies:
            ally_x, ally_y = Agent.GetXY(ally_id)
            enemies = Routines.Agents.GetFilteredEnemyArray(ally_x, ally_y, Range.Nearby.value)
            enemies = AgentArray.Filter.ByCondition(enemies, lambda eid: Agent.IsAlive(eid))
            enemy_count = len(enemies or [])
            if enemy_count > best_enemy_count:
                best_enemy_count = enemy_count
                target_agent_id = ally_id

        return target_agent_id, best_enemy_count

    def _ebon_escape_emergency(self):
        """Ebon Escape emergency bail: own or step-target health below 40%."""
        if not self.IsSkillEquipped(Ebon_Escape_ID):
            return False

        target_agent_id, _ = self._ebon_escape_target()
        if not target_agent_id:
            return False

        own_low = Agent.GetHealth(Player.GetAgentID()) < 0.40
        ally_low = Agent.GetHealth(target_agent_id) < 0.40
        if not (own_low or ally_low):
            return False

        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Ebon_Escape_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )

    def _ebon_escape_gap_close(self):
        """Ebon Escape onto an ally already standing in the pack.

        Only fires when nothing is in spell range to hit directly, so the
        recharge is saved for emergencies whenever fighting normally.
        """
        if not self.IsSkillEquipped(Ebon_Escape_ID):
            return False
        if not self._keep_energy_reserve(Ebon_Escape_ID):
            return False

        if Routines.Agents.GetNearestEnemy(Range.Spellcast.value):
            return False

        target_agent_id, best_enemy_count = self._ebon_escape_target()
        if not target_agent_id or best_enemy_count <= 0:
            return False

        return (
            yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Ebon_Escape_ID,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        )
