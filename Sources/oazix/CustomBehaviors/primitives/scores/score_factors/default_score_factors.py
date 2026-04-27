from typing import Callable, Generic, override

from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill


class condition_factor_DefaultScoreFactors(ScoreDefinition):
    def condition_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsDeepWounded(target_agent_id):
            score_offset += 5.0

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""prefer deep wound += 5"""


class target_type_factor_DefaultScoreFactors(ScoreDefinition):
    def target_type_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsCaster(target_agent_id):
            score_offset += 3.0

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        return f"""prefer caster += 3"""


class health_factor_DefaultScoreFactors(ScoreDefinition):
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
        if health <= .15:
            score_max += 7.5
            score_min += 15.0
            score_offset += 6
        elif health <= .5:
            score_max += 10.0
            score_min += 17.0
            score_offset += 5
        elif health <= .75:
            score_max += 5.0
            score_min += 15.0
            score_offset += 3
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        string = "Health => (max, min, score)"

        for _range in [0,0.25,0.50,0.75,1]:
            nearby = self._health_factors(_range, 0, 0, 0)
            string += f"""
    {round(_range*100)}% => {nearby} """

        return string


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


class hex_factor_DefaultScoreFactors(ScoreDefinition):

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


class in_range_factor_DefaultScoreFactors(ScoreDefinition):

    def __init__(
            self,
            agents_nearby_factor: ScorePerAgentQuantityDefinition,

    ):
        super().__init__()
        self.callable_score: ScorePerAgentQuantityDefinition = agents_nearby_factor

    def get_score_for_agent_count(self, agent_quantity: int) -> float:
        return self.callable_score.get_score(agent_quantity)

    def in_range_factor(
            self,
            score_max, score_min, score_offset,
            short_range, enemy_quantity_within_range
    ):
        nearby_weight = self.get_score_for_agent_count(enemy_quantity_within_range)
        if nearby_weight is None:
            nearby_weight = 0
        if short_range:
            nearby_weight /= 10.0
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


class distance_factor_DefaultScoreFactors(ScoreDefinition):

    def distance_factor(
            self,
            score_max, score_min, score_offset,
            distance, short_range
    ):
        # Distance factor
        if distance < Range.Touch.value:
            score_offset += 50 if short_range else 2.2
        elif distance < Range.Adjacent.value:
            score_offset += 35 if short_range else 2
        elif distance < Range.Nearby.value:
            score_offset += 20 if short_range else 1.5
        elif distance < Range.Area.value:
            score_offset += 10 if short_range else 1.1
        elif distance < Range.Area.value * 2:
            score_offset += 5 if short_range else 0.5
        elif distance < Range.Earshot.value:
            score_offset += 1 if short_range else 0.1
        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        string = "distance => (max, min, score) (not short range)"

        for _range in [Range.Touch, Range.Adjacent, Range.Nearby, Range.Area, Range.Earshot]:
            nearby = self.distance_factor(0, 0, 0, _range.value - 1, True)
            longer = self.distance_factor(0, 0, 0, _range.value - 1, False)
            string += f"""
    {_range.name} => {nearby} ({longer})"""

        return string


