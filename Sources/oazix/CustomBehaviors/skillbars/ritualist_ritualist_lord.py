from typing import override

from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Sources.oazix.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_spirit_utility import ProtectiveSpiritUtility
from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility
from Sources.oazix.CustomBehaviors.skills.monk.strength_of_honor_utility import StrengthOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.armor_of_unfeeling_utility import ArmorOfUnfeelingUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.summon_spirit_utility import SummonSpiritUtility

class RitualistRitualistLord_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.ritual_lord_utility: CustomSkillUtilityBase = StubUtility(event_bus=self.event_bus, skill=CustomSkill("Ritual_Lord"), current_build=in_game_build) # spirit skills should cast ritual lord themselves

        self.boon_of_creation_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Boon_of_Creation"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85), renew_before_expiration_in_milliseconds=1800, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.shelter_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Shelter"), current_build=in_game_build, score_definition=ScoreStaticDefinition(66), owned_spirit_model_id=SpiritModelID.SHELTER)
        self.union_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Union"), current_build=in_game_build, score_definition=ScoreStaticDefinition(65), owned_spirit_model_id=SpiritModelID.UNION)
        self.displacement_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Displacement"), current_build=in_game_build, score_definition=ScoreStaticDefinition(64), owned_spirit_model_id=SpiritModelID.DISPLACEMENT)
        self.armor_of_unfeeling_utility: CustomSkillUtilityBase = ArmorOfUnfeelingUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(80))

        # optional
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(0))

        # common
        self.spirits_gift_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Spirits_Gift"), current_build=in_game_build, score_definition=ScoreStaticDefinition(75), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
    
    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        skills = [
            self.ritual_lord_utility,
            self.boon_of_creation_utility,
            self.shelter_utility,
            self.union_utility,
            self.displacement_utility,
            # self.summon_spirit_kurzick,
            # self.summon_spirit_luxon,
            self.armor_of_unfeeling_utility,
            self.breath_of_the_great_dwarf_utility,
            self.spirits_gift_utility,
        ]
        return skills

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.ritual_lord_utility.custom_skill,
        ]
