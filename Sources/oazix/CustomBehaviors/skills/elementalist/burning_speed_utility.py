from tkinter.constants import N
from typing import Any, Generator, override
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Range, Routines, Agent, Player
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player, Agent
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class BurningSpeedUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    score_definition: ScoreStaticDefinition,
    mana_required_to_cast: int = 10,
    renew_before_expiration_in_milliseconds: int = 200,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Burning_Speed"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.renew_before_expiration_in_milliseconds: int = renew_before_expiration_in_milliseconds
        self.should_cast_when_mana_low: bool = PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "should_cast_when_mana_low", str(0)) == "1"
        self.mana_low_threshold: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "mana_low_threshold", str(0.40)))
        self.require_aura_of_restoration: bool = PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "require_aura_of_restoration", str(0)) == "1"
        self.require_life_attunement: bool = PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "require_life_attunement", str(0)) == "1"

        # CustomSkill instances for the enchantments so we can reference their skill_id
        self._aura_skill = CustomSkill("Aura_of_Restoration")
        self._life_skill = CustomSkill("Life_Attunement")

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        player_agent = Player.GetAgentID()

        # Check if mana is low (if enabled)
        if self.should_cast_when_mana_low:
            player_energy_percent = Agent.GetEnergy(player_agent)
            if player_energy_percent <= self.mana_low_threshold:
                return HealingScore.MEMBER_DAMAGED_EMERGENCY.value - 0.1 # force cast when mana low (to regain energy)


        # Configurable buff checks using Routines.Checks.Effects.HasBuff
        try:
            has_aura = bool(Routines.Checks.Effects.HasBuff(player_agent, self._aura_skill.skill_id))
            has_life = bool(Routines.Checks.Effects.HasBuff(player_agent, self._life_skill.skill_id))

            if Agent.GetHealth(player_agent) < 0.6:
                if self.require_aura_of_restoration and not has_aura:
                    pass
                # Check if required buffs are present (based on configuration)
                elif self.require_life_attunement and not has_life:
                    pass
                else:
                    return self.score_definition.get_score()
        except Exception:
            # If the buff-check call itself fails, be conservative and skip
            return None

        has_buff = Routines.Checks.Effects.HasBuff(player_agent, self.custom_skill.skill_id)
        if not has_buff: return self.score_definition.get_score()
        
        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent, self.custom_skill.skill_id)
        if buff_time_remaining <= self.renew_before_expiration_in_milliseconds: return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        self.require_aura_of_restoration = PyImGui.checkbox("require_aura_of_restoration##require_aura_of_restoration", self.require_aura_of_restoration)
        self.require_life_attunement = PyImGui.checkbox("require_life_attunement##require_life_attunement", self.require_life_attunement)
        self.should_cast_when_mana_low = PyImGui.checkbox("should_cast_when_mana_low##should_cast_when_mana_low", self.should_cast_when_mana_low)
        self.mana_low_threshold = PyImGui.input_float("mana_low_threshold##mana_low_threshold", self.mana_low_threshold)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "require_aura_of_restoration", "1" if self.require_aura_of_restoration else "0")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "require_life_attunement", "1" if self.require_life_attunement else "0")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "should_cast_when_mana_low", "1" if self.should_cast_when_mana_low else "0")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "mana_low_threshold", f"{self.mana_low_threshold:.2f}")
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "require_aura_of_restoration", "1" if self.require_aura_of_restoration else "0")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "require_life_attunement", "1" if self.require_life_attunement else "0")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "should_cast_when_mana_low", "1" if self.should_cast_when_mana_low else "0")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "mana_low_threshold", f"{self.mana_low_threshold:.2f}")
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "require_aura_of_restoration")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "require_life_attunement")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "should_cast_when_mana_low")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "mana_low_threshold")
        print("configuration deleted")