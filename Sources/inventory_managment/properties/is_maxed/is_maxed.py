from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.inventory_managment import constants
from Sources.inventory_managment.properties.mods.get_mods_from_item import GetMods
from Sources.marks_sources.mods_parser import ParsedModifierResult


class IsMaxed:

    def is_maxed(
            self,
            item_id,
            parsed_modifiers: ParsedModifierResult = None,
            item_type: ItemType = None
    ):

        item_type_to_int, item1_type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
        if item_type_to_int == 0:
            return True

        if item_type is None:
            item_type = ItemType(item_type_to_int)

        if parsed_modifiers is None:
            prefix, suffix, inherent, parsed_modifiers = GetMods().get_mods_from_item(item_id)

        requirements = parsed_modifiers.requirements
        offset = 0
        if requirements is not None and requirements < 9:
            offset = 9 - requirements

        res: bool | None = None

        if item_type == ItemType.Shield:
            max_armor, min_armor = parsed_modifiers.shield_armor
            if constants.DEBUG: ConsoleLog("InvUtil",
                                           f"Shield {item_id} q{requirements} Damage {max_armor} {min_armor}")
            res = (max_armor >= 16 - offset or min_armor >= 16 - offset)

        elif item_type == ItemType.Offhand:
            if constants.DEBUG: ConsoleLog("InvUtil", f"Offhand {item_id} q{requirements} : {parsed_modifiers}")
            return True

        else:
            min_dmg, max_dmg = parsed_modifiers.damage

            if constants.DEBUG: ConsoleLog("InvUtil", f"Weapon {item_id} q{requirements} Damage {min_dmg} {max_dmg}")

            if item_type == ItemType.Wand or item_type == ItemType.Staff:
                res = min_dmg >= 11 - offset and max_dmg >= 21 - offset  # i like 21 wands too

            if item_type == ItemType.Axe:
                res = min_dmg >= 6 - offset and max_dmg >= 28 - offset

            if item_type == ItemType.Bow:
                res = min_dmg >= 15 - offset and max_dmg >= 28 - offset

            if item_type == ItemType.Daggers:
                res = min_dmg >= 7 - offset and max_dmg >= 17 - offset

            if item_type == ItemType.Hammer:
                res = min_dmg >= 19 - offset and max_dmg >= 35 - offset

            if item_type == ItemType.Sword:
                res = min_dmg >= 15 - offset and max_dmg >= 22 - offset

            if item_type == ItemType.Spear:
                res = min_dmg >= 14 - offset and max_dmg >= 27 - offset

            if item_type == ItemType.Scythe:
                res = min_dmg > 9 or (
                        min_dmg >= 9 - offset and max_dmg >= 41 - offset
                )

        if res is None or res:
            res2 = len(parsed_modifiers.max_runes) > 0 or len(parsed_modifiers.max_weapon_mods) > 0
            if res2:
                if constants.DEBUG: ConsoleLog("InvUtil",
                                               f"Item {item_id} is not normal max of {item_type} but has max mods {parsed_modifiers.max_runes} and {parsed_modifiers.max_weapon_mods}, marking true.")
                return True

        if res is not None and res:
            return res

        if res is None:
            if constants.DEBUG: ConsoleLog("InvUtil", f"Item {item_id} is of unknown item type: {item_type}")
            return True

        return False