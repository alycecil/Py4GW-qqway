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

BOT_NAME = "Asterius Scythe Farm"
MODULE_ICON = "Textures\\Module_Icons\\Asterius' Scythe.png"
TEXTURE = os.path.join(
    Py4GW.Console.get_projects_path(), "Bots", "marks_coding_corner", "textures", "asterius_scythe.png"
)
OUTPOST_TO_TRAVEL = Map.GetMapIDByName('Olafstead')
VARAJAR_FELLS_MAP_ID = 553
ASTERIUS_MODEL_ID = 6509
_bds_ini_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "common_ac", "loot_settings.ini")
os.makedirs(os.path.dirname(_bds_ini_path), exist_ok=True)
_bds_ini = IniHandler(_bds_ini_path)
_FIXED_ID_KITS_TARGET = 1
_FIXED_SALVAGE_KITS_TARGET = 4
_DEFAULT_ALT_SETTLE_WAIT_MS = 2000

TRAVEL_PATH: list[tuple[float, float]] = [
    (-25341.00, -11957.00),
    (-21964, -12877),
    (17260, -7906),
    (-14092, -9662),
    (-8793, -5837),
    (-5456, -7921),
    (-5278, -5771),
    (-5767, -4300),
    (-8149, -2815),
    (-9563, -2276),
    (-12105, -868),
    (-15445, -4605),
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
              upkeep_war_supplies_restock=25,
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

def is_asterius_killed_or_time_elapsed():
    global is_asterius_killed
    global is_asterius_spotted
    global asterius_agent_id
    global elapsed

    elapsed += 1
    # Cap at 3 minutes to wait for Asterius on the final spot
    if elapsed > 180:
        return True

    if is_asterius_killed:
        return True

    if is_asterius_spotted and asterius_agent_id:
        if not Agent.IsDead(asterius_agent_id):
            return False
        is_asterius_killed = True

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array,
        lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id))
        <= Range.SafeCompass.value,
    )
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array, lambda agent_id: Player.GetAgentID() != agent_id
    )
    for enemy_id in enemy_array:
        if Agent.GetModelID(enemy_id) == ASTERIUS_MODEL_ID:
            is_asterius_spotted = True
            asterius_agent_id = enemy_id
    return False


def reset_farm_flags():
    global is_asterius_killed
    global is_asterius_spotted
    global asterius_agent_id
    global elapsed

    is_asterius_spotted = False
    is_asterius_killed = False
    asterius_agent_id = -1
    elapsed = 0


def _on_party_wipe(bot: "Botting"):
    global death_loop_headers
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    if death_loop_headers is None:
        death_loop_headers = "[H]Start Combat_4"
    bot.States.JumpToStepName(death_loop_headers)
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

def _quit_if_done():
    global is_asterius_killed
    global is_asterius_spotted
    global asterius_agent_id
    global loop_header

    if is_asterius_killed:
        print("we're done, lets wait for a minute then leave")

        yield from bot.Wait._coro_for_time(10_000)

        bot.Multibox.ResignParty()

        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
        from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants

        CustomBehaviorParty().schedule_action(PartyCommandConstants.resign)

        yield from Routines.Yield.wait(random.randint(4_000, 10_000))

        reset_farm_flags()

        bot.Wait.UntilOnOutpost()
        bot.States.JumpToStepName(loop_header)

    pass

def handle_asterius_killed_en_route():
    global is_asterius_killed
    global is_asterius_spotted
    global asterius_agent_id

    while True:
        if not Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue

        if is_asterius_killed:
            yield from Routines.Yield.wait(1000)
            continue

        if is_asterius_spotted and asterius_agent_id:
            yield from Routines.Yield.wait(1000)
            if Agent.IsDead(asterius_agent_id):
                is_asterius_killed = True
                print("We killed Asterius!")
            continue

        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id))
            <= Range.SafeCompass.value,
        )
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array, lambda agent_id: Player.GetAgentID() != agent_id
        )
        for enemy_id in enemy_array:
            if Agent.GetModelID(enemy_id) == ASTERIUS_MODEL_ID:
                is_asterius_spotted = True
                print("I see Asterius!")
                asterius_agent_id = enemy_id
                yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(1000)

# Widgets you want to force-manage at startup.
# Edit these lists to choose which widgets to enable/disable.
WIDGETS_TO_ENABLE: tuple[str, ...] = (
    "LootManager",
    "CustomBehaviors",
    "ResurrectionScroll",
    "Return to outpost on defeat",
#    "Inventory Plus",
)

