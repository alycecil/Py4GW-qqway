from typing import List, Optional
from collections.abc import Generator

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition

from ....primitives.skills.score_ai_skill_base import ScoreAISkillBase


class SimpleScoreDefinition(ScoreDefinition):
    """Simple implementation of ScoreDefinition for ScoreAI."""
    
    def __init__(self, description: str):
        self.description = description
    
    def score_definition_debug_ui(self) -> str:
        return self.description


class SimpleScoreAIUtility(ScoreAISkillBase):
    """
    Simple ScoreAI utility skill for demonstration.
    Shows the key difference: agent_id is preserved through evaluation and execution.
    """
    
    def __init__(self, event_bus: EventBus, skill: CustomSkill, in_game_build: List[CustomSkill]):
        score_def = SimpleScoreDefinition(f"Simple utility for {skill.skill_name}")
        
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=in_game_build,
            score_definition=score_def,
            mana_required_to_cast=5.0,
            allowed_states=[BehaviorState.IN_AGGRO]
        )

    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        """Common pre-checks for the utility skill."""
        if current_state is BehaviorState.IDLE: 
            return False

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return False
            
        if self.custom_skill.skill_slot == 0:
            return False
            
        return True

    def get_score_for_agent(self, agent_id: Optional[int]) -> float:
        """
        Score this skill for a specific agent_id.
        This is the key difference from CustomBehaviors - agent_id is preserved.
        """
        # Base score
        base_score = 30.0
        
        # Score varies based on agent_id (demonstrating agent_id awareness)
        if agent_id is not None:
            # Higher score for even agent IDs (example logic)
            if agent_id % 2 == 0:
                base_score += 20.0
            else:
                base_score += 10.0
                
            # Distance-based scoring (closer agents get higher priority)
            # In real implementation, you'd calculate actual distance
            distance_factor = 100 - (agent_id % 100)  # Simple distance simulation
            base_score += distance_factor / 10.0
        else:
            # Global evaluation gets medium priority
            base_score += 15.0
            
        return max(0.0, min(100.0, base_score))

    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: List[CustomSkill], agent_id: Optional[int] = None) -> Optional[float]:
        """
        Evaluate the skill for a specific agent_id.
        This is the key difference from CustomBehaviors - agent_id is preserved.
        """
        return self.get_score_for_agent(agent_id)

    def _execute(self, state: BehaviorState, agent_id: Optional[int] = None) -> Generator[None, None, BehaviorResult]:
        """
        Execute the skill for a specific agent_id.
        The agent_id is preserved from evaluation to execution.
        """
        print(f"Executing {self.custom_skill.skill_name} for agent_id: {agent_id}")
        
        # In a real implementation, you would:
        # 1. Target the specific agent if agent_id is not None
        # 2. Cast the skill
        # 3. Handle skill execution results
        
        # For demonstration, we'll just simulate execution
        if agent_id is not None:
            print(f"  Targeting agent {agent_id}")
        else:
            print("  Global execution (no specific target)")
            
        # Simulate skill cast
        print(f"  Casting {self.custom_skill.skill_name}")
        
        # Return success
        yield BehaviorResult(1)  # SUCCESS equivalent

    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug information for the skill."""
        print(f"[DEBUG] {self.custom_skill.skill_name} - Simple ScoreAI Utility")
        print(f"  Enabled: {self.is_enabled}")
        print(f"  Skill Slot: {self.custom_skill.skill_slot}")
        print(f"  Mana Required: {self.mana_required_to_cast}")
        print(f"  This skill demonstrates agent_id-aware scoring and execution")

    def has_persistence(self) -> bool:
        """Check if skill has persistent configuration."""
        return False

    def delete_persisted_configuration(self):
        """Delete persisted configuration."""
        pass

    def persist_configuration_as_global(self):
        """Persist configuration as global."""
        pass

    def persist_configuration_for_account(self):
        """Persist configuration for account."""
        pass


class SimpleScoreAISkillsProvider:
    """
    Provider for simple ScoreAI demonstration skills.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: List[CustomSkill]) -> List[ScoreAISkillBase]:
        """
        Get list of simple ScoreAI skills for demonstration.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of simple ScoreAI skills
        """
        skills: List[ScoreAISkillBase] = []
        
        # Add some example skills
        example_skills = [
            "Skill_Example_1",
            "Skill_Example_2", 
            "Skill_Example_3"
        ]
        
        for skill_name in example_skills:
            # Create skill with a dummy slot
            skill = CustomSkill(skill_name)
            skill.skill_slot = len(skills) + 1  # Assign sequential slots
            
            skills.append(SimpleScoreAIUtility(
                event_bus=event_bus,
                skill=skill,
                in_game_build=in_game_build
            ))
        
        return skills
