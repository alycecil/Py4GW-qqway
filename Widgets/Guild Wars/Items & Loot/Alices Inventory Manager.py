import ctypes
import os
import traceback
from enum import IntEnum
from typing import Generator

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, PyUIManager, UIManager, IconsFontAwesome5, Map
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui, Color, ImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer, Player, Console, ConsoleLog
from Py4GWCoreLib.enums_src.Item_enums import STORAGE_BAGS, INVENTORY_BAGS
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.Checks import Checks
from Sources.ApoSource.ApoBottingLib.wrappers import LogMessage
from Sources.frenkeyLib.ItemHandling.BTNodes import BTNodes
from Sources.inventory_managment import constants
from Sources.inventory_managment.ui_manipulators.deposit_materials import DepositMaterials
from Sources.inventory_managment.ui_manipulators.identify_all import IdentifyAllItems
from Sources.inventory_managment.util.yield_as_behavior_tree import YieldAsBehaviorTree, as_behavior_tree

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = Console.get_projects_path()

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


ticker: BehaviorTree | None = None

new_map: bool = True
action_after_new_map: bool = False
NEW_MAP_THROTTLE = ThrottledTimer(13601)
ACTION_AFTER_NEW_MAP_THROTTLE = ThrottledTimer(9427)


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
        if new_map:
            PyImGui.text("New Map Detected")
        elif action_after_new_map:
            PyImGui.text("Awaiting new map triggers")
        else:
            PyImGui.text("Manually trigger an action")
    PyImGui.separator()

    # PyImGui.same_line(0,-1)

    if PyImGui.begin_tab_bar("top_level_tabs"):
        if ImGui.begin_tab_item("Minimal"):
            ImGui.end_tab_item()

        if ImGui.begin_tab_item("Actions"):
            actions()

        if ImGui.begin_tab_item("Settings"):
            settings()

        if ImGui.begin_tab_item("Debug"):
            debug()

        PyImGui.end_tab_bar()

    PyImGui.end()


def actions():
    global ticker
    if GLOBAL_CACHE.Inventory.IsStorageOpen():
        if PyImGui.button(f"{IconsFontAwesome5.ICON_BOX_OPEN} Xunlai Opened"):
            ticker = None
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_BOX} Open Xunlai"):
            GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
            ticker = None

    PyImGui.same_line(0, -1)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_MAGNIFYING_GLASS} Identify All"):
        ticker = bt_identify_all()

    PyImGui.same_line(0, -1)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Deposit Materials"):
        ticker = bt_deposit_mats()
    # Line 2
    if PyImGui.button(f"{IconsFontAwesome5.ICON_SHOPPING_BAG} Compact Bags"):
        ticker = merge_stacks_bags()
    PyImGui.same_line(0, -1)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Compact Storage"):
        ticker = merge_stacks_storage()
    PyImGui.same_line(0, -1)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Sort Storage"):
        ticker = sort_storage()
    ImGui.end_tab_item()


def merge_stacks_bags():
    return BehaviorTree(BTNodes.Bags.CompactBags(bags=INVENTORY_BAGS, result=True))


def merge_stacks_storage():
    return BehaviorTree(BTNodes.Bags.CompactBags(bags=STORAGE_BAGS, result=True))


def sort_storage():
    return BehaviorTree(BTNodes.Bags.SortBags(bags=STORAGE_BAGS))


def bt_deposit_gold():
    def _do_the_work() -> Generator:
        ConsoleLog("bt_salvage_items", f"Opening Xunlai", Console.MessageType.Info)

        from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state = inventory_handler.module_active

        yield
        inventory_handler.module_active = False

        yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)

        yield
        inventory_handler.module_active = current_state
    return as_behavior_tree("bt_deposit_gold", _do_the_work())


def bt_salvage_items():
    def _do_the_work() -> Generator:
        ConsoleLog("bt_salvage_items", f"Opening Xunlai", Console.MessageType.Info)

        from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state = inventory_handler.module_active
        yield
        inventory_handler.module_active = False

        yield from inventory_handler.SalvageItems()
        #yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)

        yield
        inventory_handler.module_active = current_state
    return as_behavior_tree("bt_salvage_items", _do_the_work())


def bt_deposit_mats():
    return as_behavior_tree("bt_deposit_mats", DepositMaterials().DepositMaterials())


def bt_identify_all():
    return as_behavior_tree("bt_identify_all", IdentifyAllItems().IdentifyAll())


