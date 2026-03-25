from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
import Py4GW
import os
import time
import os
import random
import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Utils
from Py4GWCoreLib import Map, Agent, Player
import os
from typing import Generator, Optional, Tuple, List
import time, math
import inspect
import PyInventory
from Py4GWCoreLib import *
import Py4GW
from Py4GWCoreLib import (
    Agent,
    Botting,
    ConsoleLog,
    Effects,
    GLOBAL_CACHE,
    Map,
    Player,
    Range,
    Routines,
    SharedCommandType,
    AgentArray,
    IniHandler,
)
from Py4GWCoreLib.botting_src.helpers import BottingHelpers
from Py4GW_widget_manager import get_widget_handler
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.skills.inventory.inventory_utils import InventoryMode

BOT_NAME = "Norn title farm by Wick Divinus"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")

MODULE_NAME = "Norn Title Farm"
MODULE_ICON = "Textures/Skill_Icons/[2373] - Heart of the Norn.jpg"

OLAFSTEAD = 645
OUTPOST_TO_TRAVEL = OLAFSTEAD
VARAJAR_FELLS = 553

_bds_ini_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "common_ac", "loot_settings.ini")
os.makedirs(os.path.dirname(_bds_ini_path), exist_ok=True)
_bds_ini = IniHandler(_bds_ini_path)
_FIXED_ID_KITS_TARGET = 1
_FIXED_SALVAGE_KITS_TARGET = 4
_DEFAULT_ALT_SETTLE_WAIT_MS = 2000


Norn_Path: list[tuple[float, float]] = [
    (-2484.73, 118.55),
    (-3059.12, -419.00),
    (-3301.01, -2008.23),
    (-2034, -4512),
    (-5278, -5771),
    (-5456, -7921),
    (-8793, -5837),
    (-14092, -9662),
    (-17260, -7906),
    (-21964, -12877),
    (-22275, -12462),
    (-21671, -2163),
    (-19592, 772),
    (-13795, -751),
    (-17012, -5376),
    (-12071, -4274),
    (-8351, -2633),
    (-4362, -1610),
    (-4316, 4033),
    (-8809, 5639),
    (-14916, 2475),
    (-11282, 5466),
    (-16051, 6492),
    (-16934, 11145),
    (-19378, 14555),
    (-22751, 14163),
    (-15932, 9386),
    (-13777, 8097),
    (-4729, 15385),
    (-2290, 14879),
    (-1810, 4679),
    (-6911, 5240),
    (-15471, 6384),
    (-411, 5874),
    (2859, 3982),
    (4909, -4259),
    (7514, -6587),
    (3800, -6182),
    (7755, -11467),
    (15403, -4243),
    (21597, -6798),
    (24522, -6532),
    (22883, -4248),
    (18606, -1894),
    (14969, -4048),
    (13599, -7339),
    (10056, -4967),
    (10147, -1630),
    (8963, 4043),
    (9339.46, 3859.12),
    (15576, 7156),
    (22838, 7914),
    (22961, 12757),
    (18067, 8766),
    (13311, 11917),
    (13714, 14520),
    (11126, 10443),
    (5575, 4696),
    (-503, 9182),
    (1582, 15275),
    (7857, 10409)
]

is_asterius_spotted = False
is_asterius_killed = False
_merchant_loaded: bool = False
asterius_agent_id = -1
elapsed = 0
death_loop_headers = None
loop_header = "[H]Exit To Farm_3"
inventory_utils = None
inventory_utils_config = None
_MERCHANT_SECTION = "Merchantism"
_MAX_ALT_SETTLE_WAIT_MS = 5000
_SCROLL_MODEL_IDS = {5594, 5595, 5611, 5853, 5975, 5976, 21233}
_SCROLL_MODEL_FILTER = "5594,5595,5611,5853,5975,5976,21233"


# ==================== MERCHANT SETTINGS ====================
_ALT_SALVAGE_SECTION = "Alt Salvage Kits"
_ALT_SALVAGE_TRIGGER_THRESHOLD = 2
_ALT_SALVAGE_POLL_TIMEOUT_MS = 200
_ALT_SALVAGE_POLL_MAX_TOTAL_MS = 10_000
_merchant_enabled: bool = False
_merchant_id_kits_target: int = _FIXED_ID_KITS_TARGET
_merchant_salvage_kits_target: int = _FIXED_SALVAGE_KITS_TARGET
_merchant_store_consumable_materials: bool = False
_merchant_sell_materials: bool = False
_merchant_sell_rare_mats: bool = False
_merchant_buy_ectos: bool = False
_merchant_ecto_threshold: int = 800_000
_merchant_alt_wait_ms: int = 30_000
_POST_RETURN_TO_ARBOR_SETTLE_MS = 4000
_POST_WIDGET_REENABLE_SETTLE_MS = 2500

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True,
              upkeep_war_supplies_restock=25,
              upkeep_armor_of_salvation_active=True,
              upkeep_grail_of_might_active=True,
              upkeep_auto_loot_active=True)

