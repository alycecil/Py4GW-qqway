from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent, Routines, AgentArray, Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers import Resources
from Sources.oazix.CustomBehaviors.primitives.helpers.lock_key_helper import LockKeyHelper
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class AncestorsRageUtility(CustomSkillUtilityBase):
    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 40 if enemy_qte >= 1 else 0),
                 mana_required_to_cast: int = 15,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Ancestors_Rage"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.model_id_filter: int = int(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "model_id_filter", "5903"))

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:

        allies: list[
            custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            sort_key=(TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_allies=None,
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))

        vanguard = self._get_vanguard()
        if vanguard is not None:
            allies.extend(vanguard)

            # with vanguards added after means prefer player over npc
            return sorted(allies, key=lambda x: -x.enemy_quantity_within_range) # intentional dupe of TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC

        return allies
    
    def _get_vanguard(self) -> list[custom_behavior_helpers.SortableAgentData]:

        vanguard: list[
            custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_ncs_of_model_ordered_by_priority_raw(
            model_id=self.model_id_filter,
            within_range=Range.Spellcast.value * 1.2,
            sort_key=(TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_allies=None,
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))

        if len(vanguard) == 0: return None

        return vanguard

    def _get_lock_key(self, agent_id: int) -> str:
        return f"ancestors_rage_{agent_id}"

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        allies = self._get_targets()
        if len(allies) == 0: return None

        for ally in allies:
            if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(self._get_lock_key(ally.agent_id)):
                continue

            lock_key = self._get_lock_key(ally.agent_id)
            if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None # someone is already spiking off
            return self.score_definition.get_score(ally.enemy_quantity_within_range)

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        allies = self._get_targets()
        if len(allies) == 0: return BehaviorResult.ACTION_SKIPPED

        for target in allies:
            lock_key = self._get_lock_key(allies[0].agent_id)
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=1):# does not stack, prevent waste
                continue

            try:
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
            finally:
                # CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
                pass
            return result

        yield
        return BehaviorResult.ACTION_SKIPPED


    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "model_id_filter", str(self.model_id_filter))
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "model_id_filter", str(self.model_id_filter))
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "model_id_filter")
        print("configuration deleted")