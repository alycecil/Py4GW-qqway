"""
Guild Hall Depositor widget.

Detects when a guild hall (or a configured outpost map such as the Great
Temple of Balthazar, map 248, or Embark Beach, map 857) finishes loading,
then runs a one-shot sequence: wait a configurable delay (3-10 s), click
Identify All in the inventory, wait a short gap, deposit all materials at
the Xunlai chest, top up existing Xunlai storage stacks from the inventory
(stackable non-consumables only, never creating new stacks), then deposit
gold down to the keep amount (10 plat).

Runs once per load; re-arms whenever the character leaves the target map
(or zones through another one). A manual "Run now" button is available for
testing outside a target map.
"""

from typing import Generator, Optional

import PyImGui
import PyInventory
import PySystem

from Py4GWCoreLib import GLOBAL_CACHE, ImGui, Map, Routines
from Py4GWCoreLib.enums_src.Item_enums import MAX_STACK_SIZE, Bags, ItemType
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Settings import Settings
from Sources.inventory_managment.ui_manipulators.deposit_materials import DepositMaterials
from Sources.inventory_managment.ui_manipulators.identify_all import IdentifyAllItems

MODULE_NAME = "Guild Hall Depositor"
MODULE_ICON = "Assets/Textures/Module_Icons/Compass+.png"
WIDGET_KEY = "Widgets/Guild Wars/Guild Hall Depositor"

INI_PATH = "Widgets/GuildHallDepositor"
INI_FILENAME = "GuildHallDepositor.ini"

_MIN_DELAY_S = 3
_MAX_DELAY_S = 10
_DEFAULT_DELAY_MS = 5000
_MIN_GAP_S = 1
_MAX_GAP_S = 10
_DEFAULT_GAP_MS = 3000
_DEFAULT_KEEP_GOLD = 10_000  # 10 plat (1 plat = 1000 gold)
_DEFAULT_EXTRA_MAP_IDS = "248 857"
_DEFAULT_TOPUP_STACKS = True

_STORAGE_TOPUP_BAGS: tuple[Bags, ...] = (
    Bags.Storage1,
    Bags.Storage2,
    Bags.Storage3,
    Bags.Storage4,
    Bags.Storage5,
    Bags.Storage6,
    Bags.Storage7,
    Bags.Storage8,
    Bags.Storage9,
    Bags.Storage10,
    Bags.Storage11,
    Bags.Storage12,
    Bags.Storage13,
    Bags.Storage14,
)

# Item types treated as consumables for the top-up pass. Usage.IsUsable is
# the primary signal; the explicit type check covers scrolls even when the
# usable flag is ever stale on a snapshot.
_CONSUMABLE_TOPUP_SKIP_TYPES = frozenset({ItemType.Usable, ItemType.Scroll})

initialized = False
INI_KEY = ""
_enabled = False
_armed = False
_running = False
_stage = "idle"
_routine: Generator[None, None, None] | None = None


def _cfg() -> Settings:
    return Settings(f"{INI_PATH}/{INI_FILENAME}", "account")


def _set_enabled(value: bool) -> None:
    global _enabled
    _enabled = value
    _cfg().set("Main", "enabled", value)


def _target_map_ids() -> set[int]:
    raw = _cfg().get_str("Target", "map_ids", _DEFAULT_EXTRA_MAP_IDS)
    ids: set[int] = set()
    for part in raw.replace(",", " ").split():
        if part.isdigit():
            ids.add(int(part))
    ids.discard(0)
    return ids


def _in_target_map() -> bool:
    if not Map.IsMapReady():
        return False
    if not Map.IsOutpost():
        return False
    if not bool(GLOBAL_CACHE.Party.IsPartyLoaded()):
        return False
    if Map.IsGuildHall():
        return True
    return Map.GetMapID() in _target_map_ids()


