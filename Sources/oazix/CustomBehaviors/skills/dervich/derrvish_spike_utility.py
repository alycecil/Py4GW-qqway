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

class DervishSpikeUtility(CustomSkillUtilityBase):
    def __init__(self,
                 event_bus: EventBus,
                 skill: CustomSkill,
                 current_build: list[CustomSkill],
                 score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 66 if enemy_qte >= 3 else 51 if enemy_qte <= 2 else 26),
                 mana_required_to_cast: int = 5,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.vow_of_strength: CustomSkill = CustomSkill("Vow_of_Strength")
        self.vow_of_silence: CustomSkill = CustomSkill("Vow_of_Silence")
        self.sand_shards: CustomSkill = CustomSkill("Sand_Shards")
        self.aura_of_thorns: CustomSkill = CustomSkill("Aura_of_Thorns")
        self.staggering_force: CustomSkill = CustomSkill("Staggering_Force")
        self.mana_required_to_cast = mana_required_to_cast

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
            if top_skill_id == self.sand_shards.skill_id:
                if constants.DEBUG: print("sand_shards is top skill. wait for a recast.")
                return False

            pass

        return has_dervish

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.DISTANCE_ASC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_dervish_enchantment = self.has_dervish_enchantment()
        if not has_dervish_enchantment:
            if (self.staggering_force.skill_slot is not None
                and Routines.Checks.Skills.IsSkillSlotReady(self.staggering_force.skill_slot)
                and Resources.get_player_absolute_energy() > self.mana_required_to_cast + 10  # todo this better
            ):
                pass # its fine we have a skill to use for the spike
            elif (self.aura_of_thorns.skill_slot is not None
                    and Routines.Checks.Skills.IsSkillSlotReady(self.aura_of_thorns.skill_slot)
                    and Resources.get_player_absolute_energy() > self.mana_required_to_cast + 5  # todo this better
            ):
                pass # its fine we have a skill to use for the spike
            else:
                return None

        targets = self._get_targets()
        if len(targets) == 0: return None
        return self.score_definition.get_score(targets[0].enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]


        has_dervish_enchantment = self.has_dervish_enchantment()
        if not has_dervish_enchantment:
            if (self.staggering_force.skill_slot is not None
                    and Routines.Checks.Skills.IsSkillSlotReady(self.staggering_force.skill_slot)
                    and Resources.get_player_absolute_energy() > self.mana_required_to_cast + 10  # todo this better
            ):
                print("using spike with staggering_force")
                yield from custom_behavior_helpers.Actions.cast_skill(self.staggering_force)
            elif (self.aura_of_thorns.skill_slot is not None
                  and Routines.Checks.Skills.IsSkillSlotReady(self.aura_of_thorns.skill_slot)
                  and Resources.get_player_absolute_energy() > self.mana_required_to_cast + 5  # todo this better
            ):
                print("using spike with aura_of_thorns")
                yield from custom_behavior_helpers.Actions.cast_skill(self.aura_of_thorns)
            else:
                return None

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

    @override
    def customized_debug_ui(self, current_state):
        PyImGui.bullet_text(f"has_dervish_enchantment : {self.has_dervish_enchantment()}")
