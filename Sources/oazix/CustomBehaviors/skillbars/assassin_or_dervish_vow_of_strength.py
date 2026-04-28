from typing import List, Any, Generator, Callable, override
import time
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.assassin.disrupting_dagger_utility import DisruptingDaggerUtility
from Sources.oazix.CustomBehaviors.skills.assassin.shroud_of_distress_utility import ShroudOfDistressUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.dervich.eremites_attack_utility import EremitesAttack_Utility
from Sources.oazix.CustomBehaviors.skills.generic.auto_combat_utility import AutoCombatUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility


class VowOfStrength_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        self.shroud_of_distress_utility: CustomSkillUtilityBase = ShroudOfDistressUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(81), current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.critical_eye_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Critical_Eye"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO])
        self.critical_agility_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Critical_Agility"), current_build=in_game_build, score_definition=ScoreStaticDefinition(70), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.way_of_the_master_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Way_of_the_Master"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.critical_defenses_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Critical_Defenses"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), allowed_states=[BehaviorState.IN_AGGRO])
        self.disrupting_dagger_utility: CustomSkillUtilityBase = DisruptingDaggerUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(90), current_build=in_game_build)

        self.EremitesAttack_Utility: CustomSkillUtilityBase = EremitesAttack_Utility(event_bus=self.event_bus, current_build=in_game_build)
        self.Vow_of_Strength_Utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Vow_of_Strength"),
                                                                                       current_build=in_game_build, score_definition=ScoreStaticDefinition(90),
                                                                                       allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.Sand_Shards_Utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Sand_Shards"),
                                                                                   current_build=in_game_build, score_definition=ScoreStaticDefinition(89),
                                                                                   allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
                                                                                   renew_before_expiration_in_milliseconds=-1) # let expire

        self.Aura_of_Thorns_utility: CustomSkillUtilityBase = StubUtility(event_bus=self.event_bus, skill=CustomSkill("Aura_of_Thorns"), current_build=in_game_build)
        self.Staggering_Force_utility: CustomSkillUtilityBase = StubUtility(event_bus=self.event_bus, skill=CustomSkill("Staggering_Force"), current_build=in_game_build)

        #common
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(event_bus=self.event_bus, score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build, mana_required_to_cast=18)
        # lower priority sin, as we are the baller!
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(20), current_build=in_game_build, mana_required_to_cast=10)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.EremitesAttack_Utility,
            self.Vow_of_Strength_Utility,
            self.Sand_Shards_Utility,
            self.Aura_of_Thorns_utility,
            self.Staggering_Force_utility,

            self.critical_eye_utility,
            self.critical_agility_utility,
            self.way_of_the_master_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_honor_utility,
            self.ebon_battle_standard_of_wisdom,
            self.critical_defenses_utility,
            self.shroud_of_distress_utility,
            self.disrupting_dagger_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.EremitesAttack_Utility.custom_skill,
            self.Vow_of_Strength_Utility.custom_skill,
        ]