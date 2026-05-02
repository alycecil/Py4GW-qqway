from Py4GWCoreLib import GLOBAL_CACHE, Item
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.inventory_managment import constants
from Sources.inventory_managment.config.inventory_utils_config import WeaponConfig, InventoryMode, InventoryUtilsConfig
from Sources.inventory_managment.properties.mods.get_mods_from_item import GetMods

class WeaponHandler:

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

    def _apply_action_for_weapon(
            self,
            weapon_config: WeaponConfig,
            item_id: int,
            item_type: ItemType
    ) -> InventoryMode:
        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int == 0:
            return InventoryMode.KEEP_DONT_IDENTIFY

        default_action = self._default_apply_action_for_weapon(weapon_config, item_id)
        prefix, suffix, inherent, parsed_modifiers = GetMods().get_mods_from_item(item_id)

        if parsed_modifiers.is_highly_salvageable:  # todo make configure-able
            if constants.DEBUG: ConsoleLog("InvUtil", f"is_highly_salvageable #{item_id}")
            default_action = InventoryMode.SALVAGE
        if parsed_modifiers.has_increased_value:  # todo make configure-able
            if constants.DEBUG: ConsoleLog("InvUtil", f"has_increased_value #{item_id}")
            default_action = InventoryMode.SELL

        item_instance = Item.item_instance(item_id)
        if item_instance is None:
            if constants.DEBUG: ConsoleLog("InvUtil",
                                           f"no item instance, the item is probably already gone but lets not freak out #{item_id}")
            return InventoryMode.KEEP_DONT_IDENTIFY
        for mod in item_instance.modifiers:
            # Forget Me Not max value identifier
            if mod.GetIdentifier() == 10280 and mod.GetArg1() >= 19:
                return InventoryMode.KEEP
            # of the profession
            elif mod.GetIdentifier() == 10408:
                return InventoryMode.KEEP

            # todo result.attribute
        if not Item.Rarity.IsWhite(item_id) and parsed_modifiers.requirements is not None:

            if inventory_utils.is_maxed(item_id, parsed_modifiers, item_type):
                if constants.DEBUG: ConsoleLog("InvUtil", f"Item {item_id} is maxed")

                if parsed_modifiers.requirements == 0 and weapon_config.q0 is not None:
                    default_action = weapon_config.q0
                if parsed_modifiers.requirements == 1 and weapon_config.q1 is not None:
                    default_action = weapon_config.q1
                if parsed_modifiers.requirements == 2 and weapon_config.q2 is not None:
                    default_action = weapon_config.q2
                if parsed_modifiers.requirements == 3 and weapon_config.q3 is not None:
                    default_action = weapon_config.q3
                if parsed_modifiers.requirements == 4 and weapon_config.q4 is not None:
                    default_action = weapon_config.q4
                if parsed_modifiers.requirements == 5 and weapon_config.q5 is not None:
                    default_action = weapon_config.q5
                if parsed_modifiers.requirements == 6 and weapon_config.q6 is not None:
                    default_action = weapon_config.q6
                if parsed_modifiers.requirements == 7 and weapon_config.q7 is not None:
                    default_action = weapon_config.q7
                if parsed_modifiers.requirements == 8 and weapon_config.q8 is not None:
                    default_action = weapon_config.q8
                if parsed_modifiers.requirements == 9 and weapon_config.q9 is not None:
                    default_action = weapon_config.q9
                if parsed_modifiers.requirements == 10 and weapon_config.q10 is not None:
                    default_action = weapon_config.q10
                if parsed_modifiers.requirements == 11 and weapon_config.q11 is not None:
                    default_action = weapon_config.q11
                if parsed_modifiers.requirements == 12 and weapon_config.q12 is not None:
                    default_action = weapon_config.q12
                if parsed_modifiers.requirements == 13 and weapon_config.q13 is not None:
                    default_action = weapon_config.q13
        else:
            if constants.DEBUG: ConsoleLog("InvUtil", "No item requirements known")

        # default rules

        if weapon_config.specials is not None:
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_weapon_type
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_rune_type
            from Sources.Sasemoi.utils.inventory_utils import filter_valuable_inscription_type
            if (filter_valuable_weapon_type(item_id) or
                    filter_valuable_rune_type(item_id) or
                    filter_valuable_inscription_type(item_id)
            ):
                if constants.DEBUG: ConsoleLog("InvUtil", "!Special!")
                return weapon_config.specials

        return default_action

    def get_action_for_item(
            self,
            inventory_config: InventoryUtilsConfig,
            item_id: int,
            item_type: ItemType
    ) -> InventoryMode:

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
            return self._handle_shieled(inventory_config, item_id, item_type)
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

    def _handle_shieled(self, inventory_config, item_id, item_type):
        # TODO
        return self._apply_action_for_weapon(inventory_config.weapons_config.shield_motivation, item_id, item_type)