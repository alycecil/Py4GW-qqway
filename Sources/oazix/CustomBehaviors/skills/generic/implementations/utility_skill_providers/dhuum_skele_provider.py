from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuums_rest_utility import DhuumsRestUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.ghostly_fury_utility import GhostlyFuryUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.reversal_of_death_utility import ReversalOfDeathUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.encase_skeletal_utility import EncaseSkeletalUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.spiritual_healing_utility import SpiritualHealingUtility


class DhuumSkeleProvider:
    """
    Provider for Dhuum phase-specific utility skills.
    These skills are used during the Dhuum encounter in the Underworld.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of Dhuum phase utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of Dhuum phase utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        # Dhuum phase
        skills.append(SpiritualHealingUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(ReversalOfDeathUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(DhuumsRestUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(GhostlyFuryUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(EncaseSkeletalUtility(event_bus=event_bus, current_build=in_game_build))
        
        return skills
