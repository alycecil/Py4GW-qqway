"""
ScoreAI - Multi-boxing Skill Scoring Engine

ScoreAI is a skill scoring engine similar to CustomBehaviors but designed specifically 
for multi-boxing scenarios. The key difference is that each skill provides scores for 
specific agent_id values, and the engine preserves the agent_id when calling 
_evaluate and _execute.

Main difference from CustomBehaviors:
- Each skill utility provides scores for specific agent_id values
- Engine chooses highest score and preserves agent_id for execution
- agent_id can be None for global operations
"""

from .primitives.skills.score_ai_skill_base import ScoreAISkillBase
from .primitives.skills.score_ai_engine import ScoreAIEngine
from .skills.generic.score_ai_skills_list import ScoreAISkillsList

__all__ = ["ScoreAISkillBase", "ScoreAIEngine", "ScoreAISkillsList"]
