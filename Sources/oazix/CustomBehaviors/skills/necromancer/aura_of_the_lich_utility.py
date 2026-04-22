from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, AgentArray, Range, Player
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class Aura_of_the_Lich_Utility(CustomSkillUtilityBase):

    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda corpse_count: 70 if corpse_count >= 5 else 35 if corpse_count >= 3 else 25 if corpse_count >= 2 else 10),
                 mana_required_to_cast: int = 5,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill = CustomSkill("Aura_of_the_Lich"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self._previous_state: BehaviorState | None = None

    def _get_targets(self) -> list[int]:

        def _AllowedAlliegance(agent_id):
            _, alliegance = Agent.GetAllegiance(agent_id)

            if (alliegance == "Ally" or
                alliegance == "Neutral" or
                alliegance == "Enemy" or
                alliegance == "NPC/Minipet"
                ):
                return True
            return False

        agent_ids: list[int] = AgentArray.GetAgentArray()
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, Player.GetXY(), Range.Earshot.value)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: 
                                                  Agent.IsDead(agent_id) and 
                                                  not Agent.HasBossGlow(agent_id) and # filter out boss minions (that corpses never disappear)
                                                  not Agent.IsSpirit(agent_id) and 
                                                  not Agent.IsSpawned(agent_id) and 
                                                  not Agent.IsMinion(agent_id)
                                            )
        
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, _AllowedAlliegance)

        # we order by distance ASC
        agent_ids = AgentArray.Sort.ByDistance(agent_ids, Player.GetXY())

        return agent_ids

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # Track state transitions - reset timer when entering FAR_FROM_AGGRO
        targets = self._get_targets()
        corpse_count = len(targets)

        if corpse_count == 0 and current_state not in [BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE]:
            return None

        return self.score_definition.get_score(corpse_count)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result

    @override
    def customized_debug_ui(self, current_state):
        pass
        # targets = self._get_targets()

        # for agent_id in targets:
