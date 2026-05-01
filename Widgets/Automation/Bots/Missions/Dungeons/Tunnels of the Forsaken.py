# region Imports & Config
import math

from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog, IniManager, HeroType, \
    AgentArray, SharedCommandType, Item, AutoPathing
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
from Py4GWCoreLib.botting_src.property import Property
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
import PyInventory
import Py4GW
import os
import random
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Generator

from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

BOT_NAME = "Tunnels of the Forsaken"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Skill_Icons", "[264] - Pacifism.jpg")

MODULE_NAME = "Tunnels of the Forsaken"
MODULE_ICON = "Textures/Skill_Icons/[264] - Pacifism.jpg"

PIKEN_SQUARE = 40
ZONING_STEP_NAME = "[H]Zoning into explorable area_2"
START_COMBAT_STEP_NAME = "[H]Start Combat_3"

_MULTIBOX_ALTS_KEY = "use_multibox_alts"
_party_mode: int = 0  # 0 = Single Account with Heroes, 1 = Multiboxing
_mode_loaded: bool = False

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True,
              upkeep_hero_ai_active=True,
              upkeep_auto_inventory_management_active=True,
              upkeep_auto_loot_active=True)

bot.config.config_properties.use_conset = Property(bot.config, "use_conset", active=False)
bot.config.config_properties.use_pcons = Property(bot.config, "use_pcons", active=False)

_SETTINGS_SECTION = "TitleBotSettings"
_USE_CONSET_KEY = "use_conset"
_USE_PCONS_KEY = "use_pcons"
_USE_RESTOCK_KITS_KEY = "use_restock_kits"
_ID_KITS_TARGET_KEY = "id_kits_target"
_SALVAGE_KITS_TARGET_KEY = "salvage_kits_target"
_MERCHANT_SELL_MATERIALS_KEY = "merchant_sell_materials"
_MERCHANT_ALT_WAIT_MS_KEY = "merchant_alt_wait_ms"
_RANDOMIZE_DISTRICT_KEY = "randomize_district"
_DEFAULT_ID_KITS_TARGET = 2
_DEFAULT_SALVAGE_KITS_TARGET = 5
_DEFAULT_ALT_SETTLE_WAIT_MS = 2000
_MAX_ALT_SETTLE_WAIT_MS = 5000

_restock_kits_enabled: bool = False
_id_kits_target: int = _DEFAULT_ID_KITS_TARGET
_salvage_kits_target: int = _DEFAULT_SALVAGE_KITS_TARGET
_merchant_sell_materials: bool = False
_merchant_alt_wait_ms: int = _DEFAULT_ALT_SETTLE_WAIT_MS
_randomize_district: bool = True
_SCROLL_MODEL_IDS = {5594, 5595, 5611, 5853, 5975, 5976, 21233}
_SCROLL_MODEL_FILTER = "5594,5595,5611,5853,5975,5976,21233"
_MERCHANT_MANAGED_WIDGETS = ("InventoryPlus",)
_PRETRAVEL_DISABLE_WIDGETS = ("InventoryPlus",)
_RANDOM_DISTRICTS = [6, 7, 8, 9]

# Hero config
_BOT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_HERO_CONFIG_PATH = os.path.join(_BOT_SCRIPT_DIR, f"{BOT_NAME} Heroes.json")
_HERO_ICONS_BASE = os.path.normpath(os.path.join(
    Py4GW.Console.get_projects_path(), "..", "Property-of-Wick-Divinus-and-Kendor",
    "PVE Skills Unlocker", "Textures", "Skill_Icons"
))
_HERO_SLOTS_COUNT = 3

@dataclass
class _PartyHeroSlot:
    hero_id: int = 0
    template: str = ""

def _humanize_hero_name(enum_name: str) -> str:
    if enum_name == "None_":
        return "<Empty>"
    words: List[str] = []
    current = enum_name[0]
    for char in enum_name[1:]:
        if (char.isupper() and not current[-1].isupper()) or (char.isdigit() and not current[-1].isdigit()):
            words.append(current)
            current = char
        else:
            current += char
    words.append(current)
    return " ".join(words)

_HERO_OPTIONS: List[HeroType] = [HeroType.None_] + sorted([h for h in HeroType if h != HeroType.None_], key=lambda h: _humanize_hero_name(h.name))
_HERO_OPTION_LABELS: List[str] = [_humanize_hero_name(h.name) for h in _HERO_OPTIONS]
_HERO_ID_TO_OPTION_INDEX: Dict[int, int] = {int(h): i for i, h in enumerate(_HERO_OPTIONS)}

_HERO_ICON_FILENAMES: Dict[HeroType, str] = {
    HeroType.Norgu: "Norgu-icon.jpg",           HeroType.Goren: "Goren-icon.jpg",
    HeroType.Tahlkora: "Tahlkora-icon.jpg",      HeroType.MasterOfWhispers: "MasterOfWhispers-icon.jpg",
    HeroType.AcolyteJin: "AcolyteSousuke-icon.jpg", HeroType.Koss: "Koss-icon.jpg",
    HeroType.Dunkoro: "Dunkoro-icon.jpg",        HeroType.AcolyteSousuke: "AcolyteSousuke-icon.jpg",
    HeroType.Melonni: "Melonni-icon.jpg",        HeroType.ZhedShadowhoof: "ZhedShadowhoof-icon.jpg",
    HeroType.GeneralMorgahn: "GeneralMorgahn-icon.jpg", HeroType.MagridTheSly: "MargridTheSly-icon.jpg",
    HeroType.Zenmai: "Zenmai-icon.jpg",          HeroType.Olias: "Olias-icon.jpg",
    HeroType.Razah: "Razah-icon.jpg",            HeroType.MOX: "M.O.X.-icon.jpg",
    HeroType.KeiranThackeray: "KeiranThackeray-icon.jpg", HeroType.Jora: "Jora-icon.jpg",
    HeroType.PyreFierceshot: "Pyre_Fierceshot-icon.jpg", HeroType.Anton: "Anton-icon.jpg",
    HeroType.Livia: "Livia-icon.jpg",            HeroType.Hayda: "Hayda-icon.jpg",
    HeroType.Kahmu: "Kahmu-icon.jpg",            HeroType.Gwen: "Gwen-icon.jpg",
    HeroType.Xandra: "Xandra-icon.jpg",          HeroType.Vekk: "Vekk-icon.jpg",
    HeroType.Ogden: "Ogden_Stonehealer-icon.jpg", HeroType.Miku: "Miku-icon.jpg",
    HeroType.ZeiRi: "Zei_Ri-icon.jpg",
}

_DEFAULT_HERO_TEMPLATES: Dict[HeroType, str] = {
    HeroType.Gwen: "OQhkAsC8gFKzJIHM9MdDBcaG4iB",
    HeroType.MasterOfWhispers: "OABDUshnSyBVBoBKgbhVVfCWCA",
    HeroType.Ogden: "OwUUMsG/E4SNgbE3N3ETfQgZAMEA",
}

# Module-level hero config state
_hero_slots: List[_PartyHeroSlot] = [_PartyHeroSlot() for _ in range(_HERO_SLOTS_COUNT)]
_hero_config_dirty: bool = False
_hero_config_status: str = ""
_hero_import_source_index: int = 0

# (model_id, effect_skill_name) â€” single source of truth for consumable use & restock
CONSET_ITEMS: list[tuple[int, str]] = [
    (ModelID.Essence_Of_Celerity.value, "Essence_of_Celerity_item_effect"),
    (ModelID.Grail_Of_Might.value,      "Grail_of_Might_item_effect"),
    (ModelID.Armor_Of_Salvation.value,  "Armor_of_Salvation_item_effect"),
]

PCON_ITEMS: list[tuple[int, str]] = [
    (ModelID.Birthday_Cupcake.value,      "Birthday_Cupcake_skill"),
    (ModelID.Golden_Egg.value,            "Golden_Egg_skill"),
    (ModelID.Candy_Corn.value,            "Candy_Corn_skill"),
    (ModelID.Candy_Apple.value,           "Candy_Apple_skill"),
    (ModelID.Slice_Of_Pumpkin_Pie.value,  "Pie_Induced_Ecstasy"),
    (ModelID.Drake_Kabob.value,           "Drake_Skin"),
    (ModelID.Bowl_Of_Skalefin_Soup.value, "Skale_Vigor"),
    (ModelID.Pahnai_Salad.value,          "Pahnai_Salad_item_effect"),
    (ModelID.War_Supplies.value,          "Well_Supplied"),
]