def _start_sequence() -> None:
    global _running, _routine, _stage
    _running = True
    _routine = _sequence()
    _stage = "scheduled"
    ConsoleLog(
        MODULE_NAME,
        "Target map loaded - starting identify/deposit sequence.",
        Console.MessageType.Info,
    )


def _cancel_sequence(reason: str) -> None:
    global _running, _routine, _stage
    if _running:
        ConsoleLog(MODULE_NAME, reason, Console.MessageType.Info)
    _running = False
    _routine = None
    _stage = "idle"


def _bag_entry_item_id(entry: object) -> int:
    if hasattr(entry, "item_id"):
        try:
            return int(getattr(entry, "item_id"))
        except (TypeError, ValueError):
            return 0
    if isinstance(entry, dict):
        try:
            return int(entry.get("item_id", 0))
        except (TypeError, ValueError):
            return 0
    return 0


def _dye_key(item_id: int, model_id: int) -> Optional[int]:
    if int(model_id) != int(ModelID.Vial_Of_Dye.value):
        return None
    try:
        dye_info = GLOBAL_CACHE.Item.Dye.GetInfo(int(item_id))
        return int(dye_info.dye1.ToInt())
    except Exception:
        return None


def _is_topup_consumable(item_id: int) -> bool:
    try:
        if bool(GLOBAL_CACHE.Item.Usage.IsUsable(int(item_id))):
            return True
    except Exception:
        pass
    try:
        item_type_value, _ = GLOBAL_CACHE.Item.GetItemType(int(item_id))
        return ItemType(int(item_type_value)) in _CONSUMABLE_TOPUP_SKIP_TYPES
    except Exception:
        return False


def _storage_free_space(model_id: int, dye_key: Optional[int]) -> int:
    """Free space across existing partial storage stacks for one model."""
    if int(model_id) <= 0:
        return 0
    free = 0
    for bag_enum in _STORAGE_TOPUP_BAGS:
        try:
            bag = PyInventory.Bag(int(bag_enum.value), str(bag_enum.name))
            entries = bag.GetItems()
        except Exception:
            continue
        for entry in entries or ():
            storage_id = _bag_entry_item_id(entry)
            if storage_id <= 0:
                continue
            try:
                if int(GLOBAL_CACHE.Item.GetModelID(storage_id)) != int(model_id):
                    continue
            except Exception:
                continue
            if dye_key is not None and _dye_key(storage_id, model_id) != dye_key:
                continue
            try:
                qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(storage_id))
            except Exception:
                continue
            if 0 < qty < int(MAX_STACK_SIZE):
                free += int(MAX_STACK_SIZE) - qty
    return max(0, int(free))


def _deposit_stack_topups() -> Generator[None, None, None]:
    """Top up existing Xunlai stacks from inventory; never opens new slots."""
    from Py4GWCoreLib.Inventory import Inventory as _Inventory

    if not _Inventory.IsStorageOpen():
        _Inventory.OpenXunlaiWindow()
        yield from Routines.Yield.wait(1000)
    if not _Inventory.IsStorageOpen():
        ConsoleLog(MODULE_NAME, "Storage not open - skipping stack top-up.", Console.MessageType.Warning)
        return

    try:
        inventory_ids: list[int] = list(GLOBAL_CACHE.Inventory.GetAllInventoryItemIds())
    except Exception:
        return

    topped = 0
    moved_qty = 0
    seen_models: set[tuple[int, Optional[int]]] = set()
    for item_id in inventory_ids:
        if not _in_target_map():
            return
        try:
            item_id = int(item_id)
        except (TypeError, ValueError):
            continue
        if item_id <= 0:
            continue
        try:
            if not bool(GLOBAL_CACHE.Item.Properties.IsStackable(item_id)):
                continue
            if bool(GLOBAL_CACHE.Item.Properties.IsCustomized(item_id)):
                continue
            if bool(GLOBAL_CACHE.Item.Type.IsMaterial(item_id)):
                continue  # Deposit All Materials owns Material Storage
            if bool(GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id)):
                continue
            item_type_value, _ = GLOBAL_CACHE.Item.GetItemType(item_id)
            item_type = ItemType(int(item_type_value))
            if item_type in (ItemType.Gold_Coin, ItemType.Quest_Item):
                continue
        except Exception:
            continue
        if _is_topup_consumable(item_id):
            continue
        try:
            model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
            qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        except Exception:
            continue
        if model_id <= 0 or qty <= 0:
            continue
        key = (model_id, _dye_key(item_id, model_id))
        if key in seen_models:
            continue  # one deposit per model per pass; partial fill covers it
        free = _storage_free_space(model_id, key[1])
        if free <= 0:
            continue
        to_move = min(int(qty), int(free))
        if to_move <= 0:
            continue
        try:
            moved = bool(GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id, ammount=to_move))
        except Exception:
            continue
        if moved:
            seen_models.add(key)
            topped += 1
            moved_qty += to_move
            yield from Routines.Yield.wait(350)

    try:
        from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

        while not ActionQueueManager().IsEmpty("ACTION"):
            yield from Routines.Yield.wait(350)
            if not _in_target_map():
                return
    except Exception:
        pass

    if topped > 0:
        ConsoleLog(
            MODULE_NAME,
            f"Topped up {topped} storage stack(s) with {moved_qty} item(s).",
            Console.MessageType.Info,
        )


