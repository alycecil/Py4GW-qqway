from typing import Optional, List
from collections.abc import Generator

from Py4GWCoreLib import Routines

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

from ....primitives.skills.score_ai_skill_base import ScoreAISkillBase


class ScoreAIResurrectionUtility(ScoreAISkillBase):
    """
    ScoreAI resurrection skill that evaluates and executes resurrection for specific agent_id.
    Unlike CustomBehaviors, this skill considers which agent needs resurrection.
    """
    
    def __init__(self, event_bus: EventBus, skill: CustomSkill, in_game_build: List[CustomSkill]):
        score_def = ScoreDefinition(
            skill_name=skill.skill_name,
            base_score=50.0,
            description=f"Resurrection skill for {skill.skill_name}"
        )
        
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=in_game_build,
            score_definition=score_def,
            mana_required_to_cast=10.0,  # Typical resurrection cost
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.IDLE]
        )

    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        """Common pre-checks for resurrection skills."""
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
        Evaluate resurrection need for specific agent_id.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Previously attempted skills
            agent_id: Specific agent to check for resurrection need
            
        Returns:
            Score based on resurrection priority for the agent
        """
        # If agent_id is None, check all party members
        if agent_id is None:
            # For global evaluation, return highest priority among all dead allies
            max_score = 0.0
            for party_member in custom_behavior_helpers.Party.get_dead_allies():
                score = self._calculate_resurrection_score(party_member.agent_id)
                max_score = max(max_score, score)
            return max_score if max_score > 0 else None
            
        # For specific agent_id, check if that agent needs resurrection
        if custom_behavior_helpers.Party.is_agent_dead(agent_id):
            return self._calculate_resurrection_score(agent_id)
            
        return None

    def _calculate_resurrection_score(self, agent_id: int) -> float:
        """Calculate resurrection priority score for a specific agent."""
        base_score = 50.0
        
        # Higher priority for certain professions
        agent = custom_behavior_helpers.Agents.get_agent_by_id(agent_id)
        if agent:
            profession = agent.get_primary_profession()
            if profession in ["Monk", "Ritualist", "Elementalist"]:
                base_score += 20.0  # High priority for healers/casters
            elif profession in ["Warrior", "Dervish", "Paragon"]:
                base_score += 10.0  # Medium priority for frontline
                
        # Higher priority if we're in combat and need more allies
        if custom_behavior_helpers.Party.get_party_in_combat():
            base_score += 15.0
            
        # Distance factor - closer targets get higher priority
        distance = custom_behavior_helpers.Agents.get_distance_to_agent(agent_id)
        if distance < 500:  # Very close
            base_score += 10.0
        elif distance > 1500:  # Very far
            base_score -= 10.0
            
        return min(max(base_score, 0.0), 100.0)

    def _execute(self, state: BehaviorState, agent_id: Optional[int] = None) -> Generator[Any | None, Any | None, BehaviorResult]:
        """
        Execute resurrection for specific agent_id.
        
        Args:
            state: Current behavior state
            agent_id: Agent to resurrect
            
        Yields:
            Behavior execution steps
        """
        if agent_id is None:
            # Find best target if not specified
            dead_allies = custom_behavior_helpers.Party.get_dead_allies()
            if not dead_allies:
                yield BehaviorResult.ACTION_SKIPPED
                
            # Choose highest priority target
            best_target = max(dead_allies, key=lambda ally: self._calculate_resurrection_score(ally.agent_id))
            agent_id = best_target.agent_id
            
        if not custom_behavior_helpers.Party.is_agent_dead(agent_id):
            yield BehaviorResult.ACTION_SKIPPED
            
        # Target and cast resurrection skill
        target_agent = custom_behavior_helpers.Agents.get_agent_by_id(agent_id)
        if not target_agent:
            yield BehaviorResult.ACTION_SKIPPED
            
        # Target the dead ally
        custom_behavior_helpers.Targeting.target_agent(agent_id)
        
        # Cast the skill
        if Routines.Player.UseSkill(self.custom_skill.skill_slot):
            yield BehaviorResult.ACTION_SUCCESSFUL
        else:
            yield BehaviorResult.ACTION_SKIPPED

    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug information for the resurrection skill."""
        print(f"[DEBUG] {self.custom_skill.skill_name} - ScoreAI Resurrection")
        print(f"  Enabled: {self.is_enabled}")
        print(f"  Skill Slot: {self.custom_skill.skill_slot}")
        print(f"  Mana Required: {self.mana_required_to_cast}")
        
        dead_allies = custom_behavior_helpers.Party.get_dead_allies()
        print(f"  Dead Allies Count: {len(dead_allies)}")
        
        for ally in dead_allies:
            score = self._calculate_resurrection_score(ally.agent_id)
            print(f"    Agent {ally.agent_id}: Score {score:.1f}")

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


class ScoreAIResurrectionSkillsProvider:
    """
    Provider for ScoreAI resurrection skills.
    These skills evaluate resurrection needs for specific agent_ids.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: List[CustomSkill]) -> List[ScoreAISkillBase]:
        """
        Get list of ScoreAI resurrection skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of ScoreAI resurrection skills
        """
        skills: List[ScoreAISkillBase] = []
        
        # Add common resurrection skills
        resurrection_skills = [
            "Flesh_of_My_Flesh",
            "Signet_of_Return", 
            "Resurrection",
            "Resurrect",
            "Resurrection_Chant",
            "Resurrection_Signet",
            "Rebirth",
            "Sunspear_Rebirth_Signet"
        ]
        
        for skill_name in resurrection_skills:
            # Only add skill if it's in the current build
            if any(skill.skill_name == skill_name for skill in in_game_build):
                skills.append(ScoreAIResurrectionUtility(
                    event_bus=event_bus,
                    skill=CustomSkill(skill_name),
                    in_game_build=in_game_build
                ))
        
        return skills
