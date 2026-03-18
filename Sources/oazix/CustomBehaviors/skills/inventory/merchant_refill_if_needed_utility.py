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
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from .inventory_utils import InventoryUtilsConfig, InventoryUtils, InventoryMode
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


class MerchantType(Enum):
    MERCHANT = 1
    RUNE_TRADER = 2
    RARE_MATERIAL_TRADER = 3
    CRAFTING_MATERIAL_TRADER = 4
    XUNLAI_CHEST = 5


class InventoryConfig:
    def __init__(self, leave_free_slots = 3, keep_id_kit = 2, keep_salvage_kit = 5, keep_expert_salvage_kit = 1):
        self.leave_free_slots = leave_free_slots
        self.keep_id_kit = keep_id_kit
        self.keep_salvage_kit = keep_salvage_kit
        self.keep_expert_salvage_kit = keep_expert_salvage_kit


class MerchantRefillIfNeededUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("merchant_refill_if_needed_utility"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.INVENTORY.value),
            allowed_states=[BehaviorState.IDLE],
            utility_skill_typology=UtilitySkillTypology.INVENTORY,
            execution_strategy=UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END) # or stuck detection will make us reset each 5s...

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.INVENTORY.value)
        self.should_visit_merchant:bool = False
        self.should_visit_rune_trader:bool = False
        self.should_visit_rare_material_trader:bool = False
        self.should_visit_crafting_material_trader:bool = False

        self.should_visit_npc_config:dict[MerchantType, bool] = {
            MerchantType.XUNLAI_CHEST: True,
            MerchantType.MERCHANT: True,
            MerchantType.RUNE_TRADER: False,
            MerchantType.RARE_MATERIAL_TRADER: False,
            MerchantType.CRAFTING_MATERIAL_TRADER: False,
        }
        # this needs some indirection for primitives to enum
        # data: str | None = PersistenceLocator().skills.read(self.custom_skill.skill_name, "should_visit_npc_config")
        # if data is not None:
        #     self.should_visit_npc_config: dict[MerchantType, bool] = string_to_dict(data, self.should_visit_npc_config)
        # else:
        #     self.should_visit_npc_config: dict[MerchantType, bool] = self.should_visit_npc_config

        self.visit_duration_in_seconds_config:dict[MerchantType, int] = {
            MerchantType.MERCHANT: 25,
            MerchantType.RUNE_TRADER: 15,
            MerchantType.RARE_MATERIAL_TRADER: 10,
            MerchantType.CRAFTING_MATERIAL_TRADER: 13,
            MerchantType.XUNLAI_CHEST: 1,
        }

        self.npc_visited:dict[MerchantType, bool] = {
            MerchantType.XUNLAI_CHEST: False,
            MerchantType.MERCHANT: False,
            MerchantType.RUNE_TRADER: False,
            MerchantType.RARE_MATERIAL_TRADER: False,
            MerchantType.CRAFTING_MATERIAL_TRADER: False,
        }

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

        data: str | None = PersistenceLocator().skills.read(self.custom_skill.skill_name, "inventory_config")
        if data is not None:
            self.inventory_config: InventoryConfig = string_to_dict(data)
        else:
            self.inventory_config: InventoryConfig = InventoryConfig()

        data: str | None = PersistenceLocator().skills.read("my_inventory_config", "inventory_config")
        if data is not None:
            self.inventory_utils_config: InventoryUtilsConfig = string_to_dict(data)
        else:
            self.inventory_utils_config: InventoryUtilsConfig = InventoryUtilsConfig()

        self.inventory_utils: InventoryUtils = InventoryUtils()

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        # give us some eepy time
        lock_key = self.generic_player_lock_key()
        CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10)

        data: str | None = PersistenceLocator().skills.read("my_inventory_config", "inventory_config")
        if data is not None:
            self.inventory_utils_config: InventoryUtilsConfig = string_to_dict(data)
        else:
            self.inventory_utils_config: InventoryUtilsConfig = InventoryUtilsConfig()

        self.npc_visited[MerchantType.XUNLAI_CHEST] = False
        self.npc_visited[MerchantType.MERCHANT] = False
        self.npc_visited[MerchantType.RUNE_TRADER] = False
        self.npc_visited[MerchantType.RARE_MATERIAL_TRADER] = False
        self.npc_visited[MerchantType.CRAFTING_MATERIAL_TRADER] = False

        yield

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if Map.IsOutpost() or Map.IsGuildHall(): return True # be discret...
        return False

    def _is_merchant_agent(self, agent_id: int) -> bool:
        """Check if the agent is a merchant by checking for merchant tags in multiple languages."""
        merchant_tags = ['Merchant', 'Marchand', 'Kauffrau', 'Cyrus [Merchant]',]
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)

    def _is_xunlai_chest(self, agent_id: int) -> bool:
        merchant_tags = ['Xunlai Chest']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)

    def _is_rune_trader_agent(self, agent_id: int) -> bool:
        merchant_tags = ['Rune Trader']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)
    
    def _is_rare_material_trader_agent(self, agent_id: int) -> bool:
        merchant_tags = ['Rare Material Trader']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)
    
    def _is_crafter_material_trader_agent(self, agent_id: int) -> bool:
        merchant_tags = ['Crafting Material Trader']
        agent_name = Agent.GetNameByID(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)

    def _get_target(self, merchant_type: MerchantType) -> int | None:
        agent_ids = AgentArray.GetNPCMinipetArray()
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, Player.GetXY(), Range.Compass.value)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: Agent.IsAlive(agent_id) and Agent.IsValid(agent_id))

        if merchant_type == MerchantType.XUNLAI_CHEST:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_xunlai_chest)
        if merchant_type == MerchantType.MERCHANT:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_merchant_agent)
        if merchant_type == MerchantType.RUNE_TRADER:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_rune_trader_agent)
        if merchant_type == MerchantType.RARE_MATERIAL_TRADER:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_rare_material_trader_agent)
        if merchant_type == MerchantType.CRAFTING_MATERIAL_TRADER:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_crafter_material_trader_agent)

        if len(agent_ids) == 0: return None
        return agent_ids[0]

    def get_action_for_item(self, item_id) -> InventoryMode:
        action_for_item = self.inventory_utils.get_action_for_item(self.inventory_utils_config, item_id)

        if Inventory.GetFreeSlotCount() <= 2:
            if (action_for_item == InventoryMode.SELL_DONT_IDENTIFY or
                    action_for_item == InventoryMode.SELL):
                return InventoryMode.SALVAGE

        return action_for_item

    def include_salvage_items(self) -> bool:
        free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
        return free_slots < 5  # Todo configurable

    def hasItemsToMerch(self) -> bool:
        return len(self.get_items_to_sell(self.include_salvage_items())) > 0

    def get_items_to_deposit(self):
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        my_items = []
        inventory_item_ids = self.inventory_utils.get_inventory_items(self.inventory_utils_config)
        if constants.DEBUG: ConsoleLog("get_items_to_deposit", f"Inventory List filtered = {inventory_item_ids}", Console.MessageType.Info)
        for my_item_id in inventory_item_ids:

            action_for_item: InventoryMode = self.inventory_utils.get_action_for_item(self.inventory_utils_config, my_item_id)
            if action_for_item == InventoryMode.DEPOSIT:
                my_items.append(my_item_id)
            else:
                if constants.DEBUG: ConsoleLog("get_items_to_deposit", f"Ignoring item #{my_item_id} its a {action_for_item}", Console.MessageType.Info)

        return my_items

    def get_items_to_sell(self, include_salvage_items: bool = False) -> list[int]:
        my_items = []
        inventory_item_ids = self.inventory_utils.get_inventory_items(self.inventory_utils_config)
        for item_id in inventory_item_ids:

            if Item.Rarity.IsGreen(item_id):
                continue

            is_white = Item.Rarity.IsWhite(item_id)
            is_blue = Item.Rarity.IsBlue(item_id)

            if is_white or is_blue:
                if GLOBAL_CACHE.Item.Properties.GetValue(item_id) > 0:
                    action_for_item: InventoryMode = self.inventory_utils.get_action_for_item(self.inventory_utils_config, item_id)
                    if action_for_item == InventoryMode.SELL_DONT_IDENTIFY:
                        my_items.append(item_id)
                    if action_for_item == InventoryMode.SELL:
                        my_items.append(item_id)
                    elif include_salvage_items and (action_for_item == InventoryMode.SALVAGE):
                        my_items.append(item_id)
        return my_items

    def _needsToVisit(self, merchant_type: MerchantType) -> bool:
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        if merchant_type == MerchantType.MERCHANT:
            if (self.GetExpertSalvageKitsToBuy() > 0
                    or self.GetSalvageKitsToBuy() > 0
                    or self.GetIDKitsToBuy() > 0
                    or self.hasItemsToMerch()):
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", "I need to visit the Merchant", Console.MessageType.Info)
                return True
        elif merchant_type == MerchantType.XUNLAI_CHEST:
            return True
        else:
            # TODO specific logic for other vendors
            return True

        # Fall though if no hits
        return True

    def needsToVisit(self, merchant_type: MerchantType) -> bool:
        if (self.should_visit_npc_config[merchant_type]
                and not self.npc_visited[merchant_type]):
            return self._needsToVisit(merchant_type)

        return False

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        lock_key = self.generic_player_lock_key()
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key):
            return None
        if self.needsToVisit(MerchantType.XUNLAI_CHEST):
            return self.score_definition.get_score()
        if self.needsToVisit(MerchantType.MERCHANT):
            return self.score_definition.get_score()
        if self.needsToVisit(MerchantType.RUNE_TRADER):
            return self.score_definition.get_score()
        if self.needsToVisit(MerchantType.RARE_MATERIAL_TRADER):
            return self.score_definition.get_score()
        if self.needsToVisit(MerchantType.CRAFTING_MATERIAL_TRADER):
            return self.score_definition.get_score()
        return None

    def GetIDKitsToBuy(self):
        count_of_id_kits = Inventory.GetModelCount(ModelID.Superior_Identification_Kit) #5899 model for ID kit
        id_kits_to_buy = self.inventory_config.keep_id_kit - count_of_id_kits
        if id_kits_to_buy > 0:
            return id_kits_to_buy
        return 0

    def GetSalvageKitsToBuy(self):
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Salvage_Kit) #2992 model for salvage kit
        salvage_kits_to_buy = self.inventory_config.keep_salvage_kit - count_of_salvage_kits

        if salvage_kits_to_buy > 0:
            return salvage_kits_to_buy
        return salvage_kits_to_buy

    def GetExpertSalvageKitsToBuy(self):
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Expert_Salvage_Kit) #2991 model for expert salvage kit
        salvage_kits_to_buy = self.inventory_config.keep_expert_salvage_kit - count_of_salvage_kits
        if salvage_kits_to_buy > 0:
            return salvage_kits_to_buy
        return salvage_kits_to_buy

    def _visit(self, merchant_type: MerchantType) -> Generator[Any, None, None]:

        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console

        if not self.should_visit_npc_config[merchant_type]: return
        if self.npc_visited[merchant_type]: return

        target_agent_id = self._get_target(merchant_type)
        if target_agent_id is None: return

        ConsoleLog("MerchantRefillIfNeededUtility", f"Visiting {merchant_type.name}...", Console.MessageType.Info)
        if constants.DEBUG: Player.ChangeTarget(target_agent_id)
        target_position : tuple[float, float] = Agent.GetXY(target_agent_id)
        if Utils.Distance(target_position, Player.GetXY()) > 150:
            path3d = yield from AutoPathing().get_path_to(target_position[0], target_position[1], smooth_by_los=True, margin=100.0, step_dist=322.0)
            path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

            yield from Routines.Yield.Movement.FollowPath(
                    path_points= path2d,
                    custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()),
                    tolerance=150,
                    log=constants.DEBUG,
                    timeout=45_000,
                    progress_callback=lambda progress: ConsoleLog("MerchantRefillIfNeededUtility", f"FollowPath merchant_refill_if_needed_utility: progress: {progress}", Console.MessageType.Info) if constants.DEBUG else None,
                    custom_pause_fn=lambda: False)

        if Utils.Distance(target_position, Player.GetXY()) <= 150:
            ConsoleLog("MerchantRefillIfNeededUtility", f"Merchant {merchant_type.name} reached.", Console.MessageType.Info)
            yield from self.interact_with_merchant(merchant_type, target_agent_id)

            visit_duration_in_seconds = self.visit_duration_in_seconds_config[merchant_type]
            ConsoleLog("MerchantRefillIfNeededUtility", f"Merchant {merchant_type.name} waiting at for {visit_duration_in_seconds}s.", Console.MessageType.Info)
            milliseconds = visit_duration_in_seconds * random.randint(800, 1600)
            yield from custom_behavior_helpers.Helpers.wait_for(milliseconds)

            ConsoleLog("MerchantRefillIfNeededUtility", f"Merchant {merchant_type.name} wait complete.", Console.MessageType.Info)
            self.npc_visited[merchant_type] = True
        else:
            ConsoleLog("MerchantRefillIfNeededUtility", f"Merchant {merchant_type.name} was too far for the lock time, try again.", Console.MessageType.Info)

    def interact_with_merchant(self, merchant_type, target_agent_id):

        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console

        lock_key = self._lock_key(target_agent_id)
        visit_duration_in_seconds = self.visit_duration_in_seconds_config[merchant_type]
        if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key,timeout_seconds=visit_duration_in_seconds):
            ConsoleLog("MerchantRefillIfNeededUtility", f"Merchant Locked for Player, wait {visit_duration_in_seconds} seconds", Console.MessageType.Info)
            return

        ActionQueueManager().ResetQueue("MERCHANT")

        agent_x, agent_y = Agent.GetXY(target_agent_id)
        yield from Routines.Yield.Agents.InteractWithAgentXY(agent_x, agent_y)
        yield from Routines.Yield.Merchant._wait_for_trader_inventory(timeout_ms=1000, step_ms=100)

        if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"Should have trade window open", Console.MessageType.Info)
        if merchant_type == MerchantType.MERCHANT:
            if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", "Starting merchant buy orders", Console.MessageType.Info)
            buy = self.GetIDKitsToBuy()

            if buy > 0:
                ConsoleLog("MerchantRefillIfNeededUtility", f"GetIDKitsToBuy = {buy}", Console.MessageType.Info)
                yield from Routines.Yield.Merchant.BuyIDKits(buy, constants.DEBUG, flush_queue=False)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"I have all the id kits i could want", Console.MessageType.Info)

            buy = self.GetSalvageKitsToBuy()
            if buy > 0:
                ConsoleLog("MerchantRefillIfNeededUtility", f"GetSalvageKitsToBuy = {buy}", Console.MessageType.Info)
                yield from Routines.Yield.Merchant.BuySalvageKits(buy, constants.DEBUG, flush_queue=False)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"I have all the regular salvage kits i could want", Console.MessageType.Info)

            buy = self.GetExpertSalvageKitsToBuy()
            if buy > 0:
                ConsoleLog("MerchantRefillIfNeededUtility", f"GetExpertSalvageKitsToBuy = {buy}", Console.MessageType.Info)
                yield from Routines.Yield.Merchant.BuySalvageKits(buy, constants.DEBUG, ModelID.Expert_Salvage_Kit, flush_queue=False)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"I have all the expert salvage kits i could want", Console.MessageType.Info)

            sell = self.get_items_to_sell(self.include_salvage_items())
            if len(sell) > 0:
                ConsoleLog("MerchantRefillIfNeededUtility", f"get_items_to_sell = {sell}", Console.MessageType.Info)
                yield from Routines.Yield.Merchant.SellItems(sell)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"Nothing to sell", Console.MessageType.Info)
        elif merchant_type == MerchantType.XUNLAI_CHEST:
            ConsoleLog("MerchantRefillIfNeededUtility", f"Opening Xunlai", Console.MessageType.Info)

            deposit = self.get_items_to_deposit()
            if len(deposit) > 0:
                ConsoleLog("MerchantRefillIfNeededUtility", f"get_items_to_deposit = {deposit}", Console.MessageType.Info)
                yield from Routines.Yield.Items.DepositItems(deposit,constants.DEBUG)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"Nothing to sell", Console.MessageType.Info)

            from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
            inventory_handler = AutoInventoryHandler()
            current_state =  inventory_handler.module_active
            inventory_handler.module_active = False
            yield from inventory_handler.IdentifyItems()
            yield from inventory_handler.DepositItemsAuto()
            yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)
            inventory_handler.module_active = current_state
        else:
            ConsoleLog("MerchantRefillIfNeededUtility", f"Unknown merchant type {merchant_type}", Console.MessageType.Info)

    def _lock_key(self, target_agent_id):
        lock_key = f"merchant_user_{Player.GetAgentID()}_{target_agent_id}"
        return lock_key

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        # PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "should_visit_npc_config", dict_to_string(self.should_visit_npc_config))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "inventory_config", dict_to_string(self.inventory_config.__dict__))
        ConsoleLog("MerchantRefillIfNeededUtility", "configuration saved for account", Console.MessageType.Info)

    @override
    def persist_configuration_as_global(self):
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        # PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "should_visit_npc_config", dict_to_string(self.should_visit_npc_config))
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "inventory_config", dict_to_string(self.inventory_config.__dict__))
        ConsoleLog("MerchantRefillIfNeededUtility", "configuration saved as global", Console.MessageType.Info)

    @override
    def delete_persisted_configuration(self):
        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "should_visit_npc_config")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "inventory_config")
        ConsoleLog("MerchantRefillIfNeededUtility", "configuration deleted", Console.MessageType.Info)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = self.generic_player_lock_key()

        if not self.npc_visited[MerchantType.XUNLAI_CHEST]:
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.XUNLAI_CHEST)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.MERCHANT]:
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.MERCHANT)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.RUNE_TRADER]:
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.RUNE_TRADER)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.RARE_MATERIAL_TRADER]:
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.RARE_MATERIAL_TRADER)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.CRAFTING_MATERIAL_TRADER]:
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.CRAFTING_MATERIAL_TRADER)
            return BehaviorResult.ACTION_PERFORMED

        return BehaviorResult.ACTION_SKIPPED

    def generic_player_lock_key(self):
        lock_key = f"merchant_user_{Player.GetAgentID()}"
        return lock_key

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug UI for merchant refill utility"""

        if PyImGui.collapsing_header("Merchant Refill Status", PyImGui.TreeNodeFlags.DefaultOpen):

            # Configuration section
            PyImGui.text_colored("Configuration:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            if PyImGui.begin_table("merchant_config", 3, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
                PyImGui.table_setup_column("Merchant Type")
                PyImGui.table_setup_column("Should Visit")
                PyImGui.table_setup_column("Visit Duration (s)")
                PyImGui.table_headers_row()

                for merchant_type in MerchantType:
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(merchant_type.name.replace('_', ' ').title())

                    PyImGui.table_next_column()
                    should_visit = self.should_visit_npc_config[merchant_type]
                    new_value = PyImGui.checkbox(f"##should_visit_{merchant_type.name}", should_visit)
                    if new_value != should_visit:
                        self.should_visit_npc_config[merchant_type] = new_value

                    PyImGui.table_next_column()
                    PyImGui.text(str(self.visit_duration_in_seconds_config[merchant_type]))

                PyImGui.end_table()

            PyImGui.spacing()

            # Dailies Section
            if PyImGui.tree_node("Dailies"):
                for label, attr in [
                    ("Keep ID Kits", "keep_id_kit"),
                    ("Keep Salvage Kits", "keep_salvage_kit"),
                    ("Keep Expert Salvage Kits", "keep_expert_salvage_kit"),
                    ("Leave Empty Inventory Slots", "leave_free_slots")
                ]:
                    setattr(self.inventory_config, attr,
                            PyImGui.input_int(label, getattr(self.inventory_config, attr)))
                PyImGui.tree_pop()

            # Status section
            PyImGui.text_colored("Visit Status:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            if PyImGui.begin_table("merchant_status", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
                PyImGui.table_setup_column("Merchant Type")
                PyImGui.table_setup_column("Visited")
                PyImGui.table_headers_row()

                for merchant_type in MerchantType:
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(merchant_type.name.replace('_', ' ').title())

                    PyImGui.table_next_column()
                    visited = self.npc_visited[merchant_type]
                    if visited:
                        PyImGui.text_colored("✓ Visited", (0.0, 1.0, 0.0, 1.0))  # Green
                    else:
                        PyImGui.text_colored("✗ Not Visited", (1.0, 0.5, 0.0, 1.0))  # Orange

                PyImGui.end_table()

            PyImGui.spacing()

            # Additional debug info
            PyImGui.text_colored("Debug Info:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()
            PyImGui.bullet_text(f"Is Outpost: {Map.IsOutpost()}")
            PyImGui.bullet_text(f"Is Guild Hall: {Map.IsGuildHall()}")

            # Show nearby merchants
            PyImGui.spacing()
            PyImGui.text_colored("Nearby Merchants:", (1.0, 1.0, 0.0, 1.0))  # Yellow
            PyImGui.separator()

            for merchant_type in MerchantType:
                agent_id = self._get_target(merchant_type)
                if agent_id is not None:
                    target_pos = Agent.GetXY(agent_id)
                    player_pos = Player.GetXY()
                    distance = Utils.Distance(target_pos, player_pos)
                    PyImGui.bullet_text(f"{merchant_type.name}: (ID: {agent_id}, dist: {distance:.0f})")
                else:
                    PyImGui.bullet_text(f"{merchant_type.name}: Not found")
            # Status section
            PyImGui.separator()

        if PyImGui.begin_table("inventory_config_salvage", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
            PyImGui.table_setup_column("Item name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("action_for_item", PyImGui.TableColumnFlags.WidthFixed, 150)
            PyImGui.table_headers_row()

            inventory_item_ids = self.get_items_to_deposit()

            for inv_item_id in inventory_item_ids:
                action_for_item: InventoryMode = self.get_action_for_item(inv_item_id)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                name = f"Item #{inv_item_id}"
                PyImGui.text(name)
                PyImGui.text(str(self.describe_item(inv_item_id)))

                PyImGui.table_next_column()
                PyImGui.text_colored("Deposit", (1.0, 1.0, 0.0, 1.0))  # Yellow

            inventory_item_ids = self.get_items_to_sell(self.include_salvage_items())

            for inv_item_id in inventory_item_ids:
                action_for_item: InventoryMode = self.get_action_for_item(inv_item_id)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                name = f"Item #{inv_item_id}"
                PyImGui.text(name)
                PyImGui.text(str(self.describe_item(inv_item_id)))

                PyImGui.table_next_column()
                PyImGui.text_colored("Sell", (1.0, 1.0, 0.0, 1.0))  # Yellow~

            PyImGui.end_table()

    def describe_item(self, item_id) -> str:
        prefix, suffix, inherent, parsed_modifiers = self.inventory_utils.get_mods_from_item(item_id)

        # --- Construct name ---
        name_parts = []

        name = GLOBAL_CACHE.Item.GetName(item_id)
        name_parts.append(f"{name} #{item_id}")

        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        blocklisted = model_id in self.inventory_utils_config.block_list_model_id
        postFix = " (Blocklisted)" if blocklisted else ""
        name_parts.append(f"model={model_id}{postFix}")

        name_parts.append(parsed_modifiers.summary())

        return " \n".join(name_parts)


# TODO move to common lib
def dict_to_string(data):
    """
    Convert to a JSON string.
    Ensures non-ASCII characters are preserved.
    """
    return json.dumps(data, ensure_ascii=False)


def string_to_dict(data_str, default_value=None, object_hook=lambda d: SimpleNamespace(**d)):
    """
    Convert a JSON string back
    Includes error handling for invalid JSON.
    """
    if not isinstance(data_str, str):
        print("Input must be a string.")
        return default_value
    try:
        result = json.loads(data_str, object_hook=object_hook)
        return result
    except json.JSONDecodeError as e:
        print(f"Invalid JSON string: {e}")
        return default_value
