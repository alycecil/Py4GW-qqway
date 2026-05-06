from abc import abstractmethod
from collections.abc import Callable, Generator
from typing import Any, Optional

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives import constants

from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_option import UtilitySkillOption
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_watchdog import UtilitySkillWatchdog
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_plugin import UtilitySkillPlugin
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_precondition import UtilitySkillPrecondition
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_targeting_modifier import UtilitySkillTargetingModifier
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy


class ScoreAISkillBase:
    """
    Base class for ScoreAI skills with agent_id support.
    
    Key difference from CustomBehaviors:
    - Each skill provides scores for specific agent_id values
    - Engine preserves agent_id from evaluation to execution
    - agent_id can be None for global operations
    """
    
    def __init__(self, 
                 event_bus: EventBus,
                 skill: CustomSkill,
                 in_game_build: list[CustomSkill],
                 score_definition: ScoreDefinition,
                 mana_required_to_cast: float = 0,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
                 utility_skill_typology: UtilitySkillTypology = UtilitySkillTypology.COMBAT,
                 execution_strategy = UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END,
                 ):
        
        self.event_bus: EventBus = event_bus
        self.custom_skill: CustomSkill = skill
        self.utility_skill_typology: UtilitySkillTypology = utility_skill_typology
        self.in_game_build: list[CustomSkill] = in_game_build
        self.allowed_states: list[BehaviorState] | None = allowed_states
        self.mana_required_to_cast: float = mana_required_to_cast
        self.is_enabled: bool = True
        self.execution_strategy = execution_strategy
        self.score_definition: ScoreDefinition = score_definition
        
        self._utility_skill_plugins: list[UtilitySkillPlugin] = []

    # Plugin management (inherited from CustomBehaviors)
    def add_plugin_precondition(self, precondition: Callable[['ScoreAISkillBase'], UtilitySkillPrecondition]) -> 'ScoreAISkillBase':
        plugin_instance: UtilitySkillPlugin = precondition(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Precondition {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self
    
    def add_plugin_watchdog(self, extension: Callable[['ScoreAISkillBase'], UtilitySkillWatchdog]) -> 'ScoreAISkillBase':
        plugin_instance: UtilitySkillPlugin = extension(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Extension {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self
    
    def add_plugin_targetting_modifier(self, targeting_modifier: Callable[['ScoreAISkillBase'], UtilitySkillTargetingModifier]) -> 'ScoreAISkillBase':
        plugin_instance: UtilitySkillPlugin = targeting_modifier(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Targeting modifier {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self
    
    def add_plugin_option(self, option: Callable[['ScoreAISkillBase'], UtilitySkillOption]) -> 'ScoreAISkillBase':
        plugin_instance: UtilitySkillPlugin = option(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Option {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self

    def get_plugins(self) -> list[UtilitySkillPlugin]:
        return self._utility_skill_plugins
    
    def are_preconditions_satisfied(self) -> bool:
        for plugin in self._utility_skill_plugins:
            if not isinstance(plugin, UtilitySkillPrecondition):
                continue
            if not plugin.is_satisfied():
                return False
        return True

    def get_plugin_option(self, option_name: str) -> UtilitySkillOption | None:
        for plugin in self._utility_skill_plugins:
            if isinstance(plugin, UtilitySkillOption) and plugin.plugin_name == option_name:
                return plugin
        return None
    
    def get_plugin_watchdogs(self) -> list[UtilitySkillWatchdog]:
        return [plugin for plugin in self._utility_skill_plugins if isinstance(plugin, UtilitySkillWatchdog)]

    # Core ScoreAI methods
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        """Common pre-checks for the skill."""
        if current_state is BehaviorState.IDLE: 
            return False

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return False
            
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast:
            return False
            
        return True

    def get_score_for_agent(self, agent_id: Optional[int]) -> float:
        """
        Score this skill for a specific agent_id.
        This is the key ScoreAI difference - agent-specific scoring.
        
        Args:
            agent_id: The agent ID to score for (None for global score)
            
        Returns:
            Score for this agent (0.0 to 100.0)
        """
        # Base implementation - override in subclasses
        return 0.0

    @abstractmethod
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill], agent_id: Optional[int] = None) -> float | None:
        """
        Evaluate the skill for a specific agent_id.
        
        Args:
            current_state: Current behavior state
            previously_attempted_skills: Skills already attempted this cycle
            agent_id: The agent ID to evaluate for (None for global)
            
        Returns:
            Score for this agent (None if not applicable)
        """
        pass

    @abstractmethod
    def _execute(self, state: BehaviorState, agent_id: Optional[int] = None) -> Generator[Any | None, Any | None, BehaviorResult]:
        """
        Execute the skill for a specific agent_id.
        
        Args:
            state: Current behavior state
            agent_id: The agent ID to execute for (None for global)
            
        Yields:
            Generator for execution steps
            
        Returns:
            BehaviorResult of execution
        """
        pass

    def evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill], agent_id: Optional[int] = None) -> float | None:
        """Public evaluation method with agent_id support."""
        if not self.are_common_pre_checks_valid(current_state):
            return None
            
        if not self.are_preconditions_satisfied():
            return None
            
        return self._evaluate(current_state, previously_attempted_skills, agent_id)

    def execute(self, state: BehaviorState, agent_id: Optional[int] = None) -> Generator[Any | None, Any | None, BehaviorResult]:
        """Public execution method with agent_id support."""
        if not self.are_common_pre_checks_valid(state):
            yield BehaviorResult(1)  # FAILURE equivalent
            return
            
        if not self.are_preconditions_satisfied():
            yield BehaviorResult(1)  # FAILURE equivalent
            return
            
        # Apply targeting modifiers if any
        for plugin in self._utility_skill_plugins:
            if isinstance(plugin, UtilitySkillTargetingModifier):
                agent_id = plugin.modify_targeting(agent_id)
        
        yield from self._execute(state, agent_id)
