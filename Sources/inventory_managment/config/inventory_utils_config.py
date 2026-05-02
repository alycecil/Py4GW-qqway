from enum import Enum

DEFAULT_ITEM_TYPE_BLOCK_LIST = [7, 17, 6, 3, 4, 44, 45, 10, 13, 20, 16, 29, 19, 34, 11, 33, 21, 8, 31, 43, 30, 255, 9]
DEFAULT_MODEL_ID_BLOCK_LIST = [
    522, 525, 2473, 27974, 399, 1045, 1055, 1058, 1060, 1064, 1065, 1066, 1067, 1660,
    1752, 1768, 1769, 1770, 1771, 1772, 1773, 1870, 1879, 1880, 1881, 1883, 1884, 1885,
    1900, 1953, 1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967,
    1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1985, 1986, 1987, 1988, 1989,
    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
    2004, 2005, 2006, 2007, 2039, 2071, 2079, 2474, 27033, 27052, 31202, 31203, 31204,
    36669, 36677, 36679, 27047]


class InventoryMode(Enum):
    KEEP_DONT_IDENTIFY = 0
    KEEP = 1
    DEPOSIT = 2
    SALVAGE = 10
    SELL = 20
    SELL_DONT_IDENTIFY = 21


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


class WeaponConfig:
    def __init__(self,
                 white: InventoryMode = InventoryMode.SALVAGE,
                 blue: InventoryMode = InventoryMode.SELL,
                 purple: InventoryMode = InventoryMode.SELL,
                 gold: InventoryMode = InventoryMode.SELL,
                 green: InventoryMode = InventoryMode.DEPOSIT,
                 q0: InventoryMode = InventoryMode.DEPOSIT,
                 q1: InventoryMode = None,
                 q2: InventoryMode = None,
                 q3: InventoryMode = InventoryMode.DEPOSIT,
                 q4: InventoryMode = None,
                 q5: InventoryMode = InventoryMode.DEPOSIT,
                 q6: InventoryMode = None,
                 q7: InventoryMode = InventoryMode.DEPOSIT,
                 q8: InventoryMode = InventoryMode.DEPOSIT,
                 q9: InventoryMode = None,
                 q10: InventoryMode = None,
                 q11: InventoryMode = None,
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
        self.q1: InventoryMode = q1
        self.q2: InventoryMode = q2
        self.q3: InventoryMode = q3
        self.q4: InventoryMode = q4
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
            shield_strength: WeaponConfig = WeaponConfig(),
            shield_tactics: WeaponConfig = WeaponConfig(),
            shield_command: WeaponConfig = WeaponConfig(),
            shield_motivation: WeaponConfig = WeaponConfig(),
    ):
        self.axe: WeaponConfig = axe
        self.bow: WeaponConfig = bow
        self.offhand: WeaponConfig = offhand
        self.hammer: WeaponConfig = hammer
        self.wand: WeaponConfig = wand
        self.shield_strength: WeaponConfig = shield_strength
        self.shield_tactics: WeaponConfig = shield_tactics
        self.shield_command: WeaponConfig = shield_command
        self.shield_motivation: WeaponConfig = shield_motivation
        self.staff: WeaponConfig = staff
        self.sword: WeaponConfig = sword
        self.scroll: WeaponConfig = scroll
        self.daggers: WeaponConfig = daggers
        self.scythe: WeaponConfig = scythe
        self.spear: WeaponConfig = spear

    pass


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
