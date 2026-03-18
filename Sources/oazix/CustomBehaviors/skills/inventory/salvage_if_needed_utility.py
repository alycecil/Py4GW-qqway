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
from Sources.alice_sources.inventory.inventory_utils import InventoryUtilsConfig, InventoryUtils, InventoryMode
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
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
            score_definition=ScoreStaticDefinition(CommonScore.INVENTORY.value),
            allowed_states=[BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE],
            utility_skill_typology=UtilitySkillTypology.INVENTORY,
            execution_strategy=UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END) # or stuck detection will make us reset each 5s...

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.INVENTORY.value)

        data: str | None = PersistenceLocator().skills.read("my_inventory_config", "inventory_config")
        if data is not None:
            from Sources.oazix.CustomBehaviors.skills.inventory.merchant_refill_if_needed_utility import string_to_dict
            self.inventory_config: InventoryUtilsConfig = string_to_dict(data)
        else:
            self.inventory_config: InventoryUtilsConfig = InventoryUtilsConfig()

        self.inventory_utils: InventoryUtils = InventoryUtils()

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        # give us some eepy time
        lock_key = self.generic_player_lock_key()
        CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10)

        data: str | None = PersistenceLocator().skills.read("my_inventory_config", "inventory_config")
        if data is not None:
            from Sources.oazix.CustomBehaviors.skills.inventory.merchant_refill_if_needed_utility import string_to_dict
            self.inventory_config: InventoryUtilsConfig = string_to_dict(data)
        else:
            self.inventory_config: InventoryUtilsConfig = InventoryUtilsConfig()

        yield

    def get_salvageable_items(
            self,
            include_merchant_items: bool = False
    ) -> list[int]:
        '''
        Returns a list of all item IDs in the player's inventory excluding banlist items that qualify as salvagable
        '''
        my_items = []
        inventory_item_ids = self.inventory_utils.get_inventory_items(self.inventory_config)
        for item_id in inventory_item_ids:
            item_instance = Item.item_instance(item_id)

            if Item.Rarity.IsGreen(item_id):
                continue

            is_white = Item.Rarity.IsWhite(item_id)

            if is_white or item_instance.is_identified:
                if item_instance.is_salvageable:
                    action_for_item: InventoryMode = self.get_action_for_item(item_id, item_instance)
                    if action_for_item == InventoryMode.SALVAGE:
                        my_items.append(item_id)
                    elif include_merchant_items and (action_for_item == InventoryMode.SELL_DONT_IDENTIFY or action_for_item == InventoryMode.SELL):
                        my_items.append(item_id)

        return my_items

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if Map.IsOutpost() or Map.IsGuildHall():
            return False # leave the inventory alone while in town, thats merchant utilities time to shine
        return True

    def salvage_something(self) -> bool:
        inventory_item_ids = self.get_salvageable_items()

        if inventory_item_ids is None or len(inventory_item_ids) == 0:
            return False

        random.shuffle(inventory_item_ids)

        ConsoleLog("Salvager",f"Salvagables: {inventory_item_ids}")

        for item_id in inventory_item_ids:
            item_instance = Item.item_instance(item_id)

            require_materials_confirmation = Item.Rarity.IsPurple(item_id) or Item.Rarity.IsGold(item_id)

            if require_materials_confirmation:
                ConsoleLog("Salvager",f"I want to salvage {self.describe_item(item_instance)} but it requires confirmation")
                continue
            else:
                salvage_kit = Inventory.GetFirstSalvageKit(use_lesser=True, model_id=ModelID.Salvage_Kit.value)
                if salvage_kit == 0:
                    ConsoleLog("AutoSalvage", "No Salvage Kit found in inventory.",)
                    return False

                # ActionQueueManager().AddAction("ACTION", Inventory.SalvageItem, item_id, salvage_kit)

                ConsoleLog("Salvager",f"I want to salvage {self.describe_item(item_instance)} with salvage_kit={salvage_kit}")

                return True

        #if constants.DEBUG:
        ConsoleLog("Salvager",f"Nothing to salvage")
        return False

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
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        from Sources.oazix.CustomBehaviors.skills.inventory.merchant_refill_if_needed_utility import dict_to_string
        PersistenceLocator().skills.write_for_account("my_inventory_config", "inventory_config", dict_to_string(self.inventory_config.__dict__))
        ConsoleLog("SalvageIfNeededUtility", "configuration saved for account", Console.MessageType.Info)

    @override
    def persist_configuration_as_global(self):
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        from Sources.oazix.CustomBehaviors.skills.inventory.merchant_refill_if_needed_utility import dict_to_string
        PersistenceLocator().skills.write_global("my_inventory_config", "inventory_config", dict_to_string(self.inventory_config.__dict__))
        ConsoleLog("SalvageIfNeededUtility", "configuration saved as global", Console.MessageType.Info)

    @override
    def delete_persisted_configuration(self):
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        PersistenceLocator().skills.delete("my_inventory_config", "inventory_config")
        ConsoleLog("SalvageIfNeededUtility", "configuration deleted", Console.MessageType.Info)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = self.generic_player_lock_key()

        if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
            ConsoleLog("SalvageIfNeededUtility", "Could not get lock")
            yield
            return BehaviorResult.ACTION_SKIPPED

        ConsoleLog("SalvageIfNeededUtility", "Got lock")

        salvaged_something = self.salvage_something()
        if salvaged_something:
            yield
            return BehaviorResult.ACTION_PERFORMED
        else:
            ConsoleLog("SalvageIfNeededUtility", "Nothing to salvage")
            yield
            return BehaviorResult.ACTION_SKIPPED

    def generic_player_lock_key(self):
        lock_key = f"inventory_{Player.GetAgentID()}"
        return lock_key

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug UI for merchant refill utility"""

        if PyImGui.collapsing_header("View Full Inventory", 0):

            # Configuration section
            PyImGui.text_colored("Configuration:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            if PyImGui.begin_table("inventory_config", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
                PyImGui.table_setup_column("Item name")
                PyImGui.table_setup_column("action_for_item")
                PyImGui.table_headers_row()

                inventory_item_ids = self.inventory_utils.get_inventory_items(self.inventory_config)

                for item_id in inventory_item_ids:
                    item_instance = Item.item_instance(item_id)
                    action_for_item: InventoryMode = self.get_action_for_item(item_id, item_instance)

                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    name = item_instance.name
                    name = f"{name} #{item_instance.item_id}"
                    PyImGui.text(name)
                    PyImGui.text(str(self.describe_item(item_instance)))

                    PyImGui.table_next_column()
                    if action_for_item == InventoryMode.SALVAGE:
                        PyImGui.text_colored("Salvage", (1.0, 1.0, 0.0, 1.0))  # Yellow
                        # TODO Button
                    else:
                        PyImGui.text(str(action_for_item))

                PyImGui.end_table()

            PyImGui.spacing()

            # Status section
            PyImGui.separator()

        if PyImGui.begin_table("inventory_config_salvage", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
            PyImGui.table_setup_column("Item name")
            PyImGui.table_setup_column("action_for_item")
            PyImGui.table_headers_row()

            inventory_item_ids = self.get_salvageable_items()

            for item_id in inventory_item_ids:
                item_instance = Item.item_instance(item_id)
                action_for_item: InventoryMode = self.get_action_for_item(item_id, item_instance)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                name = item_instance.name
                name = f"{name} #{item_instance.item_id}"
                PyImGui.text(name)
                PyImGui.text(str(self.describe_item(item_instance)))

                PyImGui.table_next_column()
                if action_for_item == InventoryMode.SALVAGE:
                    PyImGui.text_colored("Salvage", (1.0, 1.0, 0.0, 1.0))  # Yellow
                    # TODO Button
                else:
                    PyImGui.text(str(action_for_item))

            PyImGui.end_table()

    def get_action_for_item(self, item_id, item_instance) -> InventoryMode:
        action_for_item = self.inventory_utils.get_action_for_item(self.inventory_config, item_id, item_instance)

        if Inventory.GetFreeSlotCount() <= 2:
            if (action_for_item == InventoryMode.SELL_DONT_IDENTIFY or
                    action_for_item == InventoryMode.SELL):
                return InventoryMode.SALVAGE

        return action_for_item

    def describe_item(self, item_instance) -> str:
        prefix, suffix, inherent, parsed_modifiers = self.inventory_utils.get_mods_from_item(item_instance)

        # --- Construct name ---
        name_parts = []

        name = item_instance.name
        name_parts.append(f"{name} #{item_instance.item_id}")

        name_parts.append(str(item_instance.quantity))

        blocklisted = item_instance.model_id in self.inventory_config.block_list_model_id
        postFix = " (Blocklisted)" if blocklisted else ""
        name_parts.append(f"model={item_instance.model_id}{postFix}")

        if prefix:
            name_parts.append(f'| {prefix}')

        if suffix:
            name_parts.append(f"| {suffix}")

        if inherent:
            name_parts.append(f"| {inherent}")

        name_parts.append(parsed_modifiers.summary())

        return " \n".join(name_parts)


