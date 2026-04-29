from typing import override

from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_frustration_utility import CryOfFrustrationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.drain_enchantment_utility import DrainEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.ether_nightmare_utility import EtherNightmareUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.leech_signet_utility import LeechSignetUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.overload_utility import OverloadUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_enchantment_utility import ShatterEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_hex_utility import ShatterHexUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.necrosis_utility import NecrosisUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.overload_utility import OverloadUtility

class MesmerESurgery_Icy_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # interrupt
        self.cry_of_pain_utility: CustomSkillUtilityBase = CryOfPainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(90))
        self.cry_of_frustration_utility: CustomSkillUtilityBase = CryOfFrustrationUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(91))
        self.leech_signet_utility: CustomSkillUtilityBase = LeechSignetUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        # hex
        self.mistrust_utility: CustomSkillUtilityBase = MistrustUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 40 if enemy_qte >= 2 else 10), mana_required_to_cast=10)
        self.unnatural_signet_utility: CustomSkillUtilityBase = UnnaturalSignetUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 90 if enemy_qte >= 2 else 40 if enemy_qte >= 2 else 10))
        self.ether_nightmare_lux_utility: CustomSkillUtilityBase = EtherNightmareUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Ether_Nightmare_luxon"))
        self.ether_nightmare_kurz_utility: CustomSkillUtilityBase = EtherNightmareUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Ether_Nightmare_kurzick"))

        #shatter/drain
        self.shatter_hex_utility: CustomSkillUtilityBase = ShatterHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 95 if enemy_qte >= 2 else 20))
        self.shatter_enchantment_utility: CustomSkillUtilityBase = ShatterEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.drain_enchantment_utility: CustomSkillUtilityBase = DrainEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        # aoe
        self.energy_surge_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus, skill=CustomSkill("Energy_Surge"), current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte:89 if enemy_qte >= 3 else 79),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            mana_required_to_cast=7)
        self.overload_utility: CustomSkillUtilityBase = OverloadUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.chaos_storm_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Chaos_Storm"), current_build=in_game_build, mana_required_to_cast=15)
        self.wastrels_demise_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Wastrels_Demise"), current_build=in_game_build, mana_required_to_cast=15)
        self.spiritual_pain_utility: CustomSkillUtilityBase = SpiritualPainUtility(event_bus=self.event_bus, current_build=in_game_build, mana_required_to_cast=10)

        # utilities
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)

        # necrosis
        self.necrosis_utility: CustomSkillUtilityBase = NecrosisUtility(event_bus=self.event_bus, current_build=in_game_build)

        # Snare / combo pair (use per-agent scoring for AOE utility)
        self.deep_freeze_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Deep_Freeze"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 2 if q >= 3 else 1 if q <= 2 else 0),
            mana_required_to_cast=8
        )

        # Auspicious configured to cast Deep Freeze immediately after if appropriate
        self.auspicious_incantation_utility: CustomSkillUtilityBase = AuspiciousIncantationUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_cast=self.deep_freeze_utility,
            score_definition=ScoreStaticDefinition(87)
        )

        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(90), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte >= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.cry_of_pain_utility,
            self.cry_of_frustration_utility,

            self.shatter_hex_utility,
            self.shatter_enchantment_utility,
            self.drain_enchantment_utility,

            self.mistrust_utility,
            self.unnatural_signet_utility,
            self.ether_nightmare_kurz_utility,
            self.ether_nightmare_lux_utility,

            self.energy_surge_utility,
            self.overload_utility,
            self.chaos_storm_utility,
            self.wastrels_demise_utility,
            self.spiritual_pain_utility,

            self.leech_signet_utility,

            self.overload_utility,

            self.fall_back_utility,
            self.deep_freeze_utility,
            self.auspicious_incantation_utility,

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.breath_of_the_great_dwarf_utility,
            self.by_urals_hammer_utility,

            self.necrosis_utility
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.energy_surge_utility.custom_skill,
            self.deep_freeze_utility.custom_skill,
            self.auspicious_incantation_utility.custom_skill
        ]