from typing import override

from Py4GWCoreLib import GLOBAL_CACHE, Agent
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class Hex_Factors(ScoreDefinition):

    def __init__(
            self,
            not_hexed_factor: float = 2.0,
            already_hexed_factor: float = 1.0,
    ):
        super().__init__()
        self.not_hexed_factor: float = not_hexed_factor
        self.already_hexed_factor: float = already_hexed_factor

    def hex_factor(
            self,
            score_max, score_min, score_offset,
            custom_skill_skill_id, target_agent_id):

        if GLOBAL_CACHE.Skill.Flags.IsHex(custom_skill_skill_id):
            if not Agent.IsHexed(target_agent_id):
                score_offset += self.not_hexed_factor
            else:
                score_offset -= self.already_hexed_factor
        else:
            if not Agent.IsHexed(target_agent_id):
                score_offset -= self.not_hexed_factor
            else:
                score_offset += self.already_hexed_factor

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""not_hexed_factor => {self.not_hexed_factor}
already_hexed_factor => {self.already_hexed_factor}"""