CONSET_RESTOCK_MODELS = [m for m, _ in CONSET_ITEMS]
PCON_RESTOCK_MODELS   = [m for m, _ in PCON_ITEMS] + [
    ModelID.Honeycomb.value,
    ModelID.Scroll_Of_Resurrection.value,
]


def __customBehaviorMode(mode : bool):
    try:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
        CustomBehaviorParty().set_party_is_combat_enabled(mode)
    except Exception:
        pass


def ConfigurePassiveEnv(bot: Botting) -> None:
    bot.Templates.PacifistForceAutocombat()
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Disable("auto_loot")

    bot.States.AddCustomState(lambda: __customBehaviorMode(False), "Custom Behaviours Off")


def ConfigureAggressiveEnv(bot: Botting) -> None:
    if _party_mode == 1:
        bot.Templates.Multibox_Aggressive()
    else:
        bot.Templates.Aggressive()
    bot.Properties.Enable("auto_inventory_management")
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Enable("auto_loot")

    bot.States.AddCustomState(lambda: __customBehaviorMode(True), "Custom Behaviours On")
# endregion

to_dungeon = [
    (20307,7240),
    (20307,7240),
    (20496,6777),
    (20686,6314),
    (20876,5852),
    (20992,5568),
    (20998,5068),
    (21005,4568),
    (21010,4176),
    (20917,3685),
    (20824,3193),
    (20731,2702),
    (20638,2211),
    (20574,1872),
    (20139,1626),
    (19703,1380),
    (19268,1134),
    (18832,889),
    (18397,643),
    (18024,432),
    (17780,-4),
    (17648,-240),
    (18032,-561),
    (18415,-881),
    (18799,-1202),
    (19182,-1523),
    (19274,-1599),
    (19338,-2095),
    (19402,-2591),
    (19466,-3087),
    (19514,-3457),
    (19398,-3944),
    (19310,-4313),
    (19310,-4313),
    (19310,-4313),
    (19085,-3867),
    (18859,-3421),
    (18633,-2975),
    (18407,-2529),
    (18182,-2083),
    (18069,-1860),
    (17811,-1513),
]

to_althena = [
    (-21338,-4975),
    (-21338,-4975),
    (-20843,-4907),
    (-20347,-4838),
    (-19852,-4769),
    (-19357,-4701),
    (-18862,-4632),
    (-18660,-4604),
    (-18160,-4606),
    (-17660,-4607),
    (-17160,-4609),
    (-16660,-4610),
    (-16643,-4610),
    (-16288,-4962),
    (-15933,-5315),
    (-15578,-5667),
    (-15224,-6019),
    (-14869,-6372),
    (-14667,-6572),
    (-14175,-6663),
    (-13683,-6753),
    (-13191,-6843),
    (-12700,-6934),
    (-12208,-7024),
    (-11716,-7114),
    (-11224,-7204),
    (-10735,-7294),
    (-10236,-7318),
    (-9930,-7332),
    (-9929,-7440),
    (-9480,-7661),
    (-9423,-7688),
    (-8996,-7950),
    (-8933,-7988),
    (-8606,-8367),
    (-8280,-8746),
    (-7953,-9124),
    (-7627,-9503),
    (-7345,-9829),
    (-7345,-9829),
]

to_bandits = [
    (-7373,-9204),
    (-7373,-9204),
    (-7587,-8752),
    (-7776,-8352),
    (-7981,-7896),
    (-8186,-7440),
    (-8392,-6984),
    (-8597,-6528),
    (-8640,-6432),
    (-8740,-5942),
    (-8840,-5452),
    (-8886,-5229),
    (-8915,-4730),
    (-8928,-4512),
    (-9074,-4034),
    (-9131,-3848),
    (-9131,-3848),
]


ROOM_TWO = [
    (-9205,-4080),
    (-9205,-4080),
    (-9516,-3689),
    (-9827,-3297),
    (-10138,-2906),
    (-10449,-2514),
    (-10464,-2496),
    (-10848,-2304),
    (-10848,-2016),
    (-10968,-1636),
    (-11005,-960),
    (-10692,-524),
    (-10357,-221),
]


OUT_OF_LEVEL_ONE = [
    (-10357,-221),
    (-10357,-221),
    (-10030,157),
    (-9696,369),
    (-9286,615),
    (-8935,931),
    (-8713,1182),
    (-8611,1577),
    (-8584,1960),
    (-8626,2411),
    (-8584,1960),
    (-8626,3025),
    (-8669,3654),
    (-8684,4619),
    (-8626,5614),
]


LEVEL_TWO_PART_ONE = [
    (-7838,8691),
    (-7838,8691),
    (-7249,8792),
    (-6672,8972),
    (-6131,9251),
    (-5726,9504),
    (-5311,9630),
    (-4987,9756),
    (-4690,9945),
    (-4383,10152),
    (-4014,10297),
    (-3690,10566),
    (-3274,10843),
    (-3131,11189),
    (-2950,11477),
    (-2796,11638),
    (-2653,11837),
    (-2320,12003),
    (-1856,12191),
    (-1320,12117),
    (-770,12387),
    (-346,12630),
    (-2,12940),
    (158,13162),
    (509,13377),
    (780,13784),
    (1158,14198),
    (1525,14481),
    (1864,14849),
    (1834,15198),
    (1771,15577),
    (1618,16253),
    (1230,16847),
    (762,17109),
    (762,17109),
    (474,17517),
    (186,17926),
    (-102,18335),
    (-390,18744),
    (-406,18767),
    (-406,18767),
    (-406,18767),
    (-436,19266),
    (-466,19765),
    (-491,20175),
    (-491,20175),
    (-491,20175),
    (-970,20316),
    (-1450,20457),
    (-1930,20599),
    (-2409,20740),
    (-2889,20881),
    (-3070,20935),
    (-3070,20935),
    (-3070,20935),
    (-3558,20824),
    (-4045,20714),
    (-4126,20695),
    (-4126,20695),
    (-4126,20695),
    (-4341,21147),
    (-4534,21554),
    (-4534,21554),
    (-4534,21554),
    (-5028,21473),
    (-5521,21392),
    (-5992,21207),
    (-6562,21185),
    (-7001,21149),
    (-7427,21091),
    (-7903,20875),
]


LEVEL_TWO_PART_TWO = [
    (-7903,20875),
    (-7996,21106),
    (-8227,21387),
    (-8688,21531),
    (-9171,21351),
    (-9770,21322),
    (-10034,21044),
    (-10392,20792),
    (-10681,20568),
    (-11072,20451),
    (-11459,20405),
    (-11820,20333),
    (-12243,20279),
    (-12638,20236),
    (-13125,20125),
    (-13550,20117),
    (-14072,20009),
    (-14577,19910),
    (-15116,19763),
    (-15649,19504),
    (-16109,19360),
    (-16410,19002),
    (-16415,19000),
    (-16415,19000),
    (-16415,19000),
    (-16429,18500),
    (-16443,18000),
    (-16449,17773),
    (-16449,17773),
    (-16449,17773),
    (-16753,17376),
    (-17011,17038),
    (-17011,17038),
    (-17011,17038),
    (-17018,16785),
    (-16997,16187),
    (-16874,15963),
    (-16874,15963),
    (-16406,15632),
    (-16406,15632),
    (-16406,15632),
    (-15934,15798),
    (-15463,15965),
    (-15425,15978),
    (-15425,15978),
    (-15425,15978),
    (-14979,16203),
    (-14418,16472),
    (-14007,16773),
    (-13724,17124),
    (-13724,17124),
    (-13724,17124),
    (-13389,17495),
    (-13053,17866),
    (-12902,18032),
    (-12902,18032),
    (-12902,18032),
    (-12431,18200),
    (-11960,18367),
    (-11489,18534),
    (-11259,18616),
    (-11259,18616),
    (-11259,18616),
    (-10759,18603),
    (-10322,18659),
    (-9879,18819),
]


LEVEL_TWO_PART_TWO_PASSIVE = [
    (-9505,18689),
    (-9092,18689),
    (-8577,18692),
    (-7946,18835),
]