def _sequence() -> Generator[None, None, None]:
    global _stage
    cfg = _cfg()
    delay_ms = cfg.get_int("Sequence", "initial_delay_ms", _DEFAULT_DELAY_MS)
    gap_ms = cfg.get_int("Sequence", "gap_ms", _DEFAULT_GAP_MS)

    _stage = f"identify in {max(delay_ms, 0) / 1000.0:.0f}s"
    yield from Routines.Yield.wait(delay_ms, break_on_map_transition=True)
    if not _in_target_map():
        return

    _stage = "identify all"
    yield from IdentifyAllItems().IdentifyAll()

    _stage = f"deposit in {max(gap_ms, 0) / 1000.0:.0f}s"
    yield from Routines.Yield.wait(gap_ms, break_on_map_transition=True)
    if not _in_target_map():
        return

    _stage = "deposit all"
    yield from DepositMaterials().DepositMaterials()

    if cfg.get_bool("Deposit", "topup_stacks", _DEFAULT_TOPUP_STACKS) and _in_target_map():
        _stage = "top-up stacks"
        yield from _deposit_stack_topups()

    if cfg.get_bool("Deposit", "deposit_gold", True) and _in_target_map():
        keep = cfg.get_int("Deposit", "keep_gold", _DEFAULT_KEEP_GOLD)
        on_char = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        if on_char > keep:
            _stage = "deposit gold"
            ConsoleLog(
                MODULE_NAME,
                f"Gold on character {on_char} above keep {keep} - depositing.",
                Console.MessageType.Info,
            )
            yield from Routines.Yield.Items.DepositGold(keep, log=True)

    ConsoleLog(MODULE_NAME, "Identify + deposit sequence complete.", Console.MessageType.Info)


def main():
    global initialized, INI_KEY, _enabled, _armed, _running, _stage, _routine

    if not Routines.Checks.Map.MapValid():
        _cancel_sequence("Sequence cancelled - map not valid.")
        _armed = False
        return

    if not INI_KEY:
        INI_KEY = _cfg().name
        if not INI_KEY:
            return
        initialized = True
        _enabled = _cfg().get_bool("Main", "enabled", False)

    if not _enabled:
        _cancel_sequence("Sequence cancelled - widget disabled.")
        _armed = False
        return

    in_target = _in_target_map()

    if _running:
        if _routine is None:
            _running = False
            return
        if not in_target:
            _cancel_sequence("Sequence cancelled - left the target map.")
            return
        try:
            next(_routine)
        except StopIteration:
            _routine = None
            _running = False
            _armed = True
            _stage = "done"
        return

    if in_target:
        if not _armed:
            _armed = True
            _start_sequence()
    else:
        _armed = False
        _stage = "idle"


