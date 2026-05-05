import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ItemArray, Item, Inventory
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.inventory_managment import constants
from Sources.inventory_managment.config.inventory_utils_config import InventoryMode, InventoryUtilsConfig
from Sources.inventory_managment.properties.is_maxed.is_maxed import IsMaxed
from Sources.inventory_managment.properties.mods.get_mods_from_item import GetMods
from Sources.inventory_managment.properties.salvage_handler import SalvageHandler
from Sources.inventory_managment.properties.weapon_handler import WeaponHandler
from Sources.marks_sources.mods_parser import ParsedModifierResult
from Sources.inventory_managment.storage.get_inventory_items import common_get_inventory_items


# Create an enumeration


# class PrefixConfig:
#     def __init__(self,
#                  zealous: InventoryMode = InventoryMode.DEPOSIT,
#                  vamparic: InventoryMode = InventoryMode.SELL,
#                  purple: InventoryMode = InventoryMode.SELL,
#                  gold: InventoryMode = InventoryMode.KEEP,
#                  specials: InventoryMode = InventoryMode.DEPOSIT,
#                  ):
#         self.white: InventoryMode = white
#         self.blue: InventoryMode = blue
#         self.purple: InventoryMode = purple
#         self.gold: InventoryMode = gold
#         self.specials: InventoryMode = specials


# colors determine default action,
#
# qualities are overrides to color default action
# typically we only want to keep best for, q5-8 sub max are trash and dont meet the qualifications
# Rare mods are kept regardless of quality
# listed rare skins are kept too


# Todo later
# class MaterialsConfig:
#     pass


class InventoryUtils:

    @staticmethod
    def GetIDKits():
        count_of_id_kits = (Inventory.GetModelCount(ModelID.Superior_Identification_Kit) +  # 5899 model for ID kit
                            Inventory.GetModelCount(ModelID.Identification_Kit)
                            )
        return count_of_id_kits

    @staticmethod
    def GetSalvageKits():
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Salvage_Kit)  # 2992 model for salvage kit
        return count_of_salvage_kits

    @staticmethod
    def GetExpertSalvageKits():
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Expert_Salvage_Kit)  # 2991 model for expert salvage kit
        return count_of_salvage_kits

    def has_salvage_kits(self):
        return self.GetSalvageKits() > 0 and self.GetExpertSalvageKits() > 0

    def get_inventory_items(
            self,
            inventory_config: InventoryUtilsConfig,
            slot_blacklist: list[tuple[int, int]] = [],
            bags=[Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2]
    ) -> list[int]:
        return common_get_inventory_items(inventory_config, slot_blacklist, bags)

    def get_mods_from_item(self, item_id) -> tuple[str | None, str | None, str | None, ParsedModifierResult]:
        return GetMods().get_mods_from_item(item_id)

    def is_maxed(
            self, item_id,
            parsed_modifiers: ParsedModifierResult = None,
            item_type: ItemType = None
    ):
        return IsMaxed().is_maxed(item_id, parsed_modifiers, item_type)

    def get_action_for_item(
            self,
            inventory_config: InventoryUtilsConfig,
            item_id: int
    ) -> InventoryMode:
        # Strict types

        if item_id < 1:
            if constants.DEBUG: ConsoleLog("InvUtil", f"item_id #{item_id} is not valid")
            return InventoryMode.KEEP_DONT_IDENTIFY

        if GLOBAL_CACHE.Item.Properties.IsCustomized(item_id):
            if constants.DEBUG: ConsoleLog("InvUtil", f"item_id #{item_id} is customized")
            return InventoryMode.KEEP_DONT_IDENTIFY

        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        mode = inventory_config.event_item_config.get_inventory_mode(model_id)
        if mode is not None:
            if constants.DEBUG: ConsoleLog("InvUtil", f"item_id #{item_id} overridden mode {mode}")
            return mode

        if model_id in inventory_config.block_list_model_id:
            if constants.DEBUG: ConsoleLog("InvUtil", f"item_id #{item_id} black listed")
            return InventoryMode.KEEP_DONT_IDENTIFY

        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int in inventory_config.block_list_item_type:
            if constants.DEBUG: ConsoleLog("InvUtil", f"item_type {item_type_to_int} ({item1_type_name}) for item #{item_id} black listed")
            return InventoryMode.KEEP_DONT_IDENTIFY

        for item_type in [
            ItemType.Axe,
            ItemType.Bow,
            ItemType.Offhand,
            ItemType.Hammer,
            ItemType.Wand,
            ItemType.Shield,
            ItemType.Staff,
            ItemType.Sword,
            ItemType.Daggers,
            ItemType.Scythe,
            ItemType.Spear,
        ]:
            if item_type_to_int == item_type:
                return WeaponHandler().get_action_for_item(inventory_config, item_id, item_type)

        if item_type == ItemType.Salvage:
            return SalvageHandler().get_action_for_salvage(inventory_config.salvage_config, item_id)

        # I dunno what this is
        return InventoryMode.KEEP_DONT_IDENTIFY
