from enum import Enum
import json
import os
import re
import shutil
import traceback
from collections import OrderedDict
from pathlib import Path

import Py4GW  # type: ignore
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Color
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import DyeColor
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Timer
from Py4GWCoreLib import Map, Player
from Py4GWCoreLib import get_texture_for_model
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums import ModelID
from Sources.marks_sources.mods_parser import ModDatabase, ParsedModifierResult
from Sources.marks_sources.mods_parser import MatchedRuneInfo
from Sources.marks_sources.mods_parser import MatchedWeaponModInfo
from Sources.marks_sources.mods_parser import parse_modifiers

from Py4GWCoreLib import ItemArray, Item, Inventory
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Sources.Sasemoi.utils.rune_quality_checker import item_has_valuable_rune
from Sources.marks_sources.mods_parser import MatchedWeaponModInfo, MatchedRuneInfo, parse_modifiers, ModDatabase
from Sources.oazix.CustomBehaviors.primitives import constants

DEFAULT_ITEM_TYPE_BLOCK_LIST = [7, 17, 6, 3, 4, 44, 45, 10, 13, 20, 16, 29, 19, 34, 11, 33, 21, 8, 31, 43, 30, 255, 9]

DEFAULT_MODEL_ID_BLOCK_LIST = [
    522, 525, 2473, 27974, 399, 1045, 1055, 1058, 1060, 1064, 1065, 1066, 1067, 1660,
    1752, 1768, 1769, 1770, 1771, 1772, 1773, 1870, 1879, 1880, 1881, 1883, 1884, 1885,
    1900, 1953, 1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967,
    1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1985, 1986, 1987, 1988, 1989,
    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
    2004, 2005, 2006, 2007, 2039, 2071, 2079, 2474, 27033, 27052, 31202, 31203, 31204,
    36669, 36677, 36679, 27047]


# Create an enumeration
class InventoryMode(Enum):
    KEEP_DONT_IDENTIFY = 0
    KEEP = 1
    DEPOSIT = 2
    SALVAGE = 10
    SELL = 20
    SELL_DONT_IDENTIFY = 21

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


class SalvageConfig:
    def __init__(self,
                 white: InventoryMode = InventoryMode.SALVAGE,
                 blue: InventoryMode = InventoryMode.SELL,
                 purple: InventoryMode = InventoryMode.SELL,
                 gold: InventoryMode = InventoryMode.SELL,
                 specials: InventoryMode = InventoryMode.DEPOSIT,
                 ):
        self.white: InventoryMode = white
        self.blue: InventoryMode = blue
        self.purple: InventoryMode = purple
        self.gold: InventoryMode = gold
        self.specials: InventoryMode = specials

# colors determine default action,
#
# qualities are overrides to color default action
# typically we only want to keep best for, q5-8 sub max are trash and dont meet the qualifications
# Rare mods are kept regardless of quality
# listed rare skins are kept too
class WeaponConfig:
    def __init__(self,
                 white: InventoryMode = InventoryMode.SALVAGE,
                 blue: InventoryMode = InventoryMode.SELL,
                 purple: InventoryMode = InventoryMode.SELL,
                 gold: InventoryMode = InventoryMode.SELL,
                 green: InventoryMode = InventoryMode.DEPOSIT,
                 q0: InventoryMode = InventoryMode.DEPOSIT,
                 q5: InventoryMode = InventoryMode.DEPOSIT,
                 q6: InventoryMode = InventoryMode.DEPOSIT,
                 q7: InventoryMode = InventoryMode.DEPOSIT,
                 q8: InventoryMode = InventoryMode.DEPOSIT,
                 q9: InventoryMode = InventoryMode.DEPOSIT,
                 q10: InventoryMode = InventoryMode.SELL,
                 q11: InventoryMode = InventoryMode.SELL,
                 q12: InventoryMode = InventoryMode.SELL,
                 q13: InventoryMode = InventoryMode.SELL,
                 specials: InventoryMode = InventoryMode.DEPOSIT,
    ):
        self.white: InventoryMode = white
        self.blue: InventoryMode = blue
        self.purple: InventoryMode = purple
        self.gold: InventoryMode = gold
        self.green: InventoryMode = green
        self.q0: InventoryMode = q0
        self.q5: InventoryMode = q5
        self.q6: InventoryMode = q6
        self.q7: InventoryMode = q7
        self.q8: InventoryMode = q8
        self.q9: InventoryMode = q9
        self.q10: InventoryMode = q10
        self.q11: InventoryMode = q11
        self.q12: InventoryMode = q12
        self.q13: InventoryMode = q13
        self.specials: InventoryMode = specials