LEVEL_TWO_PART_THREE = [
    (-7619,18729),
    (-7238,18439),
    (-6826,17895),
    (-6491,17520),
    (-6431,17234),
    (-6356,17076),
    (-6331,16932),
    (-6271,16508),
    (-6281,15969),
    (-6205,15474),
    (-6130,14980),
    (-6119,14911),
    (-6119,14911),
    (-6119,14911),
    (-6472,14556),
    (-6824,14202),
    (-7177,13847),
    (-7455,13651),
    (-7924,13674),
    (-8288,13753),
    (-8682,13962),
    (-8772,14321),
    (-8679,14812),
    (-8606,15094),
    (-8548,15502),
    (-8548,15502),
    (-8548,15502),
    (-8606,15939),
    (-8873,16423),
    (-9248,16627),
    (-9248,16627),
    (-9248,16627),
    (-9691,16857),
    (-10134,17088),
    (-10134,17088),
    (-10480,17050),
    (-10679,16745),
    (-10968,16497),
    (-11253,16355),
    (-11489,16180),
    (-11833,15891),
    (-12247,15610),
    (-12268,15596),
    (-12268,15596),
    (-12778,15359),
    (-12778,15359),
    (-13127,15000),
    (-13567,14853),
    (-13774,14588),
    (-13867,14132),
    (-13935,13665),
    (-14136,13207),
    (-14220,13016),
    (-14220,13016),
    (-14220,13016),
    (-14510,12608),
    (-14799,12200),
    (-15020,11890),
    (-15020,11890),
    (-15020,11890),
    (-15463,11657),
    (-15905,11425),
    (-15906,11425),
    (-15906,11425),
    (-15906,11425),
    (-16082,10957),
    (-16258,10489),
    (-16266,10466),
    (-16266,10466),
    (-16266,10466),
    (-16174,9975),
    (-16082,9483),
    (-16043,9277),
    (-16043,9277),
    (-16043,9277),
    (-15902,8797),
    (-15760,8317),
    (-15733,8224),
    (-15733,8224),
    (-15733,8224),
    (-15717,7724),
    (-15700,7225),
    (-15697,7121),
    (-15697,7121),
    (-15697,7121),
    (-15975,6706),
    (-16165,6422),
    (-16165,6422),
    (-16612,6062),
]


LEVEL_THREE_PART_ONE = [
    (-16351,2364),
    (-16343,2216),
    (-16336,2108),
    (-16307,1609),
    (-16300,1491),
    (-16300,1491),
    (-16300,1491),
    (-15829,1323),
    (-15479,1198),
    (-15479,1198),
    (-15479,1198),
    (-15021,1398),
    (-14563,1599),
    (-14373,1682),
    (-14373,1682),
    (-14373,1682),
    (-14007,2022),
    (-13641,2362),
    (-13274,2703),
    (-12908,3043),
    (-12896,3055),
    (-12896,3055),
    (-12896,3055),
    (-12405,3153),
    (-11915,3250),
    (-11461,3340),
    (-11461,3340),
    (-10943,3228),
    (-10943,3228),
    (-10828,3141),
    (-10494,2813),
    (-10356,2649),
    (-10304,2355),
    (-10390,2131),
    (-10580,1975),
    (-10787,1872),
    (-10986,1716),
    (-10986,1716),
    (-11310,1324),
    (-11629,938),
    (-11649,913),
    (-11764,774),
    (-11945,800),
    (-12213,740),
    (-12118,282),
    (-12429,83),
    (-12429,83),
    (-12965,126),
    (-12965,126),
    (-12965,126),
    (-13370,-166),
    (-13776,-458),
    (-14182,-750),
    (-14200,-763),
    (-14200,-763),
    (-14425,-452),
    (-14917,-496),
    (-15228,-859),
    (-15401,-1083),
    (-15799,-1178),
    (-15980,-945),
    (-16196,-703),
    (-16628,-738),
    (-17008,-746),
    (-17181,-979),
    (-17224,-1386),
    (-17164,-1671),
    (-17051,-2129),
    (-17043,-2828),
    (-16991,-3200),
    (-16749,-3433),
    (-16049,-3537),
    (-15591,-3554),
    (-14926,-3554),
    (-14511,-3649),
    (-14157,-3761),
    (-13785,-3865),
    (-13423,-3865),
    (-13042,-3900),
    (-12706,-3926),
    (-12369,-3917),
    (-11842,-3865),
    (-11487,-3805),
    (-11237,-3744),
    (-10692,-3615),
    (-10407,-3839),
    (-10381,-4142),
    (-10252,-4427),
    (-10217,-4012),
    (-10364,-3666),
    (-10826,-3633),
    (-11279,-3727),
    (-11838,-3854),
    (-12297,-3871),
    (-12778,-3943),
    (-13015,-4009),
    (-13043,-4103),
    (-13198,-4153),
    (-13198,-4153),
    (-13026,-4622),
    (-12859,-4858),
    (-12755,-5048),
    (-12617,-5385),
    (-12548,-5730),
    (-12357,-5868),
]

SPECIAL_MODEL_IDS = [
    123,
    305,
]

def pickup_torch(max_scan_dist: float = 5000, attempts: int = 40) -> Generator:
    def _dist(ax: float, ay: float, bx: float, by: float) -> float:
        return math.hypot(ax - bx, ay - by)
    inv = PyInventory.PyInventory()
    me = int(Player.GetAgentID())

    ConsoleLog("TORCH", "Scanning for Torch")

    for _ in range(attempts):
        arr = AgentArray.GetItemArray()
        arr = AgentArray.Filter.ByDistance(arr, Player.GetXY(), max_scan_dist)
        arr = AgentArray.Sort.ByDistance(arr, Player.GetXY())

        ground_item_id, owner, target_agent = find_item_on_ground(arr, me)

        if not target_agent:
            ConsoleLog("TORCH", "Failed to find")
            yield from Routines.Yield.wait(150)
            continue

        tx, ty = Agent.GetXY(target_agent)

        ConsoleLog("TORCH", f"Found the item ({tx}, {ty})")

        still_there = yield from try_interact_item(target_agent)

        if not still_there:
            ConsoleLog("TORCH", "Item picked up by first interact")
            yield
            return

        target_agent = yield from try_move_to_item(_dist, target_agent, tx, ty)

        if not target_agent:
            continue

        yield from stopMovement()

        # Ciblage
        Player.ChangeTarget(target_agent)
        yield from Routines.Yield.wait(120)

        ConsoleLog("TORCH", f"pickup try agent={target_agent} ground_item_id={ground_item_id} owner={owner}")

        # Essais : agent_id puis ground_item_id (compat multi-build)
        for _try in range(2):
            yield from try_pickup_item(ground_item_id, inv, target_agent)

            still_there = yield from try_interact_item(target_agent)

            if not still_there:
                ConsoleLog("TORCH", "Torch picked up")
                yield
                return

        ConsoleLog("TORCH", "Torch pickup attempt failed -> retry")
        yield from Routines.Yield.wait(200)

    ConsoleLog("TORCH", "Torch pickup failed")
    yield


def try_pickup_item(ground_item_id, inv, target_agent):
    try:
        inv.PickUpItem(target_agent, True)
    except Exception:
        pass
    yield from Routines.Yield.wait(250)
    try:
        inv.PickUpItem(ground_item_id, True)
    except Exception:
        pass
    yield from Routines.Yield.wait(250)


def stopMovement():
    # stop-move pour Ã©viter annulation
    try:
        px, py = Player.GetXY()
        Player.Move(px, py)
    except Exception:
        pass
    yield from Routines.Yield.wait(80)


def try_move_to_item(_dist, target_agent, tx, ty):
    # Approche
    try:
        Player.Move(tx, ty)
    except Exception:
        pass
    start = time.time() * 1000
    while True:
        px, py = Player.GetXY()
        if _dist(px, py, tx, ty) <= 178:
            break
        if (time.time() * 1000) - start > 9000:
            ConsoleLog("TORCH", "cant reach -> retry")
            target_agent = 0
            break
        yield from Routines.Yield.wait(100)
    return target_agent


def try_interact_item(target_agent):
    # fallback interact
    try:
        Player.Interact(target_agent, False)
    except Exception:
        pass
    yield from Routines.Yield.wait(450)
    # check disparition (ramassÃ©)
    try:
        still_there = bool(Agent.GetItemAgentByID(target_agent))
    except Exception:
        still_there = False
    return still_there


