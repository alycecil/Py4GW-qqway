import pathlib
import sys
from typing import List, Optional

import Py4GW
from Py4GWCoreLib import ImGui, Map, PyImGui, Routines, Color, PyUIManager, traceback, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.UIManager import UIManager
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.fps_monitor import FPSMonitor
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party import CustomBehaviorHelperParty
from Sources.oazix.CustomBehaviors.primitives.widget_monitor import WidgetMonitor
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

# Import ScoreAI components
from Sources.multiboxing.ScoreAI import ScoreAIEngine, ScoreAISkillsList

# Reload modules
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "scoreai" in module_name.lower():
                del sys.modules[module_name]
        except Exception as e:
            Py4GW.Console.Log("ScoreAI", f"Error reloading module {module_name}: {e}")

# Global variables
current_path = pathlib.Path.cwd()
monitor = FPSMonitor(history=300)
widget_monitor = WidgetMonitor()
widget_window_size: tuple[float, float] = (0, 0)
widget_window_pos: tuple[float, float] = (0, 0)

# ScoreAI specific globals
score_ai_engine: Optional[ScoreAIEngine] = None
in_game_build: List[CustomSkill] = []
detection_range = 1000.0  # Longbow range
auto_execute = True
show_debug = False

MODULE_NAME = "ScoreAI: Multi-boxing Skill Selection"
MODULE_ICON = "Textures/Module_Icons/Custom Behaviors.png"

def get_agents_in_range() -> tuple[List[int], List[int], List[int]]:
    """Get all agents, allies, and enemies within detection range."""
    try:
        from Py4GWCoreLib import AgentArray, Agent, Player, Range
        
        # Use CustomBehaviors agent detection methods
        player_pos = Player.GetXY()
        
        # Get all allies in range
        all_ally_ids = AgentArray.GetAllyArray()
        ally_ids_in_range = AgentArray.Filter.ByDistance(all_ally_ids, player_pos, detection_range)
        ally_ids_in_range = AgentArray.Filter.ByCondition(ally_ids_in_range, lambda agent_id: Agent.IsValid(agent_id))
        
        # Get all enemies in range
        all_enemy_ids = AgentArray.GetEnemyArray()
        enemy_ids_in_range = AgentArray.Filter.ByDistance(all_enemy_ids, player_pos, detection_range)
        enemy_ids_in_range = AgentArray.Filter.ByCondition(enemy_ids_in_range, lambda agent_id: Agent.IsValid(agent_id))
        
        # Combine all agents
        all_agents = list(ally_ids_in_range) + list(enemy_ids_in_range)
        
        return all_agents, list(ally_ids_in_range), list(enemy_ids_in_range)
        
    except Exception as e:
        if constants.DEBUG:
            print(f"Error getting agents in range: {e}")
        return [], [], []

def initialize_score_ai():
    """Initialize ScoreAI engine with current build."""
    global score_ai_engine, in_game_build
    
    try:
        # Get current skillbar - simplified approach
        in_game_build = []
        for slot in range(1, 9):  # Skill slots 1-8
            # Create dummy skills for demonstration
            skill = CustomSkill(f"Skill_{slot}")
            skill.skill_id = slot
            skill.skill_slot = slot
            in_game_build.append(skill)
        
        # Create ScoreAI engine
        from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
        event_bus = EventBus()
        score_ai_engine = ScoreAISkillsList.create_score_ai_engine(event_bus, in_game_build)
        
        if constants.DEBUG:
            print(f"ScoreAI initialized with {len(in_game_build)} skills")
            
    except Exception as e:
        Py4GW.Console.Log("ScoreAI", f"Error initializing: {e}")
        print(f"ScoreAI init error: {e}")

def evaluate_and_execute_skill():
    """Evaluate skills and execute best one based on current situation."""
    global score_ai_engine
    
    if not score_ai_engine or not auto_execute:
        return
        
    try:
        # Get current situation
        all_agents, allies, enemies = get_agents_in_range()
        current_state = BehaviorState.IN_AGGRO if enemies else BehaviorState.IDLE
        
        if show_debug:
            print(f"ScoreAI Evaluation:")
            print(f"  Agents in range: {len(all_agents)}")
            print(f"  Allies: {allies}")
            print(f"  Enemies: {enemies}")
            print(f"  State: {current_state}")
        
        # Get best skill for current situation using detected agents
        best_result = score_ai_engine.get_best_skill(current_state, all_agents)
        
        if best_result and best_result.score > 0:
            if show_debug:
                print(f"  Best skill: {best_result.skill.custom_skill.skill_name}")
                print(f"  Target agent: {best_result.agent_id}")
                print(f"  Score: {best_result.score:.1f}")
            
            # Execute the skill using detected agents
            for result, skill_result in score_ai_engine.execute_best_skill(current_state, all_agents):
                if result:
                    if show_debug:
                        print(f"  Executed successfully!")
                    break
        else:
            if show_debug:
                print("  No suitable skills found")
                
    except Exception as e:
        Py4GW.Console.Log("ScoreAI", f"Error in evaluation: {e}")
        if constants.DEBUG:
            print(f"ScoreAI evaluation error: {e}")

