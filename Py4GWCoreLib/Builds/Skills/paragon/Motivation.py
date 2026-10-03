from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Player, Profession, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Motivation"]


class Motivation:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _cast_combat_aria(self, skill_id: int) -> BuildCoroutine:
        """Use a spell-triggered party chant without clipping our own copy."""
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(skill_id):
            return False
        if not self.build.IsInAggro():
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, skill_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        ))

    #region A
    def Aria_of_Restoration(self) -> BuildCoroutine:
        return (yield from self._cast_combat_aria(Skill.GetID("Aria_of_Restoration")))

    def Aria_of_Zeal(self) -> BuildCoroutine:
        return (yield from self._cast_combat_aria(Skill.GetID("Aria_of_Zeal")))
    #endregion

    #region B
    def Blazing_Finale(self, *, max_target_range: float | None = None) -> BuildCoroutine:
        return (yield from self.build.SpreadEchoToAlly(Skill.GetID("Blazing_Finale"), max_range=max_target_range))

    def Burning_Refrain(self, *, max_target_range: float | None = None) -> BuildCoroutine:
        return (yield from self.build.SpreadEchoToAlly(Skill.GetID("Burning_Refrain"), max_range=max_target_range))
    #endregion

    #region E
    def Energizing_Finale(self, *, max_target_range: float | None = None) -> BuildCoroutine:
        return (yield from self.build.SpreadEchoToAlly(Skill.GetID("Energizing_Finale"), max_range=max_target_range))
    #endregion

    #region H
    def Hasty_Refrain(self, *, max_target_range: float | None = None) -> BuildCoroutine:
        return (yield from self.build.SpreadEchoToAlly(Skill.GetID("Hasty_Refrain"), max_range=max_target_range))
    #endregion

    #region I
    def Inspirational_Speech(
        self,
        *,
        required_profession: Profession = Profession.Necromancer,
        required_skill_id: int | list[int] | tuple[int, ...] | set[int] | None = None,
        prefer_secondary: Profession | int | None = Profession.Dervish,
    ) -> BuildCoroutine:
        """Feed adrenaline strikes to melee Necromancers.

        Mirrors ``DeathMagic.Dark_Aura`` targeting: allies of
        ``required_profession`` carrying ``required_skill_id`` (Soul Taker by
        default), with ``prefer_secondary`` (Dervish by default, i.e. the N/D
        scythe melees) ordered first. Cannot self-target, so ``other_ally``
        is always set.
        """
        inspirational_speech_id: int = Skill.GetID("Inspirational_Speech")
        if required_skill_id is None:
            required_skill_ids: tuple[int, ...] = (Skill.GetID("Soul_Taker"),)
        elif isinstance(required_skill_id, (list, tuple, set, frozenset)):
            required_skill_ids = tuple(int(skill_id) for skill_id in required_skill_id if int(skill_id) != 0)
        elif int(required_skill_id) != 0:
            required_skill_ids = (int(required_skill_id),)
        else:
            required_skill_ids = tuple()

        if not self.build.IsSkillEquipped(inspirational_speech_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        candidates = Routines.Targeting.TargetAlliesByProfession(
            required_profession,
            required_skill_id=required_skill_ids,
            other_ally=True,
            distance=Range.Spellcast.value,
        )
        if not candidates:
            return False

        if prefer_secondary is not None:
            try:
                prefer_secondary_id = int(prefer_secondary)
            except (TypeError, ValueError):
                prefer_secondary_id = 0
            if prefer_secondary_id:
                preferred = []
                rest = []
                for candidate_id in candidates:
                    _, secondary = Agent.GetProfessions(candidate_id)
                    if int(secondary or 0) == prefer_secondary_id:
                        preferred.append(candidate_id)
                    else:
                        rest.append(candidate_id)
                candidates = preferred + rest
                if not candidates:
                    return False

        target_agent_id = int(candidates[0] or 0)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=inspirational_speech_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region L
    def Lyric_of_Zeal(self) -> BuildCoroutine:
        """Party-wide energy on the next signet cast.

        A self-targeted chant, so it also counts as a shout/chant ending on us
        later - which is another refrain renewal tick. Guarded on our own copy
        having expired so we never replace a running chant.
        """
        lyric_of_zeal_id: int = Skill.GetID("Lyric_of_Zeal")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(lyric_of_zeal_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, lyric_of_zeal_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=lyric_of_zeal_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region M
    def Mending_Refrain(self) -> BuildCoroutine:
        mending_refrain_id: int = Skill.GetID("Mending_Refrain")
        mending_refrain = self.build.GetCustomSkill(mending_refrain_id)

        if not self.build.IsSkillEquipped(mending_refrain_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            mending_refrain_id,
            mending_refrain,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=mending_refrain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region N
    def Never_Surrender(self) -> BuildCoroutine:
        from Py4GWCoreLib.HeroAI.targeting import GetAllAlliesArray
        from Py4GWCoreLib import AgentArray
        from Py4GWCoreLib.Agent import Agent

        never_surrender_id: int = Skill.GetID("Never_Surrender")

        if not self.build.IsSkillEquipped(never_surrender_id):
            return False
        # Before the two party scans below. Each HasEffect call rebuilds that
        # agent's buff and effect lists from native, so leaving this ungated
        # pays for the whole party every frame we are in aggro - including the
        # long stretches where the shout is simply recharging.
        if not self.build.CanCastSkillID(never_surrender_id):
            return False

        nearby_allies = GetAllAlliesArray(Range.Earshot.value)
        ally_array = AgentArray.Filter.ByCondition(
            nearby_allies,
            # 75%, matching the skill: it grants regeneration to party members
            # below that mark, so a tighter filter withholds the shout in the
            # 70-75% band where it would in fact have helped everyone counted.
            lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < 0.75,
        )
        if len(ally_array or []) < 2:
            return False

        # Let the running shout expire before recasting - see the inferred
        # renewal mechanic documented on Command.Cant_Touch_This. The check has
        # to look at an ally rather than at us, because this shout only lands on
        # party members below 75% health, and the caster usually is not one of
        # them, so a self-check would be inert exactly when it matters.
        #
        # Checked over every nearby ally rather than the sub-75% set above: the
        # shout keeps running on allies who have since been healed past that
        # threshold, and they are exactly the ones a "is a copy still up?" test
        # must not lose sight of.
        if any(Routines.Checks.Agents.HasEffect(agent_id, never_surrender_id) for agent_id in (nearby_allies or [])):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=never_surrender_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
