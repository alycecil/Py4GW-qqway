import json
from enum import Enum
import random
from re import DEBUG
from types import SimpleNamespace
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, ItemArray, Routines, Range, Map, Agent, Player, Inventory
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.enums_src.Model_enums import ModelID
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


    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        self.npc_visited[MerchantType.XUNLAI_CHEST] = False
        self.npc_visited[MerchantType.MERCHANT] = False
        self.npc_visited[MerchantType.RUNE_TRADER] = False
        self.npc_visited[MerchantType.RARE_MATERIAL_TRADER] = False
        self.npc_visited[MerchantType.CRAFTING_MATERIAL_TRADER] = False
        yield

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if not Map.IsOutpost(): return False
        if not Map.IsGuildHall(): return False # be discret...
        return True

    def _is_merchant_agent(self, agent_id: int) -> bool:
        """Check if the agent is a merchant by checking for merchant tags in multiple languages."""
        merchant_tags = ['Merchant', 'Marchand', 'Kauffrau']
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

    def hasItemsToMerch(self) -> bool:
        return False

    def _needsToVisit(self, merchant_type: MerchantType) -> bool:
        if merchant_type == MerchantType.MERCHANT:
            if (self.GetExpertSalvageKitsToBuy() > 0
                    or self.GetSalvageKitsToBuy() > 0
                    or self.GetIDKitsToBuy() > 0
                    or self.hasItemsToMerch()):
                if constants.DEBUG: print("I need to visit the Merchant")
                return True
        else:
            # TODO specific logic for other vendors
            return True

        # Fall though if no hits
        return False

    def needsToVisit(self, merchant_type: MerchantType) -> bool:
        if (self.should_visit_npc_config[merchant_type]
                and not self.npc_visited[merchant_type]):
            return self._needsToVisit(merchant_type)

        return False

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # Xunlai intentionally not in list for scoring.
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
            if constants.DEBUG: print(f"I need to buy {id_kits_to_buy} id kits")
            return id_kits_to_buy
        if constants.DEBUG: print("I have enough id kits")
        return 0

    def GetSalvageKitsToBuy(self):
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Salvage_Kit) #2992 model for salvage kit
        salvage_kits_to_buy = self.inventory_config.keep_salvage_kit - count_of_salvage_kits

        if salvage_kits_to_buy > 0:
            if constants.DEBUG: print(f"I need to buy {salvage_kits_to_buy} salvage kits")
            return salvage_kits_to_buy
        if constants.DEBUG: print("I have enough salvage kits")
        return salvage_kits_to_buy

    def GetExpertSalvageKitsToBuy(self):
        count_of_salvage_kits = Inventory.GetModelCount(ModelID.Expert_Salvage_Kit) #2991 model for expert salvage kit
        salvage_kits_to_buy = self.inventory_config.keep_expert_salvage_kit - count_of_salvage_kits
        if salvage_kits_to_buy > 0:
            if constants.DEBUG: print(f"I need to buy {salvage_kits_to_buy} expert salvage kits")
            return salvage_kits_to_buy
        if constants.DEBUG: print("I have enough expert salvage kits")
        return salvage_kits_to_buy

    def _visit(self, merchant_type: MerchantType) -> Generator[Any, None, None]:

        if not self.should_visit_npc_config[merchant_type]: return
        if self.npc_visited[merchant_type]: return

        target_agent_id = self._get_target(merchant_type)
        if target_agent_id is None: return

        print(f"Visiting {merchant_type.name}...")
        if constants.DEBUG: Player.ChangeTarget(target_agent_id)
        target_position : tuple[float, float] = Agent.GetXY(target_agent_id)
        if Utils.Distance(target_position, Player.GetXY()) > 150:
            path3d = yield from AutoPathing().get_path_to(target_position[0], target_position[1], smooth_by_los=True, margin=100.0, step_dist=300.0)
            path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

            yield from Routines.Yield.Movement.FollowPath(
                    path_points= path2d,
                    custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()),
                    tolerance=150,
                    log=constants.DEBUG,
                    timeout=10_000,
                    progress_callback=lambda progress: print(f"FollowPath merchant_refill_if_needed_utility: progress: {progress}") if constants.DEBUG else None,
                    custom_pause_fn=lambda: False)

        print(f"Merchant {merchant_type.name} reached.")
        yield from self.interact_with_merchant(merchant_type, target_agent_id)

        visit_duration_in_seconds = self.visit_duration_in_seconds_config[merchant_type]
        print(f"Merchant {merchant_type.name} waiting at for {visit_duration_in_seconds}s.")
        yield from custom_behavior_helpers.Helpers.wait_for(visit_duration_in_seconds * 1000)

        print(f"Merchant {merchant_type.name} wait complete.")
        self.npc_visited[merchant_type] = True

    def interact_with_merchant(self, merchant_type, target_agent_id):

        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console
        ActionQueueManager().ResetQueue("MERCHANT")

        lock_key = f"merchant_user_{Player.GetAgentID()}_{target_agent_id}"
        visit_duration_in_seconds = self.visit_duration_in_seconds_config[merchant_type]
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=visit_duration_in_seconds) == False:
            ConsoleLog("MerchantRefillIfNeededUtility", f"Merchant Locked for Player, wait {visit_duration_in_seconds} seconds", Console.MessageType.Info)
            return

        Player.ChangeTarget(target_agent_id, queue_name="MERCHANT")
        Player.Interact(target_agent_id, queue_name="MERCHANT")
        if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"Should have trade window open", Console.MessageType.Info)
        if merchant_type == MerchantType.MERCHANT:
            if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", "Starting merchant buy orders", Console.MessageType.Info)
            buy = self.GetIDKitsToBuy()

            if buy > 0:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"GetIDKitsToBuy = {buy}", Console.MessageType.Info)
                yield from Routines.Yield.Merchant.BuyIDKits(buy, constants.DEBUG, flush_queue=False)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"I have all the id kits i could want", Console.MessageType.Info)

            buy = self.GetSalvageKitsToBuy()
            if buy > 0:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"GetSalvageKitsToBuy = {buy}", Console.MessageType.Info)
                yield from Routines.Yield.Merchant.BuySalvageKits(buy, constants.DEBUG, flush_queue=False)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"I have all the regular salvage kits i could want", Console.MessageType.Info)

            buy = self.GetExpertSalvageKitsToBuy()
            if buy > 0:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"GetExpertSalvageKitsToBuy = {buy}", Console.MessageType.Info)
                yield from Routines.Yield.Merchant.BuySalvageKits(buy, constants.DEBUG, ModelID.Expert_Salvage_Kit, flush_queue=False)
            else:
                if constants.DEBUG: ConsoleLog("MerchantRefillIfNeededUtility", f"I have all the expert salvage kits i could want", Console.MessageType.Info)
        elif merchant_type == MerchantType.XUNLAI_CHEST:
            ConsoleLog("MerchantRefillIfNeededUtility", f"Opening Xunlai", Console.MessageType.Info)
            pass
        else:
            ConsoleLog("MerchantRefillIfNeededUtility", f"Unknown merchant type {merchant_type}", Console.MessageType.Info)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        # PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "should_visit_npc_config", dict_to_string(self.should_visit_npc_config))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "inventory_config", dict_to_string(self.inventory_config.__dict__))
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        # PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "should_visit_npc_config", dict_to_string(self.should_visit_npc_config))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "inventory_config", dict_to_string(self.inventory_config.__dict__))
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "should_visit_npc_config")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "inventory_config")
        print("configuration deleted")

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = f"merchant_user_{Player.GetAgentID()}"

        if not self.npc_visited[MerchantType.XUNLAI_CHEST]:
            yield from self._visit(MerchantType.XUNLAI_CHEST)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.MERCHANT]:
            if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10) == False:
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.MERCHANT)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.RUNE_TRADER]:
            if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10) == False:
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.RUNE_TRADER)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.RARE_MATERIAL_TRADER]:
            if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10) == False:
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.RARE_MATERIAL_TRADER)
            return BehaviorResult.ACTION_PERFORMED
        if not self.npc_visited[MerchantType.CRAFTING_MATERIAL_TRADER]:
            if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10) == False:
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.CRAFTING_MATERIAL_TRADER)
            return BehaviorResult.ACTION_PERFORMED

        return BehaviorResult.ACTION_SKIPPED

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
