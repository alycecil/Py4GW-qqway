from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives import constants


class ShoutAtPartyGravity(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        skill: CustomSkill,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        mana_required_to_cast: int = 0,
        recast_on_recharge: bool = False,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition
        self.recast_on_recharge = recast_on_recharge

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        has_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        if not has_buff:
            return self.score_definition.get_score()
        elif self.recast_on_recharge:
            return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        allies = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=1550,
            condition=lambda agent_id: agent_id != Player.GetAgentID(),
            allow_pets=False
        )
        agent_ids: list[int] = [a.agent_id for a in allies]

        gravity_center: custom_behavior_helpers.GravityCenter | None = custom_behavior_helpers.Targets.find_optimal_gravity_center(Range.Area, agent_ids=agent_ids)
        if gravity_center is not None:
            if gravity_center.distance_from_player > Range.Touch.value:
                if constants.DEBUG: print("ShoutAtPartyGravity: moving to a better place (gravity center).")
                exit_condition: Callable[[], bool] = lambda: False
                tolerance: float = 100
                path_points: list[tuple[float, float]] = [gravity_center.coordinates]
                yield from Routines.Yield.Movement.FollowPath(
                    path_points=path_points,
                    custom_exit_condition=exit_condition,
                    tolerance=tolerance,
                    log=True,
                    timeout=4000,
                    progress_callback=lambda progress: print(f"ShoutAtPartyGravity: progress: {progress}") if constants.DEBUG else None)
        else:
            print("ShoutAtPartyGravity: No gravity center.")

        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill, after_cast_delay=False)
        return result