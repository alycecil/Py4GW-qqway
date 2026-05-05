import ctypes
import os
import traceback
from enum import IntEnum
from typing import Generator

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, PyUIManager, UIManager, IconsFontAwesome5, Map, Inventory, Item, ItemArray
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui, Color, ImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer, Player, Console, ConsoleLog
from Py4GWCoreLib.enums_src.Item_enums import STORAGE_BAGS, INVENTORY_BAGS, Rarity, Bags
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.Checks import Checks
from Sources.ApoSource.ApoBottingLib.wrappers import LogMessage
from Sources.frenkeyLib.ItemHandling.BTNodes import BTNodes
from Sources.inventory_managment import constants
from Sources.inventory_managment.config.inventory_utils_config import InventoryMode, InventoryUtilsConfig
from Sources.inventory_managment.inventory_utils import InventoryUtils
from Sources.inventory_managment.ui_manipulators.deposit_materials import DepositMaterials
from Sources.inventory_managment.ui_manipulators.identify_all import IdentifyAllItems
from Sources.inventory_managment.util.yield_as_behavior_tree import YieldAsBehaviorTree, as_behavior_tree
from Sources.inventory_managment.config.inventory_util_config_loader import inventory_util_config_load_json

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = Console.get_projects_path()

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "alices_inventory_manager.ini")
os.makedirs(BASE_DIR, exist_ok=True)

cached_data = CacheData()

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = ThrottledTimer(1000)
cache_window_timer = ThrottledTimer(30000)
save_window_timer.Start()

# String consts
MODULE_NAME = "Alices Inventory Manager"  # Change this Module name
MODULE_ICON = "Textures\\Module_Icons\\Gwen Loots.jpg"
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 200,50 / un-collapsed)
window_x = 200
window_y = 50
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)


ticker: BehaviorTree | None = None

new_map: bool = True
action_after_new_map: bool = False
NEW_MAP_THROTTLE = ThrottledTimer(13601)
ACTION_AFTER_NEW_MAP_THROTTLE = ThrottledTimer(9427)


class CachedItem:
    def __init__(
            self,
            item_id,
            name,
            rarity,
            action
    ):

        self.item_id = item_id
        self.name = name
        self.rarity = rarity
        self.action = action

    def item_id(self):
        return self.item_id

    def name(self):
        return self.name

    def rarity(self):
        return self.rarity

    def action(self):
        return self.action


inventory_gui_cache: list[CachedItem] = []
inventory_utils_config: InventoryUtilsConfig | None = inventory_util_config_load_json()


def draw_widget():
    global window_x, window_y, window_collapsed, first_run
    global ticker
    global ini_window

    if first_run:
        window_x = ini_window.read_int(MODULE_NAME, X_POS, window_x)
        window_y = ini_window.read_int(MODULE_NAME, Y_POS, window_y)
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    if not PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    new_collapsed = PyImGui.is_window_collapsed()

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
    end_pos = PyImGui.get_window_pos()

    post_gui(end_pos, new_collapsed)


def post_gui(end_pos, new_collapsed):
    global window_x, window_y, inventory_gui_cache, first_run
    global cache_window_timer, save_window_timer

    if save_window_timer.IsExpired():
        save_window_details(end_pos, new_collapsed)



def refresh_cache():
    global inventory_gui_cache
    global inventory_utils_config
    # cache details
    inventory_gui_cache = []

    inventory_utils_config = inventory_util_config_load_json()
    inventory_utils = InventoryUtils()

    inventory_item_ids = get_inventory_items(inventory_utils_config, allow_all_types=True)
    if constants.DEBUG: ConsoleLog("refresh_cache", f"Inventory List filtered = {inventory_item_ids}", Console.MessageType.Info)
    for my_item_id in inventory_item_ids:
        item_id = my_item_id

        action = _get_action_for_item(inventory_utils, inventory_utils_config, my_item_id)

        if Item.IsNameReady(my_item_id):
            name = Item.GetName(my_item_id)
        else:
            Item.RequestName(my_item_id)
            name = "Pending"

        rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(my_item_id)
        rarity = rarity

        item = CachedItem(
            item_id,
            name,
            rarity,
            action
        )
        inventory_gui_cache.append(item)


