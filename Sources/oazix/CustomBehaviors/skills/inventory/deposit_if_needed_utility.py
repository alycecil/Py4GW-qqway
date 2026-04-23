import json
from enum import Enum
import random
from re import DEBUG
from types import SimpleNamespace
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, ItemArray, Routines, Range, Map, Agent, Player, Inventory, Item, \
    PyUIManager
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
from .merchant_refill_if_needed_utility import MerchantType


class DepositIfNeededUtility(CustomSkillUtilityBase):
    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("deposit_if_needed_utility"),
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
            MerchantType.XUNLAI_CHEST: True
        }

        self.visit_duration_in_seconds_config:dict[MerchantType, int] = {
            MerchantType.XUNLAI_CHEST: 1,
        }

        self.npc_visited:dict[MerchantType, bool] = {
            MerchantType.XUNLAI_CHEST: False,
        }

        if Map.IsOutpost() or Map.IsGuildHall():
            self.npc_visited[MerchantType.XUNLAI_CHEST] = False

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

        self.inventory_utils: InventoryUtils = InventoryUtils()

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        # give us some eepy time
        lock_key = self.generic_player_lock_key()
        timeout_seconds: int = random.randint(5, 26)

        if Map.IsGuildHall():
            self.npc_visited[MerchantType.XUNLAI_CHEST] = False
        elif Map.IsOutpost():
            self.npc_visited[MerchantType.XUNLAI_CHEST] = False
            pass



        from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False

        yield from inventory_handler.DepositMaterials()
        inventory_handler.module_active = current_state

        yield

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if Map.IsOutpost() or Map.IsGuildHall(): return True # be discret...
        return False


    def needsToVisit(self, merchant_type: MerchantType) -> bool:
        if (self.should_visit_npc_config[merchant_type]
                and not self.npc_visited[merchant_type]):
            return True

        return False

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.needsToVisit(MerchantType.XUNLAI_CHEST):
            return self.score_definition.get_score()
        return None

    def _visit(self, merchant_type: MerchantType) -> Generator[Any, None, None]:
        yield from self.interact_with_merchant(merchant_type)

    def interact_with_merchant(self, merchant_type):

        from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console

        ActionQueueManager().ResetQueue("MERCHANT")

        if constants.DEBUG: ConsoleLog("DepositIfNeededUtility", f"Should have trade window open", Console.MessageType.Info)

        if merchant_type == MerchantType.XUNLAI_CHEST:
            ConsoleLog("DepositIfNeededUtility", f"Opening Xunlai", Console.MessageType.Info)

            from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
            inventory_handler = AutoInventoryHandler()
            current_state =  inventory_handler.module_active
            inventory_handler.module_active = False

            yield from inventory_handler.DepositMaterials()
            yield from inventory_handler.IdentifyItems()
            yield from inventory_handler.DepositItemsAuto()
            yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)
            inventory_handler.module_active = current_state


    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = self.generic_player_lock_key()

        if not self.npc_visited[MerchantType.XUNLAI_CHEST]:
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=10):
                return BehaviorResult.ACTION_SKIPPED
            yield from self._visit(MerchantType.XUNLAI_CHEST)

        return BehaviorResult.ACTION_SKIPPED

    def generic_player_lock_key(self):
        from Sources.oazix.CustomBehaviors.primitives.helpers.lock_key_helper import LockKeyHelper
        return LockKeyHelper.generic_player_lock_key()