def get_items_to_deposit():
    global inventory_utils_config
    global inventory_utils
    from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
    from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
    from Sources.oazix.CustomBehaviors.skills.inventory.merchant_refill_if_needed_utility import string_to_dict
    from Sources.oazix.CustomBehaviors.skills.inventory.inventory_utils import InventoryMode, InventoryUtils, InventoryUtilsConfig
    data: str | None = PersistenceLocator().skills.read("my_inventory_utils_config", "inventory_utils_config")
    if data is not None:
        inventory_utils_config = string_to_dict(data)
    else:
        inventory_utils_config = InventoryUtilsConfig()

    inventory_utils = InventoryUtils()
    my_items = []
    inventory_item_ids = inventory_utils.get_inventory_items(inventory_utils_config)
    from Sources.oazix.CustomBehaviors.primitives import constants
    if constants.DEBUG: ConsoleLog("get_items_to_deposit", f"Inventory List filtered = {inventory_item_ids}", Console.MessageType.Info)
    for my_item_id in inventory_item_ids:

        action_for_item: InventoryMode = inventory_utils.get_action_for_item(inventory_utils_config, my_item_id)
        if action_for_item == InventoryMode.DEPOSIT:
            my_items.append(my_item_id)
        else:
            if constants.DEBUG: ConsoleLog("get_items_to_deposit", f"Ignoring item #{my_item_id} its a {action_for_item}", Console.MessageType.Info)

    return my_items

def _get_material_item_ids_by_models(selected_models: set[int]) -> list[int]:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    result: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
        if model_id in selected_models:
            result.append(int(item_id))
    return result

def _coro_deposit_crafting_materials_to_storage(selected_models: set[int]) -> Generator:
    if not selected_models:
        yield
        return
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
        yield from Routines.Yield.wait(1000)
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        ConsoleLog(BOT_NAME, "[Merchant] Storage not open; skipping crafting material deposit", Py4GW.Console.MessageType.Warning)
        yield
        return

    item_ids = _get_material_item_ids_by_models(selected_models)
    if not item_ids:
        ConsoleLog(BOT_NAME, "[Merchant] No crafting materials to deposit")
        yield
        return

    for item_id in item_ids:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(40)


    ConsoleLog(BOT_NAME, f"[Merchant] Deposited {len(item_ids)} crafting material stack(s) to storage")
    yield

def _coro_sell_scrolls(mx: float, my: float) -> Generator:
    """Sell XP/insight scrolls to the GH merchant."""
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = [int(item_id) for item_id in item_array
                if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in _SCROLL_MODEL_IDS]
    if not sell_ids:
        ConsoleLog(BOT_NAME, "[Merchant] No scrolls to sell in bags 1-4")
        storage_hits = [(mid, GLOBAL_CACHE.Inventory.GetModelCountInStorage(mid))
                        for mid in _SCROLL_MODEL_IDS]
        storage_hits = [(mid, cnt) for mid, cnt in storage_hits if cnt > 0]
        if storage_hits:
            ConsoleLog(BOT_NAME, f"[Merchant] WARNING: scrolls found in STORAGE (InventoryPlus deposited them): {storage_hits}")
        yield
        return
    for item_id in sell_ids:
        val = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
        qty = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
        mid = GLOBAL_CACHE.Item.GetModelID(item_id)
        ConsoleLog(BOT_NAME, f"[Merchant] Scroll queued: item_id={item_id} model={mid} qty={qty} value={val}")
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (scrolls)")
    yield from Routines.Yield.wait(1200)
    ConsoleLog(BOT_NAME, f"[Merchant] Selling {len(sell_ids)} scroll(s) at merchant")
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)

def _coro_handle_sell_inventoryutil(mx: float, my: float) -> Generator:
    """Sell all identified, non-salvageable gold items (e.g. anniversary weapons) to the GH merchant."""

    from Sources.modular_bot.recipes.actions_inventory import get_crap_to_sell
    sell_ids = get_crap_to_sell()
    if not sell_ids:
        ConsoleLog(BOT_NAME, "[Merchant] No items to sell")
        yield
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (nom nom)")
    yield from Routines.Yield.wait(1200)
    ConsoleLog(BOT_NAME, f"[Merchant] Selling {len(sell_ids)} item(s) at merchant")
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)

def _load_merchant_settings() -> None:
    global _merchant_enabled, _merchant_id_kits_target, _merchant_salvage_kits_target, _merchant_store_consumable_materials, _merchant_sell_materials, _merchant_sell_rare_mats, _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms, _merchant_loaded
    if _merchant_loaded:
        return
    _merchant_enabled = _bds_ini.read_bool(_MERCHANT_SECTION, "enabled", False)
    _merchant_id_kits_target = _bds_ini.read_int(_MERCHANT_SECTION, "id_kits_target", _FIXED_ID_KITS_TARGET)
    _merchant_salvage_kits_target = _bds_ini.read_int(_MERCHANT_SECTION, "salvage_kits_target", _FIXED_SALVAGE_KITS_TARGET)
    _merchant_store_consumable_materials = _bds_ini.read_bool(_MERCHANT_SECTION, "store_consumable_materials", False)
    _merchant_sell_materials = _bds_ini.read_bool(_MERCHANT_SECTION, "sell_materials", False)
    _merchant_sell_rare_mats = _bds_ini.read_bool(_MERCHANT_SECTION, "sell_rare_mats", False)
    _merchant_buy_ectos = _bds_ini.read_bool(_MERCHANT_SECTION, "buy_ectos", False)
    _merchant_ecto_threshold = _bds_ini.read_int(_MERCHANT_SECTION, "ecto_threshold", 800_000)
    _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, _bds_ini.read_int(_MERCHANT_SECTION, "alt_wait_ms", _DEFAULT_ALT_SETTLE_WAIT_MS)))
    _merchant_loaded = True

