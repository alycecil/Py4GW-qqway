from typing import cast, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility
from Sources.oazix.CustomBehaviors.skills.monk.blessed_signet_utility import Blessed_Signet_EffectUpUtility
from Sources.oazix.CustomBehaviors.skills.monk.spell_breaker_utility import SpellBreakerUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_lost_souls_utility import SignetOfLostSoulsUtility
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_effect import ShouldWaitForEffect
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_heroic_refrain import ShouldWaitForHeroicRefrain
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_serpents_quickness import ShouldWaitForSerpentsQuickness
from Sources.oazix.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.finish_him_utility import FinishHimUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_utility import RawSimpleHealUtility
from Sources.oazix.CustomBehaviors.skills.monk.cure_hex_utility import CureHexUtility
from Sources.oazix.CustomBehaviors.skills.monk.dismiss_condition_utility import DismissConditionUtility
from Sources.oazix.CustomBehaviors.skills.monk.draw_conditions_utility import DrawConditionsUtility
from Sources.oazix.CustomBehaviors.skills.monk.dwaynas_kiss_utility import DwaynasKissUtility
from Sources.oazix.CustomBehaviors.skills.monk.protective_spirit_utility import ProtectiveSpiritUtility
from Sources.oazix.CustomBehaviors.skills.monk.reversal_of_fortune_utility import ReversalOfFortuneUtility
from Sources.oazix.CustomBehaviors.skills.monk.seed_of_life_utility import SeedOfLifeUtility
from Sources.oazix.CustomBehaviors.skills.monk.shield_of_absorption_utility import ShieldOfAbsorptionUtility
from Sources.oazix.CustomBehaviors.skills.monk.unyielding_aura_drop_utility import UnyieldingAuraDropUtility
from Sources.oazix.CustomBehaviors.skills.monk.unyielding_aura_utility import UnyieldingAuraUtility
from Sources.oazix.CustomBehaviors.skills.monk.vigorous_spirit_utility import VigorousSpiritUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_mimicry_utility import ArcaneMimicryUtility


