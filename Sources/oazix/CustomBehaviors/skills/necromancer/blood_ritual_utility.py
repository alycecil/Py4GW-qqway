from tkinter.constants import N
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Py4GWCoreLib.enums import Profession
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target import CustomBuffTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_email import BuffConfigurationPerPlayerEmail
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_is_power_utility import BloodIsPowerUtility
from Sources.oazix.CustomBehaviors.skills.plugins.targeting_modifiers.buff_configurator import BuffConfigurator

class BloodRitualUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus:EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(10),
        sacrifice_life_cost: int = 17,
        sacrifice_life_limit_percent: float = 0.55,
        sacrifice_life_limit_absolute: int = 175,
        required_target_mana_lower_than_percent: float = 0.40,
        lock_ttl = 15,
        mana_required_to_cast: int = 7,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Blood_Ritual"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = score_definition

        self.add_plugin_targetting_modifier(lambda x: BuffConfigurator(event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_CASTERS))
        self.sacrifice_life_limit_percent: float = sacrifice_life_limit_percent
        self.sacrifice_life_limit_absolute: int = sacrifice_life_limit_absolute
        self.required_target_mana_lower_than_percent: float = required_target_mana_lower_than_percent
        self.sacrifice_life_cost = sacrifice_life_cost
        self.lock_ttl = lock_ttl

    def _get_lock_key(self, agent_id: int) -> str:
        return f"necroenergy_{self.custom_skill.skill_name}_{agent_id}"

    def _get_target(self) -> int | None:

        target: int | None = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
                within_range=Range.Spellcast.value,
                condition=lambda agent_id:
                    agent_id != Player.GetAgentID() and
                    self.get_plugin_targeting_modifiers_filtering_predicate()(agent_id) and
                    custom_behavior_helpers.Resources.get_energy_percent_in_party(agent_id) < self.required_target_mana_lower_than_percent and
                    not (GLOBAL_CACHE.Effects.EffectExists(agent_id, self.custom_skill.skill_id) or GLOBAL_CACHE.Effects.BuffExists(agent_id, self.custom_skill.skill_id)) and
                    not CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(self._get_lock_key(agent_id)),
                sort_key=(TargetingOrder.ENERGY_ASC, TargetingOrder.DISTANCE_ASC),
                range_to_count_enemies=None,
                range_to_count_allies=None)

        return target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not custom_behavior_helpers.Resources.player_can_sacrifice_health(self.sacrifice_life_cost, self.sacrifice_life_limit_percent, self.sacrifice_life_limit_absolute):
            return None

        target = self._get_target()
        if target is None: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        target = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED

        lock_key = self._get_lock_key(target)
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(key=lock_key, timeout_seconds=self.lock_ttl) == False:
            yield
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        self.sacrifice_life_limit_percent = PyImGui.input_float("sacrifice_life_limit_percent##sacrifice_life_limit_percent", self.sacrifice_life_limit_percent)
        self.sacrifice_life_limit_absolute = PyImGui.input_int("sacrifice_life_limit_absolute##sacrifice_life_limit_absolute", self.sacrifice_life_limit_absolute)
        self.required_target_mana_lower_than_percent = PyImGui.input_float("required_target_mana_lower_than_percent##required_target_mana_lower_than_percent", self.required_target_mana_lower_than_percent)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        super().persist_configuration_for_account()
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "required_target_mana_lower_than_percent", f"{self.required_target_mana_lower_than_percent:.2f}")
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        super().persist_configuration_as_global()
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "required_target_mana_lower_than_percent", f"{self.required_target_mana_lower_than_percent:.2f}")
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        super().delete_persisted_configuration()
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "required_target_mana_lower_than_percent")
        print("configuration deleted")