def _save_merchant_settings() -> None:
    _bds_ini.write_key(_MERCHANT_SECTION, "enabled", str(_merchant_enabled))
    _bds_ini.write_key(_MERCHANT_SECTION, "id_kits_target", str(_merchant_id_kits_target))
    _bds_ini.write_key(_MERCHANT_SECTION, "salvage_kits_target", str(_merchant_salvage_kits_target))
    _bds_ini.write_key(_MERCHANT_SECTION, "store_consumable_materials", str(_merchant_store_consumable_materials))
    _bds_ini.write_key(_MERCHANT_SECTION, "sell_materials", str(_merchant_sell_materials))
    _bds_ini.write_key(_MERCHANT_SECTION, "sell_rare_mats", str(_merchant_sell_rare_mats))
    _bds_ini.write_key(_MERCHANT_SECTION, "buy_ectos", str(_merchant_buy_ectos))
    _bds_ini.write_key(_MERCHANT_SECTION, "ecto_threshold", str(_merchant_ecto_threshold))
    _bds_ini.write_key(_MERCHANT_SECTION, "alt_wait_ms", str(_merchant_alt_wait_ms))

def _draw_merchant_settings() -> None:
    import PyImGui
    global _merchant_enabled, _merchant_id_kits_target, _merchant_salvage_kits_target, _merchant_store_consumable_materials, _merchant_sell_materials, _merchant_sell_rare_mats, _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms

    _load_merchant_settings()

    PyImGui.separator()
    PyImGui.text("Merchant (Guild Hall) - runs on start")
    PyImGui.separator()

    new_enabled = PyImGui.checkbox("Restock kits / sell materials on startup", _merchant_enabled)
    if new_enabled != _merchant_enabled:
        _merchant_enabled = new_enabled
        _save_merchant_settings()

    if _merchant_enabled:
        PyImGui.push_item_width(100)
        new_id = PyImGui.input_int("ID Kits target##bds_id", _merchant_id_kits_target)
        if new_id != _merchant_id_kits_target:
            _merchant_id_kits_target = max(0, new_id)
            _save_merchant_settings()

        new_sal = PyImGui.input_int("Salvage Kits target##bds_sal", _merchant_salvage_kits_target)
        if new_sal != _merchant_salvage_kits_target:
            _merchant_salvage_kits_target = max(0, new_sal)
            _save_merchant_settings()
        PyImGui.pop_item_width()

        new_sell = PyImGui.checkbox("Sell common materials##bds_sell", _merchant_sell_materials)
        if new_sell != _merchant_sell_materials:
            _merchant_sell_materials = new_sell
            _save_merchant_settings()

        new_store = PyImGui.checkbox(
            "Store consumable materials (Dust/Iron/Feather/Bone/Fiber)##bds_store_cons_mats",
            _merchant_store_consumable_materials,
        )
        if new_store != _merchant_store_consumable_materials:
            _merchant_store_consumable_materials = new_store
            _save_merchant_settings()

        new_rare = PyImGui.checkbox("Sell Diamond & Onyx to Rare Material Trader##bds_rare_mats", _merchant_sell_rare_mats)
        if new_rare != _merchant_sell_rare_mats:
            _merchant_sell_rare_mats = new_rare
            _save_merchant_settings()

        new_ectos = PyImGui.checkbox("Buy Glob of Ectoplasm when storage over threshold##bds_ectos", _merchant_buy_ectos)
        if new_ectos != _merchant_buy_ectos:
            _merchant_buy_ectos = new_ectos
            _save_merchant_settings()

        if _merchant_buy_ectos:
            new_thresh = PyImGui.input_int("Storage threshold (gold)##bds_ecto_thresh", _merchant_ecto_threshold)
            if new_thresh != _merchant_ecto_threshold:
                _merchant_ecto_threshold = max(0, new_thresh)
                _save_merchant_settings()

        PyImGui.push_item_width(100)
        new_wait = PyImGui.input_int("Alt settle wait (ms)##bds_alt_wait", _merchant_alt_wait_ms)
        if new_wait != _merchant_alt_wait_ms:
            _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, new_wait))
            _save_merchant_settings()
        PyImGui.pop_item_width()
        PyImGui.same_line(0, 6)
        PyImGui.text("(time given to alts to reach NPCs and finish)")

def _find_npc_xy_by_name(name_fragment: str, max_dist: float = 15000.0):
    """Find the nearest NPC whose display name contains name_fragment."""
    npcs = AgentArray.GetNPCMinipetArray()
    npcs = AgentArray.Filter.ByDistance(npcs, Player.GetXY(), max_dist)
    for npc_id in npcs:
        npc_name = Agent.GetNameByID(int(npc_id))
        if name_fragment.lower() in npc_name.lower():
            return Agent.GetXY(int(npc_id))
    return None

def _count_model_in_inventory(model_id: int) -> int:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    count = 0
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) == int(model_id):
            count += max(1, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
    return count

def _coro_sell_rare_mats_at_trader(x: float, y: float, model_ids: set[int]) -> Generator:
    """Sell rare material items (by model ID) to the trader at (x, y), one unit at a time.
    Bypasses SellMaterialsAtTrader which skips IsRareMaterial items."""
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Agents.InteractWithAgentXY(x, y)
    yield from Routines.Yield.wait(1000)

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sold_total = 0
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) not in model_ids:
            continue
        stack_qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        while stack_qty > 0:
            quoted = yield from Routines.Yield.Merchant._wait_for_quote(
                GLOBAL_CACHE.Trading.Trader.RequestSellQuote, item_id,
                timeout_ms=750, step_ms=10)
            if quoted <= 0:
                break
            GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted)
            new_qty = yield from Routines.Yield.Merchant._wait_for_stack_quantity_drop(
                item_id, stack_qty, timeout_ms=750, step_ms=10)
            if new_qty >= stack_qty:
                break
            sold_total += stack_qty - new_qty
            stack_qty = new_qty
    ConsoleLog(BOT_NAME, f"[Merchant] Sold {sold_total} rare material unit(s) at trader")

