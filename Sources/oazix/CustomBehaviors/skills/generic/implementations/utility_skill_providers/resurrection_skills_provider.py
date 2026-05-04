from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility


class ResurrectionSkillsProvider:
    """
    Provider for resurrection utility skills.
    These skills are used to bring fallen allies back to life.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of resurrection utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of resurrection utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Flesh_of_My_Flesh"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Return"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrect"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Chant"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Signet"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Rebirth"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Sunspear_Rebirth_Signet"),
                                                 current_build=in_game_build))
        
        return skills
