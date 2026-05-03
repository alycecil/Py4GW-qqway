
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.skills.dervich.derrvish_spike_utility import DervishSpikeUtility


class PiousAssault_Utility(DervishSpikeUtility):
    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Pious_Assault"),
            current_build=current_build,
            allowed_states=allowed_states)