class MonkSpellBreaker_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills

        self.blessed_signet_utility: CustomSkillUtilityBase = Blessed_Signet_EffectUpUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(73),
        )

        self.Ether_Signet_utility: CustomSkillUtilityBase = AutoCombatUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Ether_Signet"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(40),
        )
        self.Spell_Breaker_utility: CustomSkillUtilityBase = SpellBreakerUtility(event_bus=self.event_bus, current_build=in_game_build)

        self.arcane_echo_utility: CustomSkillUtilityBase = ArcaneEchoUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_copy= self.Spell_Breaker_utility,
            new_copied_instance= SpellBreakerUtility(
                event_bus=self.event_bus,
                current_build=in_game_build),
            arcane_echo_score_definition=ScoreStaticDefinition(82))

        self.auspicious_incantation_utility: CustomSkillUtilityBase = AuspiciousIncantationUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_cast=self.arcane_echo_utility,
            score_definition=ScoreStaticDefinition(82)
        )

        self.patient_spirit_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Patient_Spirit"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.Jameis_Gaze_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Jameis_Gaze"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(6))

        self.Signet_of_Rejuvenation_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Signet_of_Rejuvenation"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(6))
        self.Signet_of_Devotion_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Signet_of_Devotion"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(5))

        self.seed_of_life_utility: CustomSkillUtilityBase = (SeedOfLifeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1))
                                                                        .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))
       
        self.protective_spirit_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.shield_of_absorption_utility: CustomSkillUtilityBase = ShieldOfAbsorptionUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.dwaynas_kiss_utility: CustomSkillUtilityBase = DwaynasKissUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(7))
        self.reversal_of_fortune_utility: CustomSkillUtilityBase = ReversalOfFortuneUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(6))

        self.cure_hex_utility: CustomSkillUtilityBase = CureHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        self.dismiss_condition_utility: CustomSkillUtilityBase = DismissConditionUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        self.draw_conditions_utility: CustomSkillUtilityBase = DrawConditionsUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(51))

        self.selfless_spirit_luxon_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_luxon"), score_definition=ScoreStaticDefinition(88))
        self.selfless_spirit_kurzick_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_kurzick"), score_definition=ScoreStaticDefinition(88))

        self.serpents_quickness_prep_utility: CustomSkillUtilityBase = PreparationUtility(event_bus=self.event_bus,
                                                             prep_skill=CustomSkill("Serpents_Quickness"),
                                                             target_utilities=[self.seed_of_life_utility, self.selfless_spirit_luxon_utility, self.selfless_spirit_kurzick_utility], current_build=in_game_build, score_definition=ScoreStaticDefinition(94))
        self.dwarven_stability_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Dwarven_Stability"), score_definition=ScoreStaticDefinition(95))
        self.rebirth_utility: CustomSkillUtilityBase = GenericResurrectionUtility(event_bus=self.event_bus, skill=CustomSkill("Rebirth"), current_build=in_game_build, score_definition=ScoreStaticDefinition(94))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.vigorous_spirit_utility: CustomSkillUtilityBase = VigorousSpiritUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(72))

        # combo Serpents_Quickness + Selfless_Spirit + Dwarven_Stability
        self.selfless_spirit_kurzick_utility: CustomSkillUtilityBase = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_kurzick"), score_definition=ScoreStaticDefinition(88))
                                                                        .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))

        self.selfless_spirit_luxon_utility: CustomSkillUtilityBase = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_luxon"), score_definition=ScoreStaticDefinition(88))
                                                                      .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))

        self.dwarven_stability_utility = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Dwarven_Stability"), score_definition=ScoreStaticDefinition(95))

        self.serpents_quickness_utility = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Serpents_Quickness"), score_definition=ScoreStaticDefinition(94))
                                           .add_plugin_precondition(lambda x: ShouldWaitForEffect(x.custom_skill, CustomSkill("Dwarven_Stability"), True)))

        self.Divine_Spirit_utility: CustomSkillUtilityBase = PreparationUtility(
            event_bus=self.event_bus,
            prep_skill=CustomSkill("Divine_Spirit"),
            target_utilities=[self.protective_spirit_utility, self.seed_of_life_utility, self.cure_hex_utility, self.dismiss_condition_utility, self.Spell_Breaker_utility],
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(55),
            mana_required_to_cast=15,
            allowed_states=[BehaviorState.IN_AGGRO]
        )

        # common
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.signet_of_lost_souls_utility: CustomSkillUtilityBase = SignetOfLostSoulsUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.finish_him_utility: CustomSkillUtilityBase = FinishHimUtility(event_bus=self.event_bus, current_build=in_game_build)

        # we have an additionnal utility to drop the buff that we could have aquired from mimicry
        self.unyielding_aura_drop_utility: CustomSkillUtilityBase = UnyieldingAuraDropUtility(event_bus=self.event_bus, current_build=in_game_build)

        self.arcane_mimicry_utility: CustomSkillUtilityBase = (ArcaneMimicryUtility(event_bus=self.event_bus,
                                                                                   current_build=in_game_build,
                                                                                   pre_check_condition= lambda: not cast(UnyieldingAuraDropUtility, self.unyielding_aura_drop_utility).has_buff(),
                                                                                   skill_to_copy_instance= lambda: UnyieldingAuraUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(93)))
                                                                        .add_plugin_precondition(lambda x: ShouldWaitForHeroicRefrain(x.custom_skill, True))
                                                                        )


    @property
    @override
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        base = super().additional_autonomous_skills
        # not part of the skillbar, if unyielding aura is aquired from mimicry
        base.append(self.unyielding_aura_drop_utility)
        return base

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.signet_of_lost_souls_utility,
            self.by_urals_hammer_utility,
            self.breath_of_the_great_dwarf_utility,
            self.finish_him_utility,

            self.Jameis_Gaze_utility,
            self.dwaynas_kiss_utility,

            self.patient_spirit_utility,
            self.Spell_Breaker_utility,
            self.seed_of_life_utility,
            self.protective_spirit_utility,
            self.shield_of_absorption_utility,
            self.cure_hex_utility,
            self.dismiss_condition_utility,
            self.draw_conditions_utility,
            self.serpents_quickness_utility,
            self.selfless_spirit_luxon_utility,
            self.selfless_spirit_kurzick_utility,
            self.vigorous_spirit_utility,
            self.arcane_mimicry_utility,
            self.dwarven_stability_utility,
            self.rebirth_utility,

            self.Divine_Spirit_utility,
            self.Signet_of_Rejuvenation_utility,
            self.Signet_of_Devotion_utility,

            self.blessed_signet_utility,
            self.Ether_Signet_utility,

            self.arcane_echo_utility,
            self.auspicious_incantation_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.Spell_Breaker_utility.custom_skill,
        ]
