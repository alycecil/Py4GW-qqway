from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range
from Sources.oazix.CustomBehaviors.primitives.infrastructure.persistence_locator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives import constants
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


class BarbedSignetUtility(CustomSkillUtilityBase):

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 62 if enemy_qte >= 5 else 42 if enemy_qte >= 3 else 25),
        mana_required_to_cast: int = 5,
        sacrifice_life_limit_percent: float = 0.55,
        sacrifice_life_limit_absolute: int = 100,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO,BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Barbed_Signet"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition = score_definition

        self.sacrifice_life_limit_percent: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "sacrifice_life_limit_percent", str(sacrifice_life_limit_percent)))
        self.sacrifice_life_limit_absolute: int = int(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "sacrifice_life_limit_absolute", str(sacrifice_life_limit_absolute)))

    def _get_lock_key(self, agent_id: int) -> str:
        return f"barbed_signet_{agent_id}"

    def _get_target_score(self, target: custom_behavior_helpers.SortableAgentData) -> float:
        score_max = 55
        score_min = 0
        score_offset = 0

        if Agent.IsBleeding(target.agent_id):
            return 0

        if not Agent.IsConditioned(target.agent_id):
            score_min += 10
            score_offset += 10

        lock_key = self._get_lock_key(target.agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key):
            return 0

        score: int = round(self.score_definition.get_score(target.enemy_quantity_within_range)) + score_offset

        return max(min(score_max, score), score_min)

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get enemies ordered by cluster size and distance."""
        by_priority_raw : list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            condition=lambda agent_id: not Agent.IsSpirit(agent_id),
            range_to_count_enemies=Range.Adjacent.value # target groups even if the skill is not aoe
        )

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

        if not custom_behavior_helpers.Resources.player_can_sacrifice_health(33, self.sacrifice_life_limit_percent, self.sacrifice_life_limit_absolute):
            return None

        targets = self._get_targets()
        if len(targets) == 0: return None
        target = targets[0]
        lock_key = self._get_lock_key(target.agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None

        return self._get_target_score(target)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        lock_key = self._get_lock_key(target.agent_id)
        CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, 10) # intentionally not blocking as

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)

        return result

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        self.sacrifice_life_limit_percent = PyImGui.input_float("sacrifice_life_limit_percent##sacrifice_life_limit_percent", self.sacrifice_life_limit_percent)
        self.sacrifice_life_limit_absolute = PyImGui.input_int("sacrifice_life_limit_absolute##sacrifice_life_limit_absolute", self.sacrifice_life_limit_absolute)

    @override
    def persist_configuration_for_account(self):
        super().persist_configuration_for_account()
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        super().persist_configuration_as_global()
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        super().delete_persisted_configuration()
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute")
        print("configuration deleted")

