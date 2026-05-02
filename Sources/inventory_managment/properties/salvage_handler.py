from Py4GWCoreLib import GLOBAL_CACHE, Item
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.inventory_managment import constants
from Sources.inventory_managment.config.inventory_utils_config import SalvageConfig, InventoryMode


class SalvageHandler:
    def _default_salvage_item(self, item_id, salvage_config):
        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int == 0:
            return InventoryMode.KEEP_DONT_IDENTIFY
        if Item.Rarity.IsGreen(item_id):
            return InventoryMode.KEEP_DONT_IDENTIFY
        if Item.Rarity.IsGold(item_id):
            return salvage_config.gold
        if Item.Rarity.IsPurple(item_id):
            return salvage_config.purple
        if Item.Rarity.IsBlue(item_id):
            return salvage_config.blue
        return salvage_config.white

    def get_action_for_salvage(
            self,
            salvage_config: SalvageConfig,
            item_id: int
    ) -> InventoryMode:
        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int == 0:
            return InventoryMode.KEEP_DONT_IDENTIFY

        default_salvage_item = self._default_salvage_item(item_id, salvage_config)

        if salvage_config.specials is not None:
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_weapon_type
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_rune_type
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_inscription_type
            if (filter_valuable_weapon_type(item_id) or
                    filter_valuable_rune_type(item_id) or
                    filter_valuable_inscription_type(item_id)
            ):
                if constants.DEBUG: ConsoleLog("InvUtil", "Special")
                return salvage_config.specials

        return default_salvage_item
