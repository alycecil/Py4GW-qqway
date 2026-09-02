import PyImGui
import PySystem

from Py4GWCoreLib import (
    GLOBAL_CACHE,
    ActionQueueManager,
    Agent,
    AgentArray,
    Color,
    ImGui,
    Inventory,
    Item,
    ItemArray,
    Map,
    Player,
    Routines,
    ThrottledTimer,
)
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Settings import Settings

MODULE_NAME = "Merchant Refill"
MODULE_ICON = "Assets/Textures/Module_Icons/Compass+.png"
WIDGET_KEY = "Widgets/Guild Wars/Merchant Refill"

INI_PATH = "Widgets/MerchantRefill"
INI_FILENAME = "MerchantRefill.ini"

# ---------------------------------------------------------------------------
# Per-town-entry "visited" state, mirroring the legacy npc_visited flags.
# ---------------------------------------------------------------------------


class VisitedState:
    def __init__(self) -> None:
        self.xunlai = False
        self.merchant = False
        self.map_signature: tuple[int, int, int] | None = None

    def reset(self) -> None:
        self.xunlai = False
        self.merchant = False


visited = VisitedState()
update_timer = ThrottledTimer(250)
initialized = False
INI_KEY = ""
_busy = False
def _cfg() -> Settings:
    return Settings(f"{INI_PATH}/{INI_FILENAME}", "account")


def _cfg_bool(section: str, key: str, default: bool) -> bool:
    return _cfg().get_bool(section, key, default)


def _cfg_int(section: str, key: str, default: int) -> int:
    return _cfg().get_int(section, key, default)


# ---------------------------------------------------------------------------
# Item disposition: a lean port of the legacy InventoryUtilsConfig + WeaponHandler
# classification. Decisions mirror the original order of precedence:
#   customized > event item > blocklist(model/type) > weapon -> exporter rules
#   (salvage-kit color handling) > KEEP for anything unrecognized.
# ---------------------------------------------------------------------------


class _Action:
    """Item disposition (port of legacy InventoryMode)."""

    KEEP = "keep"
    DEPOSIT = "deposit"
    SELL = "sell"
    SALVAGE = "salvage"


_WEAPON_TYPE_IDS = [
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
]

# Default per-requirement disposition for a *maxed-damage* weapon, mirroring the
# legacy WeaponConfig q0..q13 tiers. Low requirements (0/3/5/7/8) are DEPOSIT-worthy,
# high requirements (12/13) are sold; None means "keep the color default".
_DEFAULT_MAXED_REQ_ACTION = {
    0: _Action.DEPOSIT,
    1: None,
    2: None,
    3: _Action.DEPOSIT,
    4: None,
    5: _Action.DEPOSIT,
    6: None,
    7: _Action.DEPOSIT,
    8: _Action.DEPOSIT,
    9: None,
    10: None,
    11: None,
    12: _Action.SELL,
    13: _Action.SELL,
}

# Default salvage-kit disposition by color (port of legacy SalvageConfig).
_DEFAULT_SALVAGE_ACTION = {
    "White": _Action.SALVAGE,
    "Blue": _Action.SELL,
    "Purple": _Action.SELL,
    "Gold": _Action.SELL,
    "Green": _Action.DEPOSIT,
}


# Blocklist defaults reused from the legacy inventory_utils_config.py. These are the
# item types and model ids the old exporter refused to touch (kept as-is).
_DEFAULT_ITEM_TYPE_BLOCK_LIST = [7, 17, 6, 3, 4, 44, 45, 10, 13, 20, 16, 29, 19, 34, 11, 33, 21, 8, 31, 43, 30, 255, 9]
_DEFAULT_MODEL_ID_BLOCK_LIST = [
    522, 525, 2473, 27974, 399, 1045, 1055, 1058, 1060, 1064, 1065, 1066, 1067, 1660, 1752, 1768,
    1769, 1770, 1771, 1772, 1773, 1870, 1879, 1880, 1881, 1883, 1884, 1885, 1900, 1953, 1956,
    1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971,
    1972, 1973, 1974, 1975, 1976, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2039, 2071,
    2079, 2474, 27033, 27052, 31202, 31203, 31204, 36669, 36677, 36679, 27047,
]


def _ids_from_csv(raw: str) -> set[int]:
    if not raw:
        return set()
    return {int(x) for x in raw.replace(",", " ").split() if x.strip().isdigit()}


