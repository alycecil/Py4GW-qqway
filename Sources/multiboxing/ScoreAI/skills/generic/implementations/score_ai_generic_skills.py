from typing import Optional, List, Any
from collections.abc import Generator

from Py4GWCoreLib import Routines

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

from ....primitives.skills.score_ai_skill_base import ScoreAISkillBase


class SimpleScoreDefinition(ScoreDefinition):
    """Simple implementation of ScoreDefinition for ScoreAI."""
    
    def __init__(self, description: str):
        self.description = description
    
    def score_definition_debug_ui(self) -> str:
        return self.description


class ScoreAIHealUtility(ScoreAISkillBase):
    """
    ScoreAI healing skill that evaluates and executes healing for specific agent_id.
    """
    
    def __init__(self, event_bus: EventBus, skill: CustomSkill, in_game_build: List[CustomSkill]):
        score_def = SimpleScoreDefinition(f"Healing skill for {skill.skill_name}")
        
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=in_game_build,
            score_definition=score_def,
            mana_required_to_cast=5.0,  # Typical healing cost
            allowed_states=[BehaviorState.IN_AGGRO]
        )

    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        """Common pre-checks for healing skills."""
        if current_state is BehaviorState.IDLE: 
            return False

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return False
            
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast:
            return False
            
        if not Routines.Checks.Skills.IsSkillSlotReady(self.custom_skill.skill_slot):
            return False
            
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill):
            return False

        return True

    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: List[CustomSkill], agent_id: Optional[int] = None) -> float | None:
        """
        Evaluate healing need for specific agent_id.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Previously attempted skills
            agent_id: Specific agent to check for healing need
            
        Returns:
            Score based on healing priority for agent
        """
        # For now, return a simple score based on agent_id
        # In a real implementation, you would check the agent's health
        if agent_id is None:
            return 30.0  # Default score for global evaluation
            
        # Simple scoring based on agent_id (for demonstration)
        # In practice, you'd check actual health levels
        base_score = 40.0
        if agent_id % 2 == 0:  # Even agents get higher priority (demo logic)
            base_score += 10.0
            
        return base_score

    def _execute(self, state: BehaviorState, agent_id: Optional[int] = None) -> Generator[Any | None, Any | None, BehaviorResult]:
        """
        Execute healing for specific agent_id.
        
        Args:
            state: Current behavior state
            agent_id: Agent to heal
            
        Yields:
            Behavior execution steps
        """
        # For demonstration, just cast the skill on self if no target specified
        if agent_id is not None:
            # Target specific agent
            custom_behavior_helpers.Targeting.target_agent(agent_id)
            
        # Cast the healing skill
        if Routines.Player.UseSkill(self.custom_skill.skill_slot):
            yield BehaviorResult.ACTION_SUCCESSFUL
        else:
            yield BehaviorResult.ACTION_SKIPPED

    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug information for healing skill."""
        print(f"[DEBUG] {self.custom_skill.skill_name} - ScoreAI Healing")
        print(f"  Enabled: {self.is_enabled}")
        print(f"  Skill Slot: {self.custom_skill.skill_slot}")
        print(f"  Mana Required: {self.mana_required_to_cast}")

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


class ScoreAIGenericSkillsProvider:
    """
    Provider for ScoreAI generic utility skills.
    These skills evaluate generic actions for specific agent_ids.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: List[CustomSkill]) -> List[ScoreAISkillBase]:
        """
        Get list of ScoreAI generic skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of ScoreAI generic skills
        """
        skills: List[ScoreAISkillBase] = []
        
        # Add common healing skills
        healing_skills = [
            "Heal_Burst",
            "Heal_Area", 
            "Heal_Other",
            "Dwaynas_Kiss",
            "Healing_Breeze"
        ]
        
        for skill_name in healing_skills:
            # Only add skill if it's in the current build
            if any(skill.skill_name == skill_name for skill in in_game_build):
                skills.append(ScoreAIHealUtility(
                    event_bus=event_bus,
                    skill=CustomSkill(skill_name),
                    in_game_build=in_game_build
                ))
        
        return skills
