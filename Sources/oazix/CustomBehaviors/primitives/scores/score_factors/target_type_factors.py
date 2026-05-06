from typing import override

from Py4GWCoreLib import Agent
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class target_type_factor_DefaultScoreFactors(ScoreDefinition):

    def __init__(
            self,
            caster_factor: float = 3.0,
            non_caster_factor: float = 0.0,
    ):
        super().__init__()
        self.caster_factor: float = caster_factor
        self.non_caster_factor: float = non_caster_factor

    def target_type_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsCaster(target_agent_id):
            score_offset += self.caster_factor
        else:
            score_offset += self.non_caster_factor

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""caster += {self.caster_factor}
noncaster += {self.non_caster_factor}"""


class target_type_moving_factor(target_type_factor_DefaultScoreFactors):

    def __init__(
            self,
            moving_factor: float = 3.0,
            not_moving_factor: float = 0.0,
    ):
        super().__init__(moving_factor, not_moving_factor)
        self.moving_factor = moving_factor
        self.not_moving_factor = not_moving_factor

    def target_type_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsMoving(target_agent_id):
            score_offset += self.moving_factor
        else:
            score_offset += self.not_moving_factor

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""isMoving += {self.moving_factor}
not_moving_factor += {self.not_moving_factor}"""