def _blocked_models() -> set[int]:
    raw = _cfg().get_str("Blocklist", "models", "")
    values = _ids_from_csv(raw)
    if values:
        return values
    return set(_DEFAULT_MODEL_ID_BLOCK_LIST)


def _blocked_item_types() -> set[int]:
    raw = _cfg().get_str("Blocklist", "item_types", "")
    values = _ids_from_csv(raw)
    if values:
        return values
    return set(_DEFAULT_ITEM_TYPE_BLOCK_LIST)


def _is_blocklisted(item_id: int) -> bool:
    if Item.GetModelID(item_id) in _blocked_models():
        return True
    item_type_value, _ = Item.GetItemType(item_id)
    return int(item_type_value) in _blocked_item_types()


def _is_keep_model(item_id: int) -> bool:
    cfg = _cfg()
    keep_models = _ids_from_csv(cfg.get_str("KeepList", "models", ""))
    return bool(keep_models) and Item.GetModelID(item_id) in keep_models


def _rarity_name(item_id: int) -> str:
    _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
    return rarity


def _weapon_requirement_mode(req: int) -> str | None:
    override = _cfg().get_str("Weapons", f"maxed_req_{req}", "")
    override = override.strip().lower()
    if override in ("", "default"):
        return _DEFAULT_MAXED_REQ_ACTION.get(req)
    if override == "keep":
        return _Action.KEEP
    if override == "deposit":
        return _Action.DEPOSIT
    if override == "sell":
        return _Action.SELL
    if override == "salvage":
        return _Action.SALVAGE
    return _DEFAULT_MAXED_REQ_ACTION.get(req)


def _is_valuable_mod(item_id: int) -> bool:
    """Keep overrides from the legacy exporter rules: Forget-Me-Not inscription and
    'of the profession' prefix, regardless of damage/requirement."""
    upgrade_names = {name for name, _ in Item.Mods.GetUpgrades(item_id)}
    if "ForgetMeNot" in upgrade_names or "OfTheProfession" in upgrade_names:
        return True
    return False


def _weapon_action(item_id: int, item_type: ItemType) -> str:
    rarity = _rarity_name(item_id)
    if rarity == "Green":
        return _Action.DEPOSIT
    if rarity == "Gold":
        default = _Action.SELL
    else:
        default = _Action.SELL if rarity in ("White", "Blue", "Purple") else _Action.KEEP

    if _is_valuable_mod(item_id):
        return _Action.KEEP

    if item_type == ItemType.Shield:
        # Shields: keep the (rare) skin rather than judging by damage.
        return _Action.DEPOSIT

    # Maxed-damage + requirement-tier override (port of WeaponConfig qN), any non-white.
    if rarity != "White" and Item.Properties.IsMaxDamage(item_id):
        _, requirement = Item.Properties.GetRequirement(item_id)
        override = _weapon_requirement_mode(int(requirement))
        if override is not None:
            return override

    if default == _Action.KEEP:
        return _Action.DEPOSIT
    return default


def _salvage_action(item_id: int) -> str:
    rarity = _rarity_name(item_id)
    return _DEFAULT_SALVAGE_ACTION.get(rarity, _Action.KEEP)


def _action_for_item(item_id: int) -> str:
    if item_id < 1:
        return _Action.KEEP
    if Item.Properties.IsCustomized(item_id):
        return _Action.KEEP
    if _is_keep_model(item_id):
        return _Action.KEEP
    if _is_blocklisted(item_id):
        return _Action.KEEP

    item_type_value, _ = Item.GetItemType(item_id)
    item_type = ItemType(item_type_value)
    if item_type in _WEAPON_TYPE_IDS:
        return _weapon_action(item_id, item_type)
    if item_type == ItemType.Salvage:
        return _salvage_action(item_id)
    if item_type == ItemType.Kit:
        return _Action.KEEP
    return _Action.KEEP


def _classify() -> dict[str, list[int]]:
    buckets: dict[str, list[int]] = {a: [] for a in (_Action.SELL, _Action.DEPOSIT, _Action.SALVAGE)}
    for item_id in _get_inventory_item_ids():
        action = _action_for_item(item_id)
        if action in buckets:
            buckets[action].append(item_id)
    return buckets


def _get_inventory_item_ids() -> list[int]:
    bags = ItemArray.CreateBagList(1, 2, 3, 4)
    return ItemArray.GetItemArray(bags)


