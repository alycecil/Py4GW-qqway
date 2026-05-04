from Py4GWCoreLib import Agent
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import DistanceFactors_Short
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_targeted_utility import ProtectiveShoutTargetedUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.paragon.watch_yourself_utility import WatchYourselfPowerbatteryUtility


class ParagonSkillsProvider:
    """
    Provider for paragon utility skills.
    These skills focus on shouts, party support, and spear attacks.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of paragon utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of paragon utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(ProtectiveShoutUtility(
            event_bus=event_bus, skill=CustomSkill("Stand_Your_Ground"), current_build=in_game_build,
            allies_health_less_than_percent=0.99, allies_quantity_required=1,
            score_definition=ScoreStaticDefinition(88),
            allowed_states=[BehaviorState.IN_AGGRO])
        )
        skills.append(ProtectiveShoutTargetedUtility(
            event_bus=event_bus, skill=CustomSkill("Angelic_Bond"), current_build=in_game_build,
            allies_health_less_than_percent=0.5, allies_quantity_required=1,
            score_definition=ScoreStaticDefinition(60),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO,
                            BehaviorState.IDLE])
        )
        skills.append(ProtectiveShoutTargetedUtility(
            event_bus=event_bus, skill=CustomSkill("Help_Me"), current_build=in_game_build,
            allies_health_less_than_percent=0.7, allies_quantity_required=1,
            score_definition=ScoreStaticDefinition(88),
            allowed_states=[BehaviorState.IN_AGGRO])
        )
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Aggressive_Refrain"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO]),
        )
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Anthem_of_Fury"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=5000,  # cast as quick as we can even if we dontt use it
            allowed_states=[BehaviorState.IN_AGGRO]),
        )

        spear_distance_factor = DistanceFactors_Short(touch=5, adjacent=4, nearby=3, area=2, twice_area=1, earshot=1)
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Barbed_Spear"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            distance_factor=spear_distance_factor,
            within_range=Range.Earshot,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: not Agent.IsBleeding(agent_id),
            override_skill_range=Range.Touch.value,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Spear_of_Lightning"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            distance_factor=spear_distance_factor,
            within_range=Range.Earshot,
            ignore_spirits=True,
            override_skill_range=Range.Touch.value,
        ))
        
        return skills
