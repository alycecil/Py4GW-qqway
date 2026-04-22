from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range, AgentArray, Player
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class RitEssenceStrikeOppressiveGazeUtility(CustomSkillUtilityBase):

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 5 else 78 if enemy_qte >= 3 else 70),
        mana_required_to_cast: int = 15,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO,BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Essence_Strike"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition = score_definition

    def _get_lock_key(self, agent_id: int) -> str:
        return f"Oppressive_Gaze_{agent_id}"

    def _get_target_score(self, target: custom_behavior_helpers.SortableAgentData) -> float:
        score_max = 55
        score_min = 0
        score_offset = 0

        lock_key = self._get_lock_key(target.agent_id)
        CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key)

        score: int = round(self.score_definition.get_score(target.enemy_quantity_within_range)) + score_offset

        return max(min(score_max, score), score_min)

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get enemies ordered by cluster size and distance."""
        by_priority_raw : list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            condition=lambda agent_id: not Agent.IsSpirit(agent_id) and Agent.IsConditioned(agent_id),
            range_to_count_enemies=Range.Nearby.value
        )

        by_priority_raw.sort(key=lambda target: (
            -self._get_target_score(target),
            -target.enemy_quantity_within_range,
            target.is_caster,
        ))

        if constants.DEBUG:
            print("List of targets")
            for item in by_priority_raw:
                print(f"item: {self._get_target_score(item)} : {item}")

        return by_priority_raw

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        score_max: float = 80
        distance = Range.Earshot.value
        spirit_array = AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), distance)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsAlive(agent_id) and Agent.IsSpirit(agent_id))

        if spirit_array is None or len(spirit_array)<=0:
            score_max = 10

        targets = self._get_targets()
        if len(targets) == 0: return None
        target = targets[0]
        lock_key = self._get_lock_key(target.agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None

        return min(score_max, self._get_target_score(target))

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        lock_key = self._get_lock_key(target.agent_id)
        CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key) # intentionally not blocking as still does damage

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        finally:
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result