_merchant_tags_by_type = {
    "merchant": ["Merchant", "Marchand", "Kauffrau"],
    "xunlai": ["Xunlai Chest"],
    "rune_trader": ["Rune Trader"],
    "rare_material_trader": ["Rare Material Trader"],
    "crafting_material_trader": ["Crafting Material Trader"],
}


def _find_merchant_agent(kind: str):
    """Find the nearest matching merchant/crafting NPC on this map."""
    tags = _merchant_tags_by_type.get(kind)
    if not tags:
        return None
    player_xy = Player.GetXY()
    agent_ids = AgentArray.GetNPCMinipetArray()
    agent_ids = AgentArray.Filter.ByDistance(agent_ids, player_xy, 5000.0)
    for agent_id in agent_ids:
        if not Agent.IsAlive(agent_id):
            continue
        name = Agent.GetNameByID(agent_id) or ""
        if any(tag in name for tag in tags):
            return agent_id
    return None


def _kit_counts() -> tuple[int, int, int]:
    id_kits = Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value) + Inventory.GetModelCount(
        ModelID.Identification_Kit.value
    )
    salvage = Inventory.GetModelCount(ModelID.Salvage_Kit.value)
    expert = Inventory.GetModelCount(ModelID.Expert_Salvage_Kit.value)
    return id_kits, salvage, expert


# Unlimited-use kit model ids. These never run out, so when one is in the inventory the
# corresponding restock purchase is disabled entirely.
UNLIMITED_ID_KIT_MODEL = 4033
UNLIMITED_SALVAGE_KIT_MODEL = 275


def _has_unlimited_kit(model_id: int) -> bool:
    return Inventory.GetModelCount(model_id) > 0


def _kits_to_buy() -> tuple[int, int, int]:
    id_kits, salvage, expert = _kit_counts()
    target_id = _cfg_int("Kits", "keep_id_kits", 2)
    target_salvage = _cfg_int("Kits", "keep_salvage_kits", 5)
    target_expert = _cfg_int("Kits", "keep_expert_salvage_kits", 1)

    if _has_unlimited_kit(UNLIMITED_ID_KIT_MODEL):
        target_id = 0
    if _has_unlimited_kit(UNLIMITED_SALVAGE_KIT_MODEL):
        target_salvage = 0
        target_expert = 0

    return (
        max(0, target_id - id_kits),
        max(0, target_salvage - salvage),
        max(0, target_expert - expert),
    )


# ---------------------------------------------------------------------------
# Async merchant workflows (driven through GLOBAL_CACHE.Coroutines)
# ---------------------------------------------------------------------------


def _interact_at(x: float, y: float):
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    ok = yield from Routines.Yield.Agents.InteractWithAgentXY(x, y)
    if not ok:
        ConsoleLog(MODULE_NAME, "Merchant NPC not found, skipping.", PySystem.Console.MessageType.Warning)
        return False
    yield from Routines.Yield.wait(800)
    yield from Routines.Yield.Merchant._wait_for_trader_inventory(timeout_ms=1200, step_ms=100)
    return True


def _buy_expert_kits(count: int):
    if count <= 0:
        return
    merchant_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
    merchant_list = ItemArray.Filter.ByCondition(
        merchant_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == ModelID.Expert_Salvage_Kit.value
    )
    if not merchant_list:
        return
    bought = 0
    for _ in range(count):
        value = int(GLOBAL_CACHE.Item.Properties.GetValue(merchant_list[0])) * 2
        GLOBAL_CACHE.Trading.Merchant.BuyItem(merchant_list[0], value)
        bought += 1
    while not ActionQueueManager().IsEmpty("MERCHANT"):
        yield from Routines.Yield.wait(50)
    if bought:
        ConsoleLog(MODULE_NAME, f"Bought {bought} expert salvage kits.", PySystem.Console.MessageType.Info)


