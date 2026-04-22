from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import \
    EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.aura_of_the_lich_utility import Aura_of_the_Lich_Utility
from Sources.oazix.CustomBehaviors.skills.necromancer.dark_aura_utility import DarkAuraUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.necrosis_utility import NecrosisUtility


class Aura_of_the_Lich_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core
        self.elite_skill_utility: CustomSkillUtilityBase = Aura_of_the_Lich_Utility(
            event_bus=self.event_bus,
            current_build=in_game_build
        )

        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(
            event_bus=self.event_bus,
            score_definition=ScoreStaticDefinition(71),
            current_build=in_game_build,
            mana_required_to_cast=15
        )

        self.necrosis_utility: CustomSkillUtilityBase = NecrosisUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 69),
        )

        self.masochism_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Masochism"), current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        self.dark_aura: CustomSkillUtilityBase = DarkAuraUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(80), current_build=in_game_build, mana_required_to_cast=10)

        self.serpents_quickness_prep_utility: CustomSkillUtilityBase = PreparationUtility(
            event_bus=self.event_bus,
            prep_skill=CustomSkill("Serpents_Quickness"),
            target_utilities=[self.elite_skill_utility,
                              self.necrosis_utility,
                              self.masochism_utility
                              ],
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(94),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        )

        self.dwarven_stability_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            skill=CustomSkill("Dwarven_Stability"),
            score_definition=ScoreStaticDefinition(95),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        )

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.elite_skill_utility,
            self.necrosis_utility,
            self.serpents_quickness_prep_utility,
            self.dwarven_stability_utility,
            self.ebon_vanguard_assassin_support,
            self.masochism_utility,
            self.dark_aura
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.elite_skill_utility.custom_skill,
        ]
