# ScoreAI - Multi-boxing Skill Scoring Engine

ScoreAI is a skill scoring engine similar to CustomBehaviors but designed specifically for multi-boxing scenarios. The key difference is that each skill provides scores for specific `agent_id` values, and the engine preserves the `agent_id` when calling `_evaluate` and `_execute`.

## Key Differences from CustomBehaviors

### CustomBehaviors Approach
- Each skill utility emits a **single score** over all agents
- `_evaluate(self, current_state, previously_attempted_skills)` returns one global score
- Engine chooses highest scoring skill globally

### ScoreAI Approach  
- Each skill utility provides **scores for specific agent_id values**
- `_evaluate(self, current_state, previously_attempted_skills, agent_id)` returns score for that agent
- Engine chooses highest score **and preserves the agent_id** for execution
- `agent_id` can be `None` for global operations

## Architecture

```
Sources/multiboxing/ScoreAI/
├── __init__.py                    # Main exports
├── primitives/
│   └── skills/
│       ├── score_ai_skill_base.py   # Base class with agent_id support
│       └── score_ai_engine.py      # Scoring engine with agent_id preservation
└── skills/
    └── generic/
        ├── score_ai_skills_list.py  # Factory for skills
        └── implementations/
            └── simple_score_ai_skills.py  # Example implementations
```

## Core Classes

### ScoreAISkillBase
Abstract base class for all ScoreAI skills. Key differences from CustomBehaviors:

```python
def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: List[CustomSkill], agent_id: Optional[int] = None) -> float | None:
    """
    Evaluate the skill for a specific agent_id.
    This is the main difference from CustomBehaviors - agent_id is preserved.
    """

def _execute(self, state: BehaviorState, agent_id: Optional[int] = None) -> Generator[Any | None, Any | None, BehaviorResult]:
    """
    Execute the skill for a specific agent_id.
    """
```

### ScoreAIEngine
Main engine that evaluates skills and preserves agent_id:

```python
# Evaluate all skills for multiple agents
results = engine.evaluate_all_skills(current_state, attempted_skills, agent_ids=[1001, 1002, 1003])

# Get best skill (includes agent_id)
best_result = engine.get_best_skill(current_state, attempted_skills, agent_ids=[1001, 1002])
# best_result.skill -> the skill that won
# best_result.agent_id -> which agent it should target

# Execute best skill
for result, skill_result in engine.execute_best_skill(current_state, attempted_skills, agent_ids=[1001, 1002]):
    # skill_result.agent_id is preserved from evaluation to execution
    pass
```

### SkillScoreResult
Dataclass containing evaluation results:

```python
@dataclass
class SkillScoreResult:
    skill: ScoreAISkillBase
    score: float
    agent_id: Optional[int]  # The agent_id that generated this score
```

## Usage Example

```python
from Sources.multiboxing.ScoreAI import ScoreAIEngine, ScoreAISkillsList
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState

# Create engine with skills
event_bus = EventBus()
in_game_build = [CustomSkill("Skill_Example_1"), CustomSkill("Skill_Example_2")]
engine = ScoreAISkillsList.create_score_ai_engine(event_bus, in_game_build)

# Multi-boxing scenario: evaluate for specific agents
agent_ids = [1001, 1002, 1003]  # Your multi-box character IDs
current_state = BehaviorState.IN_AGGRO
attempted_skills = []

# Get best skill across all agents
best_result = engine.get_best_skill(current_state, attempted_skills, agent_ids)
if best_result:
    print(f"Best skill: {best_result.skill.custom_skill.skill_name}")
    print(f"Target agent: {best_result.agent_id}")
    print(f"Score: {best_result.score}")

# Execute the best skill
for result, skill_result in engine.execute_best_skill(current_state, attempted_skills, agent_ids):
    if result:
        print(f"Executed {skill_result.skill.custom_skill.skill_name} on agent {skill_result.agent_id}")
```

## Creating Custom Skills

To create a custom ScoreAI skill:

```python
class MyCustomSkill(ScoreAISkillBase):
    def __init__(self, event_bus: EventBus, skill: CustomSkill, in_game_build: List[CustomSkill]):
        score_def = SimpleScoreDefinition(f"Custom skill for {skill.skill_name}")
        super().__init__(event_bus, skill, in_game_build, score_def)

    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: List[CustomSkill], agent_id: Optional[int] = None) -> float | None:
        # Your scoring logic here
        if agent_id is None:
            return 30.0  # Global score
        
        # Agent-specific scoring
        if self.should_heal_agent(agent_id):
            return 80.0  # High priority for this agent
        return 10.0  # Low priority

    def _execute(self, state: BehaviorState, agent_id: Optional[int] = None) -> Generator[Any | None, Any | None, BehaviorResult]:
        # Your execution logic here
        if agent_id is not None:
            # Target specific agent
            target_agent(agent_id)
        
        # Cast skill
        cast_skill(self.custom_skill.skill_slot)
        yield BehaviorResult(1)
```

## Multi-boxing Use Cases

### 1. Coordinated Healing
- Each character evaluates healing needs for all party members
- Engine picks highest priority heal and preserves which agent needs it
- Multiple characters can coordinate without duplicate healing

### 2. Target Prioritization  
- Skills evaluate different targets (enemies, allies, self)
- Engine chooses best target across all agents
- Prevents multiple characters from targeting same enemy

### 3. Resource Management
- Skills consider energy/cooldowns of specific agents
- Engine balances skill usage across multiple characters
- Avoids resource conflicts between accounts

### 4. Role-based Coordination
- Different skills for different roles (tank, healer, DPS)
- Engine coordinates role-specific actions
- Maintains tactical cohesion across accounts

## Integration with CustomBehaviors

ScoreAI is designed to complement CustomBehaviors:

```python
# Use CustomBehaviors for single-character logic
custom_skills = GenericUtilitySkillsList.get_generic_utility_skills_list(event_bus, build)

# Use ScoreAI for multi-boxing coordination  
score_ai_skills = ScoreAISkillsList.get_score_ai_skills_list(event_bus, build)

# Combine as needed
all_skills = custom_skills + score_ai_skills
```

## Configuration

Skills can be configured similarly to CustomBehaviors:

```python
skill = MyCustomSkill(event_bus, skill_obj, build)
    .add_plugin_precondition(MyPrecondition)
    .add_plugin_watchdog(MyWatchdog)
    .add_plugin_targetting_modifier(MyTargetingModifier)
    .add_plugin_option(MyOption)
```

## Debugging

Each skill provides debug UI:

```python
skill.customized_debug_ui(current_state)
# Output:
# [DEBUG] MySkill - ScoreAI Utility
#   Enabled: True
#   Skill Slot: 3
#   Mana Required: 5.0
#   This skill demonstrates agent_id-aware scoring and execution
```

## Performance Considerations

- ScoreAI evaluates skills for each agent_id, so consider the number of agents
- Use agent_id filtering to limit evaluation scope when possible
- Cache expensive calculations in skill implementations
- Consider using `evaluate_skills_for_agent()` for single-agent scenarios

## Future Enhancements

Potential areas for expansion:

1. **Agent Grouping**: Support for agent groups/clusters
2. **Priority Queues**: Persistent priority tracking across evaluations  
3. **Cross-Agent Coordination**: Skills that require multiple agents
4. **Load Balancing**: Distribute actions across accounts
5. **Network Awareness**: Consider latency between accounts