def ColorByRarity(rarity):
    if rarity[0] == Rarity.White.value or rarity[1] == "White":
        return (1, 1, 0.91, 1)
    if rarity[0] == Rarity.Blue.value or rarity[1] == "Blue":
        return (0, .64, 0.91, 1)
    if rarity[0] == Rarity.Purple.value or rarity[1] == "Purple":
        return (0.76, .34, 0.76, 1)
    if rarity[0] == Rarity.Gold.value or rarity[1] == "Gold":
        return (1, .79, 0.05, 1)
    if rarity[0] == Rarity.Green.value or rarity[1] == "Green":
        return (.13, .68, 0.29, 1)

    return (0.91, 0.91, 0.91, 1)


def save_window_details(end_pos, new_collapsed):
    global window_x, window_y
    global window_collapsed
    global ini_window
    # Position changed?
    if (end_pos[0], end_pos[1]) != (window_x, window_y):

        from Py4GWCoreLib import ConsoleLog, Console

        # if constants.DEBUG:
        ConsoleLog(
            MODULE_NAME,
            f"save_window_details = {end_pos[0]}, {end_pos[1]}",
            Console.MessageType.Info
        )

        window_x, window_y = int(end_pos[0]), int(end_pos[1])
        ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
        ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))

        # Collapsed state changed?
        if new_collapsed != window_collapsed:
            window_collapsed = new_collapsed
            ini_window.write_key(MODULE_NAME, COLLAPSED, str(window_collapsed))

        save_window_timer.Reset()


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

    # Line 3
    if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH_RESTORE} Deposit All"):
        ticker = bt_deposit_items()
    # PyImGui.same_line(0, -1)
    # if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Compact Storage"):
    #     ticker = merge_stacks_storage()
    # PyImGui.same_line(0, -1)
    # if PyImGui.button(f"{IconsFontAwesome5.ICON_VAULT} Sort Storage"):
    #     ticker = sort_storage()

    ImGui.end_tab_item()


def get_inventory_items(
            inventory_config: InventoryUtilsConfig,
            slot_blacklist: list[tuple[int, int]] = [],
            bags=range(Bags.Backpack, Bags.Bag2 + 1),
            allow_all_types: bool = False
    ) -> list[int]:
        '''
        Returns a list of all item IDs in the player's inventory excluding banlist items
        '''
        my_items = []

        # Loop over all bags
        for bag_id in bags:
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)  # Get all items in the baglist

            # Loop over items
            for item_id in item_array:

                if Item.Properties.IsCustomized(item_id):
                    from Py4GWCoreLib import ConsoleLog, Console

                    if constants.DEBUG: ConsoleLog(
                        "get_inventory_items",
                        f"IsCustomized item id = {item_id}",
                        Console.MessageType.Info
                    )
                    # dont touch this stuff, the player loves it.
                    continue

                item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)

                if allow_all_types:
                    pass
                elif item_type_to_int in inventory_config.block_list_item_type:
                    from Py4GWCoreLib import ConsoleLog, Console

                    if constants.DEBUG: ConsoleLog(
                        "get_inventory_items",
                        f"block_list_item_type = {item_type_to_int}",
                        Console.MessageType.Info
                    )
                    continue

                model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
                if model_id in inventory_config.block_list_model_id:
                    from Py4GWCoreLib import ConsoleLog, Console

                    if constants.DEBUG: ConsoleLog(
                        "get_inventory_items",
                        f"block_list_model_id = {model_id}",
                        Console.MessageType.Info
                    )
                    continue

                slot = GLOBAL_CACHE.Item.GetSlot(item_id)
                if (bag_id, slot) in slot_blacklist:
                    from Py4GWCoreLib import ConsoleLog, Console

                    if constants.DEBUG: ConsoleLog(
                        "get_inventory_items",
                        f"slot_blacklist = {item_id}, slot = {slot}",
                        Console.MessageType.Info
                    )
                    continue

                my_items.append(item_id)

        return list(set(my_items))


