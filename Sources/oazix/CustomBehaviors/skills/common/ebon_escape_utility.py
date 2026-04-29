from typing import Any, Generator, override
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib import Agent, Player, Party
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.plugins.targeting_modifiers.buff_configurator import BuffConfigurator

class EbonEscapeUtility(CustomSkillUtilityBase):

    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(5),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Ebon_Escape"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerHealthGravityDefinition = score_definition
        self.add_plugin_targetting_modifier(lambda x: BuffConfigurator(event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL))

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        save_the_turtle = custom_behavior_helpers.Targets.save_the_turtle(self.custom_skill.skill_id)
        if len(save_the_turtle) > 0:
            return save_the_turtle

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id:
                agent_id != Player.GetAgentID() and 
                Agent.GetHealth(agent_id) < 0.8 and
                self.get_plugin_targeting_modifiers_filtering_predicate_any()(agent_id),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if (current_state == BehaviorState.IDLE or current_state == BehaviorState.FAR_FROM_AGGRO) and not Party.IsPartyLeader():
            if Party.IsPartyLoaded():
                my_id = Player.GetAgentID()

                distance = self.distance_from_lead(my_id, Party.GetPartyLeaderID())
                if distance > 1000:
                    pass
                elif distance > 800:
                    return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
                elif distance > 500:
                    return self.score_definition.get_score(HealingScore.PARTY_HEALTHY)


        # self heal
        if Agent.GetHealth(Player.GetAgentID()) < 0.60: return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY) 

        # allies heal
        targets = self._get_targets()
        if len(targets) == 0: return None

        if targets[0].hp < 0.40:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
        if targets[0].hp < 0.60:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED)
        
        return None

    def _get_lock_key(self, agent_id: int) -> str:
        return f"EbonEscape_{agent_id}"

    @override
    def _execute(self, current_state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        targets = self._get_targets()
        target: int | None = None
        distance_mode = False
        if len(targets) == 0:
            if (current_state == BehaviorState.IDLE or current_state == BehaviorState.FAR_FROM_AGGRO) and not Party.IsPartyLeader():
                if Party.IsPartyLoaded():
                    leader = Party.GetPartyLeaderID()

                    targets = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
                        within_range=Range.Spellcast.value,
                        condition=lambda agent_id: agent_id != Player.GetAgentID()
                        )

                    if len(targets) > 0:
                        targets=sorted(targets, key=lambda x: self.distance_from_lead(x.agent_id, leader))
                        target = targets[0].agent_id
                        distance_mode = True
                else:
                    print("Party not loaded?")

        else:
            target = targets[0].agent_id

        if target is None:
            if constants.DEBUG: print("No one there? I must have gotten stuck")
            return BehaviorResult.ACTION_SKIPPED

        if Agent.GetHealth(target) < 0.40 or Agent.GetHealth(Player.GetAgentID()) < 0.60:
            print(f"Low hp hop to target {target}")
            pass
        elif distance_mode and (current_state == BehaviorState.IDLE or current_state == BehaviorState.FAR_FROM_AGGRO) and not Party.IsPartyLeader():
            pass
        else:
            lock_key = self._get_lock_key(target)
            print(f"Check locked {lock_key}")
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, 1):
                if constants.DEBUG: print("Already locked")
                yield
                return BehaviorResult.ACTION_SKIPPED

        print(f"Trying to step to {target}")
        Player.Interact(target, False)

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)

        Player.Interact(target, False)

        return result

    def distance_from_lead(self, my_id, party_leader_id):
        leader_x, leader_y = Agent.GetXY(party_leader_id)
        my_x, my_y = Agent.GetXY(my_id)
        distance = Utils.Distance((leader_x, leader_y), (my_x, my_y))
        return distance
