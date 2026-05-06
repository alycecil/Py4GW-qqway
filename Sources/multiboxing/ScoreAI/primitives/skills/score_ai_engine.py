from typing import Optional, List, Tuple
from dataclasses import dataclass
from collections.abc import Generator

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

from .score_ai_skill_base import ScoreAISkillBase


@dataclass
class SkillScoreResult:
    """Represents a skill evaluation result with agent_id."""
    skill: ScoreAISkillBase
    score: float
    agent_id: Optional[int]


class ScoreAIEngine:
    """
    Skill scoring engine for multi-boxing scenarios.
    
    Unlike CustomBehaviors which emits a single score over all agents,
    ScoreAI evaluates each skill for specific agent_id values and preserves
    the agent_id when calling _evaluate and _execute.
    """
    
    def __init__(self, event_bus: EventBus, skills: List[ScoreAISkillBase]):
        self.event_bus = event_bus
        self.skills = skills
        
    def evaluate_all_skills(self, 
                           current_state: BehaviorState, 
                           previously_attempted_skills: List[CustomSkill],
                           agent_ids: Optional[List[int]] = None) -> List[SkillScoreResult]:
        """
        Evaluate all skills for all relevant agent_ids.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Skills that were previously attempted
            agent_ids: List of agent_ids to evaluate. If None, uses [None] for global evaluation
            
        Returns:
            List of SkillScoreResult sorted by score (highest first)
        """
        results: List[SkillScoreResult] = []
        
        # Always include None for global evaluation
        ids_to_check = [None]
        if agent_ids:
            ids_to_check.extend(agent_ids)
            
        for skill in self.skills:
            for agent_id in ids_to_check:
                score = skill.get_score_for_agent(current_state, previously_attempted_skills, agent_id)
                if score is not None and score > 0:
                    results.append(SkillScoreResult(
                        skill=skill,
                        score=score,
                        agent_id=agent_id
                    ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def get_best_skill(self, 
                      current_state: BehaviorState, 
                      previously_attempted_skills: List[CustomSkill],
                      agent_ids: Optional[List[int]] = None) -> Optional[SkillScoreResult]:
        """
        Get the highest scoring skill for the given state and agent_ids.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Skills that were previously attempted
            agent_ids: List of agent_ids to evaluate. If None, uses [None] for global evaluation
            
        Returns:
            The best SkillScoreResult or None if no valid skills found
        """
        results = self.evaluate_all_skills(current_state, previously_attempted_skills, agent_ids)
        return results[0] if results else None
    
    def execute_best_skill(self, 
                          current_state: BehaviorState, 
                          previously_attempted_skills: List[CustomSkill],
                          agent_ids: Optional[List[int]] = None) -> Generator[Tuple[Optional[BehaviorResult], Optional[SkillScoreResult]], None, None]:
        """
        Find and execute the best skill for the given state and agent_ids.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Skills that were previously attempted
            agent_ids: List of agent_ids to evaluate. If None, uses [None] for global evaluation
            
        Yields:
            Tuple of (execution_result, skill_result) or (None, None) if no valid skills found
        """
        best_result = self.get_best_skill(current_state, previously_attempted_skills, agent_ids)
        
        if best_result is None:
            yield (None, None)
            return
            
        try:
            execution_result = yield from best_result.skill.execute_for_agent(current_state, best_result.agent_id)
            yield (execution_result, best_result)
        except Exception as e:
            print(f"Error executing skill {best_result.skill.custom_skill.skill_name}: {e}")
            yield (BehaviorResult.ACTION_SKIPPED, best_result)
    
    def evaluate_skills_for_agent(self, 
                                 current_state: BehaviorState, 
                                 previously_attempted_skills: List[CustomSkill],
                                 agent_id: Optional[int]) -> List[SkillScoreResult]:
        """
        Evaluate all skills for a specific agent_id.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Skills that were previously attempted
            agent_id: Specific agent_id to evaluate (can be None for global)
            
        Returns:
            List of SkillScoreResult sorted by score (highest first)
        """
        results: List[SkillScoreResult] = []
        
        for skill in self.skills:
            score = skill.get_score_for_agent(current_state, previously_attempted_skills, agent_id)
            if score is not None and score > 0:
                results.append(SkillScoreResult(
                    skill=skill,
                    score=score,
                    agent_id=agent_id
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def get_best_skill_for_agent(self, 
                                current_state: BehaviorState, 
                                previously_attempted_skills: List[CustomSkill],
                                agent_id: Optional[int]) -> Optional[SkillScoreResult]:
        """
        Get the highest scoring skill for a specific agent_id.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Skills that were previously attempted
            agent_id: Specific agent_id to evaluate (can be None for global)
            
        Returns:
            The best SkillScoreResult or None if no valid skills found
        """
        results = self.evaluate_skills_for_agent(current_state, previously_attempted_skills, agent_id)
        return results[0] if results else None
    
    def add_skill(self, skill: ScoreAISkillBase):
        """Add a skill to the engine."""
        if skill not in self.skills:
            self.skills.append(skill)
    
    def remove_skill(self, skill: ScoreAISkillBase):
        """Remove a skill from the engine."""
        if skill in self.skills:
            self.skills.remove(skill)
    
    def get_enabled_skills(self) -> List[ScoreAISkillBase]:
        """Get all enabled skills."""
        return [skill for skill in self.skills if skill.is_enabled]
    
    def enable_skill(self, skill_name: str):
        """Enable a skill by name."""
        for skill in self.skills:
            if skill.custom_skill.skill_name == skill_name:
                skill.is_enabled = True
                break
    
    def disable_skill(self, skill_name: str):
        """Disable a skill by name."""
        for skill in self.skills:
            if skill.custom_skill.skill_name == skill_name:
                skill.is_enabled = False
                break
