from typing import List, Any, Generator, Callable, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_escape_utility import EbonEscapeUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.finish_him_utility import FinishHimUtility
from Sources.oazix.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.auto_combat_utility import AutoCombatUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import MinionInvocationFromCorpseUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_frustration_utility import CryOfFrustrationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.drain_enchantment_utility import DrainEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.ether_nightmare import EtherNightmareUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.power_drain_utility import PowerDrainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_enchantment_utility import ShatterEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_hex_utility import ShatterHexUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_bond_utility import BloodBondUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_is_power_utility import BloodIsPowerUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_of_the_master import BloodOfTheMasterUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.discord_utility import DiscordUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.foul_feast_utility import FoulFeastUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.necrosis_utility import NecrosisUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_corruption import SignetOfCorruptionUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_lost_souls_utility import SignetOfLostSoulsUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.suffering import SufferingUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.mend_body_and_soul_utility import MendBodyAndSoulUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.life_utility import LifeUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.protective_was_kaolai_utility import ProtectiveWasKaolaiUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.soothing_memories_utility import SoothingMemoriesUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.spirit_light_utility import SpiritLightUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.spirit_transfer_utility import SpiritTransferUtility


class NecromancerNecrosisFoC_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.necrosis_utility: CustomSkillUtilityBase = NecrosisUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.discord_utility: CustomSkillUtilityBase = DiscordUtility(event_bus=self.event_bus, current_build=in_game_build)

        self.cultists_fervor: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Cultists_Fervor"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(90),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])


        # MM skills
        self.animate_shambling_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Shambling_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(62))
        self.animate_bone_fiend_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Bone_Fiend"), current_build=in_game_build, score_definition=ScoreStaticDefinition(61))
        self.animate_bone_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Bone_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(59))
        self.animate_vampiric_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Vampiric_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60))
        self.blood_of_the_master_utility: CustomSkillUtilityBase = BloodOfTheMasterUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(33))

        # optional
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(30))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.foul_feast_utility: CustomSkillUtilityBase = FoulFeastUtility(event_bus=self.event_bus, skill=CustomSkill("Foul_Feast"), current_build=in_game_build, mana_required_to_cast=15, score_definition=ScoreStaticDefinition(49)) # let's keep 15 mana to not be out of mana spamming it

        # interrupt
        self.cry_of_pain_utility: CustomSkillUtilityBase = CryOfPainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(90))
        self.cry_of_frustration_utility: CustomSkillUtilityBase = CryOfFrustrationUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(91))
        self.power_drain_utility: CustomSkillUtilityBase = PowerDrainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(92))

        # hex
        self.mistrust_utility: CustomSkillUtilityBase = MistrustUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 40 if enemy_qte <= 2 else 0), mana_required_to_cast=10)
        self.unnatural_signet_utility: CustomSkillUtilityBase = UnnaturalSignetUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 90 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 5))
        self.ether_nightmare_lux_utility: CustomSkillUtilityBase = EtherNightmareUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Ether_Nightmare_luxon"))
        self.ether_nightmare_kurz_utility: CustomSkillUtilityBase = EtherNightmareUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Ether_Nightmare_kurzick"))
        self.suffering_utility: CustomSkillUtilityBase = SufferingUtility(event_bus=self.event_bus, current_build=in_game_build)

        # condispam



        #shatter/drain
        self.shatter_hex_utility: CustomSkillUtilityBase = ShatterHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 95 if enemy_qte >= 2 else 20))
        self.shatter_enchantment_utility: CustomSkillUtilityBase = ShatterEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.drain_enchantment_utility: CustomSkillUtilityBase = DrainEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        # aoe
        self.energy_surge_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Energy_Surge"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 3 else 52 if enemy_qte <= 2 else 0), mana_required_to_cast=12)
        self.overload_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Overload"), current_build=in_game_build, mana_required_to_cast=15)
        self.chaos_storm_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Chaos_Storm"), current_build=in_game_build, mana_required_to_cast=15)
        self.wastrels_demise_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Wastrels_Demise"), current_build=in_game_build, mana_required_to_cast=15)
        self.spiritual_pain_utility: CustomSkillUtilityBase = SpiritualPainUtility(event_bus=self.event_bus, current_build=in_game_build, mana_required_to_cast=10)
        self.feast_of_corruption_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Feast_of_Corruption"), current_build=in_game_build, mana_required_to_cast=15)

        self.Signet_of_Corruption_luxon_utility: CustomSkillUtilityBase = SignetOfCorruptionUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Signet_of_Corruption_luxon"),
            current_build=in_game_build)
        self.Signet_of_Corruption_kurzick_utility: CustomSkillUtilityBase = SignetOfCorruptionUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Signet_of_Corruption_kurzick"),
            current_build=in_game_build)

        self.arcane_echo_utility: CustomSkillUtilityBase = ArcaneEchoUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_copy= self.feast_of_corruption_utility,
            new_copied_instance= RawAoeAttackUtility(
                event_bus=self.event_bus,
                skill=CustomSkill("Feast_of_Corruption"),
                current_build=in_game_build,
                score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 3 else 50 if enemy_qte <= 2 else 20),
                mana_required_to_cast=12),
            arcane_echo_score_definition=ScoreStaticDefinition(82))
        self.auspicious_incantation_utility: CustomSkillUtilityBase = AuspiciousIncantationUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_cast=self.arcane_echo_utility,
            auspicious_score_definition=ScoreStaticDefinition(82)
        )

        # utilities
        # todo low energy check
        self.energy_tap_utility: CustomSkillUtilityBase = AutoCombatUtility(event_bus=self.event_bus, skill=CustomSkill("Energy_Tap"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)

        # common
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(event_bus=self.event_bus, score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.signet_of_lost_souls_utility: CustomSkillUtilityBase = SignetOfLostSoulsUtility(event_bus=self.event_bus, current_build=in_game_build)
        #self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.air_of_superiority_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Air_of_Superiority"), mana_required_to_cast=5, current_build=in_game_build, score_definition=ScoreStaticDefinition(50), allowed_states=[BehaviorState.IN_AGGRO])

        self.ebon_escape_utility: CustomSkillUtilityBase = EbonEscapeUtility(event_bus=self.event_bus, current_build=in_game_build)

        self.finish_him_utility: CustomSkillUtilityBase = FinishHimUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.necrosis_utility,
            self.discord_utility,
            self.cultists_fervor,

            self.animate_bone_fiend_utility,
            self.animate_bone_horror_utility,
            self.animate_vampiric_horror_utility,
            self.animate_shambling_horror_utility,
            self.blood_of_the_master_utility,

            self.great_dwarf_weapon_utility,
            self.breath_of_the_great_dwarf_utility,
            self.foul_feast_utility,

            self.cry_of_pain_utility,
            self.cry_of_frustration_utility,
            self.power_drain_utility,

            self.mistrust_utility,
            self.unnatural_signet_utility,
            self.ether_nightmare_kurz_utility,
            self.ether_nightmare_lux_utility,
            self.suffering_utility,
            self.shatter_hex_utility,
            self.shatter_enchantment_utility,
            self.drain_enchantment_utility,

            self.energy_surge_utility,
            self.overload_utility,
            self.chaos_storm_utility,
            self.wastrels_demise_utility,
            self.spiritual_pain_utility,
            self.feast_of_corruption_utility,
            self.Signet_of_Corruption_luxon_utility,
            self.Signet_of_Corruption_kurzick_utility,

            self.energy_tap_utility,
            self.fall_back_utility,
            self.arcane_echo_utility,
            self.auspicious_incantation_utility,

            self.ebon_battle_standard_of_honor_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.signet_of_lost_souls_utility,
            self.by_urals_hammer_utility,
            self.air_of_superiority_utility,
            self.ebon_escape_utility,
            self.finish_him_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.feast_of_corruption_utility.custom_skill,
            self.necrosis_utility.custom_skill,
            self.signet_of_lost_souls_utility.custom_skill,
        ]
