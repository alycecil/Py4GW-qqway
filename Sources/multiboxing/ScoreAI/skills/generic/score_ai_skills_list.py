from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

from ...primitives.skills.score_ai_skill_base import ScoreAISkillBase
from ...primitives.skills.score_ai_engine import ScoreAIEngine

from .implementations.simple_score_ai_skills import SimpleScoreAISkillsProvider


class ScoreAISkillsList:
    """
    Factory class for ScoreAI skills with agent_id support.
    Similar to CustomBehaviors GenericUtilitySkillsList but each skill
    provides scores for specific agent_id values.
    """
    
    def __init__(self):
        pass

    @staticmethod
    def get_score_ai_skills_list(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[ScoreAISkillBase]:
        """
        Get list of ScoreAI skills for multi-boxing scenarios.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of ScoreAI skills with agent_id support
        """
        skills: list[ScoreAISkillBase] = []

        # Add simple demonstration skills
        skills.extend(SimpleScoreAISkillsProvider.get_skills(event_bus, in_game_build))

        return skills

    @staticmethod
    def create_score_ai_engine(event_bus: EventBus, in_game_build: list[CustomSkill]) -> ScoreAIEngine:
        """
        Create a ScoreAIEngine with all available skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            Configured ScoreAIEngine instance
        """
        skills = ScoreAISkillsList.get_score_ai_skills_list(event_bus, in_game_build)
        return ScoreAIEngine(event_bus, skills)
