import PyImGui
from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class RawAoeAttackUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    skill: CustomSkill,
    current_build: list[CustomSkill],
    score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 66 if enemy_qte >= 3 else 51 if enemy_qte <= 2 else 26),
    mana_required_to_cast: int = 12,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    within_range: Range = Range.Spellcast,
    ignore_spirits: bool = False,
    custom_agent_targeting_predicate: Callable[[int], bool] | None = None
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.within_range = within_range
        self.ignore_spirits = ignore_spirits
        self.custom_agent_targeting_predicate: Callable[[int], bool] | None = custom_agent_targeting_predicate

    def _get_target_score(self, target: custom_behavior_helpers.SortableAgentData) -> float:
        score_max = 55.0
        score_min = 0.0
        score_offset = 0.0
        target_agent_id = target.agent_id

        agent_xy = Agent.GetXY(target_agent_id)
        player_xy = Player.GetXY()
        distance = Utils.Distance(agent_xy, player_xy)

        # Called target more important
        party_target_id = Routines.Party.GetPartyTargetID()
        if party_target_id == target_agent_id:
            score_max = 90.0
            score_offset += 45.0
            score_min = 40.0
        else:
            called_target_xy = Agent.GetXY(party_target_id)
            distance_called_target = Utils.Distance(agent_xy, called_target_xy)
            target_range = GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
            if target_range is None:
                target_range = Range.Touch.value

            if distance_called_target < target_range:
                score_max = 85.0
                score_offset += 25.0
                score_min = 20.0

        # is short range skill?
        short_range = self.is_short_range()

        if Agent.IsDeepWounded(target_agent_id):
            score_offset += 5.0

        if not Agent.IsHexed(target_agent_id):
            score_offset = -2.0
        else:
            score_offset += 1.0

        if Agent.IsCaster(target_agent_id):
            score_offset += 3.0

        # Health factor
        health = Agent.GetHealth(target_agent_id)

        if health < .15:
            score_max = 75.0
            score_min = 0.0
            score_offset += 6
        elif health < .5:
            score_max = 80.0
            score_min = 20.0
            score_offset += 5
        elif health < .75:
            score_max = 75.0
            score_min = 20.0
            score_offset += 3

        # Distance factor
        if distance < Range.Touch.value:
            score_offset += 50 if short_range else 2.2
        elif distance < Range.Adjacent.value:
            score_offset += 35 if short_range else 2
        elif distance < Range.Nearby.value:
            score_offset += 20 if short_range else 1.5
        elif distance < Range.Area.value:
            score_offset += 10 if short_range else 1.1
        elif distance < Range.Area.value * 2:
            score_offset += 5 if short_range else 0.5
        elif distance < Range.Earshot.value:
            score_offset += 1 if short_range else 0.1

        nearby_weight = self.score_definition.get_score(target.enemy_quantity_within_range)
        if nearby_weight is None:
            nearby_weight = 0
        if short_range:
            nearby_weight /= 10.0

        score: int = round(nearby_weight + score_offset)

        return max(min(score_max, score), score_min)

    def is_short_range(self):
        short_range = False
        if (GLOBAL_CACHE.Skill.Flags.IsTouchRange(self.custom_skill.skill_id) or
                GLOBAL_CACHE.Skill.Flags.IsAttack(self.custom_skill.skill_id)):
            short_range = True
        return short_range

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:

        def condition(agent_id: int) -> bool:
            if self.ignore_spirits:
                return not Agent.IsSpirit(agent_id)
            return True

        by_priority_raw = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            condition=lambda agent_id: condition(agent_id) and (
                        self.custom_agent_targeting_predicate is None or self.custom_agent_targeting_predicate(agent_id)
            ),
            within_range=self.within_range,
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))

        by_priority_raw.sort(key=lambda target: (
            -self._get_target_score(target),
            -target.enemy_quantity_within_range,
            target.is_caster,
        ))

        if constants.DEBUG:
            print("List of targets")
            for item in by_priority_raw:
                print(f"item: {self._get_target_score(item)} : {item}")

        return by_priority_raw

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        targets = self._get_targets()
        if len(targets) == 0: return None
        target = targets[0]
        return self._get_target_score(target)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        short_range = self.is_short_range()
        PyImGui.bullet_text(f"short_range : {short_range}")
        pass
