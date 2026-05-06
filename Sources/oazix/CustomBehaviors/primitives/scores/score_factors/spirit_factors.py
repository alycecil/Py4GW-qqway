from typing import override

from Py4GWCoreLib import Agent
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class spirit_factor_DefaultScoreFactors(ScoreDefinition):

    def __init__(
            self,
            score_offset: float = -15,
            score_max: float = -25,
            score_min: float = 0,
    ):
        super().__init__()
        self.score_offset: float = score_offset
        self.score_max: float = score_max
        self.score_min: float = score_min

    def spirit_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id):

        if Agent.IsSpirit(target_agent_id):
            score_offset += self.score_offset
            score_max += self.score_max
            score_min += self.score_min

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""spirit_factor => {self.score_max}, {self.score_min}, {self.score_offset}"""

class never_target_spirits_factor(spirit_factor_DefaultScoreFactors):

    def __init__(
            self,
            score_offset: float = 0,
            score_max: float = 0,
            score_min: float = 0,
    ):
        super().__init__(score_offset, score_max, score_min)

    def spirit_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id):

        if Agent.IsSpirit(target_agent_id):
            score_offset = self.score_offset
            score_max = self.score_max
            score_min = self.score_min

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""spirit_factor => {self.score_max}, {self.score_min}, {self.score_offset}"""