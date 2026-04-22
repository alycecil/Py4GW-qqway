from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Routines, Player, Enum
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class DestructiveWasGlaiveMode(Enum):
    MOVE_IN = 0
    SPIKE = 1
    CAST_NOT_HOLDING_ITEM = 2

class DestructiveWasGlaiveUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                current_build: list[CustomSkill],
                score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 90 if enemy_qte >= 4 else 71 if enemy_qte >= 3 else 61 if enemy_qte >= 2 else 51 if enemy_qte >= 1 else 41),
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Destructive_Was_Glaive"),
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        )
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.last_agent_quantity: int = 0

        self.throttle_timer = ThrottledTimer(5_000)

    def _get_closest_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:

        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            # condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
            sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.HP_ASC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        return targets

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:

        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Nearby,
            # condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_targets()
        mode = self._get_mode(targets, current_state)

        if mode is None:
            return None

        if mode == DestructiveWasGlaiveMode.CAST_NOT_HOLDING_ITEM:
            return 70

        if mode == DestructiveWasGlaiveMode.SPIKE:
            target = targets[0]
            return self.score_definition.get_score(target.agent_quantity_within_range)

        if mode == DestructiveWasGlaiveMode.MOVE_IN:
            if not self.throttle_timer.IsExpired(): return 10
            return 50

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        targets = self._get_targets()
        mode = self._get_mode(targets, state)

        if mode != DestructiveWasGlaiveMode.CAST_NOT_HOLDING_ITEM:

            if len(targets) <= 0:
                targets = self._get_closest_targets()

            if len(targets) > 0:
                targets__agent_id = targets[0].agent_id
                agent_id_position = Agent.GetXY(targets__agent_id)
                player_agent_id_position: tuple[float, float] = Agent.GetXY(Player.GetAgentID())
                if Utils.Distance(player_agent_id_position , agent_id_position) > Range.Adjacent.value:
                    from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Console, AutoPathing
                    Player.Interact(targets__agent_id, call_target=True)
                    path3d = yield from AutoPathing().get_path_to(agent_id_position[0], agent_id_position[1], smooth_by_los=True, margin=100.0, step_dist=322.0)
                    path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

                    yield from Routines.Yield.Movement.FollowPath(
                        path_points= path2d,
                        custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()) or Agent.IsDead(targets__agent_id),
                        tolerance=150,
                        log=constants.DEBUG,
                        timeout=2_000,
                        progress_callback=lambda progress: ConsoleLog("DestructiveWasGlaiveUtility", f"FollowPath: progress: {progress}", Console.MessageType.Info) if constants.DEBUG else None,
                        custom_pause_fn=lambda: False)
                    self.throttle_timer.Reset()

                    if mode == DestructiveWasGlaiveMode.MOVE_IN:
                        return BehaviorResult.ACTION_PERFORMED

        if mode == DestructiveWasGlaiveMode.MOVE_IN:
            return BehaviorResult.ACTION_SKIPPED

        if mode == DestructiveWasGlaiveMode.CAST_NOT_HOLDING_ITEM or mode == DestructiveWasGlaiveMode.SPIKE:
            result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
            return result

        yield
        return BehaviorResult.ACTION_SKIPPED

    def _get_mode(self, targets: list[custom_behavior_helpers.SortableAgentData], state: BehaviorState):

        if len(targets) == 0:
        # are we holding anything?
            is_player_holding_an_item: bool = custom_behavior_helpers.Resources.is_player_holding_an_item()
            if is_player_holding_an_item:
                if state == BehaviorState.IN_AGGRO:
                        return DestructiveWasGlaiveMode.MOVE_IN
                return None
            return DestructiveWasGlaiveMode.CAST_NOT_HOLDING_ITEM

        return DestructiveWasGlaiveMode.SPIKE
