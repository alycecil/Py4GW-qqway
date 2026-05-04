from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.ether_nightmare_utility import EtherNightmareUtility
from Sources.oazix.CustomBehaviors.skills.monk.cure_hex_utility import CureHexUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_corruption_utility import SignetOfCorruptionUtility
from Sources.oazix.CustomBehaviors.skills.paragon.save_yourselves_utility import SaveYourSelfKurzUtility, SaveYourSelfLuxonUtility
from Sources.oazix.CustomBehaviors.skills.paragon.spear_of_fury_utility import LuxAttackNearestEnemyHasConditionUtility, KurzAttackNearestEnemyHasConditionUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.summon_spirit_utility import SummonSpiritUtility


class PveSkillsProvider:
    """
    Provider for PvE-specific utility skills.
    These skills are only available in PvE content and include faction-specific skills.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of PvE utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of PvE utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
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
        
        return skills
