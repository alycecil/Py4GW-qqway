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
    spirit_factor_DefaultScoreFactors, never_target_spirits_factor
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import \
    DistanceFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.health_factors import \
    Health_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.hex_factors import Hex_Factors, Simple_Hex_Factors
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
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility


class ApplyHexCommonUtility(RawAoeAttackUtility):
    def __init__(self,
                 event_bus: EventBus,
                 skill: CustomSkill,
                 current_build: list[CustomSkill],
                 score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 20 if enemy_qte >= 3 else 10),
                 mana_required_to_cast: int = 12,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
                 within_range: Range = Range.Spellcast,
                 custom_agent_targeting_predicate: Callable[[int], bool] | None = None,

                 condition_factor: Condition_Factors = Condition_Factors(),
                 target_type_factor: target_type_factor_DefaultScoreFactors = target_type_factor_DefaultScoreFactors(),
                 called_target_factor: called_target_factor_DefaultScoreFactors = called_target_factor_DefaultScoreFactors(),
                 hex_factor: Hex_Factors = Simple_Hex_Factors(not_hexed_factor=20, already_hexed_factor=-10, already_hexed_maxed=10),
                 spirit_factor: spirit_factor_DefaultScoreFactors = never_target_spirits_factor(),
                 distance_factor: DistanceFactors = DistanceFactors(),
                 health_factor: Health_Factors = Health_Factors(),
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            current_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
            within_range=within_range,
            ignore_spirits=False,
            custom_agent_targeting_predicate=custom_agent_targeting_predicate,

            condition_factor=condition_factor,
            target_type_factor=target_type_factor,
            called_target_factor=called_target_factor,
            hex_factor=hex_factor,
            spirit_factor=spirit_factor,
            distance_factor=distance_factor,
            health_factor=health_factor,
        )