def find_item_on_ground(arr, me):
    target_agent: int = 0
    ground_item_id: int = 0
    owner: int = -1
    for a in arr:
        aid = int(a)
        it = Agent.GetItemAgentByID(aid)
        if not it:
            continue

        gid = None
        try:
            gid = int(Agent.GetItemAgentItemID(aid))
        except Exception:
            continue

        mid: Optional[int] = None
        if Item is not None:
            try:
                m = Item.GetModelID(gid)
                mid = int(m) if isinstance(m, int) else None
            except Exception:
                mid = None

        item_id = it.item_id

        if not Item.IsNameReady(item_id):
            Item.RequestName(item_id)

        agent_name = Agent.GetNameByID(aid)
        item_name = Item.GetName(item_id)

        right_name = "Elemental Keystone" in item_name or "Elemental Keystone" in agent_name or "Boss Key" in item_name or "Boss Key" in agent_name

        # right_model_ids = mid in SPECIAL_MODEL_IDS or item_id in SPECIAL_MODEL_IDS

        if right_name:

            try:
                owner = int(it.owner)
                if owner not in (0, me):
                    ConsoleLog("TORCH", f"Found the item but not for us - agent={agent_name},item={item_name}")
                    continue
            except Exception:
                ConsoleLog("TORCH", f"Found the item but unknown owner info - agent={agent_name},item={item_name}")
                pass

            ConsoleLog("TORCH", f"Found the item - agent={agent_name},item={item_name}")
            target_agent = aid
            ground_item_id = gid
            break
        else:
            ConsoleLog("TORCH", f"Found an item but not the one we wanted - agent={agent_name},item={item_name}")

    return ground_item_id, owner, target_agent


def command_type_routine_in_message_is_active(account_email, shared_command_type):
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

    if index == -1 or message is None:
        return False

    if message.Command != shared_command_type:
        return False
    return True


def team_loot_items():
    sender_email = Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    for account in accounts:
        if not account.AccountEmail or sender_email == account.AccountEmail:
            continue
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.PickUpLoot, (0, 0, 0, 0))
        yield from Routines.Yield.wait(1000)

        # Looting
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.PickUpLoot):
            yield from Routines.Yield.wait(1000)


def _my_on_party_member_in_danger():
    try:
        while True:
            if not Routines.Checks.Map.MapValid():
                return

            if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                return

            if Routines.Checks.Agents.InDanger():
                return

            party_member_id = Routines.Checks.Party.GetPartyMemberInDangerID()
            if party_member_id == 0 or not Agent.IsValid(party_member_id) or Agent.IsDead(party_member_id):
                return

            member_pos = Agent.GetXY(party_member_id)
            if Utils.Distance(member_pos, Player.GetXY()) <= Range.Spellcast.value:
                return

            path = yield from AutoPathing().get_path_to(member_pos[0], member_pos[1])
            if not path:
                return

            exit_condition = lambda: (
                    not Routines.Checks.Map.MapValid()
                    or Routines.Checks.Agents.InDanger()
                    or Routines.Checks.Party.IsPartyWiped()
                    or GLOBAL_CACHE.Party.IsPartyDefeated()
                    or Routines.Checks.Party.GetPartyMemberInDangerID() == 0
            )

            yield from Routines.Yield.Movement.FollowPath(
                path_points=path,
                custom_exit_condition=exit_condition,
                tolerance=Range.Spellcast.value,
                timeout=10000,
            )
            yield from Routines.Yield.wait(100)
            return
    finally:
        bot.config.FSM.resume()
        yield


def OnPartyMemberBehind():
    print ("Party Member behind, Triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnBehind_OPD", _my_on_party_member_in_danger())

# region Bot Routine
def bot_routine(bot: Botting) -> None:
    global to_althena, to_dungeon, to_bandits, ROOM_TWO, OUT_OF_LEVEL_ONE, \
        LEVEL_TWO_PART_ONE, LEVEL_TWO_PART_TWO, LEVEL_TWO_PART_TWO_PASSIVE, LEVEL_TWO_PART_THREE, \
        LEVEL_THREE_PART_ONE
    _ensure_mode_loaded(bot)
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.Events.OnPartyMemberBehindCallback(lambda: OnPartyMemberBehind())
    bot.Events.OnPartyMemberInDangerCallback(lambda: bot.Templates.Routines.OnPartyMemberInDanger())
    # bot.Events.OnPartyMemberDeadBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())
    #end events

    bot.States.AddHeader("Prepare For Farm")
    _load_consumable_settings(bot)
    _load_kit_restock_settings(bot)
    _sync_consumable_toggles(bot)
    bot.States.AddCustomState(lambda: _gh_merchant_setup_if_enabled(bot, PIKEN_SQUARE), "GH Merchant Setup If Enabled")
    bot.States.AddCustomState(lambda: _coro_travel_random_district(bot, PIKEN_SQUARE), "Travel to PIKEN_SQUARE")
    bot.States.AddCustomState(lambda: _maybe_setup_heroes(bot), "Setup Heroes")
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")

    bot.Wait.ForTime(11300)

    bot.States.AddHeader("Zoning into explorable area")
    bot.Party.SetHardMode(True)
    auto_path_list = [
        (20274,8384),
        (20285,7969),
        (20179,7508),
        (20254,7270),
    ]
    bot.Move.FollowPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=102)

    bot.States.AddHeader("to_dungeon")
    bot.Wait.ForTime(10000)
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(to_dungeon)
    bot.Wait.UntilOutOfCombat()

    path = [
        (17770,-1456),
        (17593,-1230),
        (17593,-1230),
    ]
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(path)
    bot.Wait.ForMapToChange(target_map_name="Tunnels of the Forsaken")



    bot.States.AddHeader("to_althena")
    bot.Wait.ForTime(10000)
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(lambda: _use_consumables_if_enabled(bot), "Use Consumables If Enabled")
    bot.Move.FollowPath(to_althena)

    bot.States.AddHeader("get_quest")
    bot.Move.XY(-7496, -9531, "Ghost of Althea")
    bot.Wait.ForTime(2345)
    bot.States.AddCustomState(lambda x=-7496.00, y=-9531.00, d=0x85B501: _do_dialog_at(bot, x, y, d), "Ghost of Althea Quest Dialog")
    bot.Wait.ForTime(5000)

    bot.States.AddHeader("to_bandits")
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(to_bandits)
    bot.Wait.UntilOutOfCombat()
    bot.States.AddCustomState(team_loot_items, "Grab loot")
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("level 1 ROOM_TWO")
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(ROOM_TWO)
    bot.Wait.UntilOutOfCombat()
    bot.States.AddCustomState(team_loot_items, "Grab loot")
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("level 1 OUT_OF_LEVEL_ONE")

    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(OUT_OF_LEVEL_ONE)
    bot.Wait.ForMapToChange(target_map_name="Tunnels of the Forsaken: Level 2")

    bot.States.AddHeader("level 2 PART_ONE TO Bridge")
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(LEVEL_TWO_PART_ONE)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("level 2 PART_TWO From Bridge")
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(LEVEL_TWO_PART_TWO)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("level 2 Passive Bridge")
    ConfigurePassiveEnv(bot)
    bot.Move.FollowPath(LEVEL_TWO_PART_TWO_PASSIVE)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("level 2 PART_Three")
    ConfigureAggressiveEnv(bot)
    bot.Wait.ForTime(4000)
    bot.Move.FollowPath(LEVEL_TWO_PART_THREE)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("level 2 exit level")
    ConfigureAggressiveEnv(bot)
    exit_level_two = [
        (-16612,6062),
        (-16775,5725),
        (-16833,5502),
        (-16602,4817),
        (-16797,4262),
    ]
    bot.Move.FollowPath(exit_level_two)
    bot.Wait.ForMapToChange(target_map_name="Tunnels of the Forsaken: Level 3")

    bot.States.AddHeader("level 3 LEVEL_THREE_PART_ONE TO Boss")
    ConfigureAggressiveEnv(bot)
    bot.Move.FollowPath(LEVEL_THREE_PART_ONE)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("level 3 Grab Boss Key")
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(pickup_torch, "Pickup Boss Key")
    bot.States.AddCustomState(team_loot_items, "Grab loot")

    # bot.Multibox.ResignParty()
    # bot.Wait.UntilOnOutpost()
    # bot.Map.Travel(target_map_id=PIKEN_SQUARE)
    # bot.States.JumpToStepName(ZONING_STEP_NAME)


bot.UI.override_draw_config(lambda: _draw_settings(bot))

bot.SetMainRoutine(bot_routine)
# endregion


# region Merchant
def _find_npc_xy_by_name(name_fragment: str, max_dist: float = 15000.0):
    npcs = AgentArray.GetNPCMinipetArray()
    npcs = AgentArray.Filter.ByDistance(npcs, Player.GetXY(), max_dist)
    for npc_id in npcs:
        npc_name = Agent.GetNameByID(int(npc_id))
        if name_fragment.lower() in npc_name.lower():
            return Agent.GetXY(int(npc_id))
    return None


