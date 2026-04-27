from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


class called_target_factor_DefaultScoreFactors(ScoreDefinition):
    def called_target_factor(
            self,
            score_max, score_min, score_offset,
            agent_xy, custom_skill_skill_id, target_agent_id
    ):

        # Called target more important
        party_target_id = Routines.Party.GetPartyTargetID()
        if party_target_id == target_agent_id:
            score_max += 25.0
            score_offset += 45.0
            score_min += 40.0
        else:
            called_target_xy = Agent.GetXY(party_target_id)
            distance_called_target = Utils.Distance(agent_xy, called_target_xy)
            target_range = GLOBAL_CACHE.Skill.Data.GetAoERange(custom_skill_skill_id)
            if target_range is None:
                target_range = Range.Touch.value

            if distance_called_target < target_range:
                score_max += 20.0
                score_offset += 25.0
                score_min += 20.0

        current_target = Player.GetTargetID()
        if current_target == party_target_id:
            score_max += 6.0
            score_offset += 6.0

        if current_target == target_agent_id:
            score_max += 6.0
            score_offset += 6.0

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""Prefer called target, if not available then in range nearbies
add offset for current player target and even more so if its the party target"""


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