def render_main_tab():
    """Render main ScoreAI tab."""
    global score_ai_engine, detection_range, auto_execute, show_debug
    
    ImGui.text("ScoreAI Multi-boxing Skill Selection")
    ImGui.separator()
    
    # Initialize button
    if ImGui.button("Initialize ScoreAI"):
        initialize_score_ai()
    
    if score_ai_engine:
        ImGui.text(f"Status: Active ({len(in_game_build)} skills loaded)")
    else:
        ImGui.text("Status: Not initialized")
        return
    
    ImGui.separator()
    
    # Configuration
    ImGui.text("Configuration:")
    
    # Display detected agents from game state
    all_agents, allies, enemies = get_agents_in_range()
    ImGui.text(f"Detected Agents: {len(all_agents)}")
    ImGui.text(f"  Allies: {len(allies)}")
    ImGui.text(f"  Enemies: {len(enemies)}")
    
    # Detection range
    changed, detection_range = ImGui.slider_float("Detection Range", detection_range, 100.0, 2000.0)
    
    # Auto execute
    changed, auto_execute = ImGui.checkbox("Auto Execute", auto_execute)
    
    # Debug
    changed, show_debug = ImGui.checkbox("Show Debug", show_debug)
    
    ImGui.separator()
    
    # Current situation
    ImGui.text("Current Situation:")
    ImGui.text(f"  Agents in range: {len(all_agents)}")
    ImGui.text(f"  Allies: {len(allies)}")
    ImGui.text(f"  Enemies: {len(enemies)}")
    
    if ImGui.button("Evaluate & Execute Skill"):
        evaluate_and_execute_skill()

def render_debug_tab():
    """Render debug information tab."""
    global score_ai_engine
    
    ImGui.text("ScoreAI Debug Information")
    ImGui.separator()
    
    if not score_ai_engine:
        ImGui.text("Initialize ScoreAI first")
        return
    
    # Engine info
    ImGui.text(f"Engine Status:")
    ImGui.text(f"  Total Skills: {len(score_ai_engine.skills)}")
    ImGui.text(f"  Enabled Skills: {len(score_ai_engine.get_enabled_skills())}")
    
    ImGui.separator()
    
    # Skill list
    ImGui.text("Loaded Skills:")
    for skill in score_ai_engine.skills:
        status = "Enabled" if skill.is_enabled else "Disabled"
        ImGui.text(f"  {skill.custom_skill.skill_name} - {status}")
    
    ImGui.separator()
    
    # Agent information
    all_agents, allies, enemies = get_agents_in_range()
    ImGui.text("Agent Information:")
    ImGui.text(f"  All Agents: {all_agents}")
    ImGui.text(f"  Allies: {allies}")
    ImGui.text(f"  Enemies: {enemies}")

def gui():
    """Main GUI function."""
    global monitor, widget_window_size, widget_window_pos
    
    if ImGui.begin("ScoreAI - Multi-boxing Skill Selection", ImGui.WindowFlags.AlwaysAutoResize):
        widget_window_size = ImGui.get_window_size()
        widget_window_pos = ImGui.get_window_pos()
        
        if ImGui.begin_tab_bar("scoreai_tabs"):
            if ImGui.begin_tab_item("Main"):
                render_main_tab()
                ImGui.end_tab_item()
            
            if ImGui.begin_tab_item("Debug"):
                render_debug_tab()
                ImGui.end_tab_item()
        
        ImGui.end_tab_bar()
    
    ImGui.end()

previous_map_status = False
map_change_throttler = ThrottledTimer(1500)

def main():
    """Main update function."""
    global previous_map_status, monitor, widget_monitor
    
    monitor.tick()
    widget_monitor.act()
    
    if Routines.Checks.Map.MapValid() and previous_map_status == False:
        map_change_throttler.Reset()
        if constants.DEBUG:
            print("ScoreAI: Map changed detected")
    
    previous_map_status = Routines.Checks.Map.MapValid()
    
    if not Routines.Checks.Map.MapValid():
        return
    
    if not map_change_throttler.IsExpired():
        if constants.DEBUG:
            print("ScoreAI: Map change throttling")
    
    if map_change_throttler.IsExpired():
        show_ui = not UIManager.IsWorldMapShowing() and not Map.IsInCinematic() and not Map.Pregame.InCharacterSelectScreen()
        if show_ui:
            try:
                gui()
            except Exception as e:
                print(f'ScoreAI GUI Exception: {e} : {traceback.format_exc()}')
        
        # Auto-execute if enabled
        if auto_execute and score_ai_engine:
            evaluate_and_execute_skill()

def tooltip():
    """Widget tooltip."""
    ImGui.begin_tooltip()
    
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    ImGui.text_colored("ScoreAI: Multi-boxing Skill Selection", title_color.to_tuple_normalized())
    ImGui.pop_font()
    ImGui.spacing()
    ImGui.separator()
    
    ImGui.text("ScoreAI engine for multi-boxing scenarios.")
    ImGui.text("Evaluates skills based on agents, allies, and enemies")
    ImGui.text("within range (Longbow distance) and selects optimal skill.")
    ImGui.spacing()
    
    ImGui.text_colored("Features:", title_color.to_tuple_normalized())
    ImGui.bullet_text("Agent Range Detection: Scans for agents within Longbow range")
    ImGui.bullet_text("Multi-boxing Support: Evaluates skills for multiple agent IDs")
    ImGui.bullet_text("Dynamic Skill Selection: Chooses best skill based on situation")
    ImGui.bullet_text("Real-time Execution: Auto-executes highest scoring skill")
    ImGui.bullet_text("Debug Information: Detailed evaluation and execution logs")
    
    ImGui.spacing()
    ImGui.separator()
    ImGui.spacing()
    
    ImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    ImGui.bullet_text("Based on CustomBehaviors by Oazix")
    ImGui.bullet_text("ScoreAI multi-boxing extension")
    
    ImGui.end_tooltip()

__all__ = ["main"]