def _restock_kits_locally(bot: Botting, x: float, y: float):
    yield from bot.Move._coro_xy_and_interact_npc(x, y)
    yield from bot.Wait._coro_for_time(1200)

    id_kits = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit.value))
    sup_id_kits = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value))
    salvage_kits = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value))

    id_to_buy = max(0, _id_kits_target - (id_kits + sup_id_kits))
    salvage_to_buy = max(0, _salvage_kits_target - salvage_kits)

    yield from Routines.Yield.Merchant.BuyIDKits(id_to_buy, log=True)
    yield from Routines.Yield.Merchant.BuySalvageKits(salvage_to_buy, log=True)


def _restock_kits_if_enabled(bot: Botting):
    yield from _gh_merchant_setup_if_enabled(bot, PIKEN_SQUARE)


def _coro_travel_random_district(bot: Botting, target_map_id: int):
    if target_map_id == Map.GetMapID():
        yield
        return

    if _randomize_district:
        district = random.choice(_RANDOM_DISTRICTS)
        ConsoleLog(BOT_NAME, f"Traveling to map {target_map_id} with random EU district {district}")
        Map.TravelToDistrict(target_map_id, district=district)
        yield from Routines.Yield.wait(500)
        yield from bot.Wait._coro_for_map_load(target_map_id=target_map_id)
        return

    yield from bot.Map._coro_travel(target_map_id, "")

def _get_leftover_material_item_ids(batch_size: int = 10) -> list[int]:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    leftovers: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        if 0 < qty < batch_size:
            leftovers.append(int(item_id))
    return leftovers


def _coro_sell_scrolls(bot: Botting, mx: float, my: float):
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = [int(item_id) for item_id in item_array if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in _SCROLL_MODEL_IDS]
    if not sell_ids:
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (scrolls)")
    yield from Routines.Yield.wait(1200)
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)


def _coro_sell_nonsalvageable_golds(bot: Botting, mx: float, my: float):
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = []
    for item_id in item_array:
        _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        if rarity != "Gold":
            continue
        if not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id):
            continue
        if GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            continue
        sell_ids.append(int(item_id))
    if not sell_ids:
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (non-salvageable golds)")
    yield from Routines.Yield.wait(1200)
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)


def _disable_inventoryplus_pretravel():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _PRETRAVEL_DISABLE_WIDGETS:
        wh.disable_widget(name)
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _PRETRAVEL_DISABLE_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""))
    yield from Routines.Yield.wait(1500)


def _disable_merchant_widgets():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.disable_widget(name)
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""))
    yield


def _reenable_merchant_widgets():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.enable_widget(name)
    my_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                idx = int(GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.EnableWidget, (0, 0, 0, 0), (name, "", "", "")))
                if idx >= 0:
                    refs.append((acc.AccountEmail, idx))
    yield from _wait_for_alt_dispatch_completion("enable_widgets", refs, SharedCommandType.EnableWidget, timeout_ms=15000)


def _dispatch_to_alts(command, params, extra_data=("", "", "", "")) -> list[tuple[str, int]]:
    my_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            idx = int(GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, command, params, extra_data))
            refs.append((acc.AccountEmail, idx))
    return refs


def _wait_for_alt_dispatch_completion(stage_name: str, message_refs: list[tuple[str, int]], command, timeout_ms: int = 30000):
    if not message_refs:
        return
    pending = {(email, idx): None for email, idx in message_refs if int(idx) >= 0}
    if not pending:
        return
    deadline = time.monotonic() + (max(0, int(timeout_ms)) / 1000.0)
    my_email = Player.GetAccountEmail()
    while pending and time.monotonic() < deadline:
        completed: list[tuple[str, int]] = []
        for email, idx in list(pending.keys()):
            message = GLOBAL_CACHE.ShMem.GetInbox(idx)
            is_same_message = (
                bool(getattr(message, "Active", False))
                and str(getattr(message, "ReceiverEmail", "") or "") == email
                and str(getattr(message, "SenderEmail", "") or "") == my_email
                and int(getattr(message, "Command", -1)) == int(command)
            )
            if not is_same_message:
                completed.append((email, idx))
        for key in completed:
            pending.pop(key, None)
        if pending:
            yield from Routines.Yield.wait(50)
    if pending:
        pending_accounts = ", ".join(sorted({email for email, _ in pending}))
        ConsoleLog(BOT_NAME, f"[Merchant] {stage_name}: timeout waiting for alt completion. Pending: {pending_accounts}", Py4GW.Console.MessageType.Warning)


def _wait_for_alts_on_current_map(stage_name: str, expected_alts: int, target_map_id: int, timeout_ms: int = 30000):
    if _party_mode != 1:
        return
    if expected_alts <= 0:
        return
    my_email = Player.GetAccountEmail()
    deadline = time.time() + (max(0, int(timeout_ms)) / 1000.0)
    while time.time() < deadline:
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        arrived = sum(
            1 for acc in accounts
            if acc.AccountEmail != my_email and int(getattr(acc.AgentData.Map, "MapID", 0) or 0) == target_map_id
        )
        if arrived >= expected_alts:
            yield from Routines.Yield.wait(1000)
            return
        yield from Routines.Yield.wait(500)
    ConsoleLog(BOT_NAME, f"[Merchant] {stage_name}: alt arrival timeout on map {target_map_id}", Py4GW.Console.MessageType.Warning)


def _kick_current_party_accounts():
    own_login = int(Player.GetLoginNumber() or 0)
    for member in list(GLOBAL_CACHE.Party.GetPlayers()):
        login_number = int(getattr(member, "login_number", 0) or 0)
        if login_number <= 0 or login_number == own_login:
            continue
        player_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
        if player_name:
            GLOBAL_CACHE.Party.Players.KickPlayer(str(player_name))


def _gh_merchant_setup_if_enabled(bot: Botting, outpost_id: int):
    if not _restock_kits_enabled:
        return

    if _party_mode == 1:
        _kick_current_party_accounts()
        for _ in range(20):
            yield from bot.Wait._coro_for_time(250)
            if GLOBAL_CACHE.Party.GetPlayerCount() <= 1:
                break

    yield from _disable_inventoryplus_pretravel()

    expected_gh_alts = 0
    travel_refs: list[tuple[str, int]] = []
    if _party_mode == 1:
        my_email = Player.GetAccountEmail()
        expected_gh_alts = len([acc for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() if acc.AccountEmail != my_email])
        travel_refs = _dispatch_to_alts(SharedCommandType.TravelToGuildHall, (0, 0, 0, 0))

    if not Map.IsGuildHall():
        Map.TravelGH()
    yield from bot.Wait._coro_until_on_outpost()
    if _party_mode == 1:
        yield from _wait_for_alt_dispatch_completion("travel_gh", travel_refs, SharedCommandType.TravelToGuildHall, timeout_ms=10000)

    gh_deadline = time.time() + 30.0
    while not Map.IsGuildHall() and time.time() < gh_deadline:
        yield from Routines.Yield.wait(500)
    if not Map.IsGuildHall():
        ConsoleLog(BOT_NAME, "[Merchant] Failed to reach Guild Hall, skipping merchant setup", Py4GW.Console.MessageType.Warning)
        return

    if _party_mode == 1:
        yield from _wait_for_alts_on_current_map("travel_gh_arrival", expected_gh_alts, int(Map.GetMapID()), timeout_ms=60000)

    npc_deadline = time.time() + 20.0
    while _find_npc_xy_by_name("Merchant", max_dist=30000.0) is None and time.time() < npc_deadline:
        yield from Routines.Yield.wait(500)

    yield from _disable_merchant_widgets()

    merchant_xy = _find_npc_xy_by_name("Merchant", max_dist=30000.0)
    mat_xy = _find_npc_xy_by_name("Material Trader", max_dist=30000.0) if _merchant_sell_materials else None

    if _merchant_sell_materials and mat_xy:
        tmx, tmy = mat_xy
        sell_mat_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (tmx, tmy, 0, 0), ("sell", "", "", "")) if _party_mode == 1 else []
        yield from Routines.Yield.Merchant.SellMaterialsAtTrader(tmx, tmy)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("sell_materials", sell_mat_refs, SharedCommandType.MerchantMaterials)

        if merchant_xy:
            mx, my = merchant_xy
            leftover_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_merchant_leftovers", "", "10", "")) if _party_mode == 1 else []
            leftover_ids = _get_leftover_material_item_ids()
            if leftover_ids:
                yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (leftovers)")
                yield from Routines.Yield.wait(1200)
                yield from Routines.Yield.Merchant.SellItems(leftover_ids, log=True)
                yield from Routines.Yield.wait(300)
            if _party_mode == 1:
                yield from _wait_for_alt_dispatch_completion("sell_merchant_leftovers", leftover_refs, SharedCommandType.MerchantMaterials)

    if merchant_xy:
        mx, my = merchant_xy
        sell_gold_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_nonsalvageable_golds", "", "", "")) if _party_mode == 1 else []
        yield from _coro_sell_nonsalvageable_golds(bot, mx, my)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("sell_nonsalvageable_golds", sell_gold_refs, SharedCommandType.MerchantMaterials)

        sell_scroll_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_scrolls", _SCROLL_MODEL_FILTER, "", "")) if _party_mode == 1 else []
        yield from _coro_sell_scrolls(bot, mx, my)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("sell_scrolls", sell_scroll_refs, SharedCommandType.MerchantMaterials)

        kit_refs = _dispatch_to_alts(SharedCommandType.MerchantItems, (mx, my, _id_kits_target, _salvage_kits_target)) if _party_mode == 1 else []
        yield from _restock_kits_locally(bot, mx, my)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("restock_kits", kit_refs, SharedCommandType.MerchantItems)

    if _merchant_alt_wait_ms > 0:
        yield from Routines.Yield.wait(_merchant_alt_wait_ms)

    #yield from _coro_travel_random_district(bot, outpost_id)
    if _party_mode == 1:
        yield from Routines.Yield.wait(1500)
    yield from _reenable_merchant_widgets()
