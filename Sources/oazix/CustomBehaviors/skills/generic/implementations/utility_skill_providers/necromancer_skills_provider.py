from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import MinionInvocationFromCorpseUtility


class NecromancerSkillsProvider:
    """
    Provider for necromancer utility skills.
    These skills focus on minion creation and corpse manipulation.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of necromancer utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of necromancer utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(
            MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Shambling_Horror"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Fiend"),
                                                        current_build=in_game_build,
                                                        score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Horror"),
                                                        current_build=in_game_build,
                                                        score_definition=ScoreStaticDefinition(25)))
        skills.append(
            MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Vampiric_Horror"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Minions"),
                                                        current_build=in_game_build,
                                                        score_definition=ScoreStaticDefinition(25)))
        
        return skills
