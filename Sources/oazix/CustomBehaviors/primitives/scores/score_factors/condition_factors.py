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
    def __init__(
            self,
            deep_wound_offset: float = 5.0,
            knocked_down_offset: float = 1.0,
            bleeding_offset: float = 1.0,
            poisoned_offset: float = 1.0,
            crippled_offset: float = 1.001,
    ):
        self.deep_wound_offset = deep_wound_offset
        self.knocked_down_offset = knocked_down_offset
        self.bleeding_offset = bleeding_offset
        self.poisoned_offset = poisoned_offset
        self.crippled_offset = crippled_offset

    def condition_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsDeepWounded(target_agent_id):
            score_offset += self.deep_wound_offset

        if Agent.IsKnockedDown(target_agent_id):
            score_offset += self.knocked_down_offset

        if Agent.IsBleeding(target_agent_id):
            score_offset += self.bleeding_offset

        if Agent.IsPoisoned(target_agent_id):
            score_offset += self.poisoned_offset

        if Agent.IsCrippled(target_agent_id):
            score_offset += self.crippled_offset

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""prefer deep wound += {self.deep_wound_offset}
knocked down += {self.knocked_down_offset}
bleeding += {self.bleeding_offset}
poisoned += {self.poisoned_offset}
crippled += {self.crippled_offset}"""


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