# endregion


# region Consumables
def _restock_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _party_mode == 1:
        if _as_bool(bot.Properties.Get("use_conset", "active")):
            yield from bot.helpers.Multibox._restock_conset_message(250)
        if _as_bool(bot.Properties.Get("use_pcons", "active")):
            yield from bot.helpers.Multibox._restock_all_pcons_message(250)
        return
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        yield from _restock_models_locally(CONSET_RESTOCK_MODELS, 250)
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from _restock_models_locally(PCON_RESTOCK_MODELS, 250)


def _use_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _party_mode == 1:
        yield from _use_multibox_consumables(bot)
        return
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        yield from bot.helpers.Items.use_conset()
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from bot.helpers.Items.use_pcons()


def _restock_models_locally(model_ids: list[int], quantity: int):
    for model_id in model_ids:
        yield from Routines.Yield.Items.RestockItems(model_id, quantity)


def _use_multibox_consumables(bot: Botting):
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        for model_id, effect_name in CONSET_ITEMS:
            yield from bot.helpers.Multibox._use_consumable_message((
                model_id,
                GLOBAL_CACHE.Skill.GetID(effect_name),
                0,
                0,
            ))
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        for model_id, effect_name in PCON_ITEMS:
            yield from bot.helpers.Multibox._use_consumable_message((
                model_id,
                GLOBAL_CACHE.Skill.GetID(effect_name),
                0,
                0,
            ))
        yield from bot.helpers.Multibox._use_consumable_message((
            ModelID.Honeycomb.value,
            0,
            0,
            0,
        ))
# endregion


# region Upkeep
def _upkeep_consumables(bot: "Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue
        if _party_mode == 1:
            yield from _use_multibox_consumables(bot)
            continue
        if _as_bool(bot.Properties.Get("use_conset", "active")):
            yield from bot.helpers.Items.use_conset()
        if _as_bool(bot.Properties.Get("use_pcons", "active")):
            yield from bot.helpers.Items.use_pcons()
            for _ in range(4):
                honeycomb_item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Honeycomb.value)
                if not honeycomb_item_id:
                    break
                GLOBAL_CACHE.Inventory.UseItem(honeycomb_item_id)
                yield from bot.Wait._coro_for_time(250)
# endregion


# region Events
def _nearest_path_index(path: list, x: float, y: float) -> int:
    best, best_dist = 0, float('inf')
    for i, (px, py) in enumerate(path):
        d = (px - x) ** 2 + (py - y) ** 2
        if d < best_dist:
            best_dist, best = d, i
    return best


def _on_party_wipe(bot: "Botting"):
    if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
        bot.config.FSM.resume()
        return
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
            bot.config.FSM.resume()
            return

    if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
        bot.config.FSM.resume()
        return

    # All accounts revived resume route from nearest path point
    # TODO which map
    # pos = Player.GetXY()
    # if pos:
    #     nearest_idx = _nearest_path_index(Norn_Path, pos[0], pos[1])
    #     remaining_path = Norn_Path[nearest_idx:]
    #     bot.config.path = remaining_path.copy()
    #     bot.config.path_to_draw = remaining_path.copy()
    #     yield from Routines.Yield.Movement.FollowPath(
    #         path_points=remaining_path,
    #         tolerance=bot.config.config_properties.movement_tolerance.get("value"),
    #         timeout=bot.config.config_properties.movement_timeout.get("value"),
    #         custom_pause_fn=lambda: False,
    #     )
    #
    # bot.States.JumpToStepName(START_COMBAT_STEP_NAME)
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))
# endregion


# region Settings
def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _ensure_bot_ini(bot: Botting) -> str:
    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        bot.config.ini_key_initialized = True
    return bot.config.ini_key


def _load_consumable_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    saved_use_conset = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_CONSET_KEY,
        _as_bool(bot.Properties.Get("use_conset", "active")),
    )
    saved_use_pcons = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_PCONS_KEY,
        _as_bool(bot.Properties.Get("use_pcons", "active")),
    )
    bot.Properties.ApplyNow("use_conset", "active", _as_bool(saved_use_conset))
    bot.Properties.ApplyNow("use_pcons", "active", _as_bool(saved_use_pcons))


def _load_kit_restock_settings(bot: Botting) -> None:
    global _restock_kits_enabled, _id_kits_target, _salvage_kits_target, _merchant_sell_materials, _merchant_alt_wait_ms
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    _restock_kits_enabled = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_RESTOCK_KITS_KEY,
        _restock_kits_enabled,
    )
    _id_kits_target = max(0, int(IniManager().read_int(
        ini_key,
        _SETTINGS_SECTION,
        _ID_KITS_TARGET_KEY,
        _id_kits_target,
    )))
    _salvage_kits_target = max(0, int(IniManager().read_int(
        ini_key,
        _SETTINGS_SECTION,
        _SALVAGE_KITS_TARGET_KEY,
        _salvage_kits_target,
    )))
    _merchant_sell_materials = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _MERCHANT_SELL_MATERIALS_KEY,
        _merchant_sell_materials,
    )
    _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, int(IniManager().read_int(
        ini_key,
        _SETTINGS_SECTION,
        _MERCHANT_ALT_WAIT_MS_KEY,
        _merchant_alt_wait_ms,
    ))))


def _save_consumable_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_CONSET_KEY,
        _as_bool(bot.Properties.Get("use_conset", "active")),
    )
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_PCONS_KEY,
        _as_bool(bot.Properties.Get("use_pcons", "active")),
    )


def _save_kit_restock_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _USE_RESTOCK_KITS_KEY, bool(_restock_kits_enabled))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _ID_KITS_TARGET_KEY, int(_id_kits_target))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _SALVAGE_KITS_TARGET_KEY, int(_salvage_kits_target))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_SELL_MATERIALS_KEY, bool(_merchant_sell_materials))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_ALT_WAIT_MS_KEY, int(_merchant_alt_wait_ms))


def _ensure_consumable_settings_ui_loaded(bot: Botting) -> None:
    if getattr(bot.config, "_consumable_settings_ui_loaded", False):
        return
    _load_consumable_settings(bot)
    _load_kit_restock_settings(bot)
    bot.config._consumable_settings_ui_loaded = True


