"""
ScoreAI - Multi-boxing Skill Scoring Engine

A skill scoring engine similar to CustomBehaviors but with agent_id support.
Each skill provides scores for specific agent_id values and the engine
preserves the agent_id when calling _evaluate.
"""

from .primitives.skills.score_ai_skill_base import ScoreAISkillBase
from .primitives.skills.score_ai_engine import ScoreAIEngine
from .skills.generic.score_ai_skills_list import ScoreAISkillsList

__all__ = [
    'ScoreAISkillBase',
    'ScoreAIEngine', 
    'ScoreAISkillsList'
]