class WeaponsConfig:
    def __init__(
            self,
            axe: WeaponConfig = WeaponConfig(),
            bow: WeaponConfig = WeaponConfig(),
            hammer: WeaponConfig = WeaponConfig(),
            wand: WeaponConfig = WeaponConfig(),
            staff: WeaponConfig = WeaponConfig(),
            sword: WeaponConfig = WeaponConfig(),
            scroll: WeaponConfig = WeaponConfig(),
            daggers: WeaponConfig = WeaponConfig(),
            scythe: WeaponConfig = WeaponConfig(),
            spear: WeaponConfig = WeaponConfig(),
            # TODO by attribute?
            offhand: WeaponConfig = WeaponConfig(),
            # TODO by attribute?
            shield: WeaponConfig = WeaponConfig(),
    ):
        self.axe: WeaponConfig = axe
        self.bow: WeaponConfig = bow
        self.offhand: WeaponConfig = offhand
        self.hammer: WeaponConfig = hammer
        self.wand: WeaponConfig = wand
        self.shield: WeaponConfig = shield
        self.staff: WeaponConfig = staff
        self.sword: WeaponConfig = sword
        self.scroll: WeaponConfig = scroll
        self.daggers: WeaponConfig = daggers
        self.scythe: WeaponConfig = scythe
        self.spear: WeaponConfig = spear

    pass


# Todo later
# class MaterialsConfig:
#     pass


class InventoryUtilsConfig:
    def __init__(
            self,
            salvage_config: SalvageConfig = SalvageConfig(),
            weapons_config: WeaponsConfig = WeaponsConfig(),
            # material_config: MaterialsConfig = MaterialsConfig(),
            block_list_item_type: list[int] = DEFAULT_ITEM_TYPE_BLOCK_LIST,
            block_list_model_id: list[int] = DEFAULT_MODEL_ID_BLOCK_LIST
    ):
        self.weapons_config: WeaponsConfig = weapons_config
        self.salvage_config: SalvageConfig = salvage_config
        # self.material_config: MaterialsConfig = material_config

        # TODO Keys

        # TODO Scroll

        # TODO Dye

        self.block_list_item_type: list[int] = block_list_item_type
        self.block_list_model_id: list[int] = block_list_model_id