def _do_merchant_visit():
    global _busy
    if not Routines.Checks.Map.MapValid():
        _busy = False
        return
    try:
        merchant_id = _find_merchant_agent("merchant")
        if merchant_id is None:
            ConsoleLog(MODULE_NAME, "No merchant found on this map.", PySystem.Console.MessageType.Warning)
            return

        mx, my = Agent.GetXY(merchant_id)
        ok = yield from _interact_at(mx, my)
        if not ok:
            return

        id_to_buy, salvage_to_buy, expert_to_buy = _kits_to_buy()
        if id_to_buy > 0:
            yield from Routines.Yield.wait(50)
            yield from Routines.Yield.Merchant.BuyIDKits(id_to_buy, log=True)
        if salvage_to_buy > 0:
            yield from Routines.Yield.wait(50)
            yield from Routines.Yield.Merchant.BuySalvageKits(salvage_to_buy, log=True)
        if expert_to_buy > 0:
            yield from Routines.Yield.wait(50)
            yield from _buy_expert_kits(expert_to_buy)

        buckets = _classify()
        if _cfg_bool("Actions", "do_sell", True):
            sell = buckets[_Action.SELL]
            if len(sell) > 0:
                ConsoleLog(MODULE_NAME, f"Selling {len(sell)} items: {sell}", PySystem.Console.MessageType.Info)
                yield from Routines.Yield.Merchant.SellItems(sell, log=True)

        if _cfg_bool("Actions", "do_salvage", True):
            salvage = buckets[_Action.SALVAGE]
            free_slots_low = Inventory.GetFreeSlotCount() < 5
            if len(salvage) > 0 and (free_slots_low or _cfg_bool("Salvage", "always_salvage", False)):
                ConsoleLog(MODULE_NAME, f"Salvaging {len(salvage)} items: {salvage}", PySystem.Console.MessageType.Info)
                yield from Routines.Yield.Items.SalvageItems(salvage, log=True)

        visited.merchant = True
        ConsoleLog(MODULE_NAME, "Merchant visit complete.", PySystem.Console.MessageType.Success)
    finally:
        _busy = False


def _do_xunlai_visit():
    global _busy
    if not Routines.Checks.Map.MapValid():
        _busy = False
        return
    try:
        xunlai_id = _find_merchant_agent("xunlai")
        if xunlai_id is None:
            ConsoleLog(MODULE_NAME, "No Xunlai chest found on this map.", PySystem.Console.MessageType.Warning)
            return

        x, y = Agent.GetXY(xunlai_id)
        ok = yield from _interact_at(x, y)
        if not ok:
            return

        handler = AutoInventoryHandler()
        old_state = handler.module_active
        handler.module_active = False
        try:
            buckets = _classify()
            deposit = buckets[_Action.DEPOSIT]
            if _cfg_bool("Actions", "do_deposit", True) and len(deposit) > 0:
                ConsoleLog(
                    MODULE_NAME, f"Depositing {len(deposit)} items: {deposit}", PySystem.Console.MessageType.Info
                )
                yield from Routines.Yield.Items.DepositItems(deposit, log=True)
            if _cfg_bool("Deposit", "deposit_gold", True):
                keep = _cfg_int("Deposit", "keep_gold", 5000)
                yield from Routines.Yield.Items.DepositGold(keep, log=False)
        finally:
            handler.module_active = old_state
        visited.xunlai = True
        ConsoleLog(MODULE_NAME, "Xunlai visit complete.", PySystem.Console.MessageType.Success)
    finally:
        _busy = False


# ---------------------------------------------------------------------------
# Widget lifecycle
# ---------------------------------------------------------------------------


def _current_map_signature():
    if not Routines.Checks.Map.MapValid():
        return None
    return (int(Map.GetMapID()), 1 if Map.IsOutpost() else 0, 1 if Map.IsGuildHall() else 0)


def _tick():
    global _busy
    if not Routines.Checks.Map.MapValid():
        visited.reset()
        visited.map_signature = None
        return

    sig = _current_map_signature()
    if sig != visited.map_signature:
        visited.map_signature = sig
        visited.reset()

    if not _cfg_bool("Follow", "enabled", False):
        _busy = False
        return

    in_town = Map.IsOutpost() or Map.IsGuildHall()
    if not in_town:
        _busy = False
        return

    if _busy:
        return
    if not ActionQueueManager().IsEmpty("ACTION"):
        return

    need_merchant = (
        not visited.merchant
        and _cfg_bool("Visit", "visit_merchant", True)
        and (len(_classify()[_Action.SELL]) > 0 or any(n > 0 for n in _kits_to_buy()))
    )
    need_xunlai = not visited.xunlai and _cfg_bool("Visit", "visit_xunlai", True)

    if not need_merchant and not need_xunlai:
        return

    # Order: deposit junk at Xunlai first (frees slots), then sell & restock.
    if need_xunlai:
        _busy = True
        GLOBAL_CACHE.Coroutines.append(_do_xunlai_visit())
        return
    if need_merchant:
        _busy = True
        GLOBAL_CACHE.Coroutines.append(_do_merchant_visit())


