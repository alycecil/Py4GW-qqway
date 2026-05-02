import json
from enum import Enum
import random
from re import DEBUG
from types import SimpleNamespace
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, ItemArray, Routines, Range, Map, Agent, Player, Inventory, Item
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.enums_src.Item_enums import Bags, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.inventory_managment.json_helper import string_to_dict, dict_to_string
from Sources.inventory_managment.inventory_utils import InventoryMode, InventoryUtils, InventoryUtilsConfig
from Sources.oazix.CustomBehaviors.primitives.infrastructure.persistence_locator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus


class SalvageIfNeededUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("salvage_if_needed_utility"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.INVENTORY.value+0.002),
            allowed_states=[BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE],
            utility_skill_typology=UtilitySkillTypology.INVENTORY,
            execution_strategy=UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END) # or stuck detection will make us reset each 5s...

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.INVENTORY.value)

        from Sources.inventory_managment.inventory_util_config_loader import inventory_util_config_load_json
        self.inventory_utils_config: InventoryUtilsConfig = inventory_util_config_load_json()

        self.inventory_utils: InventoryUtils = InventoryUtils()

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:

        from Sources.inventory_managment.inventory_util_config_loader import inventory_util_config_load_json
        self.inventory_utils_config: InventoryUtilsConfig = inventory_util_config_load_json()

        yield

    def get_salvageable_items(
            self,
            include_merchant_items: bool = False
    ) -> list[int]:
        '''
        Returns a list of all item IDs in the player's inventory excluding banlist items that qualify as salvagable
        '''
        my_items = []
        inventory_item_ids = self.inventory_utils.get_inventory_items(self.inventory_utils_config)
        for item_id in inventory_item_ids:

            if Item.Rarity.IsGreen(item_id):
                continue

            is_white = Item.Rarity.IsWhite(item_id)

            if is_white or Item.Usage.IsIdentified(item_id):
                if Item.Usage.IsSalvageable(item_id):
                    action_for_item: InventoryMode = self.get_action_for_item(item_id)
                    if action_for_item == InventoryMode.SALVAGE:
                        my_items.append(item_id)
                    elif include_merchant_items and (action_for_item == InventoryMode.SELL_DONT_IDENTIFY or action_for_item == InventoryMode.SELL):
                        my_items.append(item_id)

        return my_items

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if Map.IsOutpost() or Map.IsGuildHall():
            lock_key = self.generic_player_lock_key()
            if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key):
                return False # leave the inventory alone while in town, thats merchant utilities time to shine
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if Agent.IsDead(Player.GetAgentID()):
            return None

        lock_key = self.generic_player_lock_key()
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key):
            return None

        if self.inventory_utils.GetSalvageKits() > 0:
            return self.score_definition.get_score()

        ConsoleLog("SalvageIfNeededUtility", "Salvage Kits needed")

        return None

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        from Sources.inventory_managment.inventory_util_config_loader import persist_configuration_for_account
        persist_configuration_for_account(self.inventory_utils_config)

    @override
    def persist_configuration_as_global(self):
        from Sources.inventory_managment.inventory_util_config_loader import persist_configuration_as_global
        persist_configuration_as_global(self.inventory_utils_config)

    @override
    def delete_persisted_configuration(self):
        from Sources.inventory_managment.inventory_util_config_loader import delete_persisted_configuration
        delete_persisted_configuration()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = self.generic_player_lock_key()

        if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
            if constants.DEBUG: ConsoleLog("SalvageIfNeededUtility", "Could not get lock")
            yield
            return BehaviorResult.ACTION_SKIPPED

        if constants.DEBUG: ConsoleLog("SalvageIfNeededUtility", "Got lock")
        inventory_item_ids = self.get_salvageable_items()

        if inventory_item_ids is None or len(inventory_item_ids) == 0:
            if constants.DEBUG: ConsoleLog("SalvageIfNeededUtility", "Nothing to salvage")
            yield
            return BehaviorResult.ACTION_SKIPPED

        random.shuffle(inventory_item_ids)

        if constants.DEBUG: ConsoleLog("Salvager",f"Salvagables: {inventory_item_ids}")

        salvaged_something = False
        salvage_me = []

        for item_id in inventory_item_ids:

            require_materials_confirmation = Item.Rarity.IsPurple(item_id) or Item.Rarity.IsGold(item_id)

            if require_materials_confirmation:
                if constants.DEBUG: ConsoleLog("Salvager",f"I want to salvage {self.describe_item(item_id)} but it requires confirmation and I am a scaredy bot.")
                continue
            else:
                salvage_kit = Inventory.GetFirstSalvageKit(use_lesser=True, model_id=ModelID.Salvage_Kit.value)
                if salvage_kit == 0:
                    if constants.DEBUG: ConsoleLog("AutoSalvage", "No Salvage Kit found in inventory.",)
                    break

                # ActionQueueManager().AddAction("ACTION", Inventory.SalvageItem, item_id, salvage_kit)

                if constants.DEBUG: ConsoleLog("Salvager",f"I want to salvage {self.describe_item(item_id)}")

                salvage_me.append(item_id)

                salvaged_something = True
                break

        if salvaged_something:
            ConsoleLog("Salvager",f"Salvaging {len(inventory_item_ids)} items")
            # yield from Routines.Yield.Items.SalvageItems(salvage_me, log=constants.DEBUG)
            yield
            return BehaviorResult.ACTION_PERFORMED
        else:
            ConsoleLog("SalvageIfNeededUtility", "Nothing we can salvage")
            yield
            return BehaviorResult.ACTION_SKIPPED

    def generic_player_lock_key(self):
        from Sources.oazix.CustomBehaviors.primitives.helpers.lock_key_helper import LockKeyHelper
        return LockKeyHelper.generic_player_lock_key()

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug UI for merchant refill utility"""

        if PyImGui.collapsing_header("View Full Inventory", 0):

            # Configuration section
            PyImGui.text_colored("Configuration:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            if PyImGui.begin_table("inventory_utils_config", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
                PyImGui.table_setup_column("Item name", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("action_for_item", PyImGui.TableColumnFlags.WidthFixed, 150)

                PyImGui.table_headers_row()

                inventory_item_ids = self.inventory_utils.get_inventory_items(self.inventory_utils_config)

                for item_id in inventory_item_ids:
                    action_for_item: InventoryMode = self.get_action_for_item(item_id)

                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    name = f"Item #{item_id}"
                    PyImGui.text(name)
                    PyImGui.text(str(self.describe_item(item_id)))

                    PyImGui.table_next_column()
                    if action_for_item == InventoryMode.SALVAGE:
                        PyImGui.text_colored("Salvage", (1.0, 1.0, 0.0, 1.0))  # Yellow
                        # TODO Button
                    else:
                        PyImGui.text(str(action_for_item.name))

                PyImGui.end_table()

            PyImGui.spacing()

            # Status section
            PyImGui.separator()

        if PyImGui.begin_table("inventory_utils_config_salvage", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
            PyImGui.table_setup_column("Item name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("action_for_item", PyImGui.TableColumnFlags.WidthFixed, 150)
            PyImGui.table_headers_row()

            inventory_item_ids = self.get_salvageable_items()

            for item_id in inventory_item_ids:
                action_for_item: InventoryMode = self.get_action_for_item(item_id)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                name = f"Item #{item_id}"
                PyImGui.text(name)
                PyImGui.text(str(self.describe_item(item_id)))

                PyImGui.table_next_column()
                if action_for_item == InventoryMode.SALVAGE:
                    PyImGui.text_colored("Salvage", (1.0, 1.0, 0.0, 1.0))  # Yellow
                    # TODO Button
                else:
                    PyImGui.text(str(action_for_item))

            PyImGui.end_table()

    def get_action_for_item(self, item_id) -> InventoryMode:
        action_for_item = self.inventory_utils.get_action_for_item(self.inventory_utils_config, item_id)

        if Inventory.GetFreeSlotCount() <= 2:
            if (action_for_item == InventoryMode.SELL_DONT_IDENTIFY or
                    action_for_item == InventoryMode.SELL):
                return InventoryMode.SALVAGE

        return action_for_item

    def describe_item(self, item_id) -> str:
        prefix, suffix, inherent, parsed_modifiers = self.inventory_utils.get_mods_from_item(item_id)

        # --- Construct name ---
        name_parts = []

        name = GLOBAL_CACHE.Item.GetName(item_id)
        name_parts.append(f"{name} #{item_id}")

        name_parts.append(str(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))

        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        blocklisted = model_id in self.inventory_utils_config.block_list_model_id
        postFix = " (Blocklisted)" if blocklisted else ""
        name_parts.append(f"model={model_id}{postFix}")

        name_parts.append(parsed_modifiers.summary())

        return "\r\n".join(name_parts)