def _load_hero_config():
    global _hero_slots, _hero_config_dirty, _hero_config_status
    if not os.path.exists(_HERO_CONFIG_PATH):
        _hero_config_status = ""
        return
    try:
        with open(_HERO_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _hero_slots = _parse_hero_config_entries(raw)
        _hero_config_dirty = False
        _hero_config_status = "Loaded."
    except Exception as exc:
        _hero_config_status = f"Load error: {exc}"


def _save_hero_config():
    global _hero_config_dirty, _hero_config_status
    payload = [{"hero_id": int(s.hero_id), "template": s.template} for s in _hero_slots]
    try:
        os.makedirs(os.path.dirname(_HERO_CONFIG_PATH), exist_ok=True)
        with open(_HERO_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        _hero_config_dirty = False
        _hero_config_status = "Saved."
    except Exception as exc:
        _hero_config_status = f"Save error: {exc}"


def _reset_hero_config():
    global _hero_slots, _hero_config_dirty, _hero_config_status
    _hero_slots = [_PartyHeroSlot() for _ in range(_HERO_SLOTS_COUNT)]
    _hero_config_dirty = True
    _hero_config_status = "Reset to empty."


def _parse_hero_config_entries(raw) -> List[_PartyHeroSlot]:
    slots: List[_PartyHeroSlot] = []
    for i in range(_HERO_SLOTS_COUNT):
        entry = raw[i] if isinstance(raw, list) and i < len(raw) else {}
        hero_id = int(entry.get("hero_id", 0) or 0)
        if hero_id not in _HERO_ID_TO_OPTION_INDEX:
            hero_id = 0
        slots.append(_PartyHeroSlot(hero_id=hero_id, template=str(entry.get("template", "") or "")))
    return slots


def _list_importable_hero_configs() -> List[str]:
    try:
        hero_files = []
        for entry in os.listdir(_BOT_SCRIPT_DIR):
            if not entry.endswith(" Heroes.json"):
                continue
            full_path = os.path.join(_BOT_SCRIPT_DIR, entry)
            if os.path.isfile(full_path):
                hero_files.append(full_path)
        hero_files.sort(key=lambda path: os.path.basename(path).lower())
        return hero_files
    except OSError:
        return []


def _hero_import_label(path: str) -> str:
    name = os.path.splitext(os.path.basename(path))[0]
    return name[:-7] if name.endswith(" Heroes") else name


def _import_hero_config(path: str):
    global _hero_slots, _hero_config_dirty, _hero_config_status
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _hero_slots = _parse_hero_config_entries(raw)
        _hero_config_dirty = True
        _save_hero_config()
        _hero_config_status = f"Imported from {_hero_import_label(path)} and saved."
    except Exception as exc:
        _hero_config_status = f"Import error: {exc}"


def _get_hero_icon_path(hero_id: int) -> Optional[str]:
    try:
        hero_type = HeroType(hero_id)
    except ValueError:
        return None
    filename = _HERO_ICON_FILENAMES.get(hero_type)
    if not filename:
        return None
    path = os.path.join(_HERO_ICONS_BASE, filename)
    return path if os.path.exists(path) else None


def _draw_hero_icon(hero_id: int, size: int = 24):
    import PyImGui
    path = _get_hero_icon_path(hero_id)
    if path:
        try:
            cx, cy = PyImGui.get_cursor_screen_pos()
            ImGui.DrawTextureInDrawList(pos=(float(cx), float(cy)), size=(float(size), float(size)), texture_path=path)
        except Exception:
            try:
                ImGui.DrawTexture(texture_path=path, width=size, height=size)
            except Exception:
                pass
    PyImGui.dummy(int(size), int(size))


def _draw_hero_combo(label: str, hero_id: int) -> int:
    import PyImGui
    current_index = _HERO_ID_TO_OPTION_INDEX.get(hero_id, 0)
    preview = _HERO_OPTION_LABELS[current_index]
    if PyImGui.begin_combo(label, preview, PyImGui.ImGuiComboFlags.NoFlag):
        for index, hero in enumerate(_HERO_OPTIONS):
            if hero != HeroType.None_:
                _draw_hero_icon(int(hero), size=20)
            else:
                PyImGui.dummy(20, 20)
            PyImGui.same_line(0.0, 8.0)
            if PyImGui.selectable(f"{_HERO_OPTION_LABELS[index]}##{label}_{index}", index == current_index, 0, [0.0, 0.0]):
                current_index = index
        PyImGui.end_combo()
    return int(_HERO_OPTIONS[current_index])


def _draw_hero_slot_editor(slot_index: int):
    import PyImGui
    global _hero_config_dirty
    slot = _hero_slots[slot_index]
    combo_label_width = 70.0

    PyImGui.text(f"Hero {slot_index + 1}")
    PyImGui.same_line(combo_label_width, 8.0)
    _draw_hero_icon(slot.hero_id, size=24)
    PyImGui.same_line(0.0, 8.0)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_hero_id = _draw_hero_combo(f"##hero_{slot_index}", slot.hero_id)
    if new_hero_id != slot.hero_id:
        slot.hero_id = new_hero_id
        if slot.hero_id == HeroType.None_.value:
            slot.template = ""
        elif not slot.template.strip():
            try:
                hero_type = HeroType(slot.hero_id)
            except ValueError:
                hero_type = HeroType.None_
            slot.template = _DEFAULT_HERO_TEMPLATES.get(hero_type, "")
        _hero_config_dirty = True

    PyImGui.text("Template")
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.small_button(f"Clear##slot_{slot_index}"):
        if slot.hero_id != HeroType.None_.value or slot.template:
            slot.hero_id = HeroType.None_.value
            slot.template = ""
            _hero_config_dirty = True
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_template = PyImGui.input_text(f"##template_{slot_index}", slot.template)
    if new_template != slot.template:
        slot.template = new_template
        _hero_config_dirty = True


def _draw_hero_settings_tab():
    import PyImGui
    global _hero_import_source_index
    PyImGui.text("Configure up to 3 heroes for Single Account mode.")
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.7, 0.7, 0.7, 1.0))
    PyImGui.text("Heroes are added in order; duplicates and empty slots are skipped.")
    PyImGui.pop_style_color(1)
    PyImGui.spacing()

    if _hero_config_dirty:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.8, 0.2, 1.0))
        PyImGui.text("Unsaved changes")
        PyImGui.pop_style_color(1)
    elif _hero_config_status:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.6, 0.9, 0.6, 1.0))
        PyImGui.text(_hero_config_status)
        PyImGui.pop_style_color(1)

    if PyImGui.button("Save", 100, 26):
        _save_hero_config()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reload", 100, 26):
        _load_hero_config()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reset", 100, 26):
        _reset_hero_config()
    import_paths = _list_importable_hero_configs()
    if import_paths:
        if _hero_import_source_index >= len(import_paths):
            _hero_import_source_index = 0
        import_labels = [_hero_import_label(path) for path in import_paths]
        _hero_import_source_index = PyImGui.combo("Import Team From", _hero_import_source_index, import_labels)
        if PyImGui.button("Import Team", 120, 26):
            _import_hero_config(import_paths[_hero_import_source_index])
    else:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.7, 0.7, 0.7, 1.0))
        PyImGui.text("Import Team: save another title bot hero lineup first.")
        PyImGui.pop_style_color(1)
    PyImGui.separator()

    if PyImGui.begin_child("HeroSlotsChild", (0, -1), True):
        for i in range(_HERO_SLOTS_COUNT):
            _draw_hero_slot_editor(i)
            if i < _HERO_SLOTS_COUNT - 1:
                PyImGui.separator()
    PyImGui.end_child()


def _setup_heroes(bot: Botting):
    global _hero_slots
    if _party_mode == 1:
        _kick_current_party_accounts()
    else:
        GLOBAL_CACHE.Party.LeaveParty()
    for _ in range(8):
        yield from bot.Wait._coro_for_time(250)
        if GLOBAL_CACHE.Party.GetPlayerCount() <= 1:
            break
    GLOBAL_CACHE.Party.Heroes.KickAllHeroes()
    yield from bot.Wait._coro_for_time(500)
    seen: set = set()
    for slot in _hero_slots:
        hero_id = int(slot.hero_id)
        if hero_id <= 0 or hero_id in seen:
            continue
        seen.add(hero_id)
        GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
    # Single wait for all heroes to join
    yield from bot.Wait._coro_for_time(1000)
    # Load skill templates
    template_map = {int(s.hero_id): s.template for s in _hero_slots if s.template}
    party_hero_count = GLOBAL_CACHE.Party.GetHeroCount()
    for position in range(1, party_hero_count + 1):
        hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
        if hero_agent_id > 0:
            hero_id = GLOBAL_CACHE.Party.Heroes.GetHeroIDByAgentID(hero_agent_id)
            template = template_map.get(hero_id, "")
            if template:
                GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position, template)
            yield from bot.Wait._coro_for_time(500)


