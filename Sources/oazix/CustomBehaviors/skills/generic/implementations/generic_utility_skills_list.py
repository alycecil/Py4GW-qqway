from Py4GWCoreLib import Agent, Player, GLOBAL_CACHE
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.enums_src.Model_enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.distance_factors import DistanceFactors_Short
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.hex_factors import Simple_Hex_Factors
from Sources.oazix.CustomBehaviors.primitives.scores.score_factors.target_type_factors import \
    target_type_factor_DefaultScoreFactors
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.dervich.dervich_enchantment_utility import DervichEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.dervich.imbue_health_utility import ImbueHealthUtility
from Sources.oazix.CustomBehaviors.skills.dervich.vow_of_revolution_utility import \
    Vow_of_Revolution_KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.apply_hex_simple_utility import ApplyHexCommonUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import \
    MinionInvocationFromCorpseUtility
from Sources.oazix.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import MinionInvocationFromCorpseUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_targeted_utility import \
    ProtectiveShoutTargetedUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_utility import RawSimpleHealUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_party_heal_utility import RawSimplePartyHealUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_spirit_utility import RawSpiritUtility
from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.ether_nightmare_utility import EtherNightmareUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_corruption_utility import SignetOfCorruptionUtility
from Sources.oazix.CustomBehaviors.skills.paragon.save_yourselves_utility import SaveYourSelfKurzUtility, \
    SaveYourSelfLuxonUtility
from Sources.oazix.CustomBehaviors.skills.paragon.spear_of_fury_utility import LuxAttackNearestEnemyHasConditionUtility, \
    KurzAttackNearestEnemyHasConditionUtility
from Sources.oazix.CustomBehaviors.skills.paragon.watch_yourself_utility import WatchYourselfPowerbatteryUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.summon_spirit_utility import SummonSpiritUtility

from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility
from Sources.oazix.CustomBehaviors.skills.pve.junundu_bite_utility import JunundoBiteUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuums_rest_utility import DhuumsRestUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.ghostly_fury_utility import GhostlyFuryUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.reversal_of_death_utility import ReversalOfDeathUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.encase_skeletal_utility import EncaseSkeletalUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.spiritual_healing_utility import SpiritualHealingUtility

