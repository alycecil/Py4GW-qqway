from typing import override

from Py4GWCoreLib import Agent
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class Health_Factors(ScoreDefinition):
    def __init__(
            self,
            very_low_health_max: float = 7.5,
            very_low_health_min: float = 15.0,
            very_low_health_offset: float = 6,
            low_health_max: float = 10.0,
            low_health_min: float = 17.0,
            low_health_offset: float = 5,
            medium_health_max: float = 5.0,
            medium_health_min: float = 15.0,
            medium_health_offset: float = 3,
            high_health_max: float = 1.0,
            high_health_min: float = 1.0,
            high_health_offset: float = 1,
            full_health_max: float = 0.0,
            full_health_min: float = 0.0,
            full_health_offset: float = 0.0,
            very_low_health_threshold: float = 0.15,
            low_health_threshold: float = 0.5,
            medium_health_threshold: float = 0.75,
            high_health_threshold: float = 0.9,
    ):
        self.very_low_health_max = very_low_health_max
        self.very_low_health_min = very_low_health_min
        self.very_low_health_offset = very_low_health_offset
        self.low_health_max = low_health_max
        self.low_health_min = low_health_min
        self.low_health_offset = low_health_offset
        self.medium_health_max = medium_health_max
        self.medium_health_min = medium_health_min
        self.medium_health_offset = medium_health_offset
        self.high_health_max = high_health_max
        self.high_health_min = high_health_min
        self.high_health_offset = high_health_offset
        self.full_health_max = full_health_max
        self.full_health_min = full_health_min
        self.full_health_offset = full_health_offset
        self.very_low_health_threshold = very_low_health_threshold
        self.low_health_threshold = low_health_threshold
        self.medium_health_threshold = medium_health_threshold
        self.high_health_threshold = high_health_threshold

    def health_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        # Health factor
        health = Agent.GetHealth(target_agent_id)
        score_max, score_min, score_offset = self._health_factors(health, score_max, score_min, score_offset)

        return score_max, score_min, score_offset

    def _health_factors(self, health, score_max, score_min, score_offset):
        if health <= self.very_low_health_threshold:
            score_max += self.very_low_health_max
            score_min += self.very_low_health_min
            score_offset += self.very_low_health_offset
        elif health <= self.low_health_threshold:
            score_max += self.low_health_max
            score_min += self.low_health_min
            score_offset += self.low_health_offset
        elif health <= self.medium_health_threshold:
            score_max += self.medium_health_max
            score_min += self.medium_health_min
            score_offset += self.medium_health_offset
        elif health <= self.high_health_threshold:
            score_max += self.high_health_max
            score_min += self.high_health_min
            score_offset += self.high_health_offset
        else:
            score_max += self.full_health_max
            score_min += self.full_health_min
            score_offset += self.full_health_offset
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        string = "Health => (max, min, score)"

        for _range in [0,0.20,0.40,0.50,0.60,0.80,1]:
            nearby = self._health_factors(_range, 0, 0, 0)
            string += f"""
    {round(_range*100)}% => {nearby} """

        return string
