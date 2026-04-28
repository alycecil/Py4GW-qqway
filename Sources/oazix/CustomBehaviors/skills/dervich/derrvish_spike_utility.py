from enum import Enum
from typing import List, Any, Generator, Callable, override

import PyImGui

from HeroAI.types import SkillType
from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, Range, Agent
from Py4GWCoreLib.enums_src.GameData_enums import Profession
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives.infrastructure.persistence_locator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers import Resources
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import \
    UtilitySkillExecutionStrategy


class TargetingMode(Enum):
    SPIKE = 0
    CLOSEST = 1
    SPREAD = 2
    
class DervishSpikeUtility(CustomSkillUtilityBase):
    def __init__(self,
                 event_bus: EventBus,
                 skill: CustomSkill,
                 current_build: list[CustomSkill],
                 score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 66 if enemy_qte >= 3 else 51 if enemy_qte <= 2 else 26),
                 mana_required_to_cast: int = 5,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
                 mode: TargetingMode = TargetingMode.CLOSEST
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
            execution_strategy=UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END
        )

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.vow_of_strength: CustomSkill = CustomSkill("Vow_of_Strength")
        self.vow_of_silence: CustomSkill = CustomSkill("Vow_of_Silence")
        self.Ebon_Dust_Aura: CustomSkill = CustomSkill("Ebon_Dust_Aura")
        self.sand_shards: CustomSkill = CustomSkill("Sand_Shards")
        self.aura_of_thorns: CustomSkill = CustomSkill("Aura_of_Thorns")
        self.staggering_force: CustomSkill = CustomSkill("Staggering_Force")
        self.dust_cloak: CustomSkill = CustomSkill("Dust_Cloak")
        self.Deaths_Charge: CustomSkill = CustomSkill("Deaths_Charge")
        self.Ebon_Escape: CustomSkill = CustomSkill("Ebon_Escape")
        self.Asuran_Scan: CustomSkill = CustomSkill("Asuran_Scan")
        self.mana_required_to_cast = mana_required_to_cast

        self.model_id_filter: int = int(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "model_id_filter", "5903"))

        # Load mode from persistence or use default
        persisted_mode = PersistenceLocator().skills.read_or_default(
            self.custom_skill.skill_name,
            "mode",
            str(mode.value)
        )
        self.targeting_mode: TargetingMode = TargetingMode(int(persisted_mode))

    def has_dervish_enchantment(self) -> bool:

        effects = GLOBAL_CACHE.Effects.GetEffects(Player.GetAgentID())
        has_dervish: bool = True
        top_skill_id : int | None = None
        for effect in effects:
            skill_id = effect.skill_id
            skill_type, _ = GLOBAL_CACHE.Skill.GetType(skill_id)
            if skill_type == SkillType.Enchantment.value:
                profession_id, _ = GLOBAL_CACHE.Skill.GetProfession(skill_id)
                if profession_id == Profession.Dervish.value:
                    has_dervish = True
                    top_skill_id = skill_id

        if top_skill_id is not None:
            if top_skill_id == self.vow_of_strength.skill_id:
                if constants.DEBUG: print("VoStr is top skill. wait for a recast.")
                return False
            if top_skill_id == self.vow_of_silence.skill_id:
                if constants.DEBUG: print("VoSilence is top skill. wait for a recast.")
                return False
            if top_skill_id == self.Ebon_Dust_Aura.skill_id:
                if constants.DEBUG: print("VoSilence is top skill. wait for a recast.")
                return False
            if top_skill_id == self.sand_shards.skill_id:
                if constants.DEBUG: print("sand_shards is top skill. wait for a recast.")
                return False

            pass

        return has_dervish

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        sort_key = (TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC,
                    TargetingOrder.DISTANCE_ASC,
                    )

        if self.targeting_mode == TargetingMode.CLOSEST or self.targeting_mode == TargetingMode.SPREAD:
            sort_key = (
                TargetingOrder.DISTANCE_ASC,
                TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC,
                )
        
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: not Agent.IsSpirit(agent_id) and (
                    self.targeting_mode != TargetingMode.SPREAD or
                    not CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(self._get_lock_key(agent_id)) # Spread mode won't target those already locked
            ),
            sort_key=sort_key,
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))


    def _get_lock_key(self, agent_id: int) -> str:
        return f"spike_{agent_id}"

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_dervish_enchantment = self.has_dervish_enchantment()

        if not has_dervish_enchantment:

            staggering_force_available = self.is_staggering_force_available()
            dust_cloak_available = self.is_dust_cloak_available()
            aura_of_thorns_available = self.is_aura_of_thorns_available()

            if (staggering_force_available
                and Resources.get_player_absolute_energy() > self.mana_required_to_cast + 10  # todo this better
            ):
                pass # its fine we have a skill to use for the spike
            elif (dust_cloak_available
                  and Resources.get_player_absolute_energy() > self.mana_required_to_cast + 10  # todo this better
            ):
                pass # its fine we have a skill to use for the spike
            elif (aura_of_thorns_available
                  and Resources.get_player_absolute_energy() > self.mana_required_to_cast + 5  # todo this better
            ):
                pass # its fine we have a skill to use for the spike
            else:
                return None

        targets = self._get_targets()
        if len(targets) == 0: return None

        if self.targeting_mode == TargetingMode.SPREAD:
            lock_key = self._get_lock_key(targets[0].agent_id)
            if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key):
                return 10  # someone is already doing that, low priority

        return self.score_definition.get_score(targets[0].enemy_quantity_within_range)

    def is_dust_cloak_available(self):
        return self.dust_cloak.skill_slot is not None and Routines.Checks.Skills.IsSkillSlotReady(
            self.dust_cloak.skill_slot)

    def is_staggering_force_available(self):
        return self.staggering_force.skill_slot is not None and Routines.Checks.Skills.IsSkillSlotReady(
            self.staggering_force.skill_slot)

    def is_shadow_step_available(self):
        return self.Deaths_Charge.skill_slot is not None and Routines.Checks.Skills.IsSkillSlotReady(self.Deaths_Charge.skill_slot)

    def is_asuran_scan_available(self):
        return self.Asuran_Scan.skill_slot is not None and Routines.Checks.Skills.IsSkillSlotReady(self.Asuran_Scan.skill_slot)

    def is_ebon_escape_available(self):
        return self.Ebon_Escape.skill_slot is not None and Routines.Checks.Skills.IsSkillSlotReady(self.Ebon_Escape.skill_slot)

    def is_aura_of_thorns_available(self):
        return self.aura_of_thorns.skill_slot is not None and Routines.Checks.Skills.IsSkillSlotReady(self.aura_of_thorns.skill_slot)

    def _get_vanguard(self) -> list[custom_behavior_helpers.SortableAgentData] | None:

        vanguard: list[
            custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_ncs_of_model_ordered_by_priority_raw(
            model_ids=[self.model_id_filter],
            within_range=Range.Spellcast.value * 1.2,
            sort_key=(TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_allies=None,
            range_to_count_enemies=max(GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id), Range.Adjacent.value))

        if len(vanguard) == 0: return None

        return vanguard

    def _escape_get_targets(self, target_id) -> list[custom_behavior_helpers.SortableAgentData]:

        allies: list[
            custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            sort_key=(TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_allies=None,
            range_to_count_enemies=max(GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id), Range.Adjacent.value)
        )

        vanguard = self._get_vanguard()
        if vanguard is not None:
            allies.extend(vanguard)

            # with vanguards added after means prefer player over npc
            allies = sorted(allies, key=lambda x: -x.enemy_quantity_within_range) # intentional dupe of TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC

        # filter down to just those near target
        pos = Agent.GetXY(target_id)
        max_distance = self.range_for_target()

        if len(allies) == 0:
            if constants.DEBUG: print(f"Failed to find anyone near our target")
            return allies

        def _distance_filter(agent_id):
            agent_x, agent_y = Agent.GetXY(agent_id)
            distance = Utils.Distance((agent_x, agent_y), (pos[0], pos[1]))
            distance_max_distance = distance <= max_distance
            if constants.DEBUG:
                if distance_max_distance:
                    print(f"{Agent.GetNameByID(agent_id)}, agent_id={agent_id} is {distance} gwinches away")
                else:
                    print(f"EXCLUDING {Agent.GetNameByID(agent_id)}, agent_id={agent_id} is {distance} gwinches away")
            return distance_max_distance

        filtered_by_distance_from_target = lambda agent: _distance_filter(agent.agent_id)
        allies = list(filter(filtered_by_distance_from_target, allies))

        return allies

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        lock_key = self._get_lock_key(target.agent_id)
        # just lock to remove from condition
        CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=3)

        wanted_mana = self.mana_required_to_cast
        cast_staggering_force = False
        cast_aura_of_thorns = False
        cast_asuran_scan = False
        cast_dust_cloak = False

        if (self.is_staggering_force_available()
                and Resources.get_player_absolute_energy() > wanted_mana + 10  # todo this better
        ):
            wanted_mana += 10 # todo dervish cost reduction for mysticism
            if constants.DEBUG: print("using spike with staggering_force")
            cast_staggering_force = True

        if (self.is_dust_cloak_available()
                and Resources.get_player_absolute_energy() > wanted_mana + 10  # todo this better
        ):
            wanted_mana += 10 # todo dervish cost reduction for mysticism
            if constants.DEBUG: print("using spike with dust_cloak")
            cast_dust_cloak = True

        if (self.is_aura_of_thorns_available()
              and Resources.get_player_absolute_energy() > wanted_mana + 5  # todo this better
        ):
            wanted_mana += 5 # todo dervish cost reduction for mysticism
            if constants.DEBUG: print("using spike with aura_of_thorns")
            cast_aura_of_thorns = True

        ebon_escape_available = self.is_ebon_escape_available()
        shadow_step_available = self.is_shadow_step_available()

        if shadow_step_available or ebon_escape_available:
            cast_shadow_step = False

            if Resources.get_player_absolute_energy() > wanted_mana + 5:
                # shadowstep?
                wanted_mana += 5
                cast_shadow_step = True
            elif Resources.get_player_absolute_energy() > wanted_mana - 5 and cast_staggering_force and cast_aura_of_thorns:
                wanted_mana -= 5
                cast_staggering_force = False  # prefer slower recharge snare if not enough energy
                cast_shadow_step = True
            elif Resources.get_player_absolute_energy() > wanted_mana - 5 and cast_staggering_force and cast_dust_cloak:
                wanted_mana -= 5
                cast_staggering_force = False  # prefer slower recharge snare if not enough energy
                cast_dust_cloak = True

            if cast_shadow_step:
                player_hp = Agent.GetHealth(Player.GetAgentID())
                range_to_jump = self.range_for_target()

                distance = Utils.Distance(Agent.GetXY(target.agent_id), Player.GetXY())
                if distance > range_to_jump or player_hp < 0.6:
                    has_stepped = False
                    if ebon_escape_available:
                        ee_targets = self._escape_get_targets(target.agent_id)
                        if len(ee_targets) > 0:
                            ee_target = ee_targets[0]
                            print(f"using {self.Ebon_Escape.skill_name} to {ee_target} {Agent.GetNameByID(ee_target.agent_id)}")
                            ee_res = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.Ebon_Escape, target_agent_id=ee_target.agent_id)
                            if ee_res == BehaviorResult.ACTION_PERFORMED:
                                has_stepped = True
                            else:
                                if constants.DEBUG:
                                    print("ee failed, will try to shadow step otherwise")
                        else:
                            if constants.DEBUG:
                                print("Nothing in EE range, will try to fallback to deaths charge")

                    if not has_stepped and shadow_step_available:
                        # we need a heal or are out of attack range
                        print(f"using {self.Deaths_Charge.skill_name} to shadowstep")
                        yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.Deaths_Charge, target_agent_id=target.agent_id)

        if self.is_asuran_scan_available() and Resources.get_player_absolute_energy() > wanted_mana + 5:
            # asuran scan too!
            cast_asuran_scan = True
            wanted_mana += 5

        ping = 150 # todo read from frame

        # Do we need to wait for dervish flash cooldown?
        if cast_staggering_force and cast_aura_of_thorns:
            yield from custom_behavior_helpers.Actions.cast_skill(self.staggering_force)
            if cast_asuran_scan:
                yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.Asuran_Scan, target_agent_id=target.agent_id)
                yield from custom_behavior_helpers.Helpers.wait_for(750 + ping) # should add ping here
            else:
                yield from custom_behavior_helpers.Helpers.wait_for(1000 + ping) # should add ping here
            yield from custom_behavior_helpers.Actions.cast_skill(self.aura_of_thorns)
        elif cast_staggering_force and cast_dust_cloak:
            yield from custom_behavior_helpers.Actions.cast_skill(self.staggering_force)
            if cast_asuran_scan:
                yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.Asuran_Scan, target_agent_id=target.agent_id)
                yield from custom_behavior_helpers.Helpers.wait_for(750 + ping) # should add ping here
            else:
                yield from custom_behavior_helpers.Helpers.wait_for(1000 + ping) # should add ping here
            yield from custom_behavior_helpers.Actions.cast_skill(self.dust_cloak)
        else:
            if cast_staggering_force:
                yield from custom_behavior_helpers.Actions.cast_skill(self.staggering_force)
            if cast_aura_of_thorns:
                yield from custom_behavior_helpers.Actions.cast_skill(self.aura_of_thorns)
            if cast_asuran_scan:
                yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.Asuran_Scan, target_agent_id=target.agent_id)
            if cast_dust_cloak:
                yield from custom_behavior_helpers.Actions.cast_skill(self.dust_cloak)

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

    def range_for_target(self):
        range_to_jump = Range.Nearby.value
        if Agent.IsCrippled(Player.GetAgentID()):
            range_to_jump = Range.Adjacent.value
        return range_to_jump

    @override
    def customized_debug_ui(self, current_state):
        PyImGui.bullet_text(f"has_dervish_enchantment : {self.has_dervish_enchantment()}")

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text("Mode:")
        PyImGui.same_line(0, -1)

        # Radio buttons for mode selection
        mode_value = self.targeting_mode.value
        mode_value = PyImGui.radio_button(TargetingMode.SPIKE.name, mode_value, TargetingMode.SPIKE.value)
        PyImGui.same_line(0, -1)
        mode_value = PyImGui.radio_button( TargetingMode.CLOSEST.name, mode_value, TargetingMode.CLOSEST.value)
        PyImGui.same_line(0, -1)
        mode_value = PyImGui.radio_button(TargetingMode.SPREAD.name, mode_value, TargetingMode.SPREAD.value)

        # Update mode if changed
        self.targeting_mode = TargetingMode(mode_value)

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "model_id_filter", str(self.model_id_filter))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name),"targeting_mode",str(self.targeting_mode.value))
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "model_id_filter", str(self.model_id_filter))
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name),"targeting_mode",str(self.targeting_mode.value))
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "model_id_filter")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name),"targeting_mode")
        print("configuration deleted")
