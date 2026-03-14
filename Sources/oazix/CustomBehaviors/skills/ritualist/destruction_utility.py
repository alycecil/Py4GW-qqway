from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers import Resources
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class RawSpiritUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(40),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Destruction"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.ritual_lord_skill = CustomSkill("Ritual_Lord")
        self.soul_twisting_skill = CustomSkill("Soul_Twisting")
        self.score_definition: ScoreStaticDefinition = score_definition
        self.owned_spirit_model_id: SpiritModelID = SpiritModelID.DESTRUCTION

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_rit_lord = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.ritual_lord_skill.skill_id)
        if has_rit_lord:
            return 99.01 # aabove high, consume the floating ritual lord

        has_soul_twisting = False
        # if we have soul twisting care about it.
        if self.soul_twisting_skill.skill_slot is not None and self.soul_twisting_skill.skill_slot > 0:
            # Check if we have Soul Twisting active
            has_soul_twisting = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.soul_twisting_skill.skill_id)
            if not has_soul_twisting:
                return None  # Don't cast without Soul Twisting

            buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(Player.GetAgentID(), self.soul_twisting_skill.skill_id)

            if buff_time_remaining <= 1200:  # Don't cast if Soul Twisting is about to expire
                return None
        else:
            has_soul_twisting = False

        spirit_agent: custom_behavior_helpers.SpiritAgentData | None = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(
            within_range=Range.Nearby,
            spirit_model_ids=[self.owned_spirit_model_id], 
            condition=lambda agent_id: True)
        
        if spirit_agent is None: return self.score_definition.get_score()
        if spirit_agent.hp < 0.2: return self.score_definition.get_score()
        if not has_soul_twisting or not CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(self.custom_skill.skill_name):
            return CommonScore.GENERIC_SKILL_HERO_AI.value  # low priority overcast
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        if not Routines.Checks.Skills.IsSkillSlotReady(self.custom_skill.skill_slot):
            yield
            return BehaviorResult.ACTION_SKIPPED

        if not Resources.has_enough_resources(self.custom_skill):
            yield
            return BehaviorResult.ACTION_SKIPPED

        if Routines.Checks.Skills.IsSkillSlotReady(self.ritual_lord_skill.skill_slot):
            print("using ritual lord")
            yield from custom_behavior_helpers.Actions.cast_skill(self.ritual_lord_skill)

            print("using destruction after ritual lord")

        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)

        if result == BehaviorResult.ACTION_PERFORMED:
            # if you change this duration it must be shorter than the ritual lord recharge time or youll be wasting spike time
            CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(self.custom_skill.skill_name, 4) # ~6 seconds is highest damage per spike but 4 gives us max casts per soul twisting. I like max casts

            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.owned_spirit_model_id)

        return result