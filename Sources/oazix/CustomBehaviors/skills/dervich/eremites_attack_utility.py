from typing import List, Any, Generator, Callable, override

import PyImGui

from HeroAI.types import SkillType
from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, Range
from Py4GWCoreLib.enums_src.GameData_enums import Profession
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers import Resources
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.dervich.derrvish_spike_utility import DervishSpikeUtility


class EremitesAttack_Utility(DervishSpikeUtility):
    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Eremites_Attack"),
            current_build=current_build,
            allowed_states=allowed_states)