def draw_widget():
    global INI_KEY, _enabled, _running
    cfg = _cfg()

    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        new_enabled = PyImGui.checkbox("Enabled##ghd", _enabled)
        if new_enabled != _enabled:
            _set_enabled(new_enabled)
            ConsoleLog(
                MODULE_NAME,
                "Guild Hall Depositor enabled."
                if new_enabled
                else "Guild Hall Depositor disabled.",
                Console.MessageType.Info,
            )

        PyImGui.separator()

        PyImGui.text(f"State: {_stage}")
        PyImGui.text(f"Map: {Map.GetMapID()}")
        char_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        PyImGui.text(f"Gold on character: {char_gold:,}")
        PyImGui.text(
            f"Target loaded: {'yes' if _in_target_map() else 'no'}"
        )
        PyImGui.text(f"Routine: {'running' if _running else 'idle'}")

        PyImGui.separator()

        delay_s = cfg.get_int("Sequence", "initial_delay_ms", _DEFAULT_DELAY_MS) // 1000
        delay_s = max(_MIN_DELAY_S, min(_MAX_DELAY_S, delay_s))
        new_delay = PyImGui.slider_int("Delay after load (s)", delay_s, _MIN_DELAY_S, _MAX_DELAY_S)
        if new_delay != delay_s:
            cfg.set("Sequence", "initial_delay_ms", new_delay * 1000)

        gap_s = cfg.get_int("Sequence", "gap_ms", _DEFAULT_GAP_MS) // 1000
        gap_s = max(_MIN_GAP_S, min(_MAX_GAP_S, gap_s))
        new_gap = PyImGui.slider_int("Delay between actions (s)", gap_s, _MIN_GAP_S, _MAX_GAP_S)
        if new_gap != gap_s:
            cfg.set("Sequence", "gap_ms", new_gap * 1000)

        PyImGui.separator()

        dep_gold = cfg.get_bool("Deposit", "deposit_gold", True)
        new_dep = PyImGui.checkbox("Deposit Gold", dep_gold)
        if new_dep != dep_gold:
            cfg.set("Deposit", "deposit_gold", new_dep)

        topup = cfg.get_bool("Deposit", "topup_stacks", _DEFAULT_TOPUP_STACKS)
        new_topup = PyImGui.checkbox("Top-up storage stacks", topup)
        if new_topup != topup:
            cfg.set("Deposit", "topup_stacks", new_topup)

        keep_gold = cfg.get_int("Deposit", "keep_gold", _DEFAULT_KEEP_GOLD)
        new_keep = PyImGui.slider_int("Keep Gold On Char", keep_gold, 0, 100000)
        if new_keep != keep_gold:
            cfg.set("Deposit", "keep_gold", new_keep)

        PyImGui.separator()

        map_ids = cfg.get_str("Target", "map_ids", _DEFAULT_EXTRA_MAP_IDS)
        new_ids = PyImGui.input_text("Extra map IDs", map_ids)
        if new_ids != map_ids:
            cfg.set("Target", "map_ids", new_ids)

        PyImGui.separator()

        if PyImGui.button("Run now"):
            _armed = True
            if not _running:
                _start_sequence()
            else:
                ConsoleLog(MODULE_NAME, "Sequence already running.", Console.MessageType.Info)

        PyImGui.separator()

        PyImGui.text_wrapped(
            "On each target map load (any guild hall, plus the extra map IDs "
            "above): waits, clicks Identify All in the inventory, waits again, "
            "deposits all materials at the Xunlai chest, tops up existing "
            "Xunlai stacks from stackable non-consumables (usable items and "
            "scrolls stay on the character; no new storage slots are used), "
            "then deposits gold down to the keep amount (default 10 plat). "
            "Runs once per load."
        )

    ImGui.End(INI_KEY)


def draw():
    global initialized
    if initialized:
        draw_widget()


if __name__ == "__main__":
    main()