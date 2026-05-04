from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.condition_factors import condition_factor_crippled
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import DistanceFactors_Short
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.target_type_factors import target_type_moving_factor
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.dervich.dervich_enchantment_utility import DervichEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.dervich.imbue_health_utility import ImbueHealthUtility
from Sources.oazix.CustomBehaviors.skills.dervich.pious_assault_utility import PiousAssault_Utility
from Sources.oazix.CustomBehaviors.skills.dervich.vow_of_revolution_utility import Vow_of_Revolution_KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_utility import RawSimpleHealUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_party_heal_utility import RawSimplePartyHealUtility


class DervishSkillsProvider:
    """
    Provider for dervish utility skills.
    These skills focus on enchantments, scythe attacks, and party support.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of dervish utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of dervish utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, current_build=in_game_build,
            skill=CustomSkill("Vital_Boon"),
            score_definition=ScoreStaticDefinition(15),
            renew_before_expiration_in_milliseconds=0,
            target_self=False, # no need
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, current_build=in_game_build,
            skill=CustomSkill("Mystic_Vigor"),
            score_definition=ScoreStaticDefinition(15),
            renew_before_expiration_in_milliseconds=0,
            target_self=False, # no need
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, current_build=in_game_build,
            skill=CustomSkill("Zealous_Renewal"),
            score_definition=ScoreStaticDefinition(15),
            renew_before_expiration_in_milliseconds=0,
            target_self=False, # no need
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ))
        skills.append(Vow_of_Revolution_KeepSelfEffectUpUtility(
            event_bus=event_bus, current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15),
        ))
        skills.append(ImbueHealthUtility(
            event_bus=event_bus, current_build=in_game_build,
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Dust_Cloak"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(11),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Intimidating_Aura"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Staggering_Force"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(11),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Hearth_of_Holy_Flame"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Sand_Shards"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Mirage_Cloak"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Rending_Aura"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Whirling_Charge"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Eremites_Zeal"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ))
        skills.append(PiousAssault_Utility(
            event_bus=event_bus, current_build=in_game_build,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Crippling_Sweep"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            distance_factor=DistanceFactors_Short(),
            condition_factor=condition_factor_crippled(crippled_already_max=10, not_crippled_already_offset=10),
            target_type_factor=target_type_moving_factor(not_moving_factor=-10),
            override_skill_range=Range.Touch.value,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Chilling_Victory"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 21 if enemy_qte >= 2 else 13 if enemy_qte == 1 else 10),
            mana_required_to_cast=10,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: Agent.GetHealth(agent_id) < Agent.GetHealth(Player.GetAgentID()),
            override_skill_range=Range.Touch.value,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Crippling_Victory"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 21 if enemy_qte >= 2 else 13 if enemy_qte == 1 else 10),
            mana_required_to_cast=10,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: Agent.GetHealth(agent_id) < Agent.GetHealth(Player.GetAgentID()),
            override_skill_range=Range.Touch.value,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Aura_Slicer"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            mana_required_to_cast=10,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: not Agent.IsConditioned(agent_id),
            override_skill_range=Range.Touch.value,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Zealous_Sweep"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 21 if enemy_qte >= 2 else 13 if enemy_qte == 1 else 10),
            mana_required_to_cast=10,
            ignore_spirits=True,
            override_skill_range=Range.Adjacent.value,
        ))
        skills.append(
            RawSimplePartyHealUtility(
                event_bus=event_bus, skill=CustomSkill("Mystic_Healing"),
                current_build=in_game_build,
                score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(
            RawSimplePartyHealUtility(
                event_bus=event_bus, skill=CustomSkill("Mystic_Healing_(PvP)"),
                current_build=in_game_build,
                score_definition=ScorePerHealthGravityDefinition(1)))
        # TODO depend on dervish enchantment
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Pious_Light"), current_build=in_game_build,
                                 score_definition=ScorePerHealthGravityDefinition(1))
        )
        #pve
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Eternal_Aura"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ))
        
        return skills
