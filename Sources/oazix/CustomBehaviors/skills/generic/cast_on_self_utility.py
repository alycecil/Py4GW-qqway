from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player, AgentArray, Agent
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers import Resources
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.parties.party_disability_manager import PartyDisabilityManager
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_target_by_nearby import ScoreFactorsDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class CastOnSelfUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    skill: CustomSkill,
    current_build: list[CustomSkill],
    score_definition: ScoreFactorsDefinition,
    mana_required_to_cast: int = 0,
    renew_before_expiration_in_milliseconds: int = 200,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    after_cast_delay: bool = True,
    target_self: bool = True,
    range_to_count_allies: float | None = None,
    range_to_count_enemies: float | None = None,
    is_alive: bool = True,
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreFactorsDefinition = score_definition
        self.renew_before_expiration_in_milliseconds: int = renew_before_expiration_in_milliseconds

        self.after_cast_delay = after_cast_delay
        self.target_self = target_self

        self.range_to_count_allies = range_to_count_allies
        self.range_to_count_enemies = range_to_count_enemies

        self.is_alive = is_alive

    def player_agent_data(self, within_range: float = Range.Adjacent.value) -> custom_behavior_helpers.SortableAgentData:
        agent_id = Player.GetAgentID()
        player_pos: tuple[float, float] = Player.GetXY()
        all_agent_ids: list[int] = AgentArray.GetAllyArray() # only 8 team members  (no pets, no npc-allies)
        all_agent_pets = [agent_id for agent_id in AgentArray.GetSpiritPetArray() if Agent.IsPet(agent_id)] # add pets
        all_agent_ids = all_agent_ids + all_agent_pets

        all_enemies_ids: list[int] = AgentArray.GetEnemyArray()

        agent_ids = AgentArray.Filter.ByDistance(all_agent_ids, player_pos, within_range)
        if self.is_alive:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: Agent.IsAlive(agent_id))
        else:
            agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: not Agent.IsAlive(agent_id))
        # if self.nearyby_condition is not None: agent_ids = AgentArray.Filter.ByCondition(agent_ids, self.nearyby_condition)

        # scan enemies within range
        enemies_ids = AgentArray.Filter.ByCondition(all_enemies_ids, lambda agent_id: Agent.IsAlive(agent_id))
        enemies_ids = AgentArray.Filter.ByDistance(enemies_ids, player_pos, within_range)
        enemies_quantity_within_range = 0
        allies_quantity_within_range = 0

        if self.range_to_count_enemies is not None or self.range_to_count_allies is not None:
            if self.range_to_count_enemies is not None:
                for enemy_id in enemies_ids:
                    if Utils.Distance(Agent.GetXY(enemy_id), player_pos) <= self.range_to_count_enemies:
                        enemies_quantity_within_range += 1

            if self.range_to_count_allies is not None:
                for other_agent_id in agent_ids:
                    if other_agent_id != agent_id and Utils.Distance(Agent.GetXY(other_agent_id), player_pos) <= self.range_to_count_allies:
                        allies_quantity_within_range += 1

        return SortableAgentData(
            agent_id=agent_id,
            distance_from_player=0,
            hp=Agent.GetHealth(agent_id),
            is_caster=Agent.IsCaster(agent_id),
            is_melee=Agent.IsMelee(agent_id),
            is_martial=Agent.IsMartial(agent_id),
            enemy_quantity_within_range=enemies_quantity_within_range,
            agent_quantity_within_range=allies_quantity_within_range,
            energy=Resources.get_energy_percent_in_party(agent_id),
            hex_priority_level=PartyDisabilityManager().get_hex_score(agent_id),
            condition_priority_level=PartyDisabilityManager().get_condition_score(agent_id),
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        if not has_buff: return self.score_definition.get_score(self.player_agent_data())
        
        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(Player.GetAgentID(), self.custom_skill.skill_id)
        if buff_time_remaining <= self.renew_before_expiration_in_milliseconds: return self.score_definition.get_score(self.player_agent_data())
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result: BehaviorResult = BehaviorResult.ACTION_SKIPPED

        if self.target_self:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=Player.GetAgentID(), after_cast_delay=self.after_cast_delay)
        else:
            result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill, after_cast_delay=self.after_cast_delay)

        return result
