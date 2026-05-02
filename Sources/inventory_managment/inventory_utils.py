import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ItemArray, Item, Inventory
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Sources.inventory_managment.config.inventory_utils_config import InventoryMode, InventoryUtilsConfig
from Sources.inventory_managment.properties.is_maxed.is_maxed import IsMaxed
from Sources.inventory_managment.properties.mods.get_mods_from_item import GetMods
from Sources.inventory_managment.properties.salvage_handler import SalvageHandler
from Sources.inventory_managment.properties.weapon_handler import WeaponHandler
from Sources.marks_sources.mods_parser import ParsedModifierResult


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
            bags=range(Bags.Backpack, Bags.Bag2 + 1)
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
                    # dont touch this stuff, the player loves it.
                    continue

                item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)

                if item_type_to_int in inventory_config.block_list_item_type:
                    continue

                if GLOBAL_CACHE.Item.GetModelID(item_id) in inventory_config.block_list_model_id:
                    continue

                slot = GLOBAL_CACHE.Item.GetSlot(item_id)
                if (bag_id, slot) in slot_blacklist:
                    continue

                my_items.append(item_id)

        return my_items

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
        if GLOBAL_CACHE.Item.GetModelID(item_id) in inventory_config.block_list_model_id:
            return InventoryMode.KEEP_DONT_IDENTIFY

        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int in inventory_config.block_list_item_type:
            return InventoryMode.KEEP_DONT_IDENTIFY

        if GLOBAL_CACHE.Item.Properties.IsCustomized(item_id):
            return InventoryMode.KEEP_DONT_IDENTIFY

        if item_id < 1:
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
