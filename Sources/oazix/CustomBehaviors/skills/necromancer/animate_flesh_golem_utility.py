from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, AgentArray, Range, Player, Routines
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import \
    MinionInvocationFromCorpseUtility


class AnimateFleshGolemCorpseUtility(MinionInvocationFromCorpseUtility):

    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    score_definition: ScoreStaticDefinition = ScoreStaticDefinition(75),
    mana_required_to_cast: int = 10,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Animate_Flesh_Golem"),
            current_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states
        )

        self.score_definition: ScoreStaticDefinition = score_definition
        self.far_from_aggro_timer = ThrottledTimer(5_000)  # 5s max window for FAR_FROM_AGGRO
        self._previous_state: BehaviorState | None = None
        self.flesh_golem_model_id: int = 4260

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        npc_agent_id: int = Routines.Agents.GetNearestAliveAgentByModelID(self.flesh_golem_model_id, Range.Longbow.value)
        if npc_agent_id is not None and npc_agent_id != 0:
            return None

        evaluate = super()._evaluate(current_state, previously_attempted_skills)
        return evaluate