def farm_scythes(bot: Botting) -> None:
    global death_loop_headers
    global loop_header
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')

    # events
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    # end events

    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("hero_ai")
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=WIDGETS_TO_ENABLE)
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Enable("war_supplies")

    loop_header = bot.States.AddHeader('Exit To Farm')
    bot.States.AddCustomState(_gh_merchant_setup, "GH Merchant Setup")
    bot.Wait.ForTime(random.randint(11000, 19600))

    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Party.SetHardMode(True)
    bot.States.AddManagedCoroutine('Detect en route Asterius kill', handle_asterius_killed_en_route)
    bot.States.AddCustomState(_formation_of_group, "Force formation")

    bot.Properties.Disable('pause_on_danger')
    bot.Move.XYAndExitMap(-2166, 861, target_map_id=VARAJAR_FELLS_MAP_ID)
    bot.Wait.ForTime(4000)
    bot.Properties.Enable('pause_on_danger')

    # Initial path to first blessing
    bot.Move.XY(-2484.73, 118.55, "Start")
    bot.Move.XY(-3059.12, -419.00, "Move to bridge")
    bot.Move.XY(-3301.01, -2008.23, "Move to shrine")
    bot.Move.XY(-2034, -4512, "Move to blessing 1")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-1892.00, -4505.00)
    bot.Multibox.SendDialogToTarget(0x84) #Get Blessing 1
    bot.Wait.ForTime(random.randint(5000, 9600))

    death_loop_headers = bot.States.AddHeader("Path to blessing 2 - Edda")
    # Path to blessing 2
    bot.Move.XY(-5278, -5771, "Aggro: Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.Move.XY(-5456, -7921, "Aggro: Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.Move.XY(-8793, -5837, "Aggro: Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.Move.XY(-14092, -9662, "Aggro: Vaettir and Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.Move.XY(-17260, -7906, "Aggro: Vaettir and Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.Move.XY(-21964, -12877, "Aggro: Jotun")
    bot.Move.XY(-25341.00, -11957.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-25341.00, -11957.00)
    bot.Multibox.SendDialogToTarget(0x84) # Edda Blessing 2
    bot.Wait.ForTime(random.randint(11800, 14600))

    bot.States.AddHeader("Path to blessing 3 - Inga Caveborn")
    bot.States.AddCustomState(_quit_if_done, "Quit if done")
    # Path to blessing 3
    bot.Move.XY(-22275, -12462, "Move to area 2")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.States.AddCustomState(_quit_if_done, "Quit if done")
    bot.Move.XY(-21671, -2163, "Aggro: Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.States.AddCustomState(_quit_if_done, "Quit if done")
    bot.Move.XY(-19592, 772, "Aggro: Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.States.AddCustomState(_quit_if_done, "Quit if done")
    bot.Move.XY(-13795, -751, "Aggro: Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.States.AddCustomState(_quit_if_done, "Quit if done")
    bot.Move.XY(-17012, -5376, "Aggro: Berzerker")
    bot.Wait.ForTime(random.randint(1800, 4600))
    bot.States.AddCustomState(_quit_if_done, "Quit if done")
    bot.Move.XY(-10606.23, -1625.26)
    bot.Move.XY(-12158.00, -4277.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-12158.00, -4277.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 3 - Inga Caveborn
    bot.Wait.ForTime(random.randint(5800, 24600))

    # death_loop_headers = bot.States.AddHeader("Seak and Kill Path")
    # bot.States.AddCustomState(_quit_if_done, "Quit if done")
    #     bot.Move.FollowAutoPath(TRAVEL_PATH, "Kill Route")

    # bot.Wait.UntilCondition(
    #     is_asterius_killed_or_time_elapsed, duration=1000
    # )  # check every second until boss is killed
    # allow to loot
    bot.Wait.ForTime(random.randint(11000, 19600))

    bot.Multibox.ResignParty()
    bot.States.AddCustomState(reset_farm_flags, "Reset Farm detections")
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(10000)

    bot.States.JumpToStepName(loop_header)

def _draw_settings() -> None:
    import PyImGui
    PyImGui.text("Settings")
    PyImGui.separator()
    # _draw_difficulty_setting()
    _draw_merchant_settings()

bot.SetMainRoutine(farm_scythes)
bot.UI.override_draw_config(_draw_settings)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Asterius Scythe Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Asterius Scythe")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- 6-8 well-geared accounts")
    PyImGui.bullet_text("- Hero AI widget enabled on all accounts")
    PyImGui.bullet_text("- Launch the script on the party leader only")
    PyImGui.bullet_text("Designed for Normal Mode (NM) for faster and easy run, but can be change editing True or False in the code.")
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Mark")
    PyImGui.end_tooltip()

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
