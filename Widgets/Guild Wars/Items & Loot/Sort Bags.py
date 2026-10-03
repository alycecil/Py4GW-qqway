"""
Sort Bags widget.

Manual "Sort Inventory" and "Sort Storage" buttons built on the owning
frenkeyLib sort surfaces: the plan comes from
``Sources.frenkeyLib.ItemHandling.bag_sort.BagSortPlanner`` (the same
planner behind the ItemManager preview), so this widget never owns its own
ordering logic.

Weapon ordering restores the legacy Alice's Inventory Manager behavior
(``alice/custom-behaviors`` ``BTNodes.Bags.SortBags``): exact item type
first, then requirement level (highest first), then attribute (attributed
weapons before unattributed, then by attribute). Requirement and attribute
are ``SortingConfig.SortField`` members, so any other consumer can compose
the same order.
"""

from typing import Generator, Optional

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, ImGui, Map, Routines
from Py4GWCoreLib.enums_src.Item_enums import INVENTORY_BAGS, STORAGE_BAGS, Bags
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Settings import Settings
from Sources.frenkeyLib.global_configs.SortingConfig import (
    BagSortPlan,
    SortArgument,
    SortDirection,
    SortField,
    Sorter,
    SortingConfig,
)
from Sources.frenkeyLib.ItemHandling.bag_sort import BagSortPlanner

MODULE_NAME = "Sort Bags"

INI_PATH = "Widgets/SortBags"
INI_FILENAME = "SortBags.ini"

_DEFAULT_CONS_FIRST = True

_SORT_INVENTORY_BAGS: tuple[Bags, ...] = tuple(INVENTORY_BAGS)
_SORT_STORAGE_BAGS: tuple[Bags, ...] = tuple(STORAGE_BAGS)

_MOVE_WAIT_MS = 75
_DRAIN_WAIT_MS = 350

_running = False
_stage = "idle"
_routine: Generator[None, None, None] | None = None
_last_result = ""


def _cfg() -> Settings:
    return Settings(f"{INI_PATH}/{INI_FILENAME}", "account")


# Front-pinned models, in tier order. Restores the legacy Alice's Inventory
# Manager overrides (``alice/custom-behaviors`` ``BTNodes.Bags.SortBags``):
# combo consumables, party consumables, proofs, tomes, then currency.
_CONS_FIRST_MODEL_NAMES: tuple[str, ...] = (
    "Grail_Of_Might",
    "Armor_Of_Salvation",
    "Essence_Of_Celerity",
    "War_Supplies",
    "Lunar_Fortune_2007_Pig",
    "Lunar_Fortune_2008_Rat",
    "Lunar_Fortune_2009_Ox",
    "Lunar_Fortune_2010_Tiger",
    "Lunar_Fortune_2011_Rabbit",
    "Lunar_Fortune_2012_Dragon",
    "Lunar_Fortune_2013_Snake",
    "Lunar_Fortune_2014_Horse",
    "Lunar_Fortune_2015_Sheep",
    "Lunar_Fortune_2016_Monkey",
    "Lunar_Fortune_2017_Rooster",
    "Lunar_Fortune_2018_Dog",
    "Birthday_Cupcake",
    "Candy_Apple",
    "Candy_Corn",
    "Golden_Egg",
    "Slice_Of_Pumpkin_Pie",
    "Proof_Of_Legend",
    "Proof_Of_Triumph",
    "Assassin_Elite_Tome",
    "Dervish_Elite_Tome",
    "Elementalist_Elite_Tome",
    "Mesmer_Elite_Tome",
    "Monk_Elite_Tome",
    "Necromancer_Elite_Tome",
    "Paragon_Elite_Tome",
    "Ranger_Elite_Tome",
    "Ritualist_Elite_Tome",
    "Warrior_Elite_Tome",
    "Assassin_Tome",
    "Dervish_Tome",
    "Elementalist_Tome",
    "Mesmer_Tome",
    "Monk_Tome",
    "Necromancer_Tome",
    "Paragon_Tome",
    "Ranger_Tome",
    "Ritualist_Tome",
    "Warrior_Tome",
    "Gold_Zaishen_Coin",
    "Silver_Zaishen_Coin",
    "Copper_Zaishen_Coin",
    "Armbrace_Of_Truth",
    "Glob_Of_Ectoplasm",
    "Zaishen_Key",
    "Lockpick",
)


def _cons_first_model_ids() -> list[int]:
    """Tier-ordered model ids; skips names missing from the current enums."""
    model_ids: list[int] = []
    for name in _CONS_FIRST_MODEL_NAMES:
        member = getattr(ModelID, name, None)
        if member is None:
            continue
        try:
            model_ids.append(int(member.value))
        except (AttributeError, TypeError, ValueError):
            continue
    return model_ids


def _weapon_aware_sorter(cons_first: bool = _DEFAULT_CONS_FIRST) -> Sorter:
    """Type, then requirement (highest first), then attribute.

    Mirrors the legacy ``method_setup`` key minus its dead ``InventoryUtils``
    dependency: exact item type groups weapons by type, requirement sorts
    descending, and attribute sorts attributed-before-unattributed then by
    attribute value. With ``cons_first``, the legacy front-pinned models
    (combo/party consumables, proofs, tomes, currency) sort before
    everything via a ``ModelId`` custom-order argument.
    """
    arguments: list[SortArgument] = []
    if cons_first and (pinned := _cons_first_model_ids()):
        arguments.append(SortArgument(SortField.ModelId, direction=SortDirection.Ascending, custom_order=pinned))
    arguments.extend(
        [
            SortArgument(SortField.ItemType, direction=SortDirection.Ascending),
            SortArgument(SortField.Requirement, direction=SortDirection.Descending),
            SortArgument(SortField.Attribute, direction=SortDirection.Ascending),
            SortArgument(SortField.Rarity, direction=SortDirection.Descending),
            SortArgument(SortField.ModelId, direction=SortDirection.Ascending),
            SortArgument(SortField.Value, direction=SortDirection.Descending),
            SortArgument(SortField.Quantity, direction=SortDirection.Descending),
            SortArgument(SortField.Id, direction=SortDirection.Ascending),
        ]
    )
    return Sorter(arguments)


