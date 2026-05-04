from typing import override
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility

class Dervish_AoD_Heal_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        self.elite_skill_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Avatar_of_Dwayna"), current_build=in_game_build, score_definition=ScoreStaticDefinition(95), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.elite_skill_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.elite_skill_utility.custom_skill,
        ]