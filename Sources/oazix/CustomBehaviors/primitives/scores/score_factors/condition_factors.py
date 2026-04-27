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
