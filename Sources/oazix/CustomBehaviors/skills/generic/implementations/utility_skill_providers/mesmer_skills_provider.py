from Py4GWCoreLib import Agent, GLOBAL_CACHE, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import DistanceFactors_Short
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.hex_factors import Simple_Hex_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.target_type_factors import target_type_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.generic.apply_hex_simple_utility import ApplyHexCommonUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.monk.cure_hex_utility import CureHexUtility


class MesmerSkillsProvider:
    """
    Provider for mesmer utility skills.
    These skills focus on hexes, interrupts, and crowd control.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of mesmer utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of mesmer utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(ApplyHexCommonUtility(
            event_bus=event_bus, skill=CustomSkill("Shrinking_Armor"), current_build=in_game_build,
        ))
        skills.append(ApplyHexCommonUtility(
            event_bus=event_bus, skill=CustomSkill("Empathy"), current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            hex_factor=Simple_Hex_Factors(not_hexed_factor=20, already_hexed_factor=-5, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=-15.0, non_caster_factor=10)
        ))
        skills.append(ApplyHexCommonUtility(
            event_bus=event_bus, skill=CustomSkill("Empathy_(PvP)"), current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            hex_factor=Simple_Hex_Factors(not_hexed_factor=20, already_hexed_factor=-5, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=-15.0, non_caster_factor=10)
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, current_build=in_game_build,
            skill=CustomSkill("Mantra_of_Frost"),
            score_definition=ScoreStaticDefinition(60)
        ))
        skills.append(EbonBattleStandardOfHonorUtility(
            event_bus=event_bus, current_build=in_game_build, skill=CustomSkill("Time_Ward"),
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 60 if enemy_qte >= 3 else 45 if enemy_qte <= 2 else 21)
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Disruption"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80),
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsCasting(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.33, # only skills that are longer than 1s. too much changes to fail otherwise
            distance_factor=DistanceFactors_Short()
        ))
        skills.append(CureHexUtility(
                event_bus=event_bus, skill=CustomSkill("Hex_Eater_Signet"),
                current_build=in_game_build
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Ether_Feast"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            mana_required_to_cast=10,
            ignore_spirits=True,
            hex_factor=Simple_Hex_Factors(not_hexed_factor=0, already_hexed_factor=1, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=3.0, non_caster_factor=-10),
            distance_factor=DistanceFactors_Short(touch=10, adjacent=0, nearby=0, area=0, twice_area=20, earshot=7),
            custom_agent_targeting_predicate=lambda agent_id: (Agent.GetHealth(Player.GetAgentID()) < 0.5),
            override_skill_range=Range.Earshot.value,
        ))
        skills.append(ApplyHexCommonUtility(
            event_bus=event_bus, skill=CustomSkill("Backfire"), current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            hex_factor=Simple_Hex_Factors(not_hexed_factor=20, already_hexed_factor=-5, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=15.0, non_caster_factor=-20)
        ))
        
        return skills
