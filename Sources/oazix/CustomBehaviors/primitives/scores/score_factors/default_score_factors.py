from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


class called_target_factor_DefaultScoreFactors(ScoreDefinition):
    def __init__(
            self,
            party_target_max_bonus: float = 25.0,
            party_target_offset_bonus: float = 45.0,
            party_target_min_bonus: float = 40.0,
            near_party_target_max_bonus: float = 20.0,
            near_party_target_offset_bonus: float = 25.0,
            near_party_target_min_bonus: float = 20.0,
            current_target_matches_party_max_bonus: float = 6.0,
            current_target_matches_party_offset_bonus: float = 6.0,
            current_target_matches_target_max_bonus: float = 6.0,
            current_target_matches_target_offset_bonus: float = 6.0,
    ):
        self.party_target_max_bonus = party_target_max_bonus
        self.party_target_offset_bonus = party_target_offset_bonus
        self.party_target_min_bonus = party_target_min_bonus
        self.near_party_target_max_bonus = near_party_target_max_bonus
        self.near_party_target_offset_bonus = near_party_target_offset_bonus
        self.near_party_target_min_bonus = near_party_target_min_bonus
        self.current_target_matches_party_max_bonus = current_target_matches_party_max_bonus
        self.current_target_matches_party_offset_bonus = current_target_matches_party_offset_bonus
        self.current_target_matches_target_max_bonus = current_target_matches_target_max_bonus
        self.current_target_matches_target_offset_bonus = current_target_matches_target_offset_bonus

    def called_target_factor(
            self,
            score_max, score_min, score_offset,
            agent_xy, custom_skill_skill_id, target_agent_id
    ):

        # Called target more important
        party_target_id = Routines.Party.GetPartyTargetID()
        if party_target_id == target_agent_id:
            score_max += self.party_target_max_bonus
            score_offset += self.party_target_offset_bonus
            score_min += self.party_target_min_bonus
        else:
            called_target_xy = Agent.GetXY(party_target_id)
            distance_called_target = Utils.Distance(agent_xy, called_target_xy)
            target_range = GLOBAL_CACHE.Skill.Data.GetAoERange(custom_skill_skill_id)
            if target_range is None:
                target_range = Range.Touch.value

            if distance_called_target < target_range:
                score_max += self.near_party_target_max_bonus
                score_offset += self.near_party_target_offset_bonus
                score_min += self.near_party_target_min_bonus

        current_target = Player.GetTargetID()
        if current_target == party_target_id:
            score_max += self.current_target_matches_party_max_bonus
            score_offset += self.current_target_matches_party_offset_bonus

        if current_target == target_agent_id:
            score_max += self.current_target_matches_target_max_bonus
            score_offset += self.current_target_matches_target_offset_bonus

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""Prefer called target, if not available then in range nearbies
add offset for current player target and even more so if its the party target"""