class InventoryUtils:

    def __init__(
        self,
    ):
        project_root = Py4GW.Console.get_projects_path()
        self.MOD_DB = ModDatabase.load(os.path.join(project_root, "Sources/marks_sources/mods_data"))


    @staticmethod
    def GetIDKits():
        count_of_id_kits = Inventory.GetModelCount(ModelID.Superior_Identification_Kit)  #5899 model for ID kit
        return count_of_id_kits

    @staticmethod
    def GetSalvageKits():
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Salvage_Kit)  #2992 model for salvage kit
        return count_of_salvage_kits

    @staticmethod
    def GetExpertSalvageKits():
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Expert_Salvage_Kit)  #2991 model for expert salvage kit
        return count_of_salvage_kits

    def has_salvage_kits(self):
        return self.GetSalvageKits() > 0 and self.GetExpertSalvageKits() > 0

    def get_inventory_items(
            self,
            inventory_config: InventoryUtilsConfig,
            slot_blacklist: list[tuple[int, int]] = [],
            bags=range(Bags.Backpack, Bags.Bag2+1)
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

    def _apply_action_for_salvage(
            self, salvage_config: SalvageConfig,
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
                if constants.DEBUG: ConsoleLog("InvUtil","Special")
                return salvage_config.specials

        return default_salvage_item

    def _default_apply_action_for_weapon(
            self, weapon_config: WeaponConfig,
            item_id: int
    ) -> InventoryMode:
        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int == 0:
            return InventoryMode.KEEP_DONT_IDENTIFY

        if Item.Rarity.IsGreen(item_id):
            return weapon_config.green
        if Item.Rarity.IsGold(item_id):
            return weapon_config.gold
        if Item.Rarity.IsPurple(item_id):
            return weapon_config.purple
        if Item.Rarity.IsBlue(item_id):
            return weapon_config.blue
        return weapon_config.white

    def get_mods_from_item(self, item_id) -> tuple[str | None, str | None, str | None, ParsedModifierResult]:
        modifiers = []
        item = Item.item_instance(item_id)
        for mod in item.modifiers:
            modifiers.append(
                [
                    mod.GetIdentifier(),
                    mod.GetArg1(),
                    mod.GetArg2(),
                ]
            )
        # 2. Parse any item's raw modifiers
        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        result: ParsedModifierResult = parse_modifiers(
            modifiers=modifiers,
            item_type=item_type_to_int,
            model_id=GLOBAL_CACHE.Item.GetModelID(item_id),
            db=self.MOD_DB,
        )

        prefix = None
        suffix = None
        inherent = None

        if result.prefix and isinstance(result.prefix, MatchedWeaponModInfo):
            prefix = result.prefix.weapon_mod.name
        elif result.prefix and isinstance(result.prefix, MatchedRuneInfo):
            prefix = result.prefix.rune.name

        if result.inherent and isinstance(result.inherent, MatchedWeaponModInfo):
            inherent = result.inherent.weapon_mod.name

        if result.suffix and isinstance(result.suffix, MatchedWeaponModInfo):
            suffix = result.suffix.weapon_mod.name
        elif result.prefix and isinstance(result.suffix, MatchedRuneInfo):
            suffix = result.suffix.rune.name

        return prefix, suffix, inherent, result

    def is_maxed(
            self, item_id,
            parsed_modifiers: ParsedModifierResult,
            item_type: ItemType
    ):

        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int == 0:
            return True

        if parsed_modifiers is None:
            prefix, suffix, inherent, parsed_modifiers = self.get_mods_from_item(item_id)

        res : bool | None = None

        if item_type == ItemType.Wand or item_type == ItemType.Staff:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg >= 11 and max_dmg >= 21 # i like 21 wands too

        if item_type == ItemType.Axe:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg >= 6 and max_dmg >= 28

        if item_type == ItemType.Bow:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg >= 15 and max_dmg >= 28

        if item_type == ItemType.Daggers:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg >= 7 and max_dmg >= 17

        if item_type == ItemType.Hammer:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg >= 19 and max_dmg >= 35

        if item_type == ItemType.Sword:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg >= 15 and max_dmg >= 22

        if item_type == ItemType.Spear:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg >= 14 and max_dmg >= 27

        if item_type == ItemType.Scythe:
            min_dmg, max_dmg = parsed_modifiers.damage
            res = min_dmg > 9 or (
                    min_dmg >= 9 and max_dmg >= 41
            )

        if item_type == ItemType.Shield:
            max_armor, min_armor = parsed_modifiers.shield_armor
            res = (max_armor >= 16 or min_armor >= 16)

        if item_type == ItemType.Offhand:
            return True

        if res is None or res:
            res2 = len(parsed_modifiers.max_runes) > 0 or len(parsed_modifiers.max_weapon_mods) > 0
            if res2:
                if constants.DEBUG: ConsoleLog("InvUtil",f"Item {item_id} is not normal max of {item_type} but has max mods, marking true.")
                return True

        if res is not None and res:
            return res

        if res is None:
            if constants.DEBUG: ConsoleLog("InvUtil",f"Item {item_id} is of unknown item type: {item_type}")
            return True

        return False

    def _apply_action_for_weapon(
            self, weapon_config: WeaponConfig,
            item_id: int,
            item_type: ItemType
    ) -> InventoryMode:
        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int == 0:
            return InventoryMode.KEEP_DONT_IDENTIFY

        default_action = self._default_apply_action_for_weapon(weapon_config, item_id)
        prefix, suffix, inherent, parsed_modifiers = self.get_mods_from_item(item_id)

        if parsed_modifiers.is_highly_salvageable:  # todo make configure-able
            if constants.DEBUG: ConsoleLog("InvUtil",f"is_highly_salvageable #{item_id}")
            default_action = InventoryMode.SALVAGE
        if parsed_modifiers.has_increased_value:  # todo make configure-able
            if constants.DEBUG: ConsoleLog("InvUtil",f"has_increased_value #{item_id}")
            default_action = InventoryMode.SELL

        item_instance = Item.item_instance(item_id)
        if item_instance is None:
            if constants.DEBUG: ConsoleLog("InvUtil",f"no item instance, the item is probably already gone but lets not freak out #{item_id}")
            return InventoryMode.KEEP_DONT_IDENTIFY
        for mod in item_instance.modifiers:
            # Forget Me Not max value identifier
            if mod.GetIdentifier() == 10280 and mod.GetArg1() >= 19:
                return InventoryMode.KEEP
            # of the profession
            elif mod.GetIdentifier() == 10408:
                return InventoryMode.KEEP

            # todo result.attribute
        if parsed_modifiers.requirements is not None:
            if parsed_modifiers.requirements == 0:
                # todo check max
                default_action = weapon_config.q0
            if parsed_modifiers.requirements == 5:
                # todo check max
                default_action = weapon_config.q5
            if parsed_modifiers.requirements == 6:
                # todo check max
                default_action = weapon_config.q6
            if parsed_modifiers.requirements == 7:
                # todo check max
                default_action = weapon_config.q7

            if self.is_maxed(item_id, parsed_modifiers, item_type):
                if constants.DEBUG: ConsoleLog("InvUtil",f"Item {item_id} is maxed")
                if parsed_modifiers.requirements == 8:
                    default_action = weapon_config.q8
                if parsed_modifiers.requirements == 9:
                    default_action = weapon_config.q9
                if parsed_modifiers.requirements == 10:
                    default_action = weapon_config.q10
                if parsed_modifiers.requirements == 11:
                    default_action = weapon_config.q11
                if parsed_modifiers.requirements == 12:
                    default_action = weapon_config.q12
                if parsed_modifiers.requirements == 13:
                    default_action = weapon_config.q13
        else:
            if constants.DEBUG: ConsoleLog("InvUtil","No item requirements known")

        # default rules

        if weapon_config.specials is not None:
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_weapon_type
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_rune_type
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_inscription_type
            if (filter_valuable_weapon_type(item_id) or
                    filter_valuable_rune_type(item_id) or
                    filter_valuable_inscription_type(item_id)
            ):
                if constants.DEBUG: ConsoleLog("InvUtil","!Special!")
                return weapon_config.specials

        return default_action

    def _get_action_for_item(
            self,
            inventory_config: InventoryUtilsConfig,
            item_id: int,
            item_type: ItemType
    ) -> InventoryMode:

        if item_type == ItemType.Salvage:
            return self._apply_action_for_salvage(inventory_config.salvage_config, item_id)

        if item_type == ItemType.Axe:
            return self._apply_action_for_weapon(inventory_config.weapons_config.axe, item_id, item_type)
        if item_type == ItemType.Bow:
            return self._apply_action_for_weapon(inventory_config.weapons_config.bow, item_id, item_type)
        if item_type == ItemType.Offhand:
            return self._apply_action_for_weapon(inventory_config.weapons_config.offhand, item_id, item_type)
        if item_type == ItemType.Hammer:
            return self._apply_action_for_weapon(inventory_config.weapons_config.hammer, item_id, item_type)
        if item_type == ItemType.Wand:
            return self._apply_action_for_weapon(inventory_config.weapons_config.wand, item_id, item_type)
        if item_type == ItemType.Shield:
            return self._apply_action_for_weapon(inventory_config.weapons_config.shield, item_id, item_type)
        if item_type == ItemType.Staff:
            return self._apply_action_for_weapon(inventory_config.weapons_config.staff, item_id, item_type)
        if item_type == ItemType.Sword:
            return self._apply_action_for_weapon(inventory_config.weapons_config.sword, item_id, item_type)
        if item_type == ItemType.Daggers:
            return self._apply_action_for_weapon(inventory_config.weapons_config.daggers, item_id, item_type)
        if item_type == ItemType.Scythe:
            return self._apply_action_for_weapon(inventory_config.weapons_config.scythe, item_id, item_type)
        if item_type == ItemType.Spear:
            return self._apply_action_for_weapon(inventory_config.weapons_config.spear, item_id, item_type)

        return InventoryMode.KEEP_DONT_IDENTIFY

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
            ItemType.Salvage,
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
                return self._get_action_for_item(inventory_config, item_id, item_type)

        # I dunno what this is
        return InventoryMode.KEEP_DONT_IDENTIFY
