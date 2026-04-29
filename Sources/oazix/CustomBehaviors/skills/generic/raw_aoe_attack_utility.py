from typing import Any, Generator, Callable, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent, traceback
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.condition_factors import \
    condition_factor_prefer_omni, Condition_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.default_score_factors import \
    called_target_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.spirit_factors import \
    spirit_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import \
    DistanceFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.health_factors import \
    Health_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.hex_factors import Hex_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.range_factors import \
    Agents_in_Range_Skill_Aware_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.target_type_factors import \
    target_type_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_target_by_nearby import \
    ScorePerAgentWeightedBySkillDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class RawAoeAttackUtility(CustomSkillUtilityBase):
    def __init__(self,
                 event_bus: EventBus,
                 skill: CustomSkill,
                 current_build: list[CustomSkill],
                 score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 66 if enemy_qte >= 3 else 51 if enemy_qte <= 2 else 26),
                 mana_required_to_cast: int = 12,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
                 within_range: Range = Range.Spellcast,
                 ignore_spirits: bool = False,
                 custom_agent_targeting_predicate: Callable[[int], bool] | None = None,

                 condition_factor: Condition_Factors = condition_factor_prefer_omni(),
                 target_type_factor: target_type_factor_DefaultScoreFactors = target_type_factor_DefaultScoreFactors(),
                 called_target_factor: called_target_factor_DefaultScoreFactors = called_target_factor_DefaultScoreFactors(),
                 hex_factor: Hex_Factors = Hex_Factors(),
                 spirit_factor: spirit_factor_DefaultScoreFactors = spirit_factor_DefaultScoreFactors(),
                 distance_factor: DistanceFactors = DistanceFactors(),
                 health_factor: Health_Factors = Health_Factors(),
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.target_score: ScorePerAgentWeightedBySkillDefinition = ScorePerAgentWeightedBySkillDefinition(
            skill=skill,
            in_range_factor=Agents_in_Range_Skill_Aware_Factors(score_definition),
            condition_factor=condition_factor,
            target_type_factor=target_type_factor,
            called_target_factor=called_target_factor,
            hex_factor=hex_factor,
            spirit_factor=spirit_factor,
            distance_factor=distance_factor,
            health_factor=health_factor,
        )
        self.within_range = within_range
        self.ignore_spirits = ignore_spirits
        self.custom_agent_targeting_predicate: Callable[[int], bool] | None = custom_agent_targeting_predicate

    def _get_target_score(self, target: custom_behavior_helpers.SortableAgentData) -> float:
        try:
            return self.target_score.get_score(target)
        except Exception as e:
            print(f"failed to score for target {e}:{traceback.format_exc()}")
            return 10

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:

        def condition(agent_id: int) -> bool:
            if self.ignore_spirits:
                return not Agent.IsSpirit(agent_id)
            return True

        by_priority_raw = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            condition=lambda agent_id: condition(agent_id) and (
                        self.custom_agent_targeting_predicate is None or self.custom_agent_targeting_predicate(agent_id)
            ),
            within_range=self.within_range,
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))

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

    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"{self.target_score.score_definition_debug_ui()}")
        pass
