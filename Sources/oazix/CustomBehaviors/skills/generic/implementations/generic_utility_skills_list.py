from Py4GWCoreLib.enums_src.Model_enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.signet_of_capture_utility import Signet_of_Capture_Stub
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import \
    MinionInvocationFromCorpseUtility
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


class GenericUtilitySkillsList:
    def __init__(self):
        pass
    
    @staticmethod
    def get_generic_utility_skills_list(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        skills: list[CustomSkillUtilityBase] = []

        skills.append(StubUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Capture"), current_build=in_game_build))
        
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Flesh_of_My_Flesh"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Return"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrect"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Chant"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Signet"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Rebirth"), current_build=in_game_build))

        # Spirit Section
        ## Ritualist generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Vampirism"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.VAMPIRISM))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Agony"), current_build=in_game_build, score_definition=ScoreStaticDefinition(30), owned_spirit_model_id=SpiritModelID.AGONY))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Bloodsong"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.BLOODSONG))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Shadowsong"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.SHADOWSONG))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Pain"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.PAIN))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Disenchantment"), current_build=in_game_build, score_definition=ScoreStaticDefinition(49), owned_spirit_model_id=SpiritModelID.DISENCHANTMENT))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Anguish"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.ANGUISH))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Restoration"), current_build=in_game_build, score_definition=ScoreStaticDefinition(CommonScore.GENERIC_SKILL_HERO_AI.value), owned_spirit_model_id=SpiritModelID.RESTORATION)) # intentionally below hero ai util
        ## PVE generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Winds"), current_build=in_game_build, score_definition=ScoreStaticDefinition(10), owned_spirit_model_id=SpiritModelID.WINDS))
        ## Ranger Generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Winter"), current_build=in_game_build, score_definition=ScoreStaticDefinition(20), owned_spirit_model_id=SpiritModelID.WINTER))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Quickening_Zephyr"), current_build=in_game_build, score_definition=ScoreStaticDefinition(20), owned_spirit_model_id=SpiritModelID.QUICKENING_ZEPHYR))

        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Shambling_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Fiend"), current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Vampiric_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(MinionInvocationFromCorpseUtility(event_bus=event_bus, skill=CustomSkill("Animate_Bone_Minions"), current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))

        # PVE SKILLS SECTION
        skills.append(SignetOfCorruptionUtility(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Corruption_luxon"),
            current_build=in_game_build))
        skills.append(SignetOfCorruptionUtility(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Corruption_kurzick"),
            current_build=in_game_build))
        skills.append(EtherNightmareUtility(event_bus=event_bus, current_build=in_game_build, skill=CustomSkill("Ether_Nightmare_luxon")))
        skills.append(EtherNightmareUtility(event_bus=event_bus, current_build=in_game_build, skill=CustomSkill("Ether_Nightmare_kurzick")))
        skills.append(SummonSpiritUtility(event_bus=event_bus, skill=CustomSkill("Summon_Spirits_kurzick"), current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
        skills.append(SummonSpiritUtility(event_bus=event_bus, skill=CustomSkill("Summon_Spirits_luxon"), current_build=in_game_build, score_definition=ScoreStaticDefinition(25)))
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
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Elemental_Lord_kurzick"), current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Elemental_Lord_luxon"), current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Aura_of_Holy_Might_kurzick"), current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Aura_of_Holy_Might_luxon"), current_build=in_game_build,
                                              score_definition=ScoreStaticDefinition(25), mana_required_to_cast=10,
                                              allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]))

        # Shouts Section
        # Really should be limited to imbagon but whatever
        skills.append(WatchYourselfPowerbatteryUtility(
            event_bus=event_bus,
            current_build=in_game_build))

        return skills
