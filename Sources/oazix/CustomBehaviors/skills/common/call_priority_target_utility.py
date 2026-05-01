import random
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums_src.GameData_enums import Profession
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus

class CallPriorityTargetUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("call_priority_target_utility"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.AUTO_ATTACK.value + 0.001),
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.AUTO_ATTACK.value)
        self.throttle_timer = ThrottledTimer(5000+random.randint(1000, 9999))
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    def __get_target_agent_id(self) -> int:
        def my_condition(agent_id) -> bool:
            if not Agent.IsCaster(agent_id):
                return False

            skill_id = Agent.GetCastingSkillID(agent_id)
            profession, _ = GLOBAL_CACHE.Skill.GetProfession(skill_id)
            if profession == Profession.Monk:
                return True


            return False

        party_target_id = Routines.Party.GetPartyTargetID()
        if party_target_id is not None and party_target_id > 0:
            return 0 # Something is already the called target

        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            condition=my_condition,
            sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.HP_ASC))

        if len(targets) != 0: return targets[0].agent_id

        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            condition=lambda agent_id: Agent.IsCaster(agent_id),
            sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.HP_ASC))
        
        if len(targets) == 0: return 0
        return targets[0].agent_id

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        if not self.throttle_timer.IsExpired():
            return None

        if custom_behavior_helpers.Resources.is_player_holding_an_item():
            return None

        target_agent_id = self.__get_target_agent_id()
        if target_agent_id == 0: return None

        if Agent.IsAttacking(Player.GetAgentID()) and Player.GetTargetID() == target_agent_id:
            self.throttle_timer = ThrottledTimer(5000+random.randint(1000, 9999)) # redefine to force jitter in calling
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target_agent_id: int = self.__get_target_agent_id()
        if target_agent_id == 0: return BehaviorResult.ACTION_SKIPPED

        current_target_agent_id = Player.GetTargetID()
        if current_target_agent_id != target_agent_id:
            yield from Routines.Yield.Keybinds.ClearTarget()
            Player.ChangeTarget(target_agent_id)
            yield from custom_behavior_helpers.Helpers.wait_for(300)
            Player.Interact(target_agent_id, True)
            yield from custom_behavior_helpers.Helpers.wait_for(300)
        else:
            if not Agent.IsAttacking(Player.GetAgentID()):
                Player.Interact(target_agent_id, True)
                yield from custom_behavior_helpers.Helpers.wait_for(300)

        self.throttle_timer = ThrottledTimer(5000+random.randint(1000, 9999)) # redefine to force jitter in calling
        return BehaviorResult.ACTION_PERFORMED