def _formation_of_group() -> Generator:
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants

    CustomBehaviorParty().schedule_action(PartyCommandConstants.invite_all_to_leader_party)

    yield from Routines.Yield.wait(random.randint(4_000, 10_000))

    yield
    return

def _gh_merchant_setup() -> Generator:
    """Travel to Guild Hall (all accounts via SharedMemory), restock kits, sell materials,
    sell leftover stacks and optionally buy ectos. Mirrors the FoW modular bot pattern."""
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants
    from Py4GWCoreLib.enums_src.Model_enums import ModelID as _ModelID

    yield from Routines.Yield.wait(1500)
    yield from AutoInventoryHandler().IDAndSalvageItems()

    leave_party: bool = True

    _load_merchant_settings()
    if not _merchant_enabled:
        yield
        return

    # ── Step 0 (startup only): Leave current party on all accounts ────────────
    if leave_party:
        ConsoleLog(BOT_NAME, "[Merchant] Leaving party on all accounts before GH travel")
        _my_email = Player.GetAccountEmail()
        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if acc.AccountEmail != _my_email:
                GLOBAL_CACHE.ShMem.SendMessage(_my_email, acc.AccountEmail, SharedCommandType.LeaveParty, (0, 0, 0, 0), ("", "", "", ""))
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(2000)

    # # ── Pre-travel: Disable InventoryPlus BEFORE GH entry so its auto-deposit cycle
    # #    cannot send scrolls (or other items) to storage when accounts enter GH. ──
    # yield from _disable_inventoryplus_pretravel()

    # ── Step 1: Send ALL accounts to their own Guild Hall (FoW pattern) ───────
    ConsoleLog(BOT_NAME, "[Merchant] Waiting for CustomBehaviorParty to be ready")
    _cb_deadline = time.time() + 30
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(100)

    ConsoleLog(BOT_NAME, "[Merchant] Scheduling GH travel for all accounts")
    _ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.travel_gh))
    if not _ok:
        ConsoleLog(BOT_NAME, "[Merchant] CB schedule failed — falling back to local TravelGH")
        if not Map.IsGuildHall():
            Map.TravelGH()

    # Wait for all accounts to arrive at their GH
    _cb_deadline = time.time() + 60
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(200)

    # Ensure leader is in GH
    _gh_deadline = time.time() + 30
    while not Map.IsGuildHall() and time.time() < _gh_deadline:
        yield from Routines.Yield.wait(500)

    if not Map.IsGuildHall():
        ConsoleLog(BOT_NAME, "[Merchant] Failed to reach Guild Hall — skipping merchant step")
        yield
        return

    yield from Routines.Yield.wait(3000)  # wait for NPCs to finish loading

    # # ── Disable CustomBehavior and InventoryPlus on all accounts during merchant ops ──
    # yield from _disable_merchant_widgets()

    # ── Helpers ───────────────────────────────────────────────────────────────
    _my_email = Player.GetAccountEmail()

    def _dispatch_to_alts(command, params, extra_data=("", "", "", "")) -> list[tuple[str, int]]:
        refs: list[tuple[str, int]] = []
        for _acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if _acc.AccountEmail != _my_email:
                msg_index = int(
                    GLOBAL_CACHE.ShMem.SendMessage(_my_email, _acc.AccountEmail, command, params, extra_data)
                )
                refs.append((_acc.AccountEmail, msg_index))
        return refs

    def _wait_for_alt_dispatch_completion(
            stage_name: str,
            message_refs: list[tuple[str, int]],
            command,
            timeout_ms: int = 30_000,
    ):
        if not message_refs:
            return
        pending: dict[tuple[str, int], None] = {
            (acc_email, msg_index): None
            for acc_email, msg_index in message_refs
            if int(msg_index) >= 0
        }
        if not pending:
            return
        deadline = time.monotonic() + (max(0, int(timeout_ms)) / 1000.0)
        while pending and time.monotonic() < deadline:
            completed: list[tuple[str, int]] = []
            for acc_email, msg_index in list(pending.keys()):
                message = GLOBAL_CACHE.ShMem.GetInbox(msg_index)
                is_same_message = (
                        bool(getattr(message, "Active", False))
                        and str(getattr(message, "ReceiverEmail", "") or "") == acc_email
                        and str(getattr(message, "SenderEmail", "") or "") == _my_email
                        and int(getattr(message, "Command", -1)) == int(command)
                )
                if not is_same_message:
                    completed.append((acc_email, msg_index))
            for key in completed:
                pending.pop(key, None)
            if pending:
                yield from Routines.Yield.wait(50)
        if pending:
            pending_accounts = ", ".join(sorted({email for email, _ in pending}))
            ConsoleLog(
                BOT_NAME,
                f"[Merchant] {stage_name}: timeout waiting for alt completion after {timeout_ms} ms. Pending: {pending_accounts}",
                Py4GW.Console.MessageType.Warning,
            )

    # ── Step 2: Find NPC coordinates ──────────────────────────────────────────
    _RARE_MAT_MODELS = {935, 936}  # Diamond=935, Onyx Gemstone=936
    _RARE_MAT_FILTER  = "935,936"  # encoded for ShMem dispatch
    _CRAFTING_MAT_MODELS = {
        int(_ModelID.Pile_Of_Glittering_Dust.value),
        int(_ModelID.Bone.value),
        int(_ModelID.Iron_Ingot.value),
        int(_ModelID.Feather.value),
        int(_ModelID.Plant_Fiber.value),
    }
    _CRAFTING_MAT_FILTER = ",".join(str(mid) for mid in sorted(_CRAFTING_MAT_MODELS))

    merchant_xy   = _find_npc_xy_by_name("Merchant")
    mat_xy        = _find_npc_xy_by_name("Material Trader") if _merchant_sell_materials else None
    rare_xy       = _find_npc_xy_by_name("Rare") if (_merchant_buy_ectos or _merchant_sell_rare_mats) else None

    # ── Step 2.5: Store consumable crafting mats before trader sales (leader + alts)
    if _merchant_store_consumable_materials:
        ConsoleLog(BOT_NAME, "[Merchant] Depositing consumable crafting materials to storage on all accounts")
        deposit_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (0, 0, 0, 0),
            ("deposit", _CRAFTING_MAT_FILTER, "", "0"),
        )
        yield from _coro_deposit_crafting_materials_to_storage(_CRAFTING_MAT_MODELS)
        yield from _wait_for_alt_dispatch_completion("deposit_materials", deposit_refs, SharedCommandType.MerchantMaterials)

    # ── Step 3: Sell materials at trader (leader + alts) ─────────────────────
    if _merchant_sell_materials:
        if mat_xy:
            tmx, tmy = mat_xy
            ConsoleLog(BOT_NAME, f"[Merchant] Dispatching sell_materials to alts, trader at ({tmx:.0f}, {tmy:.0f})")
            sell_mat_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (tmx, tmy, 0, 0),
                ("sell", "", "", ""),
            )
            ConsoleLog(BOT_NAME, "[Merchant] Selling materials at trader (leader)")
            yield from Routines.Yield.Merchant.SellMaterialsAtTrader(tmx, tmy)
            yield from _wait_for_alt_dispatch_completion("sell_materials", sell_mat_refs, SharedCommandType.MerchantMaterials)
        else:
            ConsoleLog(BOT_NAME, "[Merchant] No Material Trader NPC found")

        # ── Step 4: Sell leftover stacks < 10 to regular merchant (leader + alts)
        # if merchant_xy:
        #     mx, my = merchant_xy
        #     ConsoleLog(BOT_NAME, "[Merchant] Dispatching sell_merchant_leftovers to alts")
        #     leftover_refs = _dispatch_to_alts(
        #         SharedCommandType.MerchantMaterials,
        #         (mx, my, 0, 0),
        #         ("sell_merchant_leftovers", "", "10", ""),
        #     )
        #     leftover_ids = _get_leftover_material_item_ids()
        #     if leftover_ids:
        #         ConsoleLog(BOT_NAME, f"[Merchant] Selling {len(leftover_ids)} leftover stacks (leader)")
        #         yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (leftovers)")
        #         yield from Routines.Yield.wait(1200)
        #         yield from Routines.Yield.Merchant.SellItems(leftover_ids, log=True)
        #         yield from Routines.Yield.wait(300)
        #     yield from _wait_for_alt_dispatch_completion(
        #         "sell_merchant_leftovers",
        #         leftover_refs,
        #         SharedCommandType.MerchantMaterials,
        #     )

    # ── Step 5: Sell non-salvageable gold items (anniversary weapons) to merchant ─
    if merchant_xy:
        mx, my = merchant_xy
        ConsoleLog(BOT_NAME, "[Merchant] Dispatching handle_sell_inventoryutil to alts")
        sell_gold_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (mx, my, 0, 0),
            ("handle_sell_inventoryutil", "", "", ""),
        )
        yield from _coro_handle_sell_inventoryutil(mx, my)
        yield from _wait_for_alt_dispatch_completion(
            "handle_sell_inventoryutil",
            sell_gold_refs,
            SharedCommandType.MerchantMaterials,
        )

    # ── Step 6: Sell XP/insight scrolls to merchant (leader + alts) ──────────
    if merchant_xy:
        mx, my = merchant_xy
        ConsoleLog(BOT_NAME, "[Merchant] Dispatching sell_scrolls to alts")
        sell_scroll_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (mx, my, 0, 0),
            ("sell_scrolls", _SCROLL_MODEL_FILTER, "", ""),
        )
        yield from _coro_sell_scrolls(mx, my)
        yield from _wait_for_alt_dispatch_completion("sell_scrolls", sell_scroll_refs, SharedCommandType.MerchantMaterials)

    # ── Step 7: Restock kits (leader + alts) — after all selling to maximise free space
    if merchant_xy:
        mx, my = merchant_xy
        ConsoleLog(BOT_NAME, f"[Merchant] Merchant at ({mx:.0f}, {my:.0f}) — dispatching kits to alts")
        kit_refs = _dispatch_to_alts(
            SharedCommandType.MerchantItems,
            (mx, my, _merchant_id_kits_target, _merchant_salvage_kits_target),
        )
        yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant")
        yield from Routines.Yield.wait(1200)
        id_kits     = _count_model_in_inventory(_ModelID.Identification_Kit.value)
        sup_id_kits = _count_model_in_inventory(_ModelID.Superior_Identification_Kit.value)
        salvage_kits = _count_model_in_inventory(_ModelID.Salvage_Kit.value)
        id_to_buy      = max(0, _merchant_id_kits_target     - (id_kits + sup_id_kits))
        salvage_to_buy = max(0, _merchant_salvage_kits_target - salvage_kits)
        ConsoleLog(BOT_NAME, f"[Merchant] Buying {id_to_buy} ID kits, {salvage_to_buy} salvage kits")
        yield from Routines.Yield.Merchant.BuyIDKits(id_to_buy, log=True)
        yield from Routines.Yield.Merchant.BuySalvageKits(salvage_to_buy, log=True)
        yield from _wait_for_alt_dispatch_completion("restock_kits", kit_refs, SharedCommandType.MerchantItems)
        yield from Routines.Yield.wait(300)
    else:
        ConsoleLog(BOT_NAME, "[Merchant] No Merchant NPC found — skipping kit purchase")

    # ── Step 6: Sell Diamonds & Onyx to Rare Material Trader (leader + alts) ──
    # if _merchant_sell_rare_mats:
    #     if rare_xy:
    #         rx, ry = rare_xy
    #         ConsoleLog(BOT_NAME, "[Merchant] Dispatching sell_rare_mats (Diamond/Onyx) to alts")
    #         rare_sell_refs = _dispatch_to_alts(
    #             SharedCommandType.MerchantMaterials,
    #             (rx, ry, 0, 0),
    #             ("sell_rare_mats", _RARE_MAT_FILTER, "", ""),
    #         )
    #         ConsoleLog(BOT_NAME, "[Merchant] Selling Diamond/Onyx at Rare Material Trader (leader)")
    #         yield from _coro_sell_rare_mats_at_trader(rx, ry, _RARE_MAT_MODELS)
    #         yield from _wait_for_alt_dispatch_completion(
    #             "sell_rare_mats",
    #             rare_sell_refs,
    #             SharedCommandType.MerchantMaterials,
    #         )
    #     else:
    #         ConsoleLog(BOT_NAME, "[Merchant] No Rare Material Trader found — skipping rare mat sell")

    # ── Step 7: Buy ectos from storage excess (leader + alts independently)
    # Storage is PER-ACCOUNT in GW — each account checks its own storage independently.
    # Always dispatch to alts so each alt can buy if ITS OWN storage exceeds threshold.
    if _merchant_buy_ectos and rare_xy:
        rx, ry = rare_xy
        ConsoleLog(BOT_NAME, f"[Merchant] Dispatching buy_ectoplasm to all alts (threshold={_merchant_ecto_threshold:,})")
        buy_ecto_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (rx, ry, _merchant_ecto_threshold, _merchant_ecto_threshold),
            ("buy_ectoplasm", "1", "0", ""),  # use_storage_gold=True; each alt checks own storage
        )
        # Leader buys from its own storage independently
        leader_storage = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
        if leader_storage > _merchant_ecto_threshold:
            ConsoleLog(BOT_NAME, f"[Merchant] Leader buying ectos (storage={leader_storage:,}, threshold={_merchant_ecto_threshold:,})")
            yield from Routines.Yield.Merchant.BuyEctoplasm(
                rx, ry,
                use_storage_gold=True,
                start_threshold=_merchant_ecto_threshold,
                stop_threshold=_merchant_ecto_threshold,
            )
        else:
            ConsoleLog(BOT_NAME, f"[Merchant] Leader storage ({leader_storage:,}) at/below threshold — skipping leader ecto buy")
        yield from _wait_for_alt_dispatch_completion("buy_ectoplasm", buy_ecto_refs, SharedCommandType.MerchantMaterials)
    elif _merchant_buy_ectos:
        ConsoleLog(BOT_NAME, "[Merchant] Ecto buy skipped — no Rare Material Trader found")

    # ── Step 8: Wait for alts to finish their queued actions ─────────────────
    if _merchant_alt_wait_ms > 0:
        ConsoleLog(BOT_NAME, f"[Merchant] Final settle wait {_merchant_alt_wait_ms}ms")
        yield from Routines.Yield.wait(_merchant_alt_wait_ms)

    CustomBehaviorParty().schedule_action(PartyCommandConstants.invite_all_to_leader_party)

    # ── Step 9: Return to Vlox's Fall ────────────────────────────────────────
    yield from Routines.Yield.wait(10_000+random.randint(100, 10_000))
    ConsoleLog(BOT_NAME, "[Merchant] Returning to the outpost")
    yield from bot.Map._coro_travel(OUTPOST_TO_TRAVEL, "")
    ConsoleLog(BOT_NAME, "[Merchant] Guild Hall merchant run complete")
    yield from Routines.Yield.wait(10_000+random.randint(100, 10_000))
    yield

