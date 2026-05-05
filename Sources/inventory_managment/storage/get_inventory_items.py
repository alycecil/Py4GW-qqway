from Py4GWCoreLib import ItemArray, Item, GLOBAL_CACHE
from Py4GWCoreLib.enums_src.Item_enums import Bags
from Sources.inventory_managment import constants
from Sources.inventory_managment.config.inventory_utils_config import InventoryUtilsConfig


def common_get_inventory_items(
        inventory_config: InventoryUtilsConfig,
        slot_blacklist: list[tuple[int, int]] = [],
        bags: list[int] = [],
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

            if item_type_to_int in inventory_config.block_list_item_type:
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