from typing import Callable, Generic, override

from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill


class ScorePerAgentWeightedBySkillDefinition(ScoreDefinition):

    def __init__(
            self,
            skill: CustomSkill,
            agents_nearby_factor: ScorePerAgentQuantityDefinition,

            ):
        super().__init__()
        self.callable_score: ScorePerAgentQuantityDefinition = agents_nearby_factor
        self.custom_skill = skill

        self.score_max = 55.0
        self.score_min = 0.0
        self.score_offset = 0.0

    def default_scoring(self):
        return self.score_max, self.score_min, self.score_offset

    def is_short_range(self):
        short_range = False
        if (GLOBAL_CACHE.Skill.Flags.IsTouchRange(self.custom_skill.skill_id) or
                GLOBAL_CACHE.Skill.Flags.IsAttack(self.custom_skill.skill_id)):
            short_range = True
        return short_range

    def get_score(self, target: custom_behavior_helpers.SortableAgentData) -> float:
        target_agent_id = target.agent_id
        custom_skill_skill_id = self.custom_skill.skill_id

        agent_xy = Agent.GetXY(target_agent_id)
        player_xy = Player.GetXY()
        distance = Utils.Distance(agent_xy, player_xy)

        # is short range skill?
        short_range = self.is_short_range()

        score_max, score_min, score_offset = self.default_scoring()

        score_max, score_min, score_offset = self.called_target_factor(
            score_max, score_min, score_offset,
            agent_xy, custom_skill_skill_id, target_agent_id)

        score_max, score_min, score_offset = self.condition_factor(
            score_max, score_min, score_offset,
            target_agent_id)

        score_max, score_min, score_offset = self.hex_factor(
            score_max, score_min, score_offset,
            custom_skill_skill_id, target_agent_id)

        score_max, score_min, score_offset = self.target_type_factor(
            score_max, score_min, score_offset,
            target_agent_id)

        score_max, score_min, score_offset = self.health_factor(
            score_max, score_min, score_offset,
            target_agent_id)

        score_max, score_min, score_offset = self.distance_factor(
            score_max, score_min, score_offset,
            distance, short_range)

        score_max, score_min, score_offset = self.in_range_factor(
            score_max, score_min, score_offset,
            short_range, target)

        score_max, score_min, score_offset = self.spirit_factor(
            score_max, score_min, score_offset,
            target)

        return min(
            max(
                min(score_max, score_offset),
                score_min
            ),
            89
        )

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

    def get_score_for_agent_count(self, agent_quantity: int) -> float:
        return self.callable_score.get_score(agent_quantity)

    def in_range_factor(
            self,
            score_max, score_min, score_offset,
            short_range, target
    ):
        nearby_weight = self.get_score_for_agent_count(target.enemy_quantity_within_range)
        if nearby_weight is None:
            nearby_weight = 0
        if short_range:
            nearby_weight /= 10.0
        return score_max, score_min, score_offset + nearby_weight

    def health_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        # Health factor
        health = Agent.GetHealth(target_agent_id)
        if health < .15:
            score_max += 7.5
            score_min += 15.0
            score_offset += 6
        elif health < .5:
            score_max += 10.0
            score_min += 17.0
            score_offset += 5
        elif health < .75:
            score_max += 5.0
            score_min += 15.0
            score_offset += 3

        return score_max, score_min, score_offset

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

        if Player.GetTargetID() == party_target_id:
            score_max += 6.0
            score_offset += 6.0

        return score_max, score_min, score_offset


    def condition_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsDeepWounded(target_agent_id):
            score_offset += 5.0

        return score_max, score_min, score_offset

    def target_type_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id
    ):
        if Agent.IsCaster(target_agent_id):
            score_offset += 3.0

        return score_max, score_min, score_offset

    def hex_factor(
            self,
            score_max, score_min, score_offset,
            custom_skill_skill_id, target_agent_id):

        not_hexed_factor=2.0
        already_hexed_factor=1.0

        if GLOBAL_CACHE.Skill.Flags.IsHex(custom_skill_skill_id):
            if not Agent.IsHexed(target_agent_id):
                score_offset += not_hexed_factor
            else:
                score_offset -= already_hexed_factor
        else:
            if not Agent.IsHexed(target_agent_id):
                score_offset -= not_hexed_factor
            else:
                score_offset += already_hexed_factor

        return score_max, score_min, score_offset

    def spirit_factor(
            self,
            score_max, score_min, score_offset,
            target_agent_id):

        if Agent.IsSpirit(target_agent_id):
            score_offset -= 15
            score_max -= 25

        return score_max, score_min, score_offset

    @override
    def score_definition_debug_ui(self) -> str:
        score_max, score_min, score_offset = self.default_scoring()

        return f"""is_short_range={self.is_short_range()}
{self.callable_score.score_definition_debug_ui()}
defaults before modifiers:
    score = ({score_min} - {score_max}),
    offset = {score_offset}
"""