import ctypes
import os
import traceback
from enum import IntEnum
from typing import Generator

import Py4GW
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, PyUIManager, UIManager, IconsFontAwesome5
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui, Color, ImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer, Player
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.inventory_managment import constants
from Sources.inventory_managment.ui_manipulators.deposit_materials import DepositMaterials
from Sources.inventory_managment.ui_manipulators.identify_all import IdentifyAllItems
from Sources.inventory_managment.util.yield_as_behavior_tree import YieldAsBehaviorTree, as_behavior_tree

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = Py4GW.Console.get_projects_path()

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "alices_inventory_manager.ini")
os.makedirs(BASE_DIR, exist_ok=True)

cached_data = CacheData()

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# String consts
MODULE_NAME = "Alices Inventory Manager"  # Change this Module name
MODULE_ICON = "Textures\\Module_Icons\\Gwen Loots.jpg"
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)

default_dialog_string: str = "0x84"

dialog_open : bool = False

ticker: BehaviorTree | None = None


def draw_widget():
    global window_x, window_y, window_collapsed, first_run
    global default_dialog_string
    global ticker

    if not PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    if ticker is not None:
        PyImGui.text("Working, clicking a button will replace the current run")

        PyImGui.same_line(0,-1)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_STOP} Stop"):
            ticker = None
    else:
        PyImGui.text("Manually trigger an action")
    PyImGui.separator()

    # PyImGui.same_line(0,-1)
    if GLOBAL_CACHE.Inventory.IsStorageOpen():
        if PyImGui.button(f"{IconsFontAwesome5.ICON_BOX_OPEN} Xunlai Opened"):
            ticker = None
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_BOX} Open Xunlai"):
            GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
            ticker = None

    PyImGui.same_line(0,-1)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_MAGNIFYING_GLASS} Identify All"):
        ticker = as_behavior_tree("IdentifyAllItems", IdentifyAllItems().IdentifyAll())

    PyImGui.same_line(0,-1)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Deposit Materials"):
        ticker = as_behavior_tree("DepositMaterials",DepositMaterials().DepositMaterials())

    PyImGui.separator()
    if ImGui.begin_tab_item("Bags"):
        PyImGui.text("Settings")

        #default_dialog_string = ImGui.input_text("Dialog Id", default_dialog_string, 0)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Save"):
            pass

        ImGui.end_tab_item()

    PyImGui.end()


# Module tooltip, not the dialog tooltip
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("Inventory management utility.")
    PyImGui.spacing()

    PyImGui.end_tooltip()


def assign_auto_ticker() -> BehaviorTree | None:
    return None


def main():
    global cached_data
    global ticker

    if not Routines.Checks.Map.MapValid():
        return

    try:
        draw_widget()

    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

    try:
        if ticker is not None:
            state = ticker.tick()
            if state != BehaviorTree.NodeState.RUNNING:
                Py4GW.Console.Log(MODULE_NAME, f"Behavior tree '{ticker.root.name}' finished with state: {state.name}", Py4GW.Console.MessageType.Success if state == BehaviorTree.NodeState.SUCCESS else Py4GW.Console.MessageType.Warning)
                ticker = None
        else:
            ticker = assign_auto_ticker()
    except StopIteration:
        ticker = None
        Py4GW.Console.Log(MODULE_NAME, f"Ticker done", Py4GW.Console.MessageType.Info)
    except Exception as e:
        ticker = None
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()
