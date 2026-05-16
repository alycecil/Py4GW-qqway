from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.enums_src.Model_enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import DistanceFactors_Short
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.hex_factors import Simple_Hex_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.target_type_factors import target_type_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_spirit_utility import RawSpiritUtility


class RangerSkillsProvider:
    """
    Provider for ranger utility skills.
    These skills focus on pet management, preparations, and nature spirits.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of ranger utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of ranger utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Run_as_One"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            target_self=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Apply_Poison"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Never_Rampage_Alone"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Feral_Aggression"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Call_of_Protection"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80), mana_required_to_cast=5,
            renew_before_expiration_in_milliseconds=130,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Call_of_Haste"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=130,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Predatory_Bond"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(40), mana_required_to_cast=20,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Throw_Dirt"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 21 if enemy_qte >= 3 else 15 if enemy_qte == 2 else 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
            hex_factor=Simple_Hex_Factors(not_hexed_factor=0, already_hexed_factor=1, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=-15.0, non_caster_factor=10),
            distance_factor=DistanceFactors_Short(touch=40),
        ))
        # Quickening_Zephyr QZ
        qz_util = RawSpiritUtility(
            event_bus=event_bus, skill=CustomSkill("Quickening_Zephyr"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(85),
            owned_spirit_model_id=SpiritModelID.QUICKENING_ZEPHYR,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        )
        serpents_quickness_prep_utility: CustomSkillUtilityBase = PreparationUtility(
            event_bus=event_bus,
            prep_skill=CustomSkill("Serpents_Quickness"),
            target_utilities=[
                qz_util,
            ],
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(94)
        )
        skills.append(qz_util)
        skills.append(serpents_quickness_prep_utility)

        common_scoring = ScorePerAgentQuantityDefinition(
            lambda enemy_qte: 16 if enemy_qte >= 2 else 13 if enemy_qte == 1 else 10)

        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Dual_Shot"),
            current_build=in_game_build,
            score_definition=common_scoring,
            mana_required_to_cast=10,
            ignore_spirits=True,
            override_skill_range=Range.Earshot.value,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Power_Shot"),
            current_build=in_game_build,
            score_definition=common_scoring,
            mana_required_to_cast=10,
            ignore_spirits=True,
            override_skill_range=Range.Earshot.value,
        ))

        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Troll_Unguent"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10), mana_required_to_cast=5,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO],
            target_self=False,
            condition=lambda agent_id: Agent.GetHealth(Player.GetAgentID()) < 0.9
        ))
        
        return skills