def _planned_layout(bags: tuple[Bags, ...], cons_first: bool = _DEFAULT_CONS_FIRST) -> BagSortPlan:
    """Plan with the weapon-aware sorter without persisting it.

    ``SortingConfig`` is a process-wide singleton shared with ItemManager,
    so the custom sorter is swapped in only for the synchronous plan call
    and the previous sorter is restored before returning.
    """
    config = SortingConfig()
    previous = config.default_sorter
    config.default_sorter = _weapon_aware_sorter(cons_first)
    try:
        return BagSortPlanner.GetBagSortPlan(list(bags), config)
    finally:
        config.default_sorter = previous


def _sort_sequence(
    bags: tuple[Bags, ...], label: str, needs_storage: bool, cons_first: bool = _DEFAULT_CONS_FIRST
) -> Generator[None, None, None]:
    global _stage, _last_result
    _stage = f"{label}: opening storage"
    if needs_storage:
        if not Map.IsOutpost():
            _last_result = f"{label}: storage sort needs an outpost."
            ConsoleLog(MODULE_NAME, _last_result, Console.MessageType.Warning)
            return
        if not Inventory.IsStorageOpen():
            Inventory.OpenXunlaiWindow()
            yield from Routines.Yield.wait(1000)
        if not Inventory.IsStorageOpen():
            _last_result = f"{label}: Xunlai storage would not open."
            ConsoleLog(MODULE_NAME, _last_result, Console.MessageType.Warning)
            return

    _stage = f"{label}: planning"
    plan = _planned_layout(bags, cons_first)
    for warning in plan.warnings:
        ConsoleLog(MODULE_NAME, f"{label}: {warning}", Console.MessageType.Warning)

    moves = [
        entry
        for entry in plan.entries
        if entry.item is not None
        and entry.item.is_valid
        and (entry.source_bag != entry.bag or entry.source_slot != entry.slot)
    ]
    if not moves:
        _last_result = f"{label}: already sorted."
        _stage = "idle"
        ConsoleLog(MODULE_NAME, _last_result, Console.MessageType.Info)
        return

    _stage = f"{label}: moving 0/{len(moves)}"
    for index, entry in enumerate(moves):
        item = entry.item
        if item is None:
            continue
        quantity = int(getattr(item, "quantity", 1) or 1)
        GLOBAL_CACHE.Inventory.MoveItem(int(item.id), int(entry.bag.value), int(entry.slot), max(1, quantity))
        _stage = f"{label}: moving {index + 1}/{len(moves)}"
        yield from Routines.Yield.wait(_MOVE_WAIT_MS)

    try:
        from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

        while not ActionQueueManager().IsEmpty("ACTION"):
            yield from Routines.Yield.wait(_DRAIN_WAIT_MS)
    except Exception:
        pass

    _last_result = f"{label}: moved {len(moves)} item(s)."
    _stage = "idle"
    ConsoleLog(MODULE_NAME, _last_result, Console.MessageType.Info)


def _start(label: str, bags: tuple[Bags, ...], needs_storage: bool, cons_first: bool) -> None:
    global _running, _routine, _stage
    _running = True
    _stage = f"{label}: starting"
    _routine = _sort_sequence(bags, label, needs_storage, cons_first)
    ConsoleLog(MODULE_NAME, f"{label} started.", Console.MessageType.Info)


def _stop() -> None:
    global _running, _routine, _stage
    _running = False
    _routine = None
    _stage = "idle"


def main() -> None:
    global _running, _routine, _stage
    if not Routines.Checks.Map.MapValid():
        _stop()
        return
    if not _running or _routine is None:
        _running = False
        return
    try:
        next(_routine)
    except StopIteration:
        _routine = None
        _running = False
        if _stage != "idle":
            _stage = "done"


def draw_widget() -> None:
    cfg = _cfg()
    if ImGui.Begin("sort_bags", MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text(f"State: {_stage}")
        if _last_result:
            PyImGui.text_wrapped(_last_result)

        PyImGui.separator()

        cons_first = cfg.get_bool("Sort", "cons_first", _DEFAULT_CONS_FIRST)
        new_cons_first = PyImGui.checkbox("Consumables first", cons_first)
        if new_cons_first != cons_first:
            cfg.set("Sort", "cons_first", new_cons_first)
            cons_first = new_cons_first

        if _running:
            if PyImGui.button("Stop"):
                _stop()
                ConsoleLog(MODULE_NAME, "Sort stopped.", Console.MessageType.Info)
        else:
            if PyImGui.button("Sort Inventory"):
                _start("Sort Inventory", _SORT_INVENTORY_BAGS, needs_storage=False, cons_first=cons_first)
            PyImGui.same_line(0, -1)
            if PyImGui.button("Sort Storage"):
                _start("Sort Storage", _SORT_STORAGE_BAGS, needs_storage=True, cons_first=cons_first)

        PyImGui.separator()

        PyImGui.text_wrapped(
            "Orders each bag with consumables, proofs, tomes and currency "
            "first, then by item type, weapon requirement (highest first), "
            "attribute, rarity and value. Storage sorting needs an outpost "
            "with Xunlai open; inventory sorting works anywhere. Moves run "
            "paced through the action queue."
        )

    ImGui.End("sort_bags")


def draw() -> None:
    draw_widget()


if __name__ == "__main__":
    main()
