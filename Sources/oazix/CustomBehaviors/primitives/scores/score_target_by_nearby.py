from typing import Callable, Generic, override

from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.default_score_factors import \
    condition_factor_DefaultScoreFactors, target_type_factor_DefaultScoreFactors, \
    called_target_factor_DefaultScoreFactors, hex_factor_DefaultScoreFactors, distance_factor_DefaultScoreFactors, \
    in_range_factor_DefaultScoreFactors, spirit_factor_DefaultScoreFactors, health_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill


class ScorePerAgentWeightedBySkillDefinition(ScoreDefinition):

    def __init__(
            self,
            skill: CustomSkill,
            in_range_factor: in_range_factor_DefaultScoreFactors,
            condition_factor: condition_factor_DefaultScoreFactors = condition_factor_DefaultScoreFactors(),
            target_type_factor: target_type_factor_DefaultScoreFactors = target_type_factor_DefaultScoreFactors(),
            called_target_factor: called_target_factor_DefaultScoreFactors = called_target_factor_DefaultScoreFactors(),
            hex_factor: hex_factor_DefaultScoreFactors = hex_factor_DefaultScoreFactors(),
            spirit_factor: spirit_factor_DefaultScoreFactors = spirit_factor_DefaultScoreFactors(),
            distance_factor: distance_factor_DefaultScoreFactors = distance_factor_DefaultScoreFactors(),
            health_factor: health_factor_DefaultScoreFactors = health_factor_DefaultScoreFactors(),
            ):
        super().__init__()
        self.in_range_factor = in_range_factor
        self.custom_skill = skill

        self.score_max = 55.0
        self.score_min = 0.0
        self.score_offset = 0.0

        self.condition_factor = condition_factor
        self.target_type_factor = target_type_factor
        self.called_target_factor = called_target_factor
        self.hex_factor = hex_factor
        self.spirit_factor = spirit_factor
        self.distance_factor = distance_factor
        self.health_factor = health_factor

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

        score_max, score_min, score_offset = self.called_target_factor.called_target_factor(
            score_max, score_min, score_offset,
            agent_xy, custom_skill_skill_id, target_agent_id)

        score_max, score_min, score_offset = self.condition_factor.condition_factor(
            score_max, score_min, score_offset,
            target_agent_id)

        score_max, score_min, score_offset = self.hex_factor.hex_factor(
            score_max, score_min, score_offset,
            custom_skill_skill_id, target_agent_id)

        score_max, score_min, score_offset = self.target_type_factor.target_type_factor(
            score_max, score_min, score_offset,
            target_agent_id)

        score_max, score_min, score_offset = self.health_factor.health_factor(
            score_max, score_min, score_offset,
            target_agent_id)

        score_max, score_min, score_offset = self.distance_factor.distance_factor(
            score_max, score_min, score_offset,
            distance, short_range)

        score_max, score_min, score_offset = self.in_range_factor.in_range_factor(
            score_max, score_min, score_offset,
            short_range, target.enemy_quantity_within_range)

        score_max, score_min, score_offset = self.spirit_factor.spirit_factor(
            score_max, score_min, score_offset,
            target)

        return min(
            max(
                min(score_max, score_offset),
                score_min
            ),
            89
        )

    @override
    def score_definition_debug_ui(self) -> str:
        score_max, score_min, score_offset = self.default_scoring()

        return f"""is_short_range={self.is_short_range()}
{self.condition_factor.score_definition_debug_ui()}
{self.target_type_factor.score_definition_debug_ui()}
{self.called_target_factor.score_definition_debug_ui()}
{self.hex_factor.score_definition_debug_ui()}
{self.spirit_factor.score_definition_debug_ui()}
{self.distance_factor.score_definition_debug_ui()}
{self.health_factor.score_definition_debug_ui()}
defaults before modifiers:
    score = ({score_min} - {score_max}),
    offset = {score_offset}
"""
