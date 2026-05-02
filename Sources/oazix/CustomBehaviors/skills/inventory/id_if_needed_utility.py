import random
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Map, Agent, Player, Item
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Sources.inventory_managment.inventory_utils import InventoryUtils
from Sources.inventory_managment.config.inventory_utils_config import InventoryMode, InventoryUtilsConfig
from Sources.inventory_managment.ui_manipulators.identify_all import IdentifyAllItems
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus


class IdIfNeededUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("id_if_needed_utility"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.INVENTORY.value+0.003),
            allowed_states=[BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE],
            utility_skill_typology=UtilitySkillTypology.INVENTORY,
            execution_strategy=UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END) # or stuck detection will make us reset each 5s...

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.INVENTORY.value)

        from Sources.inventory_managment.config.inventory_util_config_loader import inventory_util_config_load_json
        self.inventory_utils_config: InventoryUtilsConfig = inventory_util_config_load_json()

        self.inventory_utils: InventoryUtils = InventoryUtils()

        self.clicked_recently = False
        self.movement_check_timer : ThrottledTimer = ThrottledTimer(3000+random.randint(100, 5000))

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:

        from Sources.inventory_managment.config.inventory_util_config_loader import inventory_util_config_load_json
        self.inventory_utils_config: InventoryUtilsConfig = inventory_util_config_load_json()

        self.clicked_recently = False
        self.movement_check_timer = ThrottledTimer(3000+random.randint(100, 5000))
        yield

    def get_identifiable_items(
            self
    ) -> list[int]:
        '''
        Returns a list of all item IDs in the player's inventory excluding banlist items that qualify as salvagable
        '''
        my_items = []
        inventory_item_ids = self.inventory_utils.get_inventory_items(self.inventory_utils_config)
        for item_id in inventory_item_ids:

            if Item.Rarity.IsGreen(item_id):
                continue

            if not Item.Usage.IsIdentified(item_id):
                action_for_item: InventoryMode = self.get_action_for_item(item_id)
                if action_for_item != InventoryMode.SELL_DONT_IDENTIFY and action_for_item != InventoryMode.KEEP_DONT_IDENTIFY:
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

        if self.movement_check_timer.IsExpired():
            if self.inventory_utils.GetIDKits() > 0:
                return self.score_definition.get_score()
            else:
                ConsoleLog("IdIfNeededUtility", "Kits needed")
                self.movement_check_timer = ThrottledTimer(3000+random.randint(100, 35000))
                return None
        else:
            return None

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        from Sources.inventory_managment.config.inventory_util_config_loader import persist_configuration_for_account
        persist_configuration_for_account(self.inventory_utils_config)

    @override
    def persist_configuration_as_global(self):
        from Sources.inventory_managment.config.inventory_util_config_loader import persist_configuration_as_global
        persist_configuration_as_global(self.inventory_utils_config)

    @override
    def delete_persisted_configuration(self):
        from Sources.inventory_managment.config.inventory_util_config_loader import delete_persisted_configuration
        delete_persisted_configuration()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if constants.DEBUG: ConsoleLog("IdIfNeededUtility", "Got lock")

        yield from IdentifyAllItems().IdentifyAll()
        self.clicked_recently = True
        self.movement_check_timer.Reset()
        self.movement_check_timer = ThrottledTimer(3000+random.randint(100, 365000))

        if Map.IsOutpost() or Map.IsGuildHall():
            inventory_item_ids = self.get_identifiable_items()

            if inventory_item_ids is None or len(inventory_item_ids) == 0:
                if constants.DEBUG: ConsoleLog("IdIfNeededUtility", "Nothing to salvage")
                yield
                return BehaviorResult.ACTION_SKIPPED

            random.shuffle(inventory_item_ids)

            if constants.DEBUG: ConsoleLog("IdIfNeededUtility",f"Salvagables: {inventory_item_ids}")

            identify_something = False
            id_me = []

            for item_id in inventory_item_ids:
                if constants.DEBUG: ConsoleLog("IdIfNeededUtility",f"I want to id {self.describe_item(item_id)}")

                id_me.append(item_id)

                identify_something = True
                break

            if identify_something:
                ConsoleLog("IdIfNeededUtility",f"Identifying {len(inventory_item_ids)} items")
                yield from Routines.Yield.Items.IdentifyItems(id_me, log=constants.DEBUG)
                yield
                return BehaviorResult.ACTION_PERFORMED
            else:
                ConsoleLog("IdIfNeededUtility", "Nothing we can id")
                yield
                return BehaviorResult.ACTION_SKIPPED

        else:
            ConsoleLog("IdIfNeededUtility", "Nothing we can id")
            yield
            return BehaviorResult.ACTION_SKIPPED

    def generic_player_lock_key(self):
        from Sources.oazix.CustomBehaviors.primitives.helpers.lock_key_helper import LockKeyHelper
        return LockKeyHelper.generic_player_lock_key()

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Display debug UI for merchant refill utility"""

        if PyImGui.begin_table("inventory_utils_config_identidfy", 2, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg)):
            PyImGui.table_setup_column("Item name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("action_for_item", PyImGui.TableColumnFlags.WidthFixed, 150)
            PyImGui.table_headers_row()

            inventory_item_ids = self.get_identifiable_items()

            for item_id in inventory_item_ids:

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                name = f"Item #{item_id}"
                PyImGui.text(name)
                PyImGui.text(str(self.describe_item(item_id)))

                PyImGui.table_next_column()
                PyImGui.text_colored("Identify", (1.0, 1.0, 0.0, 1.0))  # Yellow

            PyImGui.end_table()

    def get_action_for_item(self, item_id) -> InventoryMode:
        action_for_item = self.inventory_utils.get_action_for_item(self.inventory_utils_config, item_id)
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