_PREVIEW_CAP = 15


def _item_label(item_id: int) -> str:
    name = Item.GetName(item_id)
    if name:
        return f"{name} (#{item_id})"
    return f"(id {item_id})"


def _preview_bucket(title: str, item_ids: list[int]) -> None:
    shown = item_ids[:_PREVIEW_CAP]
    PyImGui.text(f"{title}: {len(item_ids)}")
    for item_id in shown:
        PyImGui.bullet_text(_item_label(item_id))
    if len(item_ids) > _PREVIEW_CAP:
        PyImGui.text(f"... and {len(item_ids) - _PREVIEW_CAP} more")


def draw_widget():
    global INI_KEY
    cfg = _cfg()
    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):

        enabled = cfg.get_bool("Follow", "enabled", False)
        new_enabled = PyImGui.checkbox("Enabled##refill", enabled)
        if new_enabled != enabled:
            cfg.set("Follow", "enabled", new_enabled)
            if new_enabled:
                ConsoleLog(MODULE_NAME, "Merchant Refill enabled.", PySystem.Console.MessageType.Info)
            else:
                ConsoleLog(MODULE_NAME, "Merchant Refill disabled.", PySystem.Console.MessageType.Info)

        PyImGui.separator()

        if PyImGui.collapsing_header("Visits", PyImGui.TreeNodeFlags.DefaultOpen):
            use_merchant = cfg.get_bool("Visit", "visit_merchant", True)
            nuv = PyImGui.checkbox("Visit Merchant (sell + restock)", use_merchant)
            if nuv != use_merchant:
                cfg.set("Visit", "visit_merchant", nuv)
            use_xunlai = cfg.get_bool("Visit", "visit_xunlai", True)
            nuv = PyImGui.checkbox("Visit Xunlai (deposit)", use_xunlai)
            if nuv != use_xunlai:
                cfg.set("Visit", "visit_xunlai", nuv)

            in_town = Routines.Checks.Map.MapValid() and (Map.IsOutpost() or Map.IsGuildHall())
            visited_now = "active" if (in_town and _busy) else ("idle" if in_town else "not in town")
            PyImGui.text(f"State: {visited_now}")
            PyImGui.text(f"Merchant: {'visited' if visited.merchant else 'pending'}")
            PyImGui.text(f"Xunlai: {'visited' if visited.xunlai else 'pending'}")

        PyImGui.separator()

        if PyImGui.collapsing_header("Actions", PyImGui.TreeNodeFlags.DefaultOpen):
            do_sell = cfg.get_bool("Actions", "do_sell", True)
            nds = PyImGui.checkbox("Sell items at merchant", do_sell)
            if nds != do_sell:
                cfg.set("Actions", "do_sell", nds)
            do_deposit = cfg.get_bool("Actions", "do_deposit", True)
            ndd = PyImGui.checkbox("Deposit items at Xunlai", do_deposit)
            if ndd != do_deposit:
                cfg.set("Actions", "do_deposit", ndd)
            do_salvage = cfg.get_bool("Actions", "do_salvage", True)
            nds2 = PyImGui.checkbox("Salvage items", do_salvage)
            if nds2 != do_salvage:
                cfg.set("Actions", "do_salvage", nds2)
            PyImGui.text_wrapped(
                "Disable an action to stop it while still visiting the NPC for restocking/depositing gold."
            )

        PyImGui.separator()

        if PyImGui.collapsing_header("Kits", PyImGui.TreeNodeFlags.DefaultOpen):
            id_kits, salvage, expert = _kit_counts()
            PyImGui.text(f"In inventory - ID: {id_kits}, Salvage: {salvage}, Expert: {expert}")
            ka = cfg.get_int("Kits", "keep_id_kits", 2)
            nva = PyImGui.slider_int("Keep ID Kits", ka, 0, 20)
            if nva != ka:
                cfg.set("Kits", "keep_id_kits", nva)
            kb = cfg.get_int("Kits", "keep_salvage_kits", 5)
            nvb = PyImGui.slider_int("Keep Salvage Kits", kb, 0, 20)
            if nvb != kb:
                cfg.set("Kits", "keep_salvage_kits", nvb)
            kc = cfg.get_int("Kits", "keep_expert_salvage_kits", 1)
            nvc = PyImGui.slider_int("Keep Expert Kits", kc, 0, 10)
            if nvc != kc:
                cfg.set("Kits", "keep_expert_salvage_kits", nvc)

        PyImGui.separator()

        if PyImGui.collapsing_header("Deposit", PyImGui.TreeNodeFlags.DefaultOpen):
            dep_gold = cfg.get_bool("Deposit", "deposit_gold", True)
            ndg = PyImGui.checkbox("Deposit Gold", dep_gold)
            if ndg != dep_gold:
                cfg.set("Deposit", "deposit_gold", ndg)
            keep_gold = cfg.get_int("Deposit", "keep_gold", 5000)
            nkg = PyImGui.slider_int("Keep Gold On Char", keep_gold, 0, 1000000)
            if nkg != keep_gold:
                cfg.set("Deposit", "keep_gold", nkg)

        PyImGui.separator()

        if PyImGui.collapsing_header("Salvage", 0):
            try_salvage = cfg.get_bool("Salvage", "always_salvage", False)
            nts = PyImGui.checkbox("Always salvage (else only when near-full)", try_salvage)
            if nts != try_salvage:
                cfg.set("Salvage", "always_salvage", nts)
            PyImGui.text_wrapped(
                "White weapons/items are salvaged by default; only runs when free slots are low."
            )

        PyImGui.separator()

        if PyImGui.collapsing_header("Weapon Keep Rules", 0):
            PyImGui.text_wrapped(
                "For maxed-damage weapons, the requirement tier decides disposition. "
                "'Default' uses low-req = deposit, high-req = sell."
            )
            for req in sorted(_DEFAULT_MAXED_REQ_ACTION):
                key = f"maxed_req_{req}"
                current = cfg.get_str("Weapons", key, "")
                values = ["default", "keep", "deposit", "sell"]
                idx = values.index(current.lower()) if current.lower() in values else 0
                new_idx = PyImGui.combo(f"Req {req}", idx, [v.capitalize() for v in values])
                if new_idx != idx:
                    cfg.set("Weapons", key, values[new_idx])

        PyImGui.separator()

        keep_models = cfg.get_str("KeepList", "models", "")
        nkm = PyImGui.input_text("Always keep model IDs", keep_models)
        if nkm != keep_models:
            cfg.set("KeepList", "models", nkm)
        block_models = cfg.get_str("Blocklist", "models", "")
        nbm = PyImGui.input_text("Block model IDs", block_models)
        if nbm != block_models:
            cfg.set("Blocklist", "models", nbm)
        block_types = cfg.get_str("Blocklist", "item_types", "")
        nbt = PyImGui.input_text("Block item types", block_types)
        if nbt != block_types:
            cfg.set("Blocklist", "item_types", nbt)

        PyImGui.separator()

        if PyImGui.collapsing_header("Item Preview", 0):
            buckets = _classify()
            _preview_bucket("Sell", buckets[_Action.SELL])
            _preview_bucket("Deposit", buckets[_Action.DEPOSIT])
            _preview_bucket("Salvage", buckets[_Action.SALVAGE])

        if PyImGui.button("Reset visit state"):
            visited.reset()
            ConsoleLog(MODULE_NAME, "Visit state reset.", PySystem.Console.MessageType.Info)

    ImGui.End(INI_KEY)


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("While in town or a guild hall, visits the merchant and Xunlai"
                 " chest once to sell junk, restock ID/salvage kits, and deposit"
                 " valuables when inventory gets full.")
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Port of the legacy merchant_refill_if_needed_utility")
    PyImGui.end_tooltip()


def draw():
    global initialized
    if initialized:
        draw_widget()


def _seed_defaults():
    cfg = _cfg()
    if not cfg.get_str("Blocklist", "models", ""):
        cfg.set("Blocklist", "models", " ".join(str(x) for x in _DEFAULT_MODEL_ID_BLOCK_LIST))
    if not cfg.get_str("Blocklist", "item_types", ""):
        cfg.set("Blocklist", "item_types", " ".join(str(x) for x in _DEFAULT_ITEM_TYPE_BLOCK_LIST))


def main():
    global INI_KEY, initialized, update_timer
    if not Routines.Checks.Map.MapValid():
        return
    if not INI_KEY:
        INI_KEY = _cfg().name
        if not INI_KEY:
            return
        _seed_defaults()
        initialized = True

    if update_timer.IsExpired():
        update_timer.Reset()
        _tick()


if __name__ == "__main__":
    main()