from typing import Any, Generator, override
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums import Profession, Range
from Py4GWCoreLib import Agent, Player, Party
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

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
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE])
                
        self.score_definition: ScorePerHealthGravityDefinition = score_definition

        data: str | None = PersistenceLocator().skills.read(self.custom_skill.skill_name, "buff_configuration")
        if data is not None:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget.instanciate_from_string(self.event_bus, self.custom_skill, data)
        else:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL)

    def _save_the_turtle(self) -> list[custom_behavior_helpers.SortableAgentData] | None:
        # underworld
        #TorturedSpirit1 = 2353
        #TorturedSpirit2 = 2354
        # that gd luxon quest
        # THE_BABY_TURTLES = 3587
        THE_BABY_TURTLES2 = 3638
        # FOW
        # GRIFFS = 2827

        important_npcs: list[
            custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_ncs_of_model_ordered_by_priority_raw(
            model_ids=[
                #THE_BABY_TURTLES,
                THE_BABY_TURTLES2,
                #TorturedSpirit1,
                #TorturedSpirit2,
                #GRIFFS
            ],
            within_range=Range.Spellcast.value * 1.5,
            sort_key=(TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_allies=None,
            range_to_count_enemies=max(GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id), Range.Adjacent.value))

        if len(important_npcs) > 0:
            if constants.DEBUG: print("Turtles detected")

            condition=lambda agent: agent.agent_id != Player.GetAgentID() and Agent.GetHealth(agent.agent_id) < 0.7
            important_npcs = list(filter(condition, important_npcs))

            if len(important_npcs) > 0:
                print("I HAVE TURTLES TO SAVE")

        return important_npcs

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        save_the_turtle = self._save_the_turtle()
        if len(save_the_turtle) > 0:
            return save_the_turtle

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.1,
            condition=lambda agent_id: 
                agent_id != Player.GetAgentID() and 
                Agent.GetHealth(agent_id) < 0.8 and
                self.buff_configuration.get_agent_id_predicate()(agent_id),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if (current_state == BehaviorState.IDLE or current_state == BehaviorState.FAR_FROM_AGGRO) and not Party.IsPartyLeader():
            if Party.IsPartyLoaded():
                my_id = Player.GetAgentID()

                distance = self.distance_from_lead(my_id, Party.GetPartyLeaderID())
                if distance > Range.Area.value * 3:
                    return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
                if distance > Range.Area.value * 1.5:
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

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return self.buff_configuration

    @override
    def has_persistence(self) -> bool:
        return True
    
    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        print("configuration saved as global")