def _get_action_for_item(
    inventory_utils: InventoryUtils,
    _inventory_utils_config: InventoryUtilsConfig,
    item_id
) -> InventoryMode:
    action_for_item: InventoryMode = inventory_utils.get_action_for_item(_inventory_utils_config, item_id)

    # if Inventory.GetFreeSlotCount() <= 2:
    #     if action_for_item == InventoryMode.SELL_DONT_IDENTIFY or action_for_item == InventoryMode.SELL:
    #         return InventoryMode.SALVAGE

    return action_for_item


def _get_items_to_deposit(inventory_utils: InventoryUtils, _inventory_utils_config: InventoryUtilsConfig):
    from Py4GWCoreLib import ConsoleLog, Console
    my_items = []
    inventory_item_ids = get_inventory_items(_inventory_utils_config, allow_all_types=True)
    if constants.DEBUG: ConsoleLog("get_items_to_deposit", f"Inventory List filtered = {inventory_item_ids}", Console.MessageType.Info)
    for my_item_id in inventory_item_ids:

        action_for_item: InventoryMode = _get_action_for_item(inventory_utils, _inventory_utils_config, my_item_id)
        if action_for_item == InventoryMode.DEPOSIT:
            my_items.append(my_item_id)
        else:
            if constants.DEBUG: ConsoleLog("get_items_to_deposit", f"Ignoring item #{my_item_id} its a {action_for_item}", Console.MessageType.Info)

    return my_items


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
    global inventory_utils_config

    def _do_the_deposit() -> Generator:
        ConsoleLog("bt_deposit_items", f"Opening Xunlai", Console.MessageType.Info)

        from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state = inventory_handler.module_active
        yield
        inventory_handler.module_active = False

        yield from inventory_handler.IdentifyItems()

        yield from Routines.Yield.wait(350)

        yield from inventory_handler.DepositItemsAuto()
        yield
        inventory_handler.module_active = current_state

    inventory_utils = InventoryUtils()

    get_items_to_deposit = _get_items_to_deposit(inventory_utils, inventory_utils_config)

    tree = BehaviorTree(BTNodes.Items.DepositItems(get_items_to_deposit))
    return as_behavior_tree("bt_deposit_items", _do_the_deposit())


def settings():
    global inventory_utils_config

    from Sources.inventory_managment.config.inventory_util_config_loader import (
        persist_configuration_for_account,
        persist_configuration_as_global,
        delete_persisted_configuration
    )

    PyImGui.text("Settings")
    PyImGui.bullet_text(f"Persistence :")
    if PyImGui.button(f"Save for account {IconsFontAwesome5.ICON_SAVE}"):
        persist_configuration_for_account(inventory_utils_config)
    PyImGui.same_line(0, 5)
    if PyImGui.button(f"Save global {IconsFontAwesome5.ICON_SAVE}"):
        persist_configuration_as_global(inventory_utils_config)
    PyImGui.same_line(0, 5)
    if PyImGui.button(f"Delete {IconsFontAwesome5.ICON_TRASH}"):
        delete_persisted_configuration()
    ImGui.end_tab_item()


def debug():
    global ticker
    global inventory_gui_cache

    constants.DEBUG = PyImGui.checkbox("with_debugging_logs", constants.DEBUG)

    if PyImGui.button(f"{IconsFontAwesome5.ICON_VENUS_DOUBLE} trigger on map load"):
        ticker = _on_map_load()

    # render inventory_gui_cache
    if inventory_gui_cache:
        for item in inventory_gui_cache:
            item_rarity = item.rarity
            color = ColorByRarity(item_rarity)

            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)

            PyImGui.bullet_text(f"""{item_rarity} : #{item.item_id}: {item.name} : {item.action}""")

            PyImGui.pop_style_color(1)

    if cache_window_timer.IsExpired():
        refresh_cache()
        cache_window_timer.Reset()

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
