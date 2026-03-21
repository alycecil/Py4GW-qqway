from typing import Any, Generator, Callable, override

from pyexpat import features

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Routines, Player
from Sources.Nikon_Scripts.BotUtilities import GameAreas
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

class ToxicChillUtility(CustomSkillUtilityBase):

    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda feature_count: 80 if feature_count >= 2 else 50 if feature_count >= 1 else 10),
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Toxic_Chill"),
            in_game_build=current_build,
            score_definition=score_definition)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition


    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        priority_targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: not Agent.IsPoisoned(agent_id) and (Agent.IsEnchanted(agent_id)
                                                                           or Agent.IsHexed(agent_id)),
        )
        if len(priority_targets) >= 0:
            return self._sort_targets(priority_targets)

        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
        )

        return self._sort_targets(targets)

    def _sort_targets(self, targets):
        targets = sorted(
            targets,
            key=lambda agent_id: (
                not Agent.IsPoisoned(agent_id),
                (Agent.IsEnchanted(agent_id) and Agent.IsHexed(agent_id)),
                (Agent.IsEnchanted(agent_id) or Agent.IsHexed(agent_id))
            )
        )
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        targets = self._get_targets()
        if len(targets) == 0: return None

        target_features = 0
        enchanted = Agent.IsEnchanted(agent_id)
        hexed = Agent.IsHexed(agent_id)
        if enchanted or hexed:
            target_features += 1
        if enchanted and hexed:
            target_features += 1 # almost certainly going to poison
        if target_features > 0 and Agent.IsPoisoned(agent_id):
            target_features = 0
        return self.score_definition.get_score(target_features)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        finally:
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result

    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass


