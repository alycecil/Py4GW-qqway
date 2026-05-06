from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition


class Agents_in_Range_Factors(ScoreDefinition):

    def __init__(
            self,
    ):
        super().__init__()

    def in_range_factor(
            self,
            score_max, score_min, score_offset,
            short_range, enemy_quantity_within_range
    ):
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return "Agents in range is not a factor"


class Agents_in_Range_Skill_Aware_Factors(Agents_in_Range_Factors):

    def __init__(
            self,
            agents_nearby_factor: ScorePerAgentQuantityDefinition,
            short_range_divisor: float = 10.0,
            no_score_fallback: float = 0.0,
    ):
        super().__init__()
        self.callable_score: ScorePerAgentQuantityDefinition = agents_nearby_factor
        self.short_range_divisor = short_range_divisor
        self.no_score_fallback = no_score_fallback

    def get_score_for_agent_count(self, agent_quantity: int) -> float | None:
        return self.callable_score.get_score(agent_quantity)

    def in_range_factor(
            self,
            score_max, score_min, score_offset,
            short_range, enemy_quantity_within_range
    ):
        nearby_weight = self.get_score_for_agent_count(enemy_quantity_within_range)
        if nearby_weight is None:
            nearby_weight = self.no_score_fallback
        if short_range:
            nearby_weight /= self.short_range_divisor
        return score_max, score_min, score_offset + nearby_weight

    @override
    def score_definition_debug_ui(self) -> str:
        string = "Agent Count => (max, min, score) (not short range)"

        for _range in [0,1,2,3,5]:
            nearby = self.in_range_factor(0, 0, 0, True, _range)
            longer = self.in_range_factor(0, 0, 0, False, _range)
            string += f"""
     {_range} => {nearby} ({longer})"""

        return string


class Agents_in_Range_Simple_Factors(Agents_in_Range_Factors):

    def __init__(
            self,
            agents_nearby_factor: ScorePerAgentQuantityDefinition,
            no_score_fallback: float = 0.0,
    ):
        super().__init__()
        self.callable_score: ScorePerAgentQuantityDefinition = agents_nearby_factor
        self.no_score_fallback = no_score_fallback

    def get_score_for_agent_count(self, agent_quantity: int) -> float | None:
        return self.callable_score.get_score(agent_quantity)

    def in_range_factor(
            self,
            score_max, score_min, score_offset,
            short_range, enemy_quantity_within_range
    ):
        nearby_weight = self.get_score_for_agent_count(enemy_quantity_within_range)
        if nearby_weight is None:
            nearby_weight = self.no_score_fallback
        return score_max, score_min, score_offset + nearby_weight

    @override
    def score_definition_debug_ui(self) -> str:
        string = "Agent Count => (max, min, score) "

        for _range in [0,1,2,3,5]:
            nearby = self.in_range_factor(0, 0, 0, True, _range)
            string += f"""
     {_range} => {nearby}"""

        return string
