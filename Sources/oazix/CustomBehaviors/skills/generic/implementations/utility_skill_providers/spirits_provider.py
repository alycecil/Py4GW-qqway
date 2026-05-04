from Py4GWCoreLib.enums_src.Model_enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.raw_spirit_utility import RawSpiritUtility


class SpiritsProvider:
    """
    Provider for spirit utility skills.
    These skills create spirits that provide various effects on the battlefield.
    """
    
    @staticmethod
    def get_skills(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        """
        Get list of spirit utility skills.
        
        Args:
            event_bus: Event bus for communication
            in_game_build: Current build configuration
            
        Returns:
            List of spirit utility skills
        """
        skills: list[CustomSkillUtilityBase] = []
        
        # Ritualist generics
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
        
        # PVE generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Winds"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(10),
                                       owned_spirit_model_id=SpiritModelID.WINDS))
        
        # Ranger Generics
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Winter"), current_build=in_game_build,
                                       score_definition=ScoreStaticDefinition(20),
                                       owned_spirit_model_id=SpiritModelID.WINTER))
        
        return skills
