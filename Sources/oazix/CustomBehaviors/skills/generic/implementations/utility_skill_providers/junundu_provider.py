from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


class JununduProvider:
    """
    Provider for Junundu-specific utility skills.
    These skills are used when the player is transformed into a Junundu wurm.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of Junundu utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of Junundu utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        # naive JUNUNDU version
        skills.append(RawSimpleAttackUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Strike"),
                                             current_build=in_game_build, score_definition=ScoreStaticDefinition(65)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Tunnel"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(67),
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO,
                                                              BehaviorState.FAR_FROM_AGGRO]))
        skills.append(
            RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Blinding_Breath"), current_build=in_game_build,
                                score_definition=ScorePerAgentQuantityDefinition(
                                    lambda enemy_qte: 70 if enemy_qte >= 2 else 69)))
        skills.append(RawSimpleAttackUtility(event_bus=event_bus, skill=CustomSkill("Burning_Breath"),
                                             current_build=in_game_build, score_definition=ScoreStaticDefinition(70),
                                             custom_agent_targeting_predicate=lambda agent_id: Utils.Distance(
                                                 Player.GetXY(), Agent.GetXY(agent_id)) > Range.Nearby.value))
        skills.append(
            RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Choking_Breath"), current_build=in_game_build,
                                score_definition=ScorePerAgentQuantityDefinition(
                                    lambda enemy_qte: 70 if enemy_qte >= 2 else 69),
                                custom_agent_targeting_predicate=lambda agent_id: Agent.IsCasting(agent_id)))
        skills.append(StubUtility(event_bus=event_bus, skill=CustomSkill("Leave_Junundu"), current_build=in_game_build))
        skills.append(
            StubUtility(event_bus=event_bus, skill=CustomSkill("Unknown_Junundu_Ability"), current_build=in_game_build))
        skills.append(
            RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Siege"), current_build=in_game_build,
                                score_definition=ScorePerAgentQuantityDefinition(
                                    lambda enemy_qte: 80 if enemy_qte >= 2 else 79),
                                custom_agent_targeting_predicate=lambda agent_id: Utils.Distance(Player.GetXY(),
                                                                                                 Agent.GetXY(
                                                                                                     agent_id)) > Range.Nearby.value))
        
        return skills
