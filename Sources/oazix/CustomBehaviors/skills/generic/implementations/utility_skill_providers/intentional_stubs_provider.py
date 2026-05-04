from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility


class IntentionalStubsProvider:
    """
    Provider for intentional stub utility skills.
    These are placeholder skills used for testing or future implementation.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of intentional stub utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of stub utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(
            StubUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Capture"), current_build=in_game_build))
        
        return skills
