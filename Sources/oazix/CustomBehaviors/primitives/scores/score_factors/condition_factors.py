from typing import override

from Py4GWCoreLib import Agent
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class Condition_Factors(ScoreDefinition):
    def condition_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""No condition factors"""


class condition_factor_prefer_omni(Condition_Factors):
    def condition_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsDeepWounded(target_agent_id):
            score_offset += 5.0

        if Agent.IsKnockedDown(target_agent_id):
            score_offset += 1.0

        if Agent.IsBleeding(target_agent_id):
            score_offset += 1.0

        if Agent.IsPoisoned(target_agent_id):
            score_offset += 1.0

        if Agent.IsCrippled(target_agent_id):
            score_offset += 1.001

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""prefer deep wound += 5"""


class condition_factor_crippled(Condition_Factors):
    def __init__(
            self,
            crippled_already_offset: int | None = None,
            crippled_already_max: int | None = None,
            crippled_already_min: int | None = None,
            not_crippled_already_offset: int | None = None,
            not_crippled_already_max: int | None = None,
            not_crippled_already_min: int | None = None,
    ):
        self.crippled_already_offset = crippled_already_offset
        self.crippled_already_max = crippled_already_max
        self.crippled_already_min = crippled_already_min
        self.not_crippled_already_offset = not_crippled_already_offset
        self.not_crippled_already_max = not_crippled_already_max
        self.not_crippled_already_min = not_crippled_already_min

    def condition_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsCrippled(target_agent_id):
            if self.crippled_already_offset is not None:
                score_offset += self.crippled_already_offset
            if self.crippled_already_max is not None:
                score_max = self.crippled_already_max
            if self.crippled_already_min is not None:
                score_min = self.crippled_already_min
        else:
            if self.not_crippled_already_offset is not None:
                score_offset += self.not_crippled_already_offset
            if self.not_crippled_already_max is not None:
                score_max = self.not_crippled_already_max
            if self.not_crippled_already_min is not None:
                score_min = self.not_crippled_already_min

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""Is Crippled => {self.crippled_already_max}, {self.crippled_already_min}, {self.crippled_already_offset}
Is Not Crippled => {self.not_crippled_already_max}, {self.not_crippled_already_min}, {self.not_crippled_already_offset}"""
