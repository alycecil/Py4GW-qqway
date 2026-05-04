from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import DistanceFactors_Short
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.hex_factors import Simple_Hex_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.target_type_factors import target_type_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility


class AssassinSkillsProvider:
    """
    Provider for assassin utility skills.
    These skills focus on dagger attacks, teleportation, and stealth.
    """
    
    @classmethod
    def get_skills(cls, event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of assassin utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of assassin utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        jagged_strike_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=event_bus, skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        fox_fangs_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=event_bus, skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        death_blossom_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=event_bus, skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        skills.append(jagged_strike_utility)
        skills.append(fox_fangs_utility)
        skills.append(death_blossom_utility)
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Dash"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10), mana_required_to_cast=10,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Deaths_Charge"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            mana_required_to_cast=15,
            ignore_spirits=True,
            hex_factor=Simple_Hex_Factors(not_hexed_factor=0, already_hexed_factor=1, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=3.0, non_caster_factor=-10),
            distance_factor=DistanceFactors_Short(touch=10, adjacent=0, nearby=0, area=0, twice_area=20, earshot=7),
            custom_agent_targeting_predicate=lambda agent_id: (Agent.GetHealth(Player.GetAgentID()) < 0.5),
            override_skill_range=Range.Touch.value,
        ))

        return skills
