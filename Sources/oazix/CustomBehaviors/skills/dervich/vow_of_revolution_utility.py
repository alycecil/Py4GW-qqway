from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Player
from Py4GWCoreLib.enums_src.GameData_enums import Profession
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class Vow_of_Revolution_KeepSelfEffectUpUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    score_definition: ScoreStaticDefinition = ScoreStaticDefinition(25),
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Vow_of_Revolution"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=5,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.renew_before_expiration_in_milliseconds: int = 2222

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False

        if self.allowed_states is not None and current_state not in self.allowed_states:
            if constants.DEBUG: print(f'PreCheck Reject - Wrong State {self.custom_skill.skill_name}')
            return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast:
            if constants.DEBUG: print(f'PreCheck Reject - Energy Requirement for Utility {self.custom_skill.skill_name}')
            return False
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill):
            if constants.DEBUG: print(f'PreCheck Reject - Resources Requirement for Ability {self.custom_skill.skill_name}')
            return False

        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(Player.GetAgentID(), self.custom_skill.skill_id)
        if 1000 < buff_time_remaining <= self.renew_before_expiration_in_milliseconds: return 10

        if current_state in [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]:
            if not Routines.Checks.Skills.IsSkillSlotReady(self.custom_skill.skill_slot):
                if constants.DEBUG:
                    print(f"custom_skill.skill_slot: {self.custom_skill.skill_slot}")
                    print(f'PreCheck Reject - IsSkillSlotReady {self.custom_skill.skill_name}')
                return False

            has_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
            if not has_buff: return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        has_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        if has_buff:
            for skill in self.in_game_build:
                profession_id, _ = GLOBAL_CACHE.Skill.GetProfession(skill.skill_id)
                if profession_id != Profession.Dervish.value:
                    # yolo cast!
                    result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
                    if result != BehaviorResult.ACTION_SKIPPED:
                        return result
        else:
            if state in [BehaviorState.IN_AGGRO]:
                result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
                return result

        return BehaviorResult.ACTION_SKIPPED

