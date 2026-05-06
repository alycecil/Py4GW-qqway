from dataclasses import dataclass
from typing import List, Optional, Tuple
from collections.abc import Generator

from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

from .score_ai_skill_base import ScoreAISkillBase


@dataclass
class SkillScoreResult:
    """Result of skill evaluation with agent_id."""
    skill: ScoreAISkillBase
    score: float
    agent_id: Optional[int]  # The agent_id that generated this score


class ScoreAIEngine:
    """
    ScoreAI engine for multi-boxing scenarios.
    
    Key difference from CustomBehaviors:
    - Evaluates skills for specific agent_id values
    - Preserves agent_id from evaluation to execution
    - Supports agent_id = None for global operations
    """
    
    def __init__(self, skills: List[ScoreAISkillBase]):
        self.skills: List[ScoreAISkillBase] = skills
        self.previously_attempted_skills: List[CustomSkill] = []

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

    def evaluate_skills_for_agent(self, current_state: BehaviorState, agent_id: Optional[int]) -> List[SkillScoreResult]:
        """
        Evaluate all skills for a specific agent_id.
        
        Args:
            current_state: Current behavior state
            agent_id: Agent ID to evaluate for (None for global)
            
        Returns:
            List of skill evaluation results with scores
        """
        results = []
        
        for skill in self.get_enabled_skills():
            score = skill.evaluate(current_state, self.previously_attempted_skills, agent_id)
            if score is not None and score > 0:
                results.append(SkillScoreResult(
                    skill=skill,
                    score=score,
                    agent_id=agent_id
                ))
        
        return results

    def evaluate_all_skills(self, current_state: BehaviorState, agent_ids: List[int]) -> List[SkillScoreResult]:
        """
        Evaluate all skills for multiple agent_ids.
        
        Args:
            current_state: Current behavior state
            agent_ids: List of agent IDs to evaluate for
            
        Returns:
            List of all skill evaluation results across all agents
        """
        all_results = []
        
        for agent_id in agent_ids + [None]:  # Include None for global evaluation
            agent_results = self.evaluate_skills_for_agent(current_state, agent_id)
            all_results.extend(agent_results)
        
        return all_results

    def get_best_skill_for_agent(self, current_state: BehaviorState, agent_id: Optional[int]) -> Optional[SkillScoreResult]:
        """
        Get the best scoring skill for a specific agent_id.
        
        Args:
            current_state: Current behavior state
            agent_id: Agent ID to get best skill for (None for global)
            
        Returns:
            Best skill result for this agent_id
        """
        results = self.evaluate_skills_for_agent(current_state, agent_id)
        
        if not results:
            return None
        
        return max(results, key=lambda r: r.score)

    def get_best_skill(self, current_state: BehaviorState, agent_ids: List[int]) -> Optional[SkillScoreResult]:
        """
        Get the overall best skill across all agents.
        
        Args:
            current_state: Current behavior state
            agent_ids: List of agent IDs to consider
            
        Returns:
            Overall best skill result with preserved agent_id
        """
        all_results = self.evaluate_all_skills(current_state, agent_ids)
        
        if not all_results:
            return None
        
        return max(all_results, key=lambda r: r.score)

    def execute_skill_for_agent(self, state: BehaviorState, agent_id: Optional[int]) -> Generator[Tuple[bool, SkillScoreResult], None, BehaviorResult]:
        """
        Execute the best skill for a specific agent_id.
        
        Args:
            state: Current behavior state
            agent_id: Agent ID to execute for (None for global)
            
        Yields:
            (success, result) tuples for execution steps
        """
        best_result = self.get_best_skill_for_agent(state, agent_id)
        
        if not best_result:
            yield (False, None)
            return
        
        try:
            # Add to previously attempted skills
            if best_result.skill.custom_skill not in self.previously_attempted_skills:
                self.previously_attempted_skills.append(best_result.skill.custom_skill)
            
            # Execute the skill
            for step_result in best_result.skill.execute(state, agent_id):
                yield (True, best_result)
                
        except Exception as e:
            print(f"Error executing skill {best_result.skill.custom_skill.skill_name} for agent {agent_id}: {e}")
            yield (False, best_result)

    def execute_best_skill(self, state: BehaviorState, agent_ids: List[int]) -> Generator[Tuple[bool, SkillScoreResult], None, BehaviorResult]:
        """
        Execute the overall best skill across all agents.
        
        Args:
            state: Current behavior state
            agent_ids: List of agent IDs to consider
            
        Yields:
            (success, result) tuples for execution steps
        """
        best_result = self.get_best_skill(state, agent_ids)
        
        if not best_result:
            yield (False, None)
            return
        
        try:
            # Add to previously attempted skills
            if best_result.skill.custom_skill not in self.previously_attempted_skills:
                self.previously_attempted_skills.append(best_result.skill.custom_skill)
            
            # Execute the skill with preserved agent_id
            for step_result in best_result.skill.execute(state, best_result.agent_id):
                yield (True, best_result)
                
        except Exception as e:
            print(f"Error executing best skill {best_result.skill.custom_skill.skill_name} for agent {best_result.agent_id}: {e}")
            yield (False, best_result)
