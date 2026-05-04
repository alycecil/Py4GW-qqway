from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility


class ElementalistSkillsProvider:
    """
    Provider for elementalist utility skills.
    These skills focus on elemental attunements and energy management.
    """
    
    @classmethod
    def get_skills(cls, event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of elementalist utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of elementalist utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Aura_of_Restoration"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(40), mana_required_to_cast=7,
            renew_before_expiration_in_milliseconds=250,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        
        return skills
