"""
Example usage of ScoreAI for multi-boxing scenarios.

This example demonstrates the key difference from CustomBehaviors:
- Each skill provides scores for specific agent_id values
- Engine preserves agent_id when calling _evaluate and _execute
- Enables coordinated multi-boxing behavior
"""

from Sources.multiboxing.ScoreAI import ScoreAIEngine, ScoreAISkillsList
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill


def demonstrate_basic_usage():
    """Basic ScoreAI usage demonstration."""
    print("=== ScoreAI Basic Usage Demo ===")
    
    # Setup
    event_bus = EventBus()
    in_game_build = [
        CustomSkill("Skill_Example_1"),
        CustomSkill("Skill_Example_2"),
        CustomSkill("Skill_Example_3")
    ]
    
    # Create engine with ScoreAI skills
    engine = ScoreAISkillsList.create_score_ai_engine(event_bus, in_game_build)
    
    # Multi-boxing scenario: evaluate for specific agents
    agent_ids = [1001, 1002, 1003]  # Your multi-box character IDs
    current_state = BehaviorState.IN_AGGRO
    attempted_skills = []
    
    print(f"Evaluating skills for agents: {agent_ids}")
    print(f"Current state: {current_state}")
    
    # Get best skill across all agents
    best_result = engine.get_best_skill(current_state, attempted_skills, agent_ids)
    
    if best_result:
        print(f"\nBest skill found:")
        print(f"  Skill: {best_result.skill.custom_skill.skill_name}")
        print(f"  Target agent: {best_result.agent_id}")
        print(f"  Score: {best_result.score:.1f}")
        
        # Execute the best skill
        print(f"\nExecuting {best_result.skill.custom_skill.skill_name}...")
        for result, skill_result in engine.execute_best_skill(current_state, attempted_skills, agent_ids):
            if result:
                print(f"  Success! Executed on agent {skill_result.agent_id}")
            break
    else:
        print("No suitable skills found")


def demonstrate_agent_specific_evaluation():
    """Demonstrate evaluating skills for specific agents."""
    print("\n=== Agent-Specific Evaluation Demo ===")
    
    # Setup
    event_bus = EventBus()
    in_game_build = [CustomSkill("Skill_Example_1")]
    engine = ScoreAISkillsList.create_score_ai_engine(event_bus, in_game_build)
    
    current_state = BehaviorState.IN_AGGRO
    attempted_skills = []
    
    # Evaluate for each agent individually
    for agent_id in [1001, 1002, 1003]:
        print(f"\nEvaluating for agent {agent_id}:")
        
        results = engine.evaluate_skills_for_agent(current_state, attempted_skills, agent_id)
        
        for result in results:
            print(f"  {result.skill.custom_skill.skill_name}: score {result.score:.1f}")
        
        best = engine.get_best_skill_for_agent(current_state, attempted_skills, agent_id)
        if best:
            print(f"  Best for agent {agent_id}: {best.skill.custom_skill.skill_name} (score: {best.score:.1f})")


def demonstrate_global_vs_agent_specific():
    """Demonstrate difference between global and agent-specific evaluation."""
    print("\n=== Global vs Agent-Specific Demo ===")
    
    # Setup
    event_bus = EventBus()
    in_game_build = [CustomSkill("Skill_Example_1")]
    engine = ScoreAISkillsList.create_score_ai_engine(event_bus, in_game_build)
    
    current_state = BehaviorState.IN_AGGRO
    attempted_skills = []
    
    # Global evaluation (agent_id = None)
    print("Global evaluation (agent_id = None):")
    global_results = engine.evaluate_skills_for_agent(current_state, attempted_skills, None)
    for result in global_results:
        print(f"  {result.skill.custom_skill.skill_name}: score {result.score:.1f} (agent_id: {result.agent_id})")
    
    # Agent-specific evaluation
    print("\nAgent-specific evaluation:")
    for agent_id in [1001, 1002]:
        agent_results = engine.evaluate_skills_for_agent(current_state, attempted_skills, agent_id)
        for result in agent_results:
            print(f"  Agent {agent_id}: {result.skill.custom_skill.skill_name}: score {result.score:.1f}")


def demonstrate_skill_management():
    """Demonstrate skill management features."""
    print("\n=== Skill Management Demo ===")
    
    # Setup
    event_bus = EventBus()
    in_game_build = [CustomSkill("Skill_Example_1")]
    engine = ScoreAISkillsList.create_score_ai_engine(event_bus, in_game_build)
    
    print(f"Total skills: {len(engine.skills)}")
    print(f"Enabled skills: {len(engine.get_enabled_skills())}")
    
    # Disable a skill
    engine.disable_skill("Skill_Example_1")
    print(f"After disabling - Enabled skills: {len(engine.get_enabled_skills())}")
    
    # Re-enable the skill
    engine.enable_skill("Skill_Example_1")
    print(f"After re-enabling - Enabled skills: {len(engine.get_enabled_skills())}")


if __name__ == "__main__":
    """Run all demonstrations."""
    print("ScoreAI Multi-boxing Skill Scoring Engine")
    print("=" * 50)
    
    demonstrate_basic_usage()
    demonstrate_agent_specific_evaluation()
    demonstrate_global_vs_agent_specific()
    demonstrate_skill_management()
    
    print("\n" + "=" * 50)
    print("Demo completed! Key takeaways:")
    print("1. Skills provide scores for specific agent_id values")
    print("2. Engine preserves agent_id from evaluation to execution")
    print("3. Enables coordinated multi-boxing behavior")
    print("4. Can evaluate globally or for specific agents")
    print("5. Full skill management capabilities")
