from HeroAI.custom_skill_src.skill_types import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility


class Signet_of_Capture_Stub(StubUtility):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Capture"),
            current_build=current_build
        )