class GenericUtilitySkillsList:
    '''
    This class is a factory for generic utility skills.
    It is not meant to be used directly.
    Thoses skills are automatically added to the utility skillbar if the build is set to complete the build with generic skills.
    '''
    def __init__(self):
        pass

    @staticmethod
    def get_generic_utility_skills_list(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        skills: list[CustomSkillUtilityBase] = []

        GenericUtilitySkillsList.intentionalStubs(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.resurrectionSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.spirits(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.necromancerSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.monkSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.paragonSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.mesmerSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.warriorSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.dervishSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.assassinSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.elementalistSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.ranger_skills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.pveSkills(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.junundu(event_bus, in_game_build, skills)

        GenericUtilitySkillsList.dhuumSkele(event_bus, in_game_build, skills)

        return skills

    @staticmethod
    def necromancerSkills(event_bus, in_game_build, skills):
        skills.append(
            MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Shambling_Horror"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Fiend"),
                                                        current_build=in_game_build,
                                                        score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Horror"),
                                                        current_build=in_game_build,
                                                        score_definition=ScoreStaticDefinition(25)))
        skills.append(
            MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Vampiric_Horror"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Minions"),
                                                        current_build=in_game_build,
                                                        score_definition=ScoreStaticDefinition(25)))

    @staticmethod
    def pveSkills(event_bus, in_game_build, skills):
        # PVE SKILLS SECTION
        skills.append(SignetOfCorruptionUtility(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Corruption_luxon"),
            current_build=in_game_build))
        skills.append(SignetOfCorruptionUtility(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Corruption_kurzick"),
            current_build=in_game_build))
        skills.append(EtherNightmareUtility(event_bus=event_bus, current_build=in_game_build,
                                            skill=CustomSkill("Ether_Nightmare_luxon")))
        skills.append(EtherNightmareUtility(event_bus=event_bus, current_build=in_game_build,
                                            skill=CustomSkill("Ether_Nightmare_kurzick")))
        skills.append(SummonSpiritUtility(event_bus=event_bus, skill=CustomSkill("Summon_Spirits_kurzick"),
                                          current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(SummonSpiritUtility(event_bus=event_bus, skill=CustomSkill("Summon_Spirits_luxon"),
                                          current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(KurzAttackNearestEnemyHasConditionUtility(
            event_bus=event_bus,
            current_build=in_game_build))
        skills.append(LuxAttackNearestEnemyHasConditionUtility(
            event_bus=event_bus,
            current_build=in_game_build))
        skills.append(SaveYourSelfLuxonUtility(
            event_bus=event_bus,
            current_build=in_game_build))
        skills.append(SaveYourSelfKurzUtility(
            event_bus=event_bus,
            current_build=in_game_build))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, current_build=in_game_build,
                                              skill=CustomSkill("Selfless_Spirit_luxon"),
                                              score_definition=ScoreStaticDefinition(20)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, current_build=in_game_build,
                                              skill=CustomSkill("Selfless_Spirit_kurzick"),
                                              score_definition=ScoreStaticDefinition(20)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Elemental_Lord_kurzick"),
                                              current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO,
                                                              BehaviorState.FAR_FROM_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Elemental_Lord_luxon"),
                                              current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO,
                                                              BehaviorState.FAR_FROM_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Aura_of_Holy_Might_kurzick"),
                                              current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Aura_of_Holy_Might_luxon"),
                                              current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Air_of_Superiority"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(30),
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("I_Am_the_Strongest"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(90),
                                              allowed_states=[BehaviorState.IN_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Dwarven_Stability"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(95),
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO,
                                                              BehaviorState.FAR_FROM_AGGRO]))

        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, current_build=in_game_build,
                                              skill=CustomSkill("Summon_Ice_Imp"),
                                              score_definition=ScoreStaticDefinition(10)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, current_build=in_game_build,
                                              skill=CustomSkill("Summon_Mursaat"),
                                              score_definition=ScoreStaticDefinition(10)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, current_build=in_game_build,
                                              skill=CustomSkill("Summon_Naga_Shaman"),
                                              score_definition=ScoreStaticDefinition(10)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, current_build=in_game_build,
                                              skill=CustomSkill("Summon_Ruby_Djinn"),
                                              score_definition=ScoreStaticDefinition(10)))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Brawling_Headbutt"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
            within_range=Range.Adjacent
        ))

    @staticmethod
    def monkSkills(event_bus, in_game_build, skills):
        # monk
        skills.append(RawSimplePartyHealUtility(event_bus=event_bus, skill=CustomSkill("Divine_Healing"),
                                                current_build=in_game_build,
                                                score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(RawSimplePartyHealUtility(event_bus=event_bus, skill=CustomSkill("Heavens_Delight"),
                                                current_build=in_game_build,
                                                score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Patient_Spirit"), current_build=in_game_build,
                                 score_definition=ScorePerHealthGravityDefinition(1))
        )
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Healing_Burst"), current_build=in_game_build,
                                 score_definition=ScorePerHealthGravityDefinition(1))
        )
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Orison_of_Healing"), current_build=in_game_build,
                                 score_definition=ScorePerHealthGravityDefinition(3))
        )
        skills.append(
            RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Balthazars_Pendulum"), current_build=in_game_build,
                                 mana_required_to_cast=20,
                                 score_definition=ScorePerHealthGravityDefinition(0.75))
        )

    @staticmethod
    def paragonSkills(event_bus, in_game_build, skills):
        # paragon
        skills.append(ProtectiveShoutUtility(
            event_bus=event_bus, skill=CustomSkill("Stand_Your_Ground"), current_build=in_game_build,
            allies_health_less_than_percent=0.99, allies_quantity_required=1,
            score_definition=ScoreStaticDefinition(88),
            allowed_states=[BehaviorState.IN_AGGRO])
        )
        skills.append(ProtectiveShoutTargetedUtility(
            event_bus=event_bus, skill=CustomSkill("Angelic_Bond"), current_build=in_game_build,
            allies_health_less_than_percent=0.5, allies_quantity_required=1,
            score_definition=ScoreStaticDefinition(60),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO,
                            BehaviorState.IDLE])
        )
        skills.append(ProtectiveShoutTargetedUtility(
            event_bus=event_bus, skill=CustomSkill("Help_Me"), current_build=in_game_build,
            allies_health_less_than_percent=0.7, allies_quantity_required=1,
            score_definition=ScoreStaticDefinition(88),
            allowed_states=[BehaviorState.IN_AGGRO])
        )
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Aggressive_Refrain"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO]),
        )
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Anthem_of_Fury"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=5000,  # cast as quick as we can even if we dontt use it
            allowed_states=[BehaviorState.IN_AGGRO]),
        )

        spear_distance_factor = DistanceFactors_Short(touch=5, adjacent=4, nearby=3, area=2, twice_area=1.5, earshot=1)
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Barbed_Spear"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            distance_factor=spear_distance_factor,
            within_range=Range.Earshot,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: not Agent.IsBleeding(agent_id)
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Spear_of_Lightning"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            distance_factor=spear_distance_factor,
            within_range=Range.Earshot,
            ignore_spirits=True
        ))

    @staticmethod
    def mesmerSkills(event_bus, in_game_build, skills):
        # mesmer
        skills.append(ApplyHexCommonUtility(
            event_bus=event_bus, skill=CustomSkill("Shrinking_Armor"), current_build=in_game_build,
        ))
        skills.append(ApplyHexCommonUtility(
            event_bus=event_bus, skill=CustomSkill("Empathy"), current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 10),
            hex_factor=Simple_Hex_Factors(not_hexed_factor=20, already_hexed_factor=-5, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=-15.0, non_caster_factor=10)
        ))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, current_build=in_game_build,
                                              skill=CustomSkill("Mantra_of_Frost"),
                                              score_definition=ScoreStaticDefinition(60)))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Disruption"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80),
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsCasting(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.33, # only skills that are longer than 1s. too much changes to fail otherwise
            distance_factor=DistanceFactors_Short()
        ))

    @staticmethod
    def intentionalStubs(event_bus, in_game_build, skills):
        skills.append(
            StubUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Capture"), current_build=in_game_build))

    @staticmethod
    def dervishSkills(event_bus, in_game_build, skills):
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, current_build=in_game_build,
            skill=CustomSkill("Vital_Boon"),
            score_definition=ScoreStaticDefinition(15),
            renew_before_expiration_in_milliseconds=0,
            target_self=False, # no need
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ))
        skills.append(Vow_of_Revolution_KeepSelfEffectUpUtility(
            event_bus=event_bus, current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15),
        ))
        skills.append(ImbueHealthUtility(
            event_bus=event_bus, current_build=in_game_build,
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Dust_Cloak"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(11),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Intimidating_Aura"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Staggering_Force"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(11),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Hearth_of_Holy_Flame"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Sand_Shards"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Mirage_Cloak"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))
        skills.append(DervichEnchantmentUtility(
            event_bus=event_bus, skill=CustomSkill("Rending_Aura"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(10),
            renew_before_expiration_in_milliseconds=0
        ))

    @staticmethod
    def warriorSkills(event_bus, in_game_build, skills):
        # Warrior Things
        skills.append(RawSimpleAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Renewing_Smash"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(75),
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsKnockedDown(agent_id) and Utils.Distance(
                Player.GetXY(), Agent.GetXY(agent_id)) < Range.Adjacent.value
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Soldiers_Strike"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 12 if enemy_qte >= 3 else 10),
            distance_factor=DistanceFactors_Short()
        ))
        # Warrior # AOE
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Whirlwind_Attack"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 69 if enemy_qte >= 3 else 63 if enemy_qte == 2 else 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Crude_Swing"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 68 if enemy_qte >= 3 else 62 if enemy_qte == 2 else 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Earth_Shaker"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 71 if enemy_qte >= 3 else 70 if enemy_qte == 2 else 50),
            mana_required_to_cast=0,
            ignore_spirits=True,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Distracting_Blow"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 70.1 if enemy_qte >= 3 else 63.1 if enemy_qte == 2 else 50),
            mana_required_to_cast=0,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsCasting(agent_id),
            within_range=Range.Adjacent
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Yeti_Smash"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 6 if enemy_qte >= 3 else 1 if enemy_qte == 2 else 0),
            mana_required_to_cast=0,
            ignore_spirits=True,
            custom_agent_targeting_predicate=lambda agent_id: Agent.IsConditioned(agent_id),
            within_range=Range.Adjacent
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("For_Great_Justice"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15), mana_required_to_cast=9,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO],
            target_self=False,
        ))
        # Shouts Section
        # Really should be limited to imbagon but whatever
        skills.append(WatchYourselfPowerbatteryUtility(
            event_bus=event_bus,
            current_build=in_game_build))

    @staticmethod
    def dhuumSkele(event_bus, in_game_build, skills):
        # Dhuum phase
        skills.append(SpiritualHealingUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(ReversalOfDeathUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(DhuumsRestUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(GhostlyFuryUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(EncaseSkeletalUtility(event_bus=event_bus, current_build=in_game_build))

    @staticmethod
    def junundu(event_bus, in_game_build, skills):
        # naive JUNUNDU version
        skills.append(RawSimpleAttackUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Strike"),
                                             current_build=in_game_build, score_definition=ScoreStaticDefinition(65)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Tunnel"),
                                              current_build=in_game_build, score_definition=ScoreStaticDefinition(67),
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO,
                                                              BehaviorState.FAR_FROM_AGGRO]))
        skills.append(
            RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Blinding_Breath"), current_build=in_game_build,
                                score_definition=ScorePerAgentQuantityDefinition(
                                    lambda enemy_qte: 70 if enemy_qte >= 2 else 69)))
        skills.append(RawSimpleAttackUtility(event_bus=event_bus, skill=CustomSkill("Burning_Breath"),
                                             current_build=in_game_build, score_definition=ScoreStaticDefinition(70),
                                             custom_agent_targeting_predicate=lambda agent_id: Utils.Distance(
                                                 Player.GetXY(), Agent.GetXY(agent_id)) > Range.Nearby.value))
        skills.append(
            RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Choking_Breath"), current_build=in_game_build,
                                score_definition=ScorePerAgentQuantityDefinition(
                                    lambda enemy_qte: 70 if enemy_qte >= 2 else 69),
                                custom_agent_targeting_predicate=lambda agent_id: Agent.IsCasting(agent_id)))
        skills.append(StubUtility(event_bus=event_bus, skill=CustomSkill("Leave_Junundu"), current_build=in_game_build))
        skills.append(
            StubUtility(event_bus=event_bus, skill=CustomSkill("Unknown_Junundu_Ability"), current_build=in_game_build))
        skills.append(
            RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Siege"), current_build=in_game_build,
                                score_definition=ScorePerAgentQuantityDefinition(
                                    lambda enemy_qte: 80 if enemy_qte >= 2 else 79),
                                custom_agent_targeting_predicate=lambda agent_id: Utils.Distance(Player.GetXY(),
                                                                                                 Agent.GetXY(
                                                                                                     agent_id)) > Range.Nearby.value))

    @staticmethod
    def ranger_skills(event_bus, in_game_build, skills):
        # Ranger Things
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Run_as_One"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Apply_Poison"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(15), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Never_Rampage_Alone"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Call_of_Protection"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80), mana_required_to_cast=5,
            renew_before_expiration_in_milliseconds=130,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Call_of_Haste"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(80), mana_required_to_cast=15,
            renew_before_expiration_in_milliseconds=130,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Predatory_Bond"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(40), mana_required_to_cast=20,
            renew_before_expiration_in_milliseconds=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        skills.append(RawAoeAttackUtility(
            event_bus=event_bus,
            skill=CustomSkill("Throw_Dirt"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 21 if enemy_qte >= 3 else 15 if enemy_qte == 2 else 10),
            mana_required_to_cast=0,
            ignore_spirits=True,
            hex_factor=Simple_Hex_Factors(not_hexed_factor=0, already_hexed_factor=1, already_hexed_maxed=None),
            target_type_factor=target_type_factor_DefaultScoreFactors(caster_factor=-15.0, non_caster_factor=10),
            distance_factor=DistanceFactors_Short(touch=40.0),
        ))
        # Quickening_Zephyr QZ
        qz_util = RawSpiritUtility(
            event_bus=event_bus, skill=CustomSkill("Quickening_Zephyr"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(85),
            owned_spirit_model_id=SpiritModelID.QUICKENING_ZEPHYR,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        )
        serpents_quickness_prep_utility: CustomSkillUtilityBase = PreparationUtility(
            event_bus=event_bus,
            prep_skill=CustomSkill("Serpents_Quickness"),
            target_utilities=[
                qz_util,
            ],
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(94)
        )
        skills.append(qz_util)
        skills.append(serpents_quickness_prep_utility)

    @staticmethod
    def spirits(event_bus, in_game_build, skills):
        # Spirit Section
        ## Ritualist generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Vampirism"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(50),
                                       owned_spirit_model_id=SpiritModelID.VAMPIRISM))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Agony"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(30),
                                       owned_spirit_model_id=SpiritModelID.AGONY))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Bloodsong"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(50),
                                       owned_spirit_model_id=SpiritModelID.BLOODSONG))
        skills.append(
            RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Shadowsong"), current_build=in_game_build,
                             score_definition=ScoreStaticDefinition(50),
                             owned_spirit_model_id=SpiritModelID.SHADOWSONG))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Pain"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(50),
                                       owned_spirit_model_id=SpiritModelID.PAIN))
        skills.append(
            RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Disenchantment"), current_build=in_game_build,
                             score_definition=ScoreStaticDefinition(49),
                             owned_spirit_model_id=SpiritModelID.DISENCHANTMENT))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Anguish"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(50),
                                       owned_spirit_model_id=SpiritModelID.ANGUISH))
        skills.append(
            RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Restoration"), current_build=in_game_build,
                             score_definition=ScoreStaticDefinition(CommonScore.GENERIC_SKILL_HERO_AI.value),
                             owned_spirit_model_id=SpiritModelID.RESTORATION))  # intentionally below hero ai util
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Recovery"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(10),
                                       owned_spirit_model_id=SpiritModelID.RECOVERY))
        ## PVE generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Winds"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(10),
                                       owned_spirit_model_id=SpiritModelID.WINDS))
        ## Ranger Generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Winter"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(20),
                                       owned_spirit_model_id=SpiritModelID.WINTER))

    @staticmethod
    def resurrectionSkills(event_bus, in_game_build, skills):
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Flesh_of_My_Flesh"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Return"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrect"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Chant"),
                                                 current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Signet"),
                                                 current_build=in_game_build))
        skills.append(
            GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Rebirth"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Sunspear_Rebirth_Signet"),
                                                 current_build=in_game_build))

    @classmethod
    def assassinSkills(cls, event_bus, in_game_build, skills):
        jagged_strike_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=event_bus, skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        fox_fangs_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=event_bus, skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        death_blossom_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=event_bus, skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        skills.append(jagged_strike_utility)
        skills.append(fox_fangs_utility)
        skills.append(death_blossom_utility)
        pass

    @classmethod
    def elementalistSkills(cls, event_bus, in_game_build, skills):
        skills.append(KeepSelfEffectUpUtility(
            event_bus=event_bus, skill=CustomSkill("Aura_of_Restoration"), current_build=in_game_build,
            score_definition=ScoreStaticDefinition(40), mana_required_to_cast=7,
            renew_before_expiration_in_milliseconds=250,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
            target_self=False,
            after_cast_delay=False,
        ))
        pass
