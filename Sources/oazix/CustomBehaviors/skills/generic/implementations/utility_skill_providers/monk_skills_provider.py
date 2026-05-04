from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_utility import RawSimpleHealUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_party_heal_utility import RawSimplePartyHealUtility


class MonkSkillsProvider:
    """
    Provider for monk utility skills.
    These skills focus on healing and party support.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of monk utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of monk utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(RawSimplePartyHealUtility(event_bus=event_bus, skill=CustomSkill("Divine_Healing"),
                                                current_build=in_game_build,
                                                score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(RawSimplePartyHealUtility(event_bus=event_bus, skill=CustomSkill("Heavens_Delight"),
                                                current_build=in_game_build,
                                                score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Patient_Spirit"), current_build=in_game_build,
                                 score_definition=ScorePerHealthGravityDefinition(1))
        )
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Healing_Burst"), current_build=in_game_build,
                                 score_definition=ScorePerHealthGravityDefinition(1))
        )
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Orison_of_Healing"), current_build=in_game_build,
                                 score_definition=ScorePerHealthGravityDefinition(3))
        )
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Balthazars_Pendulum"), current_build=in_game_build,
                                 mana_required_to_cast=20,
                                 score_definition=ScorePerHealthGravityDefinition(0.75))
        )
        
        return skills