# Widgets you want to force-manage at startup.
# Edit these lists to choose which widgets to enable/disable.
WIDGETS_TO_ENABLE: tuple[str, ...] = (
    "LootManager",
    "CustomBehaviors",
    "ResurrectionScroll",
    "Return to outpost on defeat",
)

def bot_routine(bot: Botting) -> None:
    global Norn_Path, loop_header, death_loop_headers
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("hero_ai")
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=WIDGETS_TO_ENABLE)
    loop_header = bot.States.AddHeader('Exit To Farm')
    bot.States.AddCustomState(_gh_merchant_setup, "GH Merchant Setup")
    bot.Wait.ForTime(random.randint(11000, 19600))

    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OLAFSTEAD)
    bot.Properties.Enable("war_supplies")
    
    bot.Party.SetHardMode(True)
    auto_path_list = [(-328.0, 1240.0), (-1500.0, 1250.0)]
    bot.Move.FollowPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=553)
    bot.States.AddHeader("Start Combat")
    bot.Multibox.UseAllConsumables()
    # bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    bot.States.AddManagedCoroutine("Anti-Stuck Watchdog", lambda: _anti_stuck_watchdog(bot))
    
    # Initial path to first blessing
    bot.Move.XY(-2484.73, 118.55, "Start")
    bot.Move.XY(-3059.12, -419.00, "Move to bridge")
    bot.Move.XY(-3301.01, -2008.23, "Move to shrine")
    bot.Move.XY(-2034, -4512, "Move to blessing 1")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-1892.00, -4505.00)
    bot.Multibox.SendDialogToTarget(0x84) #Get Blessing 1
    bot.Wait.ForTime(5000)
    
    # Path to blessing 2
    death_loop_headers = bot.States.AddHeader("Path to blessing 2 - Edda")
    bot.Move.XY(-5278, -5771, "Aggro: Berzerker")
    bot.Move.XY(-5456, -7921, "Aggro: Berzerker")
    bot.Move.XY(-8793, -5837, "Aggro: Berzerker")
    bot.Move.XY(-14092, -9662, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-17260, -7906, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-21964, -12877, "Aggro: Jotun")
    bot.Move.XY(-25341.00, -11957.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-25341.00, -11957.00) 
    bot.Multibox.SendDialogToTarget(0x84) # Edda Blessing 2
    bot.Wait.ForTime(10000)
    
    # Path to blessing 3
    bot.States.AddHeader("Path to blessing 3 - Inga Caveborn")
    bot.Move.XY(-22275, -12462, "Move to area 2")
    bot.Move.XY(-21671, -2163, "Aggro: Berzerker")
    bot.Move.XY(-19592, 772, "Aggro: Berzerker")
    bot.Move.XY(-13795, -751, "Aggro: Berzerker")
    bot.Move.XY(-17012, -5376, "Aggro: Berzerker")
    bot.Move.XY(-10606.23, -1625.26)
    bot.Move.XY(-12158.00, -4277.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-12158.00, -4277.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 3
    bot.Wait.ForTime(10000)
    
    # Path to blessing 4
    bot.States.AddHeader("Path to blessing 4")
    bot.Move.XY(-12071, -4274, "Aggro: Berzerker")
    bot.Move.XY(-8351, -2633, "Move to regroup")
    bot.Move.XY(-4362, -1610, "Aggro: Lake")
    bot.Move.XY(-4316, 4033, "Aggro: Lake")
    bot.Move.XY(-8809, 5639, "Aggro: Lake")
    bot.Move.XY(-14916, 2475)
    bot.Move.XY(-11204.00, 5479.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-11204.00, 5479.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 4
    bot.Wait.ForTime(10000)
    
    # Path to blessing 5
    bot.States.AddHeader("Path to blessing 5")
    bot.Move.XY(-11282, 5466, "Aggro: Elemental")
    bot.Move.XY(-16051, 6492, "Aggro: Elemental")
    bot.Move.XY(-16934, 11145, "Aggro: Elemental")
    bot.Move.XY(-19378, 14555)
    bot.Move.XY(-22889.00, 14165.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-22889.00, 14165.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 5
    bot.Wait.ForTime(10000)
    
    # Path to blessing 6
    bot.States.AddHeader("Path to blessing 6")
    bot.Move.XY(-22751, 14163, "Aggro: Elemental")
    bot.Move.XY(-15932, 9386, "Move to camp")
    bot.Move.XY(-13777, 8097, "Aggro: Lake")
    bot.Move.XY(-2217.00, 14914.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 6
    bot.Wait.ForTime(10000)

    bot.States.AddHeader("The Path to Revelations")
    # The Path to Revelations (The quest is required beforehand, otherwise the enemies will not spawn)
    bot.Move.XY(19416.26, 1142.77)
    bot.Move.XY(24169.45, -4288.69)
    bot.Move.XY(24169.45, -4288.69)
    bot.Move.XY(19745, -2718)
    bot.Move.XY(23504, 1801) # First boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Second boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Third boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Fourth boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Fifth boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(23504, 1801) # Sixth boss
    bot.Wait.ForTime(10000)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("After The Path to Revelations")
    # Continue route
    bot.Move.XY(-2290, 14879, "Aggro: Modnir")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-1810, 4679, "Move to boss")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-6911, 5240, "Aggro: Boss")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-15471, 6384, "Move to regroup")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-411, 5874, "Aggro: Modniir")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(2859, 3982, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(4909, -4259, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7514, -6587, "Aggro: Berserker")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(3800, -6182, "Aggro: Berserker")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7755, -11467, "Aggro: Elementals and Griffins")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(15403, -4243, "Aggro: Elementals and Griffins")
    bot.Wait.UntilOutOfCombat()
    
    # Path to blessing 7
    bot.States.AddHeader("Path to blessing 7")
    bot.Move.XY(21597, -6798)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-2217.00, 14914.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 7
    bot.Wait.ForTime(10000)
    
    bot.Move.XY(24522, -6532, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(22883, -4248, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(18606, -1894, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(14969, -4048, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(13599, -7339, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(10056, -4967, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(10147, -1630, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat()
    
    # Path to blessing 8
    bot.States.AddHeader("Path to blessing 8")
    bot.Move.XY(8963, 4043, "Take blessing 8")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(8963, 4043)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 8
    bot.Wait.ForTime(10000)
    
    bot.Move.XY(9339.46, 3859.12, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(15576, 7156, "Aggro: Berserker")
    bot.Wait.UntilOutOfCombat()
    
    # Path to blessing 9
    bot.States.AddHeader("Path to blessing 9")
    bot.Move.XY(22838, 7914, "Take blessing 9")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(22838, 7914)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 9
    bot.Wait.ForTime(10000)
    
    # Final route section
    bot.Move.XY(22961, 12757, "Move to shrine")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(18067, 8766, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(13311, 11917, "Aggro: Area")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(13714, 14520, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(11126, 10443, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(5575, 4696, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-503, 9182, "Aggro: Modniir and Elemental 2")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(1582, 15275, "Aggro: Modniir and Elemental 2")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7857, 10409, "Aggro: Modniir and Elemental 2")
    bot.Wait.UntilOutOfCombat()
    
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    
    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName(loop_header)
    
EXPLORABLE_TIMEOUT_SECONDS = 3 * 3600  # 3 hours

def _anti_stuck_resign(bot: "Botting"):
    """Called when the timeout fires: resign, wait for outpost, then restart."""
    yield from bot.helpers.Multibox._resignParty()
    while True:
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            continue
        if Routines.Checks.Map.IsOutpost():
            break
    bot.States.JumpToStepName(loop_header)
    bot.config.FSM.resume()
    yield


def _anti_stuck_watchdog(bot: "Botting"):
    """Resign the party if stuck in explorable for more than 3 hours."""
    explorable_entry_time = None
    while True:
        yield from bot.Wait._coro_for_time(60000)  # check every minute
        if not Routines.Checks.Map.MapValid():
            explorable_entry_time = None
            continue
        if Routines.Checks.Map.IsOutpost():
            explorable_entry_time = None
            continue
        # We are in explorable
        if explorable_entry_time is None:
            explorable_entry_time = time.time()
            continue
        elapsed = time.time() - explorable_entry_time
        if elapsed >= EXPLORABLE_TIMEOUT_SECONDS:
            ConsoleLog(BOT_NAME, f"Anti-stuck: {elapsed/3600:.1f}h in explorable — resigning party.", Py4GW.Console.MessageType.Warning)
            explorable_entry_time = None
            bot.config.FSM.pause()
            bot.config.FSM.AddManagedCoroutine("AntiStuck_Resign", lambda: _anti_stuck_resign(bot))


# def _upkeep_multibox_consumables(bot: "Botting"):
#     while True:
#         yield from bot.Wait._coro_for_time(15000)
#         if not Routines.Checks.Map.MapValid():
#             continue
#
#         if Routines.Checks.Map.IsOutpost():
#             continue
#
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Essence_Of_Celerity.value,
#                                             GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Grail_Of_Might.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Armor_Of_Salvation.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Birthday_Cupcake.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Golden_Egg.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Corn.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Apple.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Slice_Of_Pumpkin_Pie.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Drake_Kabob.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Bowl_Of_Skalefin_Soup.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.Pahnai_Salad.value,
#                                                 GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))
#         yield from bot.helpers.Multibox._use_consumable_message((ModelID.War_Supplies.value,
#                                                                 GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))
#         for i in range(1, 5):
#             GLOBAL_CACHE.Inventory.UseItem(ModelID.Honeycomb.value)
#             yield from bot.Wait._coro_for_time(250)
            
def _nearest_path_index(path: list, x: float, y: float) -> int:
    best, best_dist = 0, float('inf')
    for i, (px, py) in enumerate(path):
        d = (px - x) ** 2 + (py - y) ** 2
        if d < best_dist:
            best_dist, best = d, i
    return best


def _all_accounts_alive() -> bool:
    current_map = Map.GetMapID()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if account.AgentData.Map.MapID != current_map:
            continue  # skip accounts not in the same explorable (other maps, outpost, etc.)
        if account.AgentData.Health.Current <= 0:
            return False
    return True


def _on_party_wipe(bot: "Botting"):
    global death_loop_headers
    while Agent.IsDead(Player.GetAgentID()) or not _all_accounts_alive():
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return

    # All accounts revived — resume route from nearest path point
    pos = Player.GetXY()
    if pos:
        nearest_idx = _nearest_path_index(Norn_Path, pos[0], pos[1])
        for (wx, wy) in Norn_Path[nearest_idx:]:
            if not Routines.Checks.Map.MapValid():
                break
            yield from bot.Move._coro_xy(wx, wy)

    bot.States.JumpToStepName(death_loop_headers)
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot)) 

bot.SetMainRoutine(bot_routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Norn Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account, farm Norn title")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick Divinus")
    PyImGui.end_tooltip()

_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}

def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui
    title_idx = int(TitleID.Norn)
    tiers = TITLE_TIERS.get(TitleID.Norn, [])
    now = time.time()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        prev_required = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        is_maxed = tiers and pts >= tiers[-1].required
        PyImGui.separator()
        PyImGui.text(f"{name}  [{tier_name}]")
        if is_maxed:
            PyImGui.text_colored("Maximum rank achieved. Title complete.", (0.4, 1.0, 0.4, 1.0))
            continue
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        PyImGui.text(f"Points: {pts:,} / {next_required:,}")
        if next_required > prev_required:
            frac = min((pts - prev_required) / (next_required - prev_required), 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{pts - prev_required:,} / {next_required - prev_required:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")

REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "Wick Divinus bots", "Reforged_Icon.png")
def main():
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, extra_tabs=[("Statistics", _draw_title_track)])

if __name__ == "__main__":
    main()
