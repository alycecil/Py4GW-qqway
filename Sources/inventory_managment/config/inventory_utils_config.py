from enum import Enum

from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Sources.inventory_managment import constants

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


class CommonItemConfig:
    def __init__(
            self,
            champagnepopper: InventoryMode | None | None = InventoryMode.DEPOSIT,
            krytanbrandy: InventoryMode | None = InventoryMode.DEPOSIT,
            huntersale: InventoryMode | None = InventoryMode.DEPOSIT,
            bottlerocket: InventoryMode | None = InventoryMode.DEPOSIT,
            hardapplecider: InventoryMode | None = InventoryMode.DEPOSIT,
            birthdaycupcake: InventoryMode | None = InventoryMode.DEPOSIT,
            shamrockale: InventoryMode | None = InventoryMode.DEPOSIT,
            fourleafclover: InventoryMode | None = InventoryMode.DEPOSIT,
            bottleofgrog: InventoryMode | None = InventoryMode.DEPOSIT,
            sugarybluedrink: InventoryMode | None = InventoryMode.DEPOSIT,
            wintergreencandycane: InventoryMode | None = InventoryMode.DEPOSIT,
            victorytoken: InventoryMode | None = InventoryMode.DEPOSIT,
            snowmansummoner: InventoryMode | None = InventoryMode.DEPOSIT,
            ghostinthebox: InventoryMode | None = InventoryMode.DEPOSIT,
            vialofabsinthe: InventoryMode | None = InventoryMode.DEPOSIT,
            squashserum: InventoryMode | None = InventoryMode.DEPOSIT,
            eggnog: InventoryMode | None = InventoryMode.DEPOSIT,
            spikedeggnog: InventoryMode | None = InventoryMode.DEPOSIT,
            candycorn: InventoryMode | None = InventoryMode.DEPOSIT,
            candyapple: InventoryMode | None = InventoryMode.DEPOSIT,
            pumpkincookie: InventoryMode | None = InventoryMode.DEPOSIT,
            trickortreatbag: InventoryMode | None = InventoryMode.DEPOSIT,
            fruitcake: InventoryMode | None = InventoryMode.DEPOSIT,
            peppermintcandycane: InventoryMode | None = InventoryMode.DEPOSIT,
            rainbowcandycane: InventoryMode | None = InventoryMode.DEPOSIT,
            honeycomb: InventoryMode | None = InventoryMode.DEPOSIT,
            wintersdaygift: InventoryMode | None = InventoryMode.DEPOSIT,
            yuletidetonic: InventoryMode | None = InventoryMode.DEPOSIT,
            lunartoken: InventoryMode | None = InventoryMode.DEPOSIT,
            candycaneshard: InventoryMode | None = InventoryMode.DEPOSIT,
            goldenegg: InventoryMode | None = InventoryMode.DEPOSIT,
            sliceofpumpkinpie: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2007pig: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2008rat: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2009ox: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2010tiger: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2011rabbit: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2012dragon: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2013snake: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2014horse: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2015sheep: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2016monkey: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2017rooster: InventoryMode | None = InventoryMode.DEPOSIT,
            lunarfortune2018dog: InventoryMode | None = InventoryMode.DEPOSIT,
            vialofdye: InventoryMode | None = InventoryMode.DEPOSIT,
    ):
        self.champagnepopper = champagnepopper
        self.krytanbrandy = krytanbrandy
        self.huntersale = huntersale
        self.bottlerocket = bottlerocket
        self.hardapplecider = hardapplecider
        self.birthdaycupcake = birthdaycupcake
        self.shamrockale = shamrockale
        self.fourleafclover = fourleafclover
        self.bottleofgrog = bottleofgrog
        self.sugarybluedrink = sugarybluedrink
        self.wintergreencandycane = wintergreencandycane
        self.victorytoken = victorytoken
        self.snowmansummoner = snowmansummoner
        self.ghostinthebox = ghostinthebox
        self.vialofabsinthe = vialofabsinthe
        self.squashserum = squashserum
        self.eggnog = eggnog
        self.spikedeggnog = spikedeggnog
        self.candycorn = candycorn
        self.candyapple = candyapple
        self.pumpkincookie = pumpkincookie
        self.trickortreatbag = trickortreatbag
        self.fruitcake = fruitcake
        self.peppermintcandycane = peppermintcandycane
        self.rainbowcandycane = rainbowcandycane
        self.honeycomb = honeycomb
        self.wintersdaygift = wintersdaygift
        self.yuletidetonic = yuletidetonic
        self.lunartoken = lunartoken
        self.candycaneshard = candycaneshard
        self.goldenegg = goldenegg
        self.sliceofpumpkinpie = sliceofpumpkinpie
        self.lunarfortune2007pig = lunarfortune2007pig
        self.lunarfortune2008rat = lunarfortune2008rat
        self.lunarfortune2009ox = lunarfortune2009ox
        self.lunarfortune2010tiger = lunarfortune2010tiger
        self.lunarfortune2011rabbit = lunarfortune2011rabbit
        self.lunarfortune2012dragon = lunarfortune2012dragon
        self.lunarfortune2013snake = lunarfortune2013snake
        self.lunarfortune2014horse = lunarfortune2014horse
        self.lunarfortune2015sheep = lunarfortune2015sheep
        self.lunarfortune2016monkey = lunarfortune2016monkey
        self.lunarfortune2017rooster = lunarfortune2017rooster
        self.lunarfortune2018dog = lunarfortune2018dog
        self.vialofdye = vialofdye

    def get_inventory_mode(self, model_id: int) -> InventoryMode | None:
        """Return the InventoryMode for the given model_id if it matches a configured common item."""
        if constants.DEBUG: ConsoleLog("CommonItemConfig", f"lookup for model {model_id}.", Console.MessageType.Error, log=True)

        if model_id == ModelID.Champagne_Popper.value:
            return self.champagnepopper
        elif model_id == ModelID.Krytan_Brandy.value:
            return self.krytanbrandy
        elif model_id == ModelID.Hunters_Ale.value:
            return self.huntersale
        elif model_id == ModelID.Bottle_Rocket.value:
            return self.bottlerocket
        elif model_id == ModelID.Hard_Apple_Cider.value:
            return self.hardapplecider
        elif model_id == ModelID.Birthday_Cupcake.value:
            return self.birthdaycupcake
        elif model_id == ModelID.Shamrock_Ale.value:
            return self.shamrockale
        elif model_id == ModelID.Four_Leaf_Clover.value:
            return self.fourleafclover
        elif model_id == ModelID.Bottle_Of_Grog.value:
            return self.bottleofgrog
        elif model_id == ModelID.Sugary_Blue_Drink.value:
            return self.sugarybluedrink
        elif model_id == ModelID.Wintergreen_Candy_Cane.value:
            return self.wintergreencandycane
        elif model_id == ModelID.Victory_Token.value:
            return self.victorytoken
        elif model_id == ModelID.Snowman_Summoner.value:
            return self.snowmansummoner
        elif model_id == ModelID.Ghost_In_The_Box.value:
            return self.ghostinthebox
        elif model_id == ModelID.Vial_Of_Absinthe.value:
            return self.vialofabsinthe
        elif model_id == ModelID.Squash_Serum.value:
            return self.squashserum
        elif model_id == ModelID.Eggnog.value:
            return self.eggnog
        elif model_id == ModelID.Spiked_Eggnog.value:
            return self.spikedeggnog
        elif model_id == ModelID.Candy_Corn.value:
            return self.candycorn
        elif model_id == ModelID.Candy_Apple.value:
            return self.candyapple
        elif model_id == ModelID.Pumpkin_Cookie.value:
            return self.pumpkincookie
        elif model_id == ModelID.Trick_Or_Treat_Bag.value:
            return self.trickortreatbag
        elif model_id == ModelID.Fruitcake.value:
            return self.fruitcake
        elif model_id == ModelID.Peppermint_Candy_Cane.value:
            return self.peppermintcandycane
        elif model_id == ModelID.Rainbow_Candy_Cane.value:
            return self.rainbowcandycane
        elif model_id == ModelID.Honeycomb.value:
            return self.honeycomb
        elif model_id == ModelID.Wintersday_Gift.value:
            return self.wintersdaygift
        elif model_id == ModelID.Yuletide_Tonic.value:
            return self.yuletidetonic
        elif model_id == ModelID.Lunar_Token.value:
            return self.lunartoken
        elif model_id == ModelID.Candy_Cane_Shard.value:
            return self.candycaneshard
        elif model_id == ModelID.Golden_Egg.value:
            return self.goldenegg
        elif model_id == ModelID.Slice_Of_Pumpkin_Pie.value:
            return self.sliceofpumpkinpie
        elif model_id == ModelID.Lunar_Fortune_2007_Pig.value:
            return self.lunarfortune2007pig
        elif model_id == ModelID.Lunar_Fortune_2008_Rat.value:
            return self.lunarfortune2008rat
        elif model_id == ModelID.Lunar_Fortune_2009_Ox.value:
            return self.lunarfortune2009ox
        elif model_id == ModelID.Lunar_Fortune_2010_Tiger.value:
            return self.lunarfortune2010tiger
        elif model_id == ModelID.Lunar_Fortune_2011_Rabbit.value:
            return self.lunarfortune2011rabbit
        elif model_id == ModelID.Lunar_Fortune_2012_Dragon.value:
            return self.lunarfortune2012dragon
        elif model_id == ModelID.Lunar_Fortune_2013_Snake.value:
            return self.lunarfortune2013snake
        elif model_id == ModelID.Lunar_Fortune_2014_Horse.value:
            return self.lunarfortune2014horse
        elif model_id == ModelID.Lunar_Fortune_2015_Sheep.value:
            return self.lunarfortune2015sheep
        elif model_id == ModelID.Lunar_Fortune_2016_Monkey.value:
            return self.lunarfortune2016monkey
        elif model_id == ModelID.Lunar_Fortune_2017_Rooster.value:
            return self.lunarfortune2017rooster
        elif model_id == ModelID.Lunar_Fortune_2018_Dog.value:
            return self.lunarfortune2018dog
        elif model_id == ModelID.Vial_Of_Dye.value:
            return self.vialofdye
        else:
            if constants.DEBUG: ConsoleLog("CommonItemConfig", f"no get_inventory_mode for model {model_id}.", Console.MessageType.Error, log=True)
            return None


class InventoryUtilsConfig:
    def __init__(
            self,
            salvage_config: SalvageConfig = SalvageConfig(),
            weapons_config: WeaponsConfig = WeaponsConfig(),
            event_item_config: CommonItemConfig = CommonItemConfig(),
            # material_config: MaterialsConfig = MaterialsConfig(),
            block_list_item_type: list[int] = DEFAULT_ITEM_TYPE_BLOCK_LIST,
            block_list_model_id: list[int] = DEFAULT_MODEL_ID_BLOCK_LIST
    ):
        self.weapons_config: WeaponsConfig = weapons_config
        self.salvage_config: SalvageConfig = salvage_config
        self.event_item_config: CommonItemConfig = event_item_config
        # self.material_config: MaterialsConfig = material_config

        # TODO Keys

        # TODO Scroll

        # TODO Dye

        self.block_list_item_type: list[int] = block_list_item_type
        self.block_list_model_id: list[int] = block_list_model_id
