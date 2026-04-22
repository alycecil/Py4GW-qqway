from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Routines, Player
from Sources.Nikon_Scripts.BotUtilities import GameAreas
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class NecrosisUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                current_build: list[CustomSkill],
                score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 2 else 50),
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Necrosis"),
            in_game_build=current_build,
            score_definition=score_definition)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get enemies ordered by cluster size and distance."""
        by_priority_raw : list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            range_to_count_enemies=Range.Adjacent.value # target groups even if the skill is not aoe
        )

        by_priority_raw.sort(key=lambda target: (
            -self._get_target_score(target, len(by_priority_raw)),
            -target.enemy_quantity_within_range,
            target.is_caster,
        ))

        if constants.DEBUG:
            print("List of targets")
            for item in by_priority_raw:
                print(f"Target: {self._get_target_score(item)} : {item}")

        return by_priority_raw

    def _get_target_score(self, target: custom_behavior_helpers.SortableAgentData, enemy_quantity_within_range=1) -> float:
        if not Agent.IsHexed(target.agent_id) and not Agent.IsConditioned(target.agent_id):
            return 0

        score_max = 60
        score_min = 0
        score_offset = 0

        health_of_target = Agent.GetHealth(target.agent_id) # (0.0, 1.0]
        HEALTH_FACTOR = 30.0
        health_of_target *= HEALTH_FACTOR  # (0.0, 30.0]
        health_score = round(HEALTH_FACTOR - health_of_target)

        score_max += health_score
        score_offset += health_score

        # safer targets are better
        if Agent.IsHexed(target.agent_id) and Agent.IsConditioned(target.agent_id):
            score_max += 2
            score_min += 2
            score_offset += 2

        # spike these more
        if Agent.IsDeepWounded(target.agent_id):
            score_max += 2
            score_min += 2
            score_offset += 2

        # prefer current target when possible
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

        score: int = round(self.score_definition.get_score(enemy_quantity_within_range)) + score_offset

        return max(min(score_max, score), score_min)

    def _get_best_target(self) -> int | None:

        candidates = self._get_targets()

        if not candidates:
            return None

        target = candidates[0]

        if self._get_target_score(target) < 10:
            return None

        return target.agent_id

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        player_pos = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], GameAreas.Earshot)

        return self.score_definition.get_score(len(enemy_array))

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        target = self._get_best_target()
        if target is None:
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)

        return result