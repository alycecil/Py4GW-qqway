from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_with_alcohol_level_definition import \
    ScoreWithAlcoholLevelDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.dwarven_stability import DwarvenStabilityUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.auto_combat_utility import AutoCombatUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility
from Sources.oazix.CustomBehaviors.skills.paragon.blazing_finale_utility import BlazingFinaleUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility
from Sources.oazix.CustomBehaviors.skills.paragon.holy_spear_utility import HolySpearUtility
from Sources.oazix.CustomBehaviors.skills.warrior.protectors_defense_utility import ProtectorsDefenseUtility


class ParagonSoldiersStance_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        #core
        self.dwarven_stability_utility: CustomSkillUtilityBase = DwarvenStabilityUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreWithAlcoholLevelDefinition(95,95))
        self.soldiers_stance_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Soldiers_Stance"), score_definition=ScoreStaticDefinition(94))

        #optional
        self.never_surrender: CustomSkillUtilityBase = ProtectiveShoutUtility(event_bus=self.event_bus, skill=CustomSkill("Never_Surrender"), current_build=in_game_build, allies_health_less_than_percent=0.7,allies_quantity_required=2,score_definition=ScoreStaticDefinition(88), allowed_states=[BehaviorState.IN_AGGRO])

        self.blazing_finale_utility: CustomSkillUtilityBase = BlazingFinaleUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(33))
        self.holy_spear_utility: CustomSkillUtilityBase = HolySpearUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 2 else 35 if enemy_qte <= 2 else 0))

        self.jagged_strike_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.fox_fangs_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.death_blossom_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.vicious_attack_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Vicious_Attack"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)

        #common
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.protectors_defense_utility: CustomSkillUtilityBase = ProtectorsDefenseUtility(event_bus=self.event_bus, current_build=in_game_build,score_definition=ScoreStaticDefinition(60))
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)

    
    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [

            self.dwarven_stability_utility,
            self.soldiers_stance_utility,

            self.never_surrender,
            self.blazing_finale_utility,
            self.holy_spear_utility,

            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,
            self.vicious_attack_utility,

            self.i_am_unstopabble,
            self.fall_back_utility,
            self.protectors_defense_utility,
            self.by_urals_hammer_utility,
            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.soldiers_stance_utility.custom_skill,
            self.dwarven_stability_utility.custom_skill,
        ]