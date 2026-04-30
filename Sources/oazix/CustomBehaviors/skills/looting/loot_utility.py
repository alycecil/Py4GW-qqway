import math
from typing import Any, Generator, override

import PyImGui
import Py4GW
import os
import json

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Party, Routines, Range, Player
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig, ThrottledTimer, Utils
from Py4GWCoreLib.enums import SharedCommandType
from Py4GWCoreLib.enums_src.Py4GW_enums import Console
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.cooldown_timer import CooldownTimer
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.parties.memory_cache_manager import MemoryCacheManager
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

from Py4GWCoreLib import ModelID

loot_filter_singleton = LootConfig()
loot_items = []


class LootUtility(CustomSkillUtilityBase):

    def __init__(
            self,
            event_bus:EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
            # CLOSE_TO_AGGRO is required to avoid infinite-loop, if when approching an item to loot, player is aggroing.
            # otherwise once approching enemies, player will infinitely loop between loot & follow_party_leader
        ) -> None:
        global loot_filter_singleton

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("loot"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.LOOT.value),
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.LOOTING,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.LOOT.value)
        self.throttle_timer: ThrottledTimer = ThrottledTimer(1_000)
        self.loot_cooldown_timer:CooldownTimer = CooldownTimer(10_000)  # 10s cooldown after blacklist
        self._eval_throttler: ThrottledTimer = ThrottledTimer(1_500)  # Only scan loot every 1.5s
        self._last_eval_score: float | None = None
        self.script_directory = Py4GW.Console.get_projects_path()
        self.CONFIG_FILE = os.path.join(self.script_directory, "Widgets", "Config", "loot_config.json")
        self.RARITY_FILTER_DATA_FILE = os.path.join(self.script_directory, "Widgets", "Data", "rarity_filter_data.json")
        self.loot_config: LootConfig = loot_filter_singleton
        self.load_rarity_filter_data()

    _LOOT_CACHE_KEY = "filtered_loot_earshot"

    def load_rarity_filter_data(self):
        global loot_items

        def load_loot_config():
            global loot_items
            """
            Merge saved user settings back onto the fresh catalog.
            """
            def _normalize_model_id(mid):
                """
                Return a numeric model id or None.
                Accepts ints, ModelID enum members, and strings like 'ModelID.Foo'.
                """
                try:
                    if isinstance(mid, int):
                        return mid
                    if isinstance(mid, ModelID):
                        return mid.value
                    if isinstance(mid, str):
                        if mid.startswith("ModelID."):
                            name = mid.split(".", 1)[1]
                            if hasattr(ModelID, name):
                                return getattr(ModelID, name).value
                        return None
                    # last resort (will raise if not numeric)
                    return int(mid)
                except Exception:
                    return None

            # 1) Read saved data
            saved_items = {}
            saved_blacklist = []
            saved_dye_whitelist = []
            if os.path.exists(self.CONFIG_FILE):
                try:
                    with open(self.CONFIG_FILE, "r") as f:
                        data = json.load(f)
                        # Handle both old format (just items) and new format (items + blacklist + dye_whitelist)
                        if isinstance(data, list):
                            # Old format - just items
                            for entry in data:
                                saved_items[entry["model_id"]] = entry
                        else:
                            # New format - items, blacklist, and dye_whitelist
                            for entry in data.get("items", []):
                                saved_items[entry["model_id"]] = entry
                            saved_blacklist = data.get("blacklist", [])
                            saved_dye_whitelist = data.get("dye_whitelist", [])
                except Exception as e:
                    Py4GW.Console.Log("LootManager", f"Failed to parse {self.CONFIG_FILE}: {e}", Console.MessageType.Error)

            # 2) Clear the whitelist, blacklist, and dye whitelist
            self.loot_config.ClearWhitelist()
            self.loot_config.ClearBlacklist()
            self.loot_config.ClearDyeWhitelist()

            # 3) Load blacklist
            for model_id in saved_blacklist:
                self.loot_config.AddToBlacklist(model_id)

            # 4) Load dye whitelist
            for dye_id in saved_dye_whitelist:
                self.loot_config.AddToDyeWhitelist(dye_id)

            # 4) Merge saved flags onto each catalog item
            for item in loot_items:
                key = item["model_id"]
                if key in saved_items:
                    item["enabled"]       = saved_items[key].get("enabled", False)
                    item["rarity_filter"] = saved_items[key].get("rarity_filter", False)
                else:
                    item["enabled"]       = False
                    item["rarity_filter"] = False

                # 4) Whitelist enabled items
                if item["enabled"]:
                    # Handle dye items differently
                    if item.get("group") == "Dyes":
                        from Py4GWCoreLib import DyeColor
                        dye_name = item["name"].replace(" Dye", "")
                        try:
                            dye_enum = DyeColor[dye_name]
                            self.loot_config.AddToDyeWhitelist(dye_enum.value)
                        except KeyError:
                            pass
                    else:
                        # Handle regular items
                        mid = item["model_id"]
                        if isinstance(mid, str) and mid.startswith("ModelID."):
                            name = mid.split(".", 1)[1]
                            if hasattr(ModelID, name):
                                mid = getattr(ModelID, name)
                        self.loot_config.AddToWhitelist(mid)

            # 5) Always keep gold coins if that toggle’s on
            if self.loot_config.loot_gold_coins:
                self.loot_config.AddToWhitelist(ModelID.Gold_Coins.value)

            # Rebuild singleton whitelist
            self.loot_config.ClearWhitelist()
            for item in loot_items:
                if item.get("enabled", False) and item.get("group") != "Dyes":  # ← guard out dyes
                    model_id = item.get("model_id")
                    if isinstance(model_id, str) and model_id.startswith("ModelID."):
                        model_id_name = model_id.split("ModelID.")[1]
                        if hasattr(ModelID, model_id_name):
                            model_id = getattr(ModelID, model_id_name)
                    self.loot_config.AddToWhitelist(_normalize_model_id(model_id))

            # ——— KEEP GOLD COINS WHITELISTED ———
            if self.loot_config.loot_gold_coins:
                # ensure you have ModelID.Gold_Coin in your enum
                self.loot_config.AddToWhitelist(ModelID.Gold_Coins.value)

        def load_json():
            if os.path.exists(self.RARITY_FILTER_DATA_FILE):
                try:
                    with open(self.RARITY_FILTER_DATA_FILE, "r") as f:
                        data = json.load(f)
                    # Py4GW.Console.Log("loot_utility", "Loaded rarity_filter_data.json")
                    return data
                except Exception as e:
                    Py4GW.Console.Log("loot_utility", f"Failed to load rarity_filter_data.json: {str(e)}", Py4GW.Console.MessageType.Error)
            else:
                Py4GW.Console.Log("loot_utility","rarity_filter_data.json not found", Py4GW.Console.MessageType.Error)
            return {}

        try:
            rarity_data = load_json()
            self.loot_config = LootConfig()
            self.loot_config.SetProperties(
                loot_whites=rarity_data.get("white", False),
                loot_blues=rarity_data.get("blue", False),
                loot_purples=rarity_data.get("purple", False),
                loot_golds=rarity_data.get("gold", False),
                loot_greens=rarity_data.get("green", False),
                loot_gold_coins=rarity_data.get("gold_coins", False)
            )
            load_loot_config()
        except Exception as e:
            Py4GW.Console.Log("loot_utility", f"Error finding loots: {str(e)}", Py4GW.Console.MessageType.Error)

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # Eval throttle: return cached score if not expired
        if not self._eval_throttler.IsExpired():
            return self._last_eval_score
        self._eval_throttler.Reset()

        # Check cooldown after blacklist
        if self.loot_cooldown_timer.IsInCooldown():
            self._last_eval_score = None
            return None

        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
            self._last_eval_score = None
            return None

        if custom_behavior_helpers.Targets.is_party_leader_in_aggro():
            self._last_eval_score = None
            return None

        if custom_behavior_helpers.Targets.is_party_in_aggro():
            self._last_eval_score = None
            return None

        self.load_rarity_filter_data()

        loot_array = self.loot_config.GetfilteredLootArray(Range.Longbow.value, multibox_loot=False)
        # print(f"Loot array: {loot_array}")
        if len(loot_array) == 0:
            self._last_eval_score = None
            return None

        self._last_eval_score = self.score_definition.get_score()
        return self._last_eval_score

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.throttle_timer.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        # Use per-cycle cache for entry check (deduplicates with _evaluate scan)
        loot_array = self.loot_config.GetfilteredLootArray(Range.Longbow.value, multibox_loot=False)
        if len(loot_array) == 0:
            yield
            return BehaviorResult.ACTION_SKIPPED

        self.throttle_timer.Reset()

        while True:

            if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: break
            loot_array:list[int] = self.loot_config.GetfilteredLootArray(Range.Longbow.value, multibox_loot=False)
            if len(loot_array) == 0: break
            item_id = loot_array.pop(0)
            if item_id is None or item_id == 0:
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue
            if not Agent.IsValid(item_id):
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue

            # 1) try to loot
            pos = Agent.GetXY(item_id)
            follow_success = yield from Routines.Yield.Movement.FollowPath([pos], timeout=6_000)
            if not follow_success:
                print("Failed to follow path to loot item, halting.")
                real_item_id = Agent.GetItemAgentItemID(item_id)
                self.loot_config.AddItemIDToBlacklist(real_item_id)
                self.loot_cooldown_timer.Restart()
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue

            Player.Interact(item_id, call_target=False)
            yield from custom_behavior_helpers.Helpers.wait_for(100)

            # 2) check if loot has been looted
            pickup_timer = ThrottledTimer(7_000)
            while not pickup_timer.IsExpired():
                loot_array = self.loot_config.GetfilteredLootArray(Range.Longbow.value, multibox_loot=False)
                if item_id not in loot_array or len(loot_array) == 0:
                    break
                yield from custom_behavior_helpers.Helpers.wait_for(100)

            # 3) Check if we timed out and add to blacklist if so
            if pickup_timer.IsExpired():
                real_item_id = Agent.GetItemAgentItemID(item_id)
                self.loot_config.AddItemIDToBlacklist(real_item_id)
                self.loot_cooldown_timer.Restart()

        yield from custom_behavior_helpers.Helpers.wait_for(100)
        return BehaviorResult.ACTION_PERFORMED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"is_in_loot_cooldown : {self.loot_cooldown_timer.IsInCooldown()}")
        PyImGui.bullet_text(f"loot_cd_remaining_ms: {int(self.loot_cooldown_timer.GetTimeRemaining())}")
        PyImGui.bullet_text(f"loot_array : {self.loot_config.GetfilteredLootArray(Range.Longbow.value, multibox_loot=False)}")
        PyImGui.bullet_text(f"loot_array_all_players : {self.loot_config.GetfilteredLootArray(Range.Longbow.value, multibox_loot=True)}")
        return