def _maybe_setup_heroes(bot: Botting):
    if _party_mode == 1:
        yield from bot.helpers.Multibox._summon_all_accounts()
        yield from bot.Wait._coro_for_time(4000)
        yield from bot.helpers.Multibox._invite_all_accounts()
        return
    yield from _setup_heroes(bot)


def _resign(bot: Botting):
    bot.UI.SendChatCommand("resign")
    yield from bot.Wait._coro_for_time(500)


def _sync_consumable_toggles(bot: Botting) -> None:
    use_conset = _as_bool(bot.Properties.Get("use_conset", "active"))
    use_pcons = _as_bool(bot.Properties.Get("use_pcons", "active"))

    for key in ("armor_of_salvation", "essence_of_celerity", "grail_of_might"):
        bot.Properties.ApplyNow(key, "active", use_conset)

    for key in (
        "birthday_cupcake",
        "golden_egg",
        "candy_corn",
        "candy_apple",
        "slice_of_pumpkin_pie",
        "drake_kabob",
        "bowl_of_skalefin_soup",
        "pahnai_salad",
        "war_supplies",
        "honeycomb",
    ):
        bot.Properties.ApplyNow(key, "active", use_pcons)


# endregion


# region GUI
def _load_mode_setting(bot: Botting) -> None:
    global _party_mode, _randomize_district
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    raw = IniManager().read_bool(ini_key, _SETTINGS_SECTION, _MULTIBOX_ALTS_KEY, False)
    _party_mode = 1 if raw else 0
    _randomize_district = IniManager().read_bool(ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, _randomize_district)


def _ensure_mode_loaded(bot: Botting) -> None:
    global _mode_loaded
    if _mode_loaded:
        return
    _load_mode_setting(bot)
    _mode_loaded = True


def _save_mode_setting(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MULTIBOX_ALTS_KEY, _party_mode == 1)
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, bool(_randomize_district))


def _do_dialog_at(bot: Botting, x: float, y: float, dialog_id: int, broadcast_to_alts: bool = True):
    if _party_mode == 1 and broadcast_to_alts:
        yield from bot.Move._coro_xy_and_interact_npc(x, y)
        yield from bot.Wait._coro_for_time(1500)
        yield from bot.helpers.Multibox._send_dialog_with_target(dialog_id)
        yield from bot.Wait._coro_for_time(1500)
    else:
        yield from bot.Move._coro_xy_and_dialog(x, y, dialog_id)
        yield from bot.Wait._coro_for_time(500)


def _draw_settings(bot: Botting):
    import PyImGui

    PyImGui.text("Bot Settings")

    _ensure_consumable_settings_ui_loaded(bot)

    global _party_mode, _randomize_district
    _ensure_mode_loaded(bot)
    PyImGui.separator()
    PyImGui.text("Party Mode:")
    new_mode = PyImGui.radio_button("Single Account with Heroes", _party_mode, 0)
    PyImGui.same_line(0, 16)
    new_mode = PyImGui.radio_button("Multiboxing", new_mode, 1)
    if new_mode != _party_mode:
        _party_mode = new_mode
        _save_mode_setting(bot)
    if _party_mode == 1:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.6, 0.9, 1.0, 1.0))
        PyImGui.text("Resign uses Multibox Party Resign. Hero setup is skipped.")
        PyImGui.pop_style_color(1)
    new_randomize = PyImGui.checkbox("Randomize EU District", _randomize_district)
    if new_randomize != _randomize_district:
        _randomize_district = new_randomize
        _save_mode_setting(bot)
    PyImGui.separator()

    PyImGui.text("Combat Backend")
    PyImGui.text("Current: Auto Combat")

    use_conset = _as_bool(bot.Properties.Get("use_conset", "active"))
    new_use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    if new_use_conset != use_conset:
        bot.Properties.ApplyNow("use_conset", "active", new_use_conset)
        _save_consumable_settings(bot)

    use_pcons = _as_bool(bot.Properties.Get("use_pcons", "active"))
    new_use_pcons = PyImGui.checkbox("Restock & use Pcons", use_pcons)
    if new_use_pcons != use_pcons:
        bot.Properties.ApplyNow("use_pcons", "active", new_use_pcons)
        _save_consumable_settings(bot)
    _sync_consumable_toggles(bot)

    global _restock_kits_enabled, _id_kits_target, _salvage_kits_target, _merchant_sell_materials, _merchant_alt_wait_ms
    PyImGui.separator()
    new_restock_kits = PyImGui.checkbox("Guild Hall merchant on startup", _restock_kits_enabled)
    if new_restock_kits != _restock_kits_enabled:
        _restock_kits_enabled = new_restock_kits
        _save_kit_restock_settings(bot)

    if _restock_kits_enabled:
        new_id_target = PyImGui.input_int("ID Kits target##norn_id", _id_kits_target)
        if new_id_target != _id_kits_target:
            _id_kits_target = max(0, new_id_target)
            _save_kit_restock_settings(bot)

        new_salvage_target = PyImGui.input_int("Salvage Kits target##norn_salv", _salvage_kits_target)
        if new_salvage_target != _salvage_kits_target:
            _salvage_kits_target = max(0, new_salvage_target)
            _save_kit_restock_settings(bot)

        new_sell_materials = PyImGui.checkbox("Sell common materials##norn_sell", _merchant_sell_materials)
        if new_sell_materials != _merchant_sell_materials:
            _merchant_sell_materials = new_sell_materials
            _save_kit_restock_settings(bot)

        new_wait = PyImGui.input_int("Alt settle wait (ms)##norn_alt_wait", _merchant_alt_wait_ms)
        if new_wait != _merchant_alt_wait_ms:
            _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, new_wait))
            _save_kit_restock_settings(bot)


def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Tunnels of the Forsaken", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account, farm Norn title in Varajar Fells")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick Divinus")
    PyImGui.end_tooltip()


_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}


def _get_title_track_accounts():
    accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData())
    if _party_mode == 1:
        return accounts if accounts else []
    own_email = Player.GetAccountEmail()
    filtered = [account for account in accounts if getattr(account, "AccountEmail", "") == own_email]
    if filtered:
        return filtered
    own_name = Player.GetName()
    filtered = [account for account in accounts if getattr(account.AgentData, "CharacterName", "") == own_name]
    if filtered:
        return filtered
    return accounts[:1] if len(accounts) == 1 else []


def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui
    title_idx = int(TitleID.Norn)
    tiers = TITLE_TIERS.get(TitleID.Norn, [])
    now = time.time()
    accounts = _get_title_track_accounts()
    if not accounts:
        PyImGui.text("No local account statistics available yet.")
        return
    for account in accounts:
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        tier_rank = 0
        prev_required = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                tier_rank = i + 1
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        is_maxed = tiers and pts >= tiers[-1].required
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        tier_missing = max(next_required - pts, 0)
        next_rank_progress_current = max(pts, 0)
        next_rank_progress_total = max(next_required, 1)
        PyImGui.separator()
        PyImGui.text(f"{name}  [{tier_name} (Rank {tier_rank})]")
        PyImGui.text(f"Total Points: {pts:,}")
        if is_maxed:
            PyImGui.text("Next Rank: Maxed")
            PyImGui.text("Points To Go: 0")
            PyImGui.progress_bar(1.0, -1, 0, "Complete")
            PyImGui.text_colored("Maximum rank achieved. Title complete.", (0.4, 1.0, 0.4, 1.0))
        else:
            PyImGui.text(f"Next Rank: {next_required:,}")
            PyImGui.text(f"Points To Go: {tier_missing:,}")
            frac = min(next_rank_progress_current / next_rank_progress_total, 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{next_rank_progress_current:,} / {next_rank_progress_total:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")


REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "Wick Divinus bots", "Reforged_Icon.png")
_EXPANDED_TAB_CHILD_SIZE = (500, 620)
# endregion


# region Entry Point
_hero_config_loaded = False


def _draw_statistics_tab() -> None:
    import PyImGui
    if PyImGui.begin_child("NornStatisticsTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_title_track()
    PyImGui.end_child()


def _draw_heroes_tab() -> None:
    import PyImGui
    if PyImGui.begin_child("NornHeroesTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_hero_settings_tab()
    PyImGui.end_child()


def main():
    global _hero_config_loaded
    if not _hero_config_loaded:
        _load_hero_config()
        _hero_config_loaded = True
    if Map.IsMapLoading():
        return
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, extra_tabs=[
        ("Statistics", _draw_statistics_tab),
        ("Heroes", _draw_heroes_tab),
    ])


if __name__ == "__main__":
    main()
# endregion