def bt_deposit_items():
    def _do_the_deposit() -> Generator:
        ConsoleLog("bt_deposit_items", f"Opening Xunlai", Console.MessageType.Info)

        from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state = inventory_handler.module_active
        yield
        inventory_handler.module_active = False

        yield from inventory_handler.IdentifyItems()
        yield
        inventory_handler.module_active = current_state
    return as_behavior_tree("bt_deposit_items", _do_the_deposit())


def settings():
    PyImGui.text("Settings")
    if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Save"):
        pass
    ImGui.end_tab_item()


def debug():
    global ticker

    constants.DEBUG = PyImGui.checkbox("with_debugging_logs", constants.DEBUG)

    if PyImGui.button(f"{IconsFontAwesome5.ICON_VENUS_DOUBLE} trigger on map load"):
        ticker = _on_map_load()

    ImGui.end_tab_item()


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


def arrived_guild_hall() -> BehaviorTree | None:
    on_map_entry = [
        BehaviorTree.ConditionNode(name="IsOutpost", condition_fn=lambda: Checks.Map.IsOutpost()),
        LogMessage("IsOutpost GH On Map Entry"),
    ]

    on_map_entry.append(bt_identify_all())
    on_map_entry.append(bt_deposit_mats())

    on_map_entry.append(merge_stacks_storage())
    on_map_entry.append(merge_stacks_bags())
    # on_map_entry.append(sort_storage())

    on_map_entry.append(bt_deposit_items())

    return as_btt(on_map_entry)


def arrived_outpost() -> BehaviorTree | None:
    on_map_entry = [
        BehaviorTree.ConditionNode(name="IsOutpost", condition_fn=lambda: Checks.Map.IsOutpost()),
        LogMessage("IsOutpost On Map Entry"),
    ]

    on_map_entry.append(bt_identify_all())
    on_map_entry.append(bt_deposit_mats())

    # on_map_entry.append(merge_stacks_storage())
    # on_map_entry.append(merge_stacks_bags())
    # on_map_entry.append(sort_storage())

    on_map_entry.append(bt_deposit_items())

    return as_btt(on_map_entry)


def arrived_random_map() -> BehaviorTree | None:
    on_map_entry = [
        BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda: Checks.Map.IsExplorable()),
        LogMessage("InExplorable On Map Entry"),
    ]

    on_map_entry.append(bt_identify_all())

    on_map_entry.append(merge_stacks_bags())

    return as_btt(on_map_entry)


def as_btt(on_map_entry):
    tree = BehaviorTree.SequenceNode(children=on_map_entry)
    bt = BehaviorTree(root=tree)
    return bt


def assign_auto_ticker() -> BehaviorTree | None:
    global NEW_MAP_THROTTLE, ACTION_AFTER_NEW_MAP_THROTTLE, new_map, action_after_new_map

    if new_map:
        new_map = False
        action_after_new_map = True
        ACTION_AFTER_NEW_MAP_THROTTLE.Reset()

    if action_after_new_map and ACTION_AFTER_NEW_MAP_THROTTLE.IsExpired():
        NEW_MAP_THROTTLE.Reset()
        return _on_map_load()

    return None


def _on_map_load():
    global new_map, action_after_new_map
    new_map = False
    action_after_new_map = False
    if Map.IsGuildHall():
        return arrived_guild_hall()
    elif Map.IsOutpost():
        return arrived_outpost()
    elif Map.IsExplorable():
        return arrived_random_map()
    else:
        return None


def main():
    global cached_data
    global ticker
    global NEW_MAP_THROTTLE, new_map

    if not Routines.Checks.Map.MapValid():
        ticker = None
        if NEW_MAP_THROTTLE.IsExpired():
            new_map = True
        return

    try:
        draw_widget()

    except ImportError as e:
        Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Console.MessageType.Error)
        Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)
    except ValueError as e:
        Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Console.MessageType.Error)
        Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)
    except TypeError as e:
        Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Console.MessageType.Error)
        Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Console.MessageType.Error)
        Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)
    finally:
        pass

    try:
        if ticker is not None:
            state = ticker.tick()
            if state != BehaviorTree.NodeState.RUNNING:
                Console.Log(
                    MODULE_NAME,
                    f"Behavior tree '{ticker.root.name}' finished with state: {state.name}",
                    Console.MessageType.Success if state == BehaviorTree.NodeState.SUCCESS else Console.MessageType.Warning
                )
                ticker = None
        else:
            ticker = assign_auto_ticker()
    except Exception as e:
        ticker = None
        # Catch-all for any other unexpected exceptions
        Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Console.MessageType.Error)
        Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()
