from typing import Any, Generator, override

from Py4GWCoreLib import Routines, Range, GLOBAL_CACHE
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class RuptureSoulUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 90 if enemy_qte >= 4 else 80 if enemy_qte >= 3 else 70 if enemy_qte >= 2 else 15 if enemy_qte >= 1 else 0),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Rupture_Soul"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

        # todo propose to be customizable
        self.target_spirit_skill: CustomSkill = CustomSkill("Destruction")
        self.target_spirit_spirit_model_id: SpiritModelID = SpiritModelID.DESTRUCTION

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:

        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Nearby,
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(self.target_spirit_skill.skill_name): return None # give destruction time to charge

        # if not Routines.Checks.Skills.IsSkillIDReady(self.target_spirit_skill.skill_id): return None # if target_spirit not-ready, we can't cast

        is_target_spirit_spirit_exist = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(within_range=Range.Spellcast, spirit_model_ids=[self.target_spirit_spirit_model_id], condition=lambda agent_id: True)
        if not is_target_spirit_spirit_exist: return None # no cast, if target_spirit spirit not exist

        targets = self._get_targets()
        if len(targets) == 0: return None

        return self.score_definition.get_score(len(targets))

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        # we target Destruction spirit to destroy it

        target_spirit_spirit: custom_behavior_helpers.SpiritAgentData | None = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(within_range=Range.Spirit, spirit_model_ids=[self.target_spirit_spirit_model_id], condition=lambda agent_id: True)
        if target_spirit_spirit is None: return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target_spirit_spirit.agent_id)
        return result