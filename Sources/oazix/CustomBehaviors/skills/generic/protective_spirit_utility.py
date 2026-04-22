from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ProtectiveSpiritUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        skill: CustomSkill,
        current_build: list[CustomSkill],
        owned_spirit_model_id: SpiritModelID,
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(60),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition
        self.ritual_lord_skill = CustomSkill("Ritual_Lord")
        self.soul_twisting_skill = CustomSkill("Soul_Twisting")
        self.owned_spirit_model_id: SpiritModelID = owned_spirit_model_id
        self.has_logged = False

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        max_score = 99.0

        # if we have soul twisting care about it.
        if self.soul_twisting_skill.skill_slot is not None and self.soul_twisting_skill.skill_slot > 0:
            # Check if we have Soul Twisting active
            has_soul_twisting = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.soul_twisting_skill.skill_id)
            if not has_soul_twisting:
                return None  # Don't cast without Soul Twisting

            buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(Player.GetAgentID(), self.soul_twisting_skill.skill_id)

            if buff_time_remaining <= 1200:  # Don't cast if Soul Twisting is about to expire
                return None

            if buff_time_remaining <= 5000:  # if less than 5 seconds, let's try to exhaust charges by force casting spirits

                if custom_behavior_helpers.Resources.is_spirit_exist(
                        within_range=Range.Spellcast,
                        associated_to_skill=self.custom_skill,
                        condition=lambda agent_id: Agent.GetHealth(agent_id) < 0.80): # we only refresh low life spirits
                    return self.score_definition.get_score()

        elif self.ritual_lord_skill.skill_slot is not None and self.ritual_lord_skill.skill_slot > 0:
            has_rit_lord = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.ritual_lord_skill.skill_id)
            if not has_rit_lord and not Routines.Checks.Skills.IsSkillSlotReady(self.ritual_lord_skill.skill_slot):
                max_score = CommonScore.GENERIC_SKILL_HERO_AI.value # low priority the spirit as no benefit
        else:
            # This is likely a developer mistake
            if not self.has_logged:
                print(f"Warning, ProtectiveSpiritUtility could not detect Ritual Lord or Soul Twisting. Its acting like RawSpiritUtility which is probably okay short term.")
                self.has_logged = True

        # Check if we need to cast the spirit
        if not custom_behavior_helpers.Resources.is_spirit_exist(
                within_range=Range.Spellcast,
                associated_to_skill=self.custom_skill,
                condition=lambda agent_id: Agent.GetHealth(agent_id) > 0.3):
            return min(max_score, self.score_definition.get_score())  # High priority if spirit doesn't exist or is low health
            
        return None  # No need to cast if spirit exists and is healthy

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if Routines.Checks.Skills.IsSkillSlotReady(self.ritual_lord_skill.skill_slot):
            yield from custom_behavior_helpers.Actions.cast_skill(self.ritual_lord_skill, after_cast_delay=False)

        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        if result == BehaviorResult.ACTION_PERFORMED:
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.owned_spirit_model_id)
        
        return result