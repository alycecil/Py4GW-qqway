from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import DistanceFactors_Short
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_self_utility import RawSimpleHealSelfUtility
from Sources.oazix.CustomBehaviors.skills.paragon.watch_yourself_utility import WatchYourselfPowerbatteryUtility
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


class WarriorSkillsProvider:
    """
    Provider for warrior utility skills.
    These skills focus on melee attacks, shouts, and adrenaline management.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of warrior utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of warrior utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(RawSimpleAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Renewing_Smash"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(75),
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsKnockedDown(agent_id) and Utils.Distance(
                Player.GetXY(), Agent.GetXY(agent_id)) < Range.Adjacent.value
        ))
        distance_factors_short = DistanceFactors_Short(
            touch=50,
            adjacent=20,
            nearby=10,
            area=3,
            twice_area=2,
            earshot=1,
            beyond_earshot=0,
        )
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Soldiers_Strike"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            distance_factor=distance_factors_short,
            override_skill_range=Range.Touch.value,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Thrill_of_Victory"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            custom_agent_targeting_predicate=lambda agent_id: Agent.GetHealth(agent_id) < 0.5 < Agent.GetHealth(Player.GetAgentID()),
            distance_factor=distance_factors_short,
            override_skill_range=Range.Touch.value,
        ))
        # Warrior # AOE
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Whirlwind_Attack"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 69 if enemy_qte >= 3 else 63 if enemy_qte == 2 else 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
            override_skill_range=Range.Adjacent.value,
            distance_factor=distance_factors_short,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Crude_Swing"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 68 if enemy_qte >= 3 else 62 if enemy_qte == 2 else 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
            override_skill_range=Range.Touch.value,
            distance_factor=distance_factors_short,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Cyclone_Axe"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 22 if enemy_qte >= 3 else 18 if enemy_qte == 2 else 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
            override_skill_range=Range.Touch.value,
            distance_factor=distance_factors_short,
        ))

        # Common support for this archetype
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus,
            skill=CustomSkill("For_Great_Justice"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(92),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        ))

        # Core axe attacks
        skills.append(RawSimpleAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Dismember"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(74),
        ))
        skills.append(RawSimpleAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Axe_Rake"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
        ))
        skills.append(RawSimpleAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Executioners_Strike"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(69),
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus,
            skill=CustomSkill("Endure_Pain"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus,
            skill=CustomSkill("Call_of_Protection"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(65),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Earth_Shaker"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 71 if enemy_qte >= 3 else 70 if enemy_qte == 2 else 50),
            mana_required_to_cast=0,
            ignore_spirits=True,
            override_skill_range=Range.Adjacent.value,
            distance_factor=distance_factors_short,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Distracting_Blow"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 70.1 if enemy_qte >= 3 else 63.1 if enemy_qte == 2 else 50),
            mana_required_to_cast=0,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsCasting(agent_id),
            within_range=Range.Touch,
            override_skill_range=Range.Touch.value,
            distance_factor=distance_factors_short,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Yeti_Smash"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 6 if enemy_qte >= 3 else 1 if enemy_qte == 2 else 0),
            mana_required_to_cast=0,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsConditioned(agent_id),
            within_range=Range.Adjacent,
            override_skill_range=Range.Adjacent.value,
            distance_factor=distance_factors_short,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("For_Great_Justice"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15), mana_required_to_cast=9,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO],
            target_self=False,
        ))
        # Shouts Section
        # Really should be limited to imbagon but whatever
        skills.append(WatchYourselfPowerbatteryUtility(
            event_bus=event_bus,
            current_build=in_game_build))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Sprint"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10), mana_required_to_cast=12,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("You_Will_Die"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            mana_required_to_cast=10,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: Agent.GetHealth(agent_id) < 0.89,
            within_range=Range.Adjacent,
            override_skill_range=Range.Adjacent.value,
        ))
        skills.append(RawSimpleHealSelfUtility(
            event_bus=event_bus,
            skill=CustomSkill("Healing_Signet"),
            current_build=in_game_build,
        ))
        # TODO if we're hurt
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Endure_Pain"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10), mana_required_to_cast=12,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Signet_of_Strength"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10), mana_required_to_cast=0,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        
        return skills
