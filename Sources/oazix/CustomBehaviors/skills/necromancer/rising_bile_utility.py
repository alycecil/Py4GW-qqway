from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class RisingBileUtility(CustomSkillUtilityBase):

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 79 if enemy_qte >= 5 else 44 if enemy_qte >= 3 else 29 if enemy_qte >= 2 else 10),
        mana_required_to_cast: int = 15,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO,BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Rising_Bile"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition = score_definition

    def _get_target_score(self, target: custom_behavior_helpers.SortableAgentData) -> float:
        score_max = 50
        score_min = 0
        score_offset = 0
        if not Agent.IsHexed(target.agent_id):
            score_offset = 10
            score_max = 60

        health = Agent.GetHealth(target.agent_id)

        if health < .1:
            # let finish him do the work here, we will waste our cast
            score_max = 60
            score_min = 0
        elif health < .5:
            score_max = 90
            score_min = 20
            score_offset += 10
        elif health < .75:
            score_max = 75
            score_min = 20
            score_offset += 5

        if 0.1 < health < 0.6:
            score_offset += 20
            score_min = 40

        score: int = round(self.score_definition.get_score(target.enemy_quantity_within_range)) + score_offset

        return max(min(score_max, score), score_min)

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get enemies ordered by cluster size and distance."""
        by_priority_raw : list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
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
        target = targets[0]

        return self._get_target_score(target)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

