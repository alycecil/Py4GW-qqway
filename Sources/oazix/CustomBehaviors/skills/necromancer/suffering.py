from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Player
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class SufferingUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 40 if enemy_qte >= 2 else 28 if enemy_qte >= 1 else 10),
        mana_required_to_cast: int = 18,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO,BehaviorState.CLOSE_TO_AGGRO],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Suffering"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_lock_key(self, agent_id: int) -> str:
        return f"SufferingHex_{agent_id}"


    def _get_target_score(self, target: custom_behavior_helpers.SortableAgentData) -> float:
        score_max = 55
        score_min = 0
        score_offset = 0

        if Agent.IsHexed(target.agent_id):
            score_max = 10

        if not Agent.IsDegenHexed(target.agent_id):
            score_max += 5
            score_offset += 5

        if Player.GetTargetID() == target.agent_id:
            score_max += 6
            score_offset += 6

        from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party import \
            CustomBehaviorHelperParty
        party_forced_target_agent_id: int | None = CustomBehaviorHelperParty.get_party_custom_target()
        # Final sort: move party forced target to the front if it exists in the array
        if party_forced_target_agent_id is not None:
            if Player.GetTargetID() == target.agent_id:
                score_max += 15
                score_offset += 15

        lock_key = self._get_lock_key(target.agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key):
            return 0

        score: int = round(self.score_definition.get_score(target.enemy_quantity_within_range)) + score_offset

        return max(min(score_max, score), score_min)

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get enemies ordered by cluster size and distance."""
        by_priority_raw : list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            condition=lambda agent_id: not Agent.IsSpirit(agent_id),
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
        
        targets = self._get_targets()
        if len(targets) == 0: return None
        lock_key = self._get_lock_key(targets[0].agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None #someone is already doing that

        return self.score_definition.get_score(targets[0].enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        lock_key = self._get_lock_key(target.agent_id)
        CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, 10) # intentionally not blocking as

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)

        return result

