# python
from enum import Enum
from typing import Any, Generator, override, Tuple

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Player
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class AuspiciousIncantationState(Enum):
    CAST_AUSPICIOUS = 1
    CAST_SKILL = 2
    IDLE = 3

class AuspiciousIncantationListUtility(CustomSkillUtilityBase):

    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 original_skills_to_cast: list[CustomSkillUtilityBase],
                 auspicious_score_definition: ScoreStaticDefinition = ScoreStaticDefinition(85),
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Auspicious_Incantation"),
            in_game_build=current_build,
            score_definition=auspicious_score_definition,
            allowed_states=allowed_states
        )

        self.auspicious_score_definition: ScoreStaticDefinition = auspicious_score_definition
        self.original_skills_to_cast: list[CustomSkillUtilityBase] = original_skills_to_cast

    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE:
            return False
        if self.allowed_states is not None and current_state not in self.allowed_states:
            return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast:
            return False
        return True

    def get_original_skills_to_cast(self):
        def condition(x : CustomSkillUtilityBase):
            return x is not None and x.custom_skill is not None and x.custom_skill.skill_slot != 0
        return filter(condition, self.original_skills_to_cast)

    def _get_auspicious_state(self, current_state: BehaviorState) -> Tuple[AuspiciousIncantationState, CustomSkillUtilityBase|None]:

        # If under Auspicious buff, priority is to cast the target skill immediately
        if Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id):
            return AuspiciousIncantationState.CAST_SKILL, None

        # If Auspicious and the target skill are both ready and resources/prechecks ok -> cast Auspicious first
        is_auspicious_ready = Routines.Checks.Skills.IsSkillIDReady(self.custom_skill.skill_id)
        has_energy_for_auspicious = custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill)

        skills_to_cast = self.get_original_skills_to_cast()
        for skill_to_cast in skills_to_cast:
            try:
                is_target_ready = Routines.Checks.Skills.IsSkillIDReady(skill_to_cast.custom_skill.skill_id)
                has_energy_for_target = custom_behavior_helpers.Resources.has_enough_resources(skill_to_cast.custom_skill)
                is_target_prechecks_valid = skill_to_cast.are_common_pre_checks_valid(current_state)

                if is_auspicious_ready and is_target_ready and has_energy_for_auspicious and has_energy_for_target and is_target_prechecks_valid:
                    return AuspiciousIncantationState.CAST_AUSPICIOUS, skill_to_cast
            except Exception:
                pass

        return AuspiciousIncantationState.IDLE, None

    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        state, skill = self._get_auspicious_state(current_state)

        match state:
            case AuspiciousIncantationState.CAST_AUSPICIOUS:
                return self.auspicious_score_definition.get_score()
            case AuspiciousIncantationState.CAST_SKILL:
                return 95  # force immediate cast of the target skill while buff is active
            case AuspiciousIncantationState.IDLE:
                return None
        return None

    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        auspicious_state, original_skill_to_cast = self._get_auspicious_state(state)

        match auspicious_state:
            case AuspiciousIncantationState.CAST_AUSPICIOUS:
                result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
                return result
            case AuspiciousIncantationState.CAST_SKILL:
                if original_skill_to_cast is not None:
                    result = yield from original_skill_to_cast.execute(state)
                    return result
                else:
                    return BehaviorResult.ACTION_SKIPPED
            case AuspiciousIncantationState.IDLE:
                return BehaviorResult.ACTION_SKIPPED
        return BehaviorResult.ACTION_SKIPPED

    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        state, skill = self._get_auspicious_state(current_state)
        PyImGui.bullet_text(f"internal state : {state}")

        if skill is None:
            PyImGui.bullet_text(f"No skills available")
        else:
            try:
                PyImGui.bullet_text(f"skill to use :")
                skill.customized_debug_ui(current_state)
            except Exception:
                if skill.custom_skill:
                    PyImGui.bullet_text(f"skill name : {skill.custom_skill.skill_name}")
                else:
                    PyImGui.bullet_text(f"skill : {skill}")
                pass

        if self.get_original_skills_to_cast():
            for setup_skill in self.get_original_skills_to_cast():
                try:
                    PyImGui.bullet_text(f"""configured skill : {setup_skill.custom_skill.skill_name}""")
                    setup_skill.customized_debug_ui(current_state)
                except Exception:
                    PyImGui.bullet_text(f"configured skill :: {setup_skill}")
