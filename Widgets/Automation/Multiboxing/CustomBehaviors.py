
import pathlib
import sys

import Py4GW
from Py4GWCoreLib import ImGui, Map, PyImGui, Routines, Color, PyUIManager, traceback, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.UIManager import UIManager
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.fps_monitor import FPSMonitor
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party import CustomBehaviorHelperParty
from Sources.oazix.CustomBehaviors.primitives.widget_monitor import WidgetMonitor

# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "behavior" in module_name.lower():
                # Py4GW.Console.Log("CustomBehaviors", f"Reloading module: {module_name}")
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            Py4GW.Console.Log("CustomBehaviors", f"Error reloading module {module_name}: {e}")

party_forced_state_combo = 0
current_path = pathlib.Path.cwd()
monitor = FPSMonitor(history=300)
widget_monitor = WidgetMonitor()
# print(f"current_path is : {current_path}")
widget_window_size:tuple[float, float] = (0,0)
widget_window_pos:tuple[float, float] = (0,0)

MODULE_NAME = "Custom Behaviors: Utility AI"
MODULE_ICON = "Textures/Module_Icons/Custom Behaviors.png"

to_hex : str = "?"
dialog_int : int = 0
def draw_dialog_overlay():
    global frame_coords, dialog_open, dialog_coords, to_hex, dialog_int

    account_email = Player.GetAccountEmail()
    own_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
    if own_data is None:
        # print("no cache data")
        return

    dialog_open = UIManager.IsNPCDialogVisible()
    frame_coords = UIManager.GetDialogButtonFrames() if dialog_open else []

    if not frame_coords or not dialog_open:
        # print("no dialog data")
        return

    pyimgui_io = PyImGui.get_io()
    mouse_pos = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y)

    sorted_frames = sorted(frame_coords, key=lambda x: (x[1][1], x[1][0]))  # Sort by Y, then X

    # print("dialog open")
    for i, (frame_id, frame) in enumerate(sorted_frames):
        from HeroAI.ui import is_left_mouse_clicked, gray_color
        if ImGui.is_mouse_in_rect((frame[0], frame[1], frame[2] - frame[0], frame[3] - frame[1]), mouse_pos):

            frame_obj = PyUIManager.UIFrame(frame_id)
            if frame_obj is not None:
                dialog_int = frame_obj.field105_0x1c4
                to_hex = f"0x{dialog_int:X}"

                from Sources.oazix.CustomBehaviors.gui.botting import set_dialog_id
                set_dialog_id(to_hex)

            if is_left_mouse_clicked():
                if pyimgui_io.key_ctrl:

                    # hero ai does this...
                    # accounts = [acc for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() if acc.AccountEmail != account_email]
                    # print(f"sending dialog {i + 1}")
                    # commands.send_dialog(accounts, i + 1)

                    # this is the field in toolbox:
                    # PyUIManager.UIFrame(frame_id).field105_0x1c4
                    from Sources.oazix.CustomBehaviors.gui.botting import send_dialog_for_all
                    send_dialog_for_all(to_hex, dialog_int, include_sender = False)

                    return
                else:
                    print("clicked without ctrl")
            else:

                if pyimgui_io.key_ctrl:
                    ImGui.begin_tooltip()
                    ImGui.text_colored(f"(Ctrl) + Click to send dialog {to_hex} ({dialog_int}) on all accounts.", gray_color.color_tuple, 12)
                    ImGui.end_tooltip()
                else:
                    ImGui.begin_tooltip()
                    ImGui.text_colored(f"Ctrl + Click to send dialog {to_hex} ({dialog_int}) on all accounts.", gray_color.color_tuple, 12)
                    ImGui.end_tooltip()

        else:
            # print("no dialog")
            pass

    pass

def gui():
    draw_dialog_overlay()

    # PyImGui.set_next_window_size(260, 650)
    # PyImGui.set_next_window_size(460, 800)
    from Sources.oazix.CustomBehaviors.primitives import constants
    from Sources.oazix.CustomBehaviors.primitives.fps_monitor import FPSMonitor
    from Sources.oazix.CustomBehaviors.primitives.widget_monitor import WidgetMonitor
    from Sources.oazix.CustomBehaviors.gui.current_build import render as current_build_render
    from Sources.oazix.CustomBehaviors.gui.party import render as party
    from Sources.oazix.CustomBehaviors.gui.debug_skillbars import render as debug_skilbars
    from Sources.oazix.CustomBehaviors.gui.debug_execution import render as debug_execution
    from Sources.oazix.CustomBehaviors.gui.debug_sharedlocks import render as debug_sharedlocks
    from Sources.oazix.CustomBehaviors.gui.debug_eventbus import render as debug_eventbus
    from Sources.oazix.CustomBehaviors.gui.debug_eval_profiler import render as debug_eval_profiler
    from Sources.oazix.CustomBehaviors.gui.auto_mover import render as auto_mover
    from Sources.oazix.CustomBehaviors.gui.teambuild import render as teambuild
    from Sources.oazix.CustomBehaviors.gui.botting import render as botting
    from Sources.oazix.CustomBehaviors.gui.skill_metrics import render as skill_metrics
    from Sources.oazix.CustomBehaviors.gui.debug_disabilities import render as debug_disabilities

    global party_forced_state_combo, monitor, widget_window_size, widget_window_pos
    
    # window_module:ImGui.WindowModule = ImGui.WindowModule("Custom behaviors", window_name="Custom behaviors - Multiboxing over utility-ai algorithm.", window_size=(0, 600), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

    if PyImGui.begin("Custom behaviors - Multiboxing over utility-ai algorithm.", PyImGui.WindowFlags.AlwaysAutoResize):
        widget_window_size = PyImGui.get_window_size()
        widget_window_pos = PyImGui.get_window_pos()

        PyImGui.begin_tab_bar("tabs")
        if PyImGui.begin_tab_item("party"):
            party()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("player"):
            current_build_render()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("waypoint builder / auto_mover"):
            auto_mover()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("teambuild"):
            teambuild()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("botting"):
            botting()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("debug"):

                PyImGui.text(f"{monitor.fps_stats()[1]}")
                PyImGui.text(f"{monitor.frame_stats()[1]}")
                constants.DEBUG = PyImGui.checkbox("with_debugging_logs#with_debugging_logs", constants.DEBUG)

                PyImGui.begin_tab_bar("debug_tab_bar")

                if PyImGui.begin_tab_item("debug_execution"):
                    debug_execution()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_sharedlock"):
                    debug_sharedlocks()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_eventbus"):
                    debug_eventbus()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_loader"):
                    PyImGui.text(f"History (newest on top) : ")
                    debug_skilbars()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_profiler"):
                    debug_eval_profiler()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_disabilities"):
                    debug_disabilities()
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()

                PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("metrics"):
            skill_metrics()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()
    PyImGui.end()
    return

previous_map_status = False
map_change_throttler = ThrottledTimer(1_500)

def main():
    from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
    from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
    from Sources.oazix.CustomBehaviors.daemon import daemon

    global previous_map_status, monitor, widget_window_size, widget_window_pos

    monitor.tick()
    widget_monitor.act()

    if Routines.Checks.Map.MapValid() and previous_map_status == False:
        map_change_throttler.Reset()
        if constants.DEBUG: print("map changed detected - we will throttle.")

    previous_map_status = Routines.Checks.Map.MapValid()
    
    if not Routines.Checks.Map.MapValid():
        return
    
    if not map_change_throttler.IsExpired():
        if constants.DEBUG: print("map changed - throttling.")

    if map_change_throttler.IsExpired():
        show_ui = not UIManager.IsWorldMapShowing() and not Map.IsInCinematic() and not Map.Pregame.InCharacterSelectScreen()
        if show_ui:
            try:
                gui()
            except Exception as e:
                print(f'GUI Exception: {e} : {traceback.format_exc()}')

        daemon()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Custom Behaviors: Utility AI", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A specialized combat engine that utilizes Utility AI (Scoring)")
    PyImGui.text("logic rather than fixed trees. This system evaluates the current")
    PyImGui.text("game state to choose the most mathematically optimal action.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Utility Scoring: Dynamically weights skills and behaviors based on priority")
    PyImGui.bullet_text("Advanced Party Sync: Real-time coordination via Shared Memory (SMM)")
    PyImGui.bullet_text("Behavior Injection: Modular system for custom skill and party routines")
    PyImGui.bullet_text("Diagnostic Suite: Integrated FPS monitoring and Skillbar debugging")
    PyImGui.bullet_text("Automated Handling: Built-in NPC interaction and loot management")
    PyImGui.bullet_text("Event Bus Architecture: Decoupled communication for reactive combat states")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Oazix")

    PyImGui.end_tooltip()

__all__ = ["main